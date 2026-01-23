"""Core codebase indexing functionality."""

import os
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import fnmatch

try:
    from gitignore_parser import parse_gitignore
    GITIGNORE_AVAILABLE = True
except ImportError:
    GITIGNORE_AVAILABLE = False

from .parsers import CodeParser, Symbol
from .cache import IndexCache


class CodebaseIndexer:
    """Indexes a codebase for fast searching."""

    # Common directories to ignore
    DEFAULT_IGNORE_DIRS = {
        ".git", ".svn", ".hg",
        "node_modules", "venv", "env", ".venv", ".env",
        "__pycache__", ".pytest_cache",
        "dist", "build", ".eggs", "*.egg-info",
        ".idea", ".vscode",
        "target",  # Rust
        "vendor",  # Go
    }

    # File extensions to index
    DEFAULT_EXTENSIONS = {
        ".py", ".js", ".jsx", ".ts", ".tsx",
        ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp",
        ".rb", ".php", ".cs", ".swift", ".kt",
        ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
    }

    def __init__(self, cache: Optional[IndexCache] = None):
        """Initialize the indexer.

        Args:
            cache: Optional cache instance. If None, creates a new one.
        """
        self.parser = CodeParser()
        self.cache = cache or IndexCache()

    def should_ignore(self, path: Path, root: Path, gitignore_matcher=None) -> bool:
        """Check if a path should be ignored.

        Args:
            path: Path to check
            root: Root directory of the codebase
            gitignore_matcher: Optional gitignore matcher function

        Returns:
            True if the path should be ignored
        """
        # Check against default ignore patterns
        parts = path.relative_to(root).parts
        for part in parts:
            if part in self.DEFAULT_IGNORE_DIRS:
                return True
            for pattern in self.DEFAULT_IGNORE_DIRS:
                if fnmatch.fnmatch(part, pattern):
                    return True

        # Check gitignore
        if gitignore_matcher and GITIGNORE_AVAILABLE:
            try:
                if gitignore_matcher(str(path)):
                    return True
            except Exception:
                pass

        return False

    def collect_files(self, root: Path) -> List[Path]:
        """Collect all files to index.

        Args:
            root: Root directory of the codebase

        Returns:
            List of file paths to index
        """
        files = []
        root = Path(root).resolve()

        # Try to parse .gitignore
        gitignore_matcher = None
        gitignore_path = root / ".gitignore"
        if GITIGNORE_AVAILABLE and gitignore_path.exists():
            try:
                gitignore_matcher = parse_gitignore(str(gitignore_path))
            except Exception as e:
                print(f"Warning: Failed to parse .gitignore: {e}")

        # Walk the directory tree
        for dirpath, dirnames, filenames in os.walk(root):
            current_path = Path(dirpath)

            # Filter out ignored directories (modify in-place to affect os.walk)
            dirnames[:] = [
                d for d in dirnames
                if not self.should_ignore(current_path / d, root, gitignore_matcher)
            ]

            # Collect files with supported extensions
            for filename in filenames:
                file_path = current_path / filename
                ext = file_path.suffix.lower()

                if ext in self.DEFAULT_EXTENSIONS:
                    if not self.should_ignore(file_path, root, gitignore_matcher):
                        files.append(file_path)

        return files

    def index_file(self, file_path: Path) -> Dict[str, Any]:
        """Index a single file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing file metadata and symbols
        """
        try:
            # Parse symbols
            symbols = self.parser.parse_file(str(file_path))

            # Get file stats
            stats = file_path.stat()

            return {
                "path": str(file_path),
                "size": stats.st_size,
                "modified": stats.st_mtime,
                "symbols": [
                    {
                        "name": s.name,
                        "type": s.type,
                        "line": s.line,
                        "column": s.column,
                        "end_line": s.end_line,
                        "end_column": s.end_column,
                    }
                    for s in symbols
                ],
            }

        except Exception as e:
            print(f"Warning: Failed to index {file_path}: {e}")
            return {
                "path": str(file_path),
                "error": str(e),
                "symbols": [],
            }

    def index_codebase(
        self,
        path: Path,
        force_reindex: bool = False,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """Index an entire codebase.

        Args:
            path: Root path of the codebase
            force_reindex: Force re-indexing even if cache exists
            max_workers: Number of parallel workers for indexing

        Returns:
            Dictionary containing the complete index
        """
        path = Path(path).resolve()

        # Check cache first
        if not force_reindex:
            cached = self.cache.get(path)
            if cached:
                print(f"Using cached index for {path}")
                return cached.get("index", {})

        print(f"Indexing codebase at {path}...")

        # Collect files
        files = self.collect_files(path)
        print(f"Found {len(files)} files to index")

        # Index files in parallel
        file_indices = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.index_file, f): f for f in files}

            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result()
                    file_indices.append(result)
                except Exception as e:
                    print(f"Error indexing {file_path}: {e}")

        # Build the complete index
        index = {
            "root": str(path),
            "total_files": len(file_indices),
            "files": file_indices,
            "symbol_count": sum(len(f.get("symbols", [])) for f in file_indices),
        }

        # Cache the index
        self.cache.set(path, index)

        print(f"Indexed {index['total_files']} files with {index['symbol_count']} symbols")

        return index

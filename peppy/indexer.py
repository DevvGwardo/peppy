"""Core codebase indexing functionality."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import fnmatch

try:
    from gitignore_parser import parse_gitignore
    GITIGNORE_AVAILABLE = True
except ImportError:
    GITIGNORE_AVAILABLE = False

from .parsers import CodeParser
from .cache import IndexCache


class CodebaseIndexer:
    """Indexes a codebase for fast searching."""

    DEFAULT_IGNORE_DIRS = {
        ".git", ".svn", ".hg",
        "node_modules", "venv", "env", ".venv", ".env",
        "__pycache__", ".pytest_cache",
        "dist", "build", ".eggs", "*.egg-info",
        ".idea", ".vscode",
        "target",
        "vendor",
    }

    DEFAULT_EXTENSIONS = {
        ".py", ".js", ".jsx", ".ts", ".tsx",
        ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp",
        ".rb", ".php", ".cs", ".swift", ".kt",
        ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
    }

    def __init__(self, cache: Optional[IndexCache] = None):
        self.parser = CodeParser()
        self.cache = cache or IndexCache()
        self._ignore_exact = {p for p in self.DEFAULT_IGNORE_DIRS if "*" not in p and "?" not in p and "[" not in p}
        self._ignore_globs = [p for p in self.DEFAULT_IGNORE_DIRS if p not in self._ignore_exact]

    def _is_ignored_part(self, part: str) -> bool:
        if part in self._ignore_exact:
            return True
        return any(fnmatch.fnmatch(part, pattern) for pattern in self._ignore_globs)

    def should_ignore(self, path: Path, root: Path, gitignore_matcher=None) -> bool:
        try:
            relative = path.relative_to(root)
        except ValueError:
            return True

        for part in relative.parts:
            if self._is_ignored_part(part):
                return True

        if gitignore_matcher and GITIGNORE_AVAILABLE:
            try:
                if gitignore_matcher(relative.as_posix()):
                    return True
            except Exception:
                pass

        return False

    def collect_files(self, root: Path) -> List[Path]:
        files: List[Path] = []
        root = Path(root).resolve()

        gitignore_matcher = None
        gitignore_path = root / ".gitignore"
        if GITIGNORE_AVAILABLE and gitignore_path.exists():
            try:
                gitignore_matcher = parse_gitignore(str(gitignore_path))
            except Exception as e:
                print(f"Warning: Failed to parse .gitignore: {e}")

        for dirpath, dirnames, filenames in os.walk(root):
            current_path = Path(dirpath)
            dirnames[:] = [
                d for d in dirnames
                if not self.should_ignore(current_path / d, root, gitignore_matcher)
            ]

            for filename in filenames:
                file_path = current_path / filename
                if file_path.suffix.lower() in self.DEFAULT_EXTENSIONS and not self.should_ignore(file_path, root, gitignore_matcher):
                    files.append(file_path)

        return files

    def index_file(self, file_path: Path) -> Dict[str, Any]:
        try:
            symbols = self.parser.parse_file(str(file_path))
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
            return {"path": str(file_path), "error": str(e), "symbols": []}

    def index_codebase(
        self,
        path: Path,
        force_reindex: bool = False,
        max_workers: Optional[int] = None,
    ) -> Dict[str, Any]:
        path = Path(path).resolve()

        if not force_reindex:
            cached = self.cache.get(path)
            if cached:
                print(f"Using cached index for {path}")
                return cached.get("index", {})

        print(f"Indexing codebase at {path}...")
        files = self.collect_files(path)
        print(f"Found {len(files)} files to index")

        workers = max_workers if max_workers and max_workers > 0 else min(32, max(2, (os.cpu_count() or 4) * 2))

        file_indices: List[Dict[str, Any]] = []
        symbol_types: Dict[str, int] = {}
        file_extensions: Dict[str, int] = {}

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.index_file, f): f for f in files}
            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result()
                    file_indices.append(result)

                    ext = Path(result.get("path", str(file_path))).suffix
                    file_extensions[ext] = file_extensions.get(ext, 0) + 1
                    for symbol in result.get("symbols", []):
                        sym_type = symbol.get("type", "unknown")
                        symbol_types[sym_type] = symbol_types.get(sym_type, 0) + 1
                except Exception as e:
                    print(f"Error indexing {file_path}: {e}")

        index = {
            "root": str(path),
            "total_files": len(file_indices),
            "files": file_indices,
            "symbol_count": sum(len(f.get("symbols", [])) for f in file_indices),
            "symbol_types": symbol_types,
            "file_extensions": file_extensions,
        }

        self.cache.set(path, index)
        print(f"Indexed {index['total_files']} files with {index['symbol_count']} symbols")
        return index

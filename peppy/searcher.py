"""Search and grep functionality for indexed codebases."""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import fnmatch

from .cache import IndexCache


class CodebaseSearcher:
    """Provides search and grep functionality over indexed codebases."""

    def __init__(self, cache: Optional[IndexCache] = None):
        """Initialize the searcher.

        Args:
            cache: Optional cache instance. If None, creates a new one.
        """
        self.cache = cache or IndexCache()

    def get_index(self, path: Path) -> Optional[Dict[str, Any]]:
        """Get the index for a codebase.

        Args:
            path: Root path of the codebase

        Returns:
            Index dictionary or None if not found
        """
        cached = self.cache.get(path)
        if cached:
            return cached.get("index")
        return None

    def search_symbols(
        self,
        codebase_path: Path,
        query: str,
        symbol_type: Optional[str] = None,
        file_pattern: Optional[str] = None,
        use_regex: bool = True,
    ) -> List[Dict[str, Any]]:
        """Search for symbols in the indexed codebase.

        Args:
            codebase_path: Root path of the codebase
            query: Search query (supports regex)
            symbol_type: Optional filter by symbol type (function, class, etc.)
            file_pattern: Optional file pattern filter (e.g., "*.py")
            use_regex: Whether to treat query as regex

        Returns:
            List of matching symbols
        """
        index = self.get_index(codebase_path)
        if not index:
            return []

        # Compile regex pattern if needed
        pattern = None
        if use_regex:
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error:
                # Invalid regex, fall back to literal search
                use_regex = False

        results = []

        for file_info in index.get("files", []):
            file_path = file_info.get("path", "")

            # Apply file pattern filter
            if file_pattern and not fnmatch.fnmatch(file_path, file_pattern):
                continue

            # Search symbols in this file
            for symbol in file_info.get("symbols", []):
                # Apply symbol type filter
                if symbol_type and symbol.get("type") != symbol_type:
                    continue

                # Check if symbol name matches query
                name = symbol.get("name", "")
                matches = False

                if use_regex and pattern:
                    matches = pattern.search(name) is not None
                else:
                    matches = query.lower() in name.lower()

                if matches:
                    results.append(
                        {
                            "name": name,
                            "type": symbol.get("type"),
                            "file": file_path,
                            "line": symbol.get("line"),
                            "column": symbol.get("column"),
                        }
                    )

        return results

    def get_file_symbols(self, codebase_path: Path, file_path: str) -> List[Dict[str, Any]]:
        """Get all symbols in a specific file.

        Args:
            codebase_path: Root path of the codebase
            file_path: Path to the file (can be relative or absolute)

        Returns:
            List of symbols in the file
        """
        index = self.get_index(codebase_path)
        if not index:
            return []

        # Normalize both paths for comparison
        file_path = str(Path(file_path).resolve())

        for file_info in index.get("files", []):
            cached_path = str(Path(file_info.get("path", "")).resolve())
            if cached_path == file_path:
                return [
                    {
                        "name": s.get("name"),
                        "type": s.get("type"),
                        "line": s.get("line"),
                        "column": s.get("column"),
                    }
                    for s in file_info.get("symbols", [])
                ]

        return []

    def grep_code(
        self,
        codebase_path: Path,
        pattern: str,
        file_pattern: Optional[str] = None,
        context_lines: int = 0,
        use_regex: bool = True,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """Perform grep search across the codebase.

        Args:
            codebase_path: Root path of the codebase
            pattern: Search pattern (supports regex)
            file_pattern: Optional file pattern filter
            context_lines: Number of context lines to include
            use_regex: Whether to treat pattern as regex
            max_results: Maximum number of results to return

        Returns:
            List of matches with context
        """
        index = self.get_index(codebase_path)
        if not index:
            return []

        # Compile regex pattern
        regex_pattern = None
        if use_regex:
            try:
                regex_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            except re.error:
                use_regex = False

        results = []
        result_count = 0

        for file_info in index.get("files", []):
            if result_count >= max_results:
                break

            file_path = file_info.get("path", "")

            # Apply file pattern filter
            if file_pattern and not fnmatch.fnmatch(file_path, file_pattern):
                continue

            # Read file and search
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                for i, line in enumerate(lines):
                    if result_count >= max_results:
                        break

                    # Check if line matches
                    matches = False
                    if use_regex and regex_pattern:
                        matches = regex_pattern.search(line) is not None
                    else:
                        matches = pattern.lower() in line.lower()

                    if matches:
                        # Get context lines
                        start_line = max(0, i - context_lines)
                        end_line = min(len(lines), i + context_lines + 1)

                        context = {
                            "before": [
                                {
                                    "line": start_line + j + 1,
                                    "content": lines[start_line + j].rstrip(),
                                }
                                for j in range(i - start_line)
                            ],
                            "match": {"line": i + 1, "content": line.rstrip()},
                            "after": [
                                {"line": i + j + 2, "content": lines[i + j + 1].rstrip()}
                                for j in range(end_line - i - 1)
                            ],
                        }

                        results.append(
                            {
                                "file": file_path,
                                "line": i + 1,
                                "context": context if context_lines > 0 else None,
                                "content": line.rstrip(),
                            }
                        )

                        result_count += 1

            except Exception as e:
                print(f"Warning: Failed to grep {file_path}: {e}")
                continue

        return results

    def get_statistics(self, codebase_path: Path) -> Dict[str, Any]:
        """Get statistics about the indexed codebase.

        Args:
            codebase_path: Root path of the codebase

        Returns:
            Dictionary with statistics
        """
        index = self.get_index(codebase_path)
        if not index:
            return {}

        # Count symbols by type
        symbol_types = {}
        file_extensions = {}

        for file_info in index.get("files", []):
            # Count file extensions
            file_path = file_info.get("path", "")
            ext = Path(file_path).suffix
            file_extensions[ext] = file_extensions.get(ext, 0) + 1

            # Count symbol types
            for symbol in file_info.get("symbols", []):
                sym_type = symbol.get("type", "unknown")
                symbol_types[sym_type] = symbol_types.get(sym_type, 0) + 1

        return {
            "root": index.get("root"),
            "total_files": index.get("total_files", 0),
            "total_symbols": index.get("symbol_count", 0),
            "symbol_types": symbol_types,
            "file_extensions": file_extensions,
        }

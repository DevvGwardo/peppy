"""Search and grep functionality for indexed codebases."""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import fnmatch

from .cache import IndexCache


class CodebaseSearcher:
    """Provides search and grep functionality over indexed codebases."""

    def __init__(self, cache: Optional[IndexCache] = None):
        self.cache = cache or IndexCache()

    def get_index(self, path: Path) -> Optional[Dict[str, Any]]:
        cached = self.cache.get(path)
        if cached:
            return cached.get("index")
        return None

    @staticmethod
    def _matches_file_pattern(file_path: str, root: Path, file_pattern: Optional[str]) -> bool:
        if not file_pattern:
            return True
        p = Path(file_path)
        rel = p
        try:
            rel = p.resolve().relative_to(root.resolve())
        except Exception:
            pass
        rel_posix = rel.as_posix()
        return (
            fnmatch.fnmatch(rel_posix, file_pattern)
            or fnmatch.fnmatch(p.name, file_pattern)
            or fnmatch.fnmatch(file_path, file_pattern)
        )

    def search_symbols(
        self,
        codebase_path: Path,
        query: str,
        symbol_type: Optional[str] = None,
        file_pattern: Optional[str] = None,
        use_regex: bool = True,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        index = self.get_index(codebase_path)
        if not index:
            return []

        pattern = None
        if use_regex:
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error:
                use_regex = False

        results = []
        query_lower = query.lower()
        root = Path(index.get("root", codebase_path))

        for file_info in index.get("files", []):
            if max_results is not None and len(results) >= max_results:
                break

            file_path = file_info.get("path", "")
            if not self._matches_file_pattern(file_path, root, file_pattern):
                continue

            for symbol in file_info.get("symbols", []):
                if max_results is not None and len(results) >= max_results:
                    break

                if symbol_type and symbol.get("type") != symbol_type:
                    continue

                name = symbol.get("name", "")
                if (use_regex and pattern and pattern.search(name)) or (not use_regex and query_lower in name.lower()):
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
        index = self.get_index(codebase_path)
        if not index:
            return []

        root = Path(index.get("root", codebase_path)).resolve()
        requested = Path(file_path)
        if not requested.is_absolute():
            requested = (root / requested).resolve()
        else:
            requested = requested.resolve()

        for file_info in index.get("files", []):
            cached_path = str(Path(file_info.get("path", "")).resolve())
            if cached_path == str(requested):
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
        index = self.get_index(codebase_path)
        if not index:
            return []

        regex_pattern = None
        if use_regex:
            try:
                regex_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            except re.error:
                use_regex = False

        pattern_lower = pattern.lower()
        results: List[Dict[str, Any]] = []
        result_count = 0
        root = Path(index.get("root", codebase_path))

        for file_info in index.get("files", []):
            if result_count >= max_results:
                break

            file_path = file_info.get("path", "")
            if not self._matches_file_pattern(file_path, root, file_pattern):
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.read().splitlines()

                for i, line in enumerate(lines):
                    if result_count >= max_results:
                        break

                    is_match = (use_regex and regex_pattern and regex_pattern.search(line) is not None) or (
                        not use_regex and pattern_lower in line.lower()
                    )
                    if not is_match:
                        continue

                    result = {
                        "file": file_path,
                        "line": i + 1,
                        "content": line,
                        "context": None,
                    }

                    if context_lines > 0:
                        start_line = max(0, i - context_lines)
                        end_line = min(len(lines), i + context_lines + 1)
                        result["context"] = {
                            "before": [
                                {"line": ln + 1, "content": lines[ln]}
                                for ln in range(start_line, i)
                            ],
                            "match": {"line": i + 1, "content": line},
                            "after": [
                                {"line": ln + 1, "content": lines[ln]}
                                for ln in range(i + 1, end_line)
                            ],
                        }

                    results.append(result)
                    result_count += 1
            except Exception as e:
                print(f"Warning: Failed to grep {file_path}: {e}")
                continue

        return results

    def get_statistics(self, codebase_path: Path) -> Dict[str, Any]:
        index = self.get_index(codebase_path)
        if not index:
            return {}

        symbol_types = index.get("symbol_types")
        file_extensions = index.get("file_extensions")

        if symbol_types is None or file_extensions is None:
            symbol_types = {}
            file_extensions = {}
            for file_info in index.get("files", []):
                ext = Path(file_info.get("path", "")).suffix
                file_extensions[ext] = file_extensions.get(ext, 0) + 1
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

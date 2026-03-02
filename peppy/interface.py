"""Peppy Interface - A unified high-level API for codebase indexing and search.

This module provides a clean interface for integrating Peppy with workflow
orchestration tools like Siggy. It offers token-efficient methods optimized
for AI-assisted development workflows.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import re

from .indexer import CodebaseIndexer
from .searcher import CodebaseSearcher
from .cache import IndexCache


class WorkflowPhase(Enum):
    """Siggy workflow phases that Peppy can optimize."""
    PLANNING = "planning"
    EXECUTION = "execution"
    VERIFICATION = "verification"


@dataclass
class SearchResult:
    """A single search result with all relevant information."""
    name: str
    type: str
    file: str
    line: int
    column: int = 0
    context: Optional[str] = None

    def to_location(self) -> str:
        """Return a compact file:line location string."""
        return f"{self.file}:{self.line}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "context": self.context,
        }


@dataclass
class GrepResult:
    """A grep search result with context."""
    file: str
    line: int
    content: str
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)

    def to_location(self) -> str:
        """Return a compact file:line location string."""
        return f"{self.file}:{self.line}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file": self.file,
            "line": self.line,
            "content": self.content,
            "context_before": self.context_before,
            "context_after": self.context_after,
        }


@dataclass
class CodebaseStats:
    """Statistics about an indexed codebase."""
    root: str
    total_files: int
    total_symbols: int
    symbol_types: Dict[str, int]
    file_extensions: Dict[str, int]

    def summary(self) -> str:
        """Return a compact summary string."""
        top_types = sorted(self.symbol_types.items(), key=lambda x: -x[1])[:5]
        top_exts = sorted(self.file_extensions.items(), key=lambda x: -x[1])[:5]

        lines = [
            f"Codebase: {self.root}",
            f"Files: {self.total_files}, Symbols: {self.total_symbols}",
            f"Top types: {', '.join(f'{t}({c})' for t, c in top_types)}",
            f"Top extensions: {', '.join(f'{e}({c})' for e, c in top_exts)}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "root": self.root,
            "total_files": self.total_files,
            "total_symbols": self.total_symbols,
            "symbol_types": self.symbol_types,
            "file_extensions": self.file_extensions,
        }


class PeppyInterface:
    """High-level interface for Peppy codebase indexing and search.

    This interface provides a unified API optimized for:
    - Siggy workflow integration (planning, execution, verification phases)
    - Token-efficient operations for AI-assisted development
    - Clean, chainable method calls

    Example usage:
        peppy = PeppyInterface()
        peppy.index("/path/to/project")

        # For planning phase
        overview = peppy.get_overview("/path/to/project")
        routes = peppy.find_symbols(".*Router", symbol_type="class")

        # For execution phase
        location = peppy.find_definition("AuthService")
        usages = peppy.find_usages("AuthService")

        # For verification phase
        stats = peppy.get_stats("/path/to/project")
    """

    def __init__(self, cache: Optional[IndexCache] = None):
        """Initialize the Peppy interface.

        Args:
            cache: Optional shared cache instance. Creates one if not provided.
        """
        self.cache = cache or IndexCache()
        self.indexer = CodebaseIndexer(self.cache)
        self.searcher = CodebaseSearcher(self.cache)
        self._current_codebase: Optional[Path] = None

    # =========================================================================
    # Core Operations
    # =========================================================================

    def index(
        self,
        path: str,
        force: bool = False,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> CodebaseStats:
        """Index a codebase for fast searching.

        Args:
            path: Path to the codebase root directory
            force: Force re-indexing even if cache exists
            on_progress: Optional callback for progress updates

        Returns:
            CodebaseStats with indexing results
        """
        codebase_path = Path(path).resolve()

        if on_progress:
            on_progress(f"Indexing {codebase_path}...")

        index = self.indexer.index_codebase(codebase_path, force_reindex=force)
        self._current_codebase = codebase_path

        return self._make_stats(index)

    def set_codebase(self, path: str) -> "PeppyInterface":
        """Set the current working codebase for subsequent operations.

        Args:
            path: Path to the codebase root directory

        Returns:
            Self for method chaining
        """
        self._current_codebase = Path(path).resolve()
        return self

    def _get_codebase(self, path: Optional[str] = None) -> Path:
        """Get the codebase path to use for operations."""
        if path:
            return Path(path).resolve()
        if self._current_codebase:
            return self._current_codebase
        raise ValueError("No codebase specified. Call index() or set_codebase() first.")

    # =========================================================================
    # Symbol Search Operations
    # =========================================================================

    def find_symbols(
        self,
        query: str,
        codebase: Optional[str] = None,
        symbol_type: Optional[str] = None,
        file_pattern: Optional[str] = None,
        limit: int = 50
    ) -> List[SearchResult]:
        """Find symbols matching a query.

        Args:
            query: Search query (supports regex)
            codebase: Optional codebase path (uses current if not specified)
            symbol_type: Filter by type (function, class, method, variable, interface, type)
            file_pattern: Filter by file pattern (e.g., "*.py", "**/*.ts")
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        codebase_path = self._get_codebase(codebase)

        results = self.searcher.search_symbols(
            codebase_path,
            query,
            symbol_type=symbol_type,
            file_pattern=file_pattern,
            use_regex=True
        )

        return [
            SearchResult(
                name=r["name"],
                type=r["type"],
                file=r["file"],
                line=r["line"],
                column=r.get("column", 0),
            )
            for r in results[:limit]
        ]

    def find_definition(
        self,
        name: str,
        codebase: Optional[str] = None
    ) -> Optional[SearchResult]:
        """Find the definition of a symbol by exact name.

        Args:
            name: Exact symbol name to find
            codebase: Optional codebase path

        Returns:
            SearchResult or None if not found
        """
        escaped = re.escape(name)
        results = self.find_symbols(f"^{escaped}$", codebase=codebase, limit=1)
        return results[0] if results else None

    def find_classes(
        self,
        query: str = ".*",
        codebase: Optional[str] = None,
        file_pattern: Optional[str] = None,
        limit: int = 50
    ) -> List[SearchResult]:
        """Find class definitions.

        Args:
            query: Search query (default matches all)
            codebase: Optional codebase path
            file_pattern: Optional file pattern filter
            limit: Maximum results

        Returns:
            List of matching class definitions
        """
        return self.find_symbols(
            query,
            codebase=codebase,
            symbol_type="class",
            file_pattern=file_pattern,
            limit=limit
        )

    def find_functions(
        self,
        query: str = ".*",
        codebase: Optional[str] = None,
        file_pattern: Optional[str] = None,
        limit: int = 50
    ) -> List[SearchResult]:
        """Find function definitions.

        Args:
            query: Search query (default matches all)
            codebase: Optional codebase path
            file_pattern: Optional file pattern filter
            limit: Maximum results

        Returns:
            List of matching function definitions
        """
        return self.find_symbols(
            query,
            codebase=codebase,
            symbol_type="function",
            file_pattern=file_pattern,
            limit=limit
        )

    def find_methods(
        self,
        query: str = ".*",
        codebase: Optional[str] = None,
        file_pattern: Optional[str] = None,
        limit: int = 50
    ) -> List[SearchResult]:
        """Find method definitions.

        Args:
            query: Search query (default matches all)
            codebase: Optional codebase path
            file_pattern: Optional file pattern filter
            limit: Maximum results

        Returns:
            List of matching method definitions
        """
        return self.find_symbols(
            query,
            codebase=codebase,
            symbol_type="method",
            file_pattern=file_pattern,
            limit=limit
        )

    # =========================================================================
    # Grep Operations
    # =========================================================================

    def grep(
        self,
        pattern: str,
        codebase: Optional[str] = None,
        file_pattern: Optional[str] = None,
        context: int = 0,
        limit: int = 100
    ) -> List[GrepResult]:
        """Search for text patterns in code.

        Args:
            pattern: Search pattern (supports regex)
            codebase: Optional codebase path
            file_pattern: Filter by file pattern
            context: Number of context lines before/after
            limit: Maximum results

        Returns:
            List of GrepResult objects
        """
        codebase_path = self._get_codebase(codebase)

        results = self.searcher.grep_code(
            codebase_path,
            pattern,
            file_pattern=file_pattern,
            context_lines=context,
            use_regex=True,
            max_results=limit
        )

        grep_results = []
        for r in results:
            ctx = r.get("context", {}) or {}
            grep_results.append(GrepResult(
                file=r["file"],
                line=r["line"],
                content=r["content"],
                context_before=[l["content"] for l in ctx.get("before", [])],
                context_after=[l["content"] for l in ctx.get("after", [])],
            ))

        return grep_results

    def find_usages(
        self,
        name: str,
        codebase: Optional[str] = None,
        file_pattern: Optional[str] = None,
        limit: int = 50
    ) -> List[GrepResult]:
        """Find usages of a symbol in code.

        Args:
            name: Symbol name to search for
            codebase: Optional codebase path
            file_pattern: Optional file pattern filter
            limit: Maximum results

        Returns:
            List of GrepResult objects showing usages
        """
        # Create pattern that matches the name as a word boundary
        pattern = rf"\b{re.escape(name)}\b"
        return self.grep(
            pattern,
            codebase=codebase,
            file_pattern=file_pattern,
            context=1,
            limit=limit
        )

    # =========================================================================
    # File Operations
    # =========================================================================

    def get_file_symbols(
        self,
        file_path: str,
        codebase: Optional[str] = None
    ) -> List[SearchResult]:
        """Get all symbols defined in a specific file.

        Args:
            file_path: Path to the file
            codebase: Optional codebase path

        Returns:
            List of SearchResult objects
        """
        codebase_path = self._get_codebase(codebase)

        symbols = self.searcher.get_file_symbols(codebase_path, file_path)

        return [
            SearchResult(
                name=s["name"],
                type=s["type"],
                file=file_path,
                line=s["line"],
                column=s.get("column", 0),
            )
            for s in symbols
        ]

    def get_file_structure(
        self,
        file_path: str,
        codebase: Optional[str] = None
    ) -> str:
        """Get a compact structure overview of a file.

        Args:
            file_path: Path to the file
            codebase: Optional codebase path

        Returns:
            Formatted string showing file structure
        """
        symbols = self.get_file_symbols(file_path, codebase)

        if not symbols:
            return f"No symbols found in {file_path}"

        lines = [f"Structure of {file_path}:"]

        # Group by type
        by_type: Dict[str, List[SearchResult]] = {}
        for s in symbols:
            by_type.setdefault(s.type, []).append(s)

        for sym_type in ["class", "function", "method", "variable", "interface", "type"]:
            if sym_type in by_type:
                lines.append(f"\n{sym_type.title()}s:")
                for s in by_type[sym_type]:
                    lines.append(f"  {s.name} (line {s.line})")

        return "\n".join(lines)

    # =========================================================================
    # Statistics & Overview
    # =========================================================================

    def get_stats(self, codebase: Optional[str] = None) -> Optional[CodebaseStats]:
        """Get statistics about the indexed codebase.

        Args:
            codebase: Optional codebase path

        Returns:
            CodebaseStats or None if not indexed
        """
        codebase_path = self._get_codebase(codebase)
        stats = self.searcher.get_statistics(codebase_path)

        if not stats:
            return None

        return CodebaseStats(
            root=stats["root"],
            total_files=stats["total_files"],
            total_symbols=stats["total_symbols"],
            symbol_types=stats["symbol_types"],
            file_extensions=stats["file_extensions"],
        )

    def get_overview(self, codebase: Optional[str] = None) -> str:
        """Get a compact overview of the codebase for planning.

        This is optimized for Siggy's planning phase, providing
        just enough context to understand the codebase structure.

        Args:
            codebase: Optional codebase path

        Returns:
            Formatted overview string
        """
        stats = self.get_stats(codebase)

        if not stats:
            return "Codebase not indexed. Run index() first."

        codebase_path = self._get_codebase(codebase)

        lines = [
            f"# Codebase Overview: {stats.root}",
            "",
            f"**Files:** {stats.total_files}",
            f"**Symbols:** {stats.total_symbols}",
            "",
            "## File Types:",
        ]

        for ext, count in sorted(stats.file_extensions.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"  {ext}: {count} files")

        lines.extend(["", "## Symbol Types:"])
        for sym_type, count in sorted(stats.symbol_types.items(), key=lambda x: -x[1]):
            lines.append(f"  {sym_type}: {count}")

        # Add key entry points
        lines.extend(["", "## Key Entry Points:"])

        # Find main/index files
        main_patterns = ["main", "index", "app", "server", "cli"]
        for pattern in main_patterns:
            results = self.find_functions(pattern, codebase=str(codebase_path), limit=5)
            for r in results:
                lines.append(f"  {r.name}: {r.to_location()}")

        return "\n".join(lines)

    # =========================================================================
    # Siggy Workflow Helpers
    # =========================================================================

    def for_planning(
        self,
        codebase: Optional[str] = None,
        focus_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get information optimized for Siggy's planning phase.

        This provides a structured overview suitable for creating PROMPT.md.

        Args:
            codebase: Optional codebase path
            focus_patterns: Optional list of patterns to focus research on

        Returns:
            Dictionary with planning information
        """
        codebase_path = self._get_codebase(codebase)
        stats = self.get_stats(str(codebase_path))

        result = {
            "overview": stats.to_dict() if stats else {},
            "key_classes": [],
            "key_functions": [],
            "focus_results": {},
        }

        # Get key classes (top 20)
        classes = self.find_classes(codebase=str(codebase_path), limit=20)
        result["key_classes"] = [
            {"name": c.name, "location": c.to_location()}
            for c in classes
        ]

        # Get key functions (main entry points)
        for pattern in ["^main$", "^run$", "^start$", "^init"]:
            funcs = self.find_functions(pattern, codebase=str(codebase_path), limit=5)
            for f in funcs:
                result["key_functions"].append({
                    "name": f.name,
                    "location": f.to_location()
                })

        # Search for focus patterns if provided
        if focus_patterns:
            for pattern in focus_patterns:
                symbols = self.find_symbols(pattern, codebase=str(codebase_path), limit=10)
                grep_results = self.grep(pattern, codebase=str(codebase_path), limit=10)

                result["focus_results"][pattern] = {
                    "symbols": [s.to_dict() for s in symbols],
                    "usages": [g.to_dict() for g in grep_results],
                }

        return result

    def for_execution(
        self,
        target: str,
        codebase: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get information optimized for Siggy's execution phase.

        This provides precise location information for making changes.

        Args:
            target: The symbol or pattern to work with
            codebase: Optional codebase path

        Returns:
            Dictionary with execution information
        """
        codebase_path = self._get_codebase(codebase)

        # Find the target definition
        definition = self.find_definition(target, codebase=str(codebase_path))

        # Find usages
        usages = self.find_usages(target, codebase=str(codebase_path), limit=20)

        result = {
            "target": target,
            "definition": definition.to_dict() if definition else None,
            "usages": [u.to_dict() for u in usages],
            "usage_count": len(usages),
        }

        # If we found a definition, get the file structure
        if definition:
            file_symbols = self.get_file_symbols(definition.file, codebase=str(codebase_path))
            result["file_structure"] = [s.to_dict() for s in file_symbols]

        return result

    def for_verification(
        self,
        expected_symbols: Optional[List[str]] = None,
        codebase: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get information optimized for Siggy's verification phase.

        This checks that expected changes were made correctly.

        Args:
            expected_symbols: List of symbol names that should exist
            codebase: Optional codebase path

        Returns:
            Dictionary with verification results
        """
        codebase_path = self._get_codebase(codebase)
        stats = self.get_stats(str(codebase_path))

        result = {
            "stats": stats.to_dict() if stats else {},
            "verification_results": {},
        }

        # Verify expected symbols exist
        if expected_symbols:
            for symbol in expected_symbols:
                found = self.find_definition(symbol, codebase=str(codebase_path))
                result["verification_results"][symbol] = {
                    "found": found is not None,
                    "location": found.to_location() if found else None,
                }

        return result

    # =========================================================================
    # Cache Management
    # =========================================================================

    def clear_cache(self, codebase: Optional[str] = None) -> None:
        """Clear the index cache.

        Args:
            codebase: Optional specific codebase to clear. Clears all if not specified.
        """
        if codebase:
            self.cache.clear(Path(codebase))
        else:
            self.cache.clear()

    def is_indexed(self, codebase: Optional[str] = None) -> bool:
        """Check if a codebase is indexed.

        Args:
            codebase: Optional codebase path

        Returns:
            True if the codebase is indexed
        """
        try:
            codebase_path = self._get_codebase(codebase)
            return self.cache.get(codebase_path) is not None
        except ValueError:
            return False

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _make_stats(self, index: Dict[str, Any]) -> CodebaseStats:
        """Create CodebaseStats from an index dictionary."""
        # Count symbols by type
        symbol_types: Dict[str, int] = {}
        file_extensions: Dict[str, int] = {}

        for file_info in index.get("files", []):
            # Count file extensions
            file_path = file_info.get("path", "")
            ext = Path(file_path).suffix
            file_extensions[ext] = file_extensions.get(ext, 0) + 1

            # Count symbol types
            for symbol in file_info.get("symbols", []):
                sym_type = symbol.get("type", "unknown")
                symbol_types[sym_type] = symbol_types.get(sym_type, 0) + 1

        return CodebaseStats(
            root=index.get("root", ""),
            total_files=index.get("total_files", 0),
            total_symbols=index.get("symbol_count", 0),
            symbol_types=symbol_types,
            file_extensions=file_extensions,
        )


# Convenience function for quick access
def create_interface(cache: Optional[IndexCache] = None) -> PeppyInterface:
    """Create a new PeppyInterface instance.

    Args:
        cache: Optional shared cache instance

    Returns:
        New PeppyInterface instance
    """
    return PeppyInterface(cache)

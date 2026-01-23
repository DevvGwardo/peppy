"""Peppy - A codebase indexing and search plugin for Claude Code."""

__version__ = "0.1.0"

from .indexer import CodebaseIndexer
from .searcher import CodebaseSearcher
from .interface import PeppyInterface, create_interface, SearchResult, GrepResult, CodebaseStats

__all__ = [
    "CodebaseIndexer",
    "CodebaseSearcher",
    "PeppyInterface",
    "create_interface",
    "SearchResult",
    "GrepResult",
    "CodebaseStats",
]

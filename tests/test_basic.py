"""Basic tests for Peppy."""

import pytest
from pathlib import Path
from peppy import CodebaseIndexer, CodebaseSearcher
from peppy.cache import IndexCache


def test_cache_initialization():
    """Test that cache can be initialized."""
    cache = IndexCache()
    assert cache.cache_dir.exists()


def test_indexer_initialization():
    """Test that indexer can be initialized."""
    indexer = CodebaseIndexer()
    assert indexer is not None
    assert indexer.parser is not None


def test_searcher_initialization():
    """Test that searcher can be initialized."""
    searcher = CodebaseSearcher()
    assert searcher is not None


def test_extension_detection():
    """Test language detection from file extensions."""
    from peppy.parsers import CodeParser

    parser = CodeParser()
    assert parser.get_language_from_extension("test.py") == "python"
    assert parser.get_language_from_extension("test.js") == "javascript"
    assert parser.get_language_from_extension("test.ts") == "typescript"
    assert parser.get_language_from_extension("test.go") == "go"
    assert parser.get_language_from_extension("test.rs") == "rust"
    assert parser.get_language_from_extension("test.java") == "java"


def test_index_current_directory():
    """Test indexing the current directory."""
    indexer = CodebaseIndexer()
    current_dir = Path.cwd()

    # Index the current directory (should include peppy package)
    index = indexer.index_codebase(current_dir, force_reindex=True)

    assert index is not None
    assert "total_files" in index
    assert "symbol_count" in index
    assert index["total_files"] > 0


def test_search_symbols():
    """Test symbol search functionality."""
    indexer = CodebaseIndexer()
    searcher = CodebaseSearcher()
    current_dir = Path.cwd()

    # Index first
    indexer.index_codebase(current_dir, force_reindex=True)

    # Search for a symbol that should exist
    results = searcher.search_symbols(current_dir, "CodebaseIndexer", use_regex=False)

    assert results is not None
    assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

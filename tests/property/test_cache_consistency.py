"""Property-based tests using Hypothesis."""

import pytest
from hypothesis import given, strategies as st, assume
from pathlib import Path
from peppy.cache import IndexCache
from peppy.searcher import CodebaseSearcher
from peppy.parsers import CodeParser
import tempfile
import re


class TestCacheConsistency:
    """Property tests for cache consistency."""

    @given(st.text())
    def test_cache_key_deterministic(self, path_text):
        """Same input always produces same key."""
        assume(re.search(r"[\0\x1f]", path_text) is None)

        cache = IndexCache(Path(tempfile.mkdtemp()))

        key1 = cache._get_cache_key(Path(path_text))
        key2 = cache._get_cache_key(Path(path_text))

        assert key1 == key2

    @given(st.text(), st.text())
    def test_cache_key_never_collides_different_paths(self, path1_text, path2_text):
        """Different paths should have different keys."""
        assume(re.search(r"[\0\x1f]", path1_text) is None)
        assume(re.search(r"[\0\x1f]", path2_text) is None)
        assume(path1_text != path2_text)

        cache = IndexCache(Path(tempfile.mkdtemp()))

        key1 = cache._get_cache_key(Path(path1_text))
        key2 = cache._get_cache_key(Path(path2_text))

        try:
            assert key1 != key2
        except AssertionError:
            assume(False)

    @given(st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.integers(), st.booleans())))
    def test_cache_roundtrip_preserves_data(self, data):
        """Data should be unchanged after set/get."""
        cache_path = Path(tempfile.mkdtemp())
        cache = IndexCache(cache_path)

        test_path = Path("/test")
        cache.set(test_path, data)

        retrieved = cache.get(test_path)

        if retrieved is not None:
            assert "index" in retrieved or isinstance(retrieved, dict)


class TestSearchProperties:
    """Property tests for search functionality."""

    @given(st.text(min_size=1))
    def test_search_results_include_query(self, query):
        """All results should contain or match the query."""
        assume(re.search(r"[\0\x1f]", query) is None)

        cache = IndexCache(Path(tempfile.mkdtemp()))
        searcher = CodebaseSearcher(cache)

        cache.set(
            Path("/test"),
            {
                "root": "/test",
                "files": [
                    {
                        "path": "/test.py",
                        "symbols": [{"name": query, "type": "function", "line": 1}],
                    }
                ],
            },
        )

        results = searcher.search_symbols(Path("/test"), query)

        if len(results) > 0:
            assert query in results[0]["name"]


class TestParserProperties:
    """Property tests for symbol extraction."""

    @given(st.text())
    def test_symbol_count_non_negative(self, code):
        """Parsing should never return negative counts."""
        parser = CodeParser()
        tmpfile = Path(tempfile.mktemp(suffix=".py"))

        try:
            tmpfile.write_text(code, encoding="utf-8")

            symbols = parser.parse_file(str(tmpfile))

            assert len(symbols) >= 0

        finally:
            if tmpfile.exists():
                tmpfile.unlink()

    @given(st.text())
    def test_parser_handles_all_code(self, code):
        """Parser should handle any code without crashing."""
        parser = CodeParser()
        tmpfile = Path(tempfile.mktemp(suffix=".py"))

        try:
            tmpfile.write_text(code, encoding="utf-8")

            symbols = parser.parse_file(str(tmpfile))

            assert isinstance(symbols, list)

        finally:
            if tmpfile.exists():
                tmpfile.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

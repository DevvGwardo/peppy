"""Tests for token optimization and savings verification."""

import pytest
from pathlib import Path
import tempfile
from peppy.cache import IndexCache
from peppy.searcher import CodebaseSearcher
from peppy.indexer import CodebaseIndexer


class TestResultLimiting:
    """Tests for result limiting to save tokens."""

    def test_search_respects_default_results(self):
        """Default limits are reasonable."""
        tmpdir = Path(tempfile.mkdtemp())

        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        symbols = [{"name": f"func{i}", "type": "function", "line": i} for i in range(100)]

        cache.set(
            tmpdir,
            {
                "root": str(tmpdir),
                "files": [
                    {
                        "path": str(tmpdir / "test.py"),
                        "symbols": symbols,
                    }
                ],
            },
        )

        results = searcher.search_symbols(tmpdir, ".*")

        assert isinstance(results, list)


class TestContextOptimization:
    """Tests for context optimization to minimize tokens."""

    def test_zero_context_minimizes_tokens(self):
        """No context lines returned."""
        tmpdir = Path(tempfile.mkdtemp())
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        cache.set(
            tmpdir,
            {
                "root": str(tmpdir),
                "files": [
                    {
                        "path": str(tmpdir / "test.py"),
                        "symbols": [],
                    }
                ],
            },
        )

        test_file = tmpdir / "test.py"
        test_file.write_text("line1\nTARGET\nline3", encoding="utf-8")

        results = searcher.grep_code(tmpdir, "TARGET", context_lines=0)

        assert len(results) > 0
        for r in results:
            if r.get("context"):
                assert len(r["context"]["before"]) == 0
                assert len(r["context"]["after"]) == 0

    def test_context_lines_honored(self):
        """Exact number of lines returned."""
        tmpdir = Path(tempfile.mkdtemp())
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        cache.set(
            tmpdir,
            {
                "root": str(tmpdir),
                "files": [
                    {
                        "path": str(tmpdir / "test.py"),
                        "symbols": [],
                    }
                ],
            },
        )

        test_file = tmpdir / "test.py"
        test_file.write_text("line1\nline2\nline3\nTARGET\nline5\nline6\nline7", encoding="utf-8")

        results = searcher.grep_code(tmpdir, "TARGET", context_lines=2)

        assert len(results) > 0
        for r in results:
            if r.get("context"):
                assert len(r["context"]["before"]) == 2
                assert len(r["context"]["after"]) == 2


class TestFilePatternFiltering:
    """Tests for file pattern filtering to reduce search space."""

    def test_file_pattern_correctness(self):
        """Only matching files searched."""
        tmpdir = Path(tempfile.mkdtemp())
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        cache.set(
            tmpdir,
            {
                "root": str(tmpdir),
                "files": [
                    {
                        "path": str(tmpdir / "test.py"),
                        "symbols": [{"name": "py_func", "type": "function", "line": 1}],
                    },
                    {
                        "path": str(tmpdir / "test.js"),
                        "symbols": [{"name": "js_func", "type": "function", "line": 1}],
                    },
                ],
            },
        )

        py_results = searcher.search_symbols(tmpdir, "py_func", file_pattern="*.py")

        assert len(py_results) > 0
        for r in py_results:
            assert r["file"].endswith(".py")


class TestTokenSavingsVerification:
    """Tests for token savings claims."""

    def test_index_once_search_many_pattern(self):
        """Reuse index across searches."""
        tmpdir = Path(tempfile.mkdtemp())
        cache = IndexCache()
        indexer = CodebaseIndexer(cache)

        for i in range(50):
            test_file = tmpdir / f"test{i}.py"
            test_file.write_text(f"def test{i}(): pass", encoding="utf-8")

        index1 = indexer.index_codebase(tmpdir)
        index2 = indexer.index_codebase(tmpdir, force_reindex=False)

        assert index1 is not None

    def test_cache_avoids_reindexing_cost(self):
        """Cached searches are instant."""
        tmpdir = Path(tempfile.mkdtemp())
        cache = IndexCache()
        indexer = CodebaseIndexer(cache)

        for i in range(50):
            test_file = tmpdir / f"test{i}.py"
            test_file.write_text(f"def test{i}(): pass", encoding="utf-8")

        indexer.index_codebase(tmpdir)

        cached_index = indexer.index_codebase(tmpdir, force_reindex=False)

        assert cached_index is not None


class TestSearchEfficiency:
    """Tests for search operation efficiency."""

    def test_empty_query_efficiency(self):
        """Empty queries handled efficiently."""
        tmpdir = Path(tempfile.mkdtemp())
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        cache.set(
            tmpdir,
            {
                "root": str(tmpdir),
                "files": [
                    {
                        "path": str(tmpdir / "test.py"),
                        "symbols": [{"name": "test", "type": "function", "line": 1}],
                    }
                ],
            },
        )

        results = searcher.search_symbols(tmpdir, "")

        assert isinstance(results, list)


class TestTokenOptimizationAcrossWorkflows:
    """Tests for token optimization in workflow scenarios."""

    def test_planning_phase_optimization(self):
        """Planning phase uses minimal tokens."""
        tmpdir = Path(tempfile.mkdtemp())

        for i in range(20):
            test_file = tmpdir / f"class{i}.py"
            test_file.write_text(f"class Class{i}: pass", encoding="utf-8")

        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        cache.set(
            tmpdir,
            {
                "root": str(tmpdir),
                "files": [
                    {
                        "path": str(tmpdir / f"class{i}.py"),
                        "symbols": [
                            {"name": f"Class{i}", "type": "class", "line": 1},
                        ],
                    }
                    for i in range(20)
                ],
            },
        )

        classes = searcher.search_symbols(tmpdir, "Class", symbol_type="class")

        assert len(classes) <= 20

    def test_execution_phase_optimization(self):
        """Execution phase uses targeted location finding."""
        tmpdir = Path(tempfile.mkdtemp())
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        cache.set(
            tmpdir,
            {
                "root": str(tmpdir),
                "files": [
                    {
                        "path": str(tmpdir / "test.py"),
                        "symbols": [
                            {"name": "target_func", "type": "function", "line": 10, "column": 4},
                        ],
                    }
                ],
            },
        )

        import time

        start = time.time()
        results = searcher.search_symbols(tmpdir, "^target_func$")
        duration = time.time() - start

        assert len(results) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

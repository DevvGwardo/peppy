"""Unit tests for CodebaseSearcher (focus: context token savings)."""

import pytest
from pathlib import Path
from peppy.searcher import CodebaseSearcher
from peppy.cache import IndexCache


class TestSymbolSearch:
    """Tests for symbol search functionality."""

    def test_symbol_search_basic(self, sample_codebase):
        """Exact match query."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        searcher.cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": str(sample_codebase / "test.py"),
                        "symbols": [{"name": "test_func", "type": "function", "line": 1}],
                    }
                ],
            },
        )

        results = searcher.search_symbols(sample_codebase, "test_func")

        assert len(results) > 0
        assert results[0]["name"] == "test_func"

    def test_symbol_search_regex(self, sample_codebase):
        """Regex pattern matching."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        searcher.cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": str(sample_codebase / "test.py"),
                        "symbols": [
                            {"name": "test_func", "type": "function", "line": 1},
                            {"name": "another_func", "type": "function", "line": 5},
                        ],
                    }
                ],
            },
        )

        results = searcher.search_symbols(sample_codebase, ".*func$")

        assert len(results) == 2

    def test_symbol_search_empty_results(self, sample_codebase):
        """No matches returns empty."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        results = searcher.search_symbols(sample_codebase, "nonexistent")

        assert len(results) == 0

    def test_symbol_search_type_filter(self, sample_codebase):
        """Filter by function/class/method."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        searcher.cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": str(sample_codebase / "test.py"),
                        "symbols": [
                            {"name": "test_func", "type": "function", "line": 1},
                            {"name": "TestClass", "type": "class", "line": 5},
                        ],
                    }
                ],
            },
        )

        results = searcher.search_symbols(sample_codebase, "test", symbol_type="function")

        assert len(results) == 1
        assert results[0]["type"] == "function"

    def test_symbol_search_file_pattern_filter(self, sample_codebase):
        """Filter by *.py, *.js."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        searcher.cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": str(sample_codebase / "test.py"),
                        "symbols": [{"name": "test_func", "type": "function", "line": 1}],
                    }
                ],
            },
        )

        py_results = searcher.search_symbols(sample_codebase, "test", file_pattern="*.py")
        js_results = searcher.search_symbols(sample_codebase, "test", file_pattern="*.js")

        assert len(py_results) == 1
        assert "test.py" in py_results[0]["file"]
        assert len(js_results) == 0

    def test_symbol_search_limit(self, sample_codebase):
        """Respects limit parameter."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        symbols = [{"name": f"func{i}", "type": "function", "line": i} for i in range(10)]

        searcher.cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": str(sample_codebase / "test.py"),
                        "symbols": symbols,
                    }
                ],
            },
        )

        results = searcher.search_symbols(
            sample_codebase,
            "func.*",
            file_pattern="*.py",
            max_results=3,
        )

        assert len(results) == 3
        assert "test.py" in results[0]["file"]


class TestGrepSearch:
    """Tests for grep search with token savings focus."""

    def test_grep_basic_pattern(self, sample_codebase):
        """Simple pattern matching."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        test_file = sample_codebase / "test.py"
        test_file.write_text("import os\nimport sys", encoding="utf-8")

        # Add file to cache so grep can find it
        cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": str(test_file),
                        "symbols": [],
                    }
                ],
            },
        )

        results = searcher.grep_code(sample_codebase, "import")

        assert len(results) > 0
        assert "import" in results[0]["content"]

    def test_grep_with_context_lines(self, sample_codebase):
        """Context returned correctly."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        lines = ["line1", "line2 TARGET", "line3"]
        test_file = sample_codebase / "test.py"
        test_file.write_text("\n".join(lines), encoding="utf-8")

        # Add file to cache
        cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": str(test_file),
                        "symbols": [],
                    }
                ],
            },
        )

        results = searcher.grep_code(sample_codebase, "TARGET", context_lines=1)

        assert len(results) > 0
        assert results[0]["context"] is not None
        assert len(results[0]["context"]["before"]) == 1
        assert len(results[0]["context"]["after"]) == 1

    def test_grep_no_context_minimizes_tokens(self, sample_codebase):
        """Zero context saves tokens."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        test_file = sample_codebase / "test.py"
        test_file.write_text("TARGET line", encoding="utf-8")

        # Add file to cache
        cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": str(test_file),
                        "symbols": [],
                    }
                ],
            },
        )

        results = searcher.grep_code(sample_codebase, "TARGET", context_lines=0)

        assert len(results) > 0
        assert results[0]["context"] is None

    def test_grep_max_results_limited(self, sample_codebase):
        """Respects max_results parameter."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        searcher.cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": str(sample_codebase / "test.py"),
                        "symbols": [],
                    }
                ],
            },
        )

        test_file = sample_codebase / "test.py"
        test_file.write_text("\n".join(["TARGET"] * 200), encoding="utf-8")

        results = searcher.grep_code(sample_codebase, "TARGET", max_results=50)

        assert len(results) <= 50

    def test_grep_file_pattern_filter(self, sample_codebase):
        """Reduces search space (token savings)."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        py_file = sample_codebase / "test.py"
        py_file.write_text("TARGET", encoding="utf-8")

        js_file = sample_codebase / "test.js"
        js_file.write_text("TARGET", encoding="utf-8")

        # Add files to cache
        cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": str(py_file),
                        "symbols": [],
                    },
                    {
                        "path": str(js_file),
                        "symbols": [],
                    },
                ],
            },
        )

        py_results = searcher.grep_code(sample_codebase, "TARGET", file_pattern="*.py")

        assert len(py_results) > 0
        assert "test.py" in py_results[0]["file"]

    def test_grep_regex_handling(self, sample_codebase):
        """Invalid regex falls back gracefully."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        results = searcher.grep_code(sample_codebase, "[invalid(regex")

        assert isinstance(results, list)


class TestFileOperations:
    """Tests for file operations."""

    def test_get_file_symbols(self, sample_codebase):
        """Returns all symbols in file."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        test_file = str(sample_codebase / "test.py")

        cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": test_file,
                        "symbols": [
                            {"name": "func1", "type": "function", "line": 1, "column": 4},
                            {"name": "func2", "type": "function", "line": 5, "column": 4},
                        ],
                    }
                ],
            },
        )

        symbols = searcher.get_file_symbols(sample_codebase, test_file)

        assert len(symbols) == 2

    def test_get_file_symbols_empty(self, tmp_path):
        """Empty file returns empty list."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        cache.set(tmp_path, {"root": str(tmp_path), "files": []})

        results = searcher.get_file_symbols(tmp_path, "nonexistent.py")

        assert len(results) == 0

    def test_get_file_symbols_relative_to_codebase(self, tmp_path):
        """Relative file path resolves against codebase root."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        src = tmp_path / "src"
        src.mkdir(parents=True, exist_ok=True)
        file_path = src / "mod.py"
        file_path.write_text("def ok():\n    pass\n", encoding="utf-8")

        cache.set(
            tmp_path,
            {
                "root": str(tmp_path),
                "files": [
                    {
                        "path": str(file_path),
                        "symbols": [{"name": "ok", "type": "function", "line": 1, "column": 4}],
                    }
                ],
            },
        )

        symbols = searcher.get_file_symbols(tmp_path, "src/mod.py")
        assert len(symbols) == 1
        assert symbols[0]["name"] == "ok"

    def test_nonexistent_file(self, sample_codebase):
        """Returns empty gracefully."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        results = searcher.get_file_symbols(sample_codebase, "nonexistent.py")

        assert len(results) == 0


class TestStatistics:
    """Tests for statistics retrieval."""

    def test_statistics_correct_counts(self, sample_codebase):
        """File and symbol counts accurate."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "total_files": 10,
                "symbol_count": 50,
                "files": [
                    {
                        "path": str(sample_codebase / "test.py"),
                        "symbols": [{"name": "func", "type": "function", "line": 1}],
                    }
                ],
            },
        )

        stats = searcher.get_statistics(sample_codebase)

        assert stats["total_files"] == 10
        assert stats["total_symbols"] == 50

    def test_statistics_correct_types(self, sample_codebase):
        """Symbol types and extensions correct."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "total_files": 2,
                "symbol_count": 3,
                "files": [
                    {
                        "path": str(sample_codebase / "test.py"),
                        "symbols": [
                            {"name": "func", "type": "function", "line": 1},
                            {"name": "Test", "type": "class", "line": 5},
                        ],
                    },
                    {
                        "path": str(sample_codebase / "test.js"),
                        "symbols": [{"name": "func_js", "type": "function", "line": 1}],
                    },
                ],
            },
        )

        stats = searcher.get_statistics(sample_codebase)

        assert "function" in stats["symbol_types"]
        assert ".py" in stats["file_extensions"]


class TestSearcherEdgeCases:
    """Tests for searcher edge cases."""

    def test_search_not_indexed(self):
        """Returns empty for unindexed codebase."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        results = searcher.search_symbols(Path("/nonexistent"), "test")

        assert len(results) == 0

    def test_search_regex_error_handling(self, sample_codebase):
        """Invalid regex handled."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        results = searcher.search_symbols(sample_codebase, "[invalid")

        assert isinstance(results, list)

    def test_search_large_result_set(self, sample_codebase):
        """Handles thousands of results."""
        cache = IndexCache()
        searcher = CodebaseSearcher(cache)

        cache.set(
            sample_codebase,
            {
                "root": str(sample_codebase),
                "files": [
                    {
                        "path": str(sample_codebase / "test.py"),
                        "symbols": [
                            {"name": f"func{i}", "type": "function", "line": i} for i in range(1000)
                        ],
                    }
                ],
            },
        )

        results = searcher.search_symbols(sample_codebase, ".*")

        assert isinstance(results, list)


@pytest.fixture
def sample_codebase():
    import tempfile

    return Path(tempfile.mkdtemp())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

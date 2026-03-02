"""Performance tests for scalability benchmarks."""

import pytest
import time
from pathlib import Path
import tempfile
from peppy.indexer import CodebaseIndexer
from peppy.searcher import CodebaseSearcher
from peppy.cache import IndexCache
import sys

# Optional psutil for memory tests
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class TestSmallCodebase:
    """Tests for small codebase (~10 files)."""

    @pytest.mark.timeout(5)
    def test_small_codebase_10_files(self):
        """Baseline performance (~100ms)."""
        tmpdir = Path(tempfile.mkdtemp())

        for i in range(10):
            test_file = tmpdir / f"file{i}.py"
            test_file.write_text(f"def test{i}(): pass\n", encoding="utf-8")

        indexer = CodebaseIndexer()

        start = time.time()
        index = indexer.index_codebase(tmpdir)
        duration = time.time() - start

        assert index is not None
        assert index["total_files"] == 10
        assert duration < 5

    @pytest.mark.timeout(5)
    def test_small_codebase_search_speed(self):
        """Query performance (~50ms)."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def target(): pass", encoding="utf-8")

        cache = IndexCache()
        indexer = CodebaseIndexer(cache)
        searcher = CodebaseSearcher(cache)

        indexer.index_codebase(tmpdir)

        start = time.time()
        results = searcher.search_symbols(tmpdir, "target")
        duration = time.time() - start

        assert len(results) > 0
        assert duration < 5


class TestMediumCodebase:
    """Tests for medium codebase (~100 files)."""

    @pytest.mark.timeout(60)
    def test_medium_codebase_100_files(self):
        """Scaling performance (~1s)."""
        tmpdir = Path(tempfile.mkdtemp())

        for i in range(100):
            test_file = tmpdir / f"file{i}.py"
            test_file.write_text(f"def test{i}(): pass", encoding="utf-8")

        indexer = CodebaseIndexer()

        start = time.time()
        index = indexer.index_codebase(tmpdir)
        duration = time.time() - start

        assert index is not None
        assert index["total_files"] == 100
        assert duration < 60

    @pytest.mark.timeout(60)
    def test_medium_codebase_search_speed(self):
        """Query performance (~200ms)."""
        tmpdir = Path(tempfile.mkdtemp())

        for i in range(100):
            test_file = tmpdir / f"file{i}.py"
            test_file.write_text(f"def test{i}(): pass\nclass Test{i}: pass", encoding="utf-8")

        cache = IndexCache()
        indexer = CodebaseIndexer(cache)
        searcher = CodebaseSearcher(cache)

        indexer.index_codebase(tmpdir)

        start = time.time()
        results = searcher.search_symbols(tmpdir, "test1")
        duration = time.time() - start

        assert len(results) > 0
        assert duration < 60


class TestLargeCodebase:
    """Tests for large codebase (~1000 files)."""

    @pytest.mark.timeout(60)
    def test_large_codebase_1000_files(self):
        """Stress test performance (~30s)."""
        tmpdir = Path(tempfile.mkdtemp())

        for i in range(1000):
            test_file = tmpdir / f"file{i}.py"
            test_file.write_text(f"def test{i}(): pass\nclass Test{i}: pass", encoding="utf-8")

        indexer = CodebaseIndexer()

        start = time.time()
        index = indexer.index_codebase(tmpdir)
        duration = time.time() - start

        assert index is not None
        assert index["total_files"] == 1000
        assert duration < 60

    @pytest.mark.timeout(60)
    def test_large_codebase_search_speed(self):
        """Query performance (~1s)."""
        tmpdir = Path(tempfile.mkdtemp())

        for i in range(1000):
            test_file = tmpdir / f"file{i}.py"
            test_file.write_text(f"def test{i}(): pass", encoding="utf-8")

        cache = IndexCache()
        indexer = CodebaseIndexer(cache)
        searcher = CodebaseSearcher(cache)

        indexer.index_codebase(tmpdir)

        start = time.time()
        results = searcher.search_symbols(tmpdir, "test500")
        duration = time.time() - start

        assert len(results) > 0
        assert duration < 60


class TestMemoryUsage:
    """Tests for memory usage."""

    @pytest.mark.timeout(60)
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not installed")
    def test_indexing_memory_usage(self):
        """Memory bounded during indexing."""
        tmpdir = Path(tempfile.mkdtemp())

        for i in range(500):
            test_file = tmpdir / f"file{i}.py"
            test_file.write_text(f"def test{i}(): pass\n" * 100, encoding="utf-8")

        indexer = CodebaseIndexer()

        import psutil
        import os

        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss

        index = indexer.index_codebase(tmpdir)

        end_mem = process.memory_info().rss
        mem_increase = (end_mem - start_mem) / 1024 / 1024

        assert index is not None
        assert mem_increase < 1000

    @pytest.mark.timeout(60)
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not installed")
    def test_search_memory_usage(self):
        """Memory bounded during search."""
        tmpdir = Path(tempfile.mkdtemp())

        for i in range(500):
            test_file = tmpdir / f"file{i}.py"
            test_file.write_text(f"def test{i}(): pass\n" * 100, encoding="utf-8")

        cache = IndexCache()
        indexer = CodebaseIndexer(cache)
        searcher = CodebaseSearcher(cache)

        indexer.index_codebase(tmpdir)

        import psutil
        import os

        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss

        searcher.search_symbols(tmpdir, "test250")

        end_mem = process.memory_info().rss
        mem_increase = (end_mem - start_mem) / 1024 / 1024

        assert mem_increase < 100


class TestCachePerformance:
    """Tests for cache performance."""

    @pytest.mark.timeout(60)
    def test_cache_load_save_speed(self):
        """Cache persistence speed (~100ms)."""
        tmpdir = Path(tempfile.mkdtemp())

        for i in range(100):
            test_file = tmpdir / f"file{i}.py"
            test_file.write_text(f"def test{i}(): pass", encoding="utf-8")

        cache = IndexCache()
        indexer = CodebaseIndexer(cache)

        start = time.time()
        index = indexer.index_codebase(tmpdir)
        duration = time.time() - start

        assert index is not None
        assert duration < 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

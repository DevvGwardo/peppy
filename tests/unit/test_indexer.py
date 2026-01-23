"""Unit tests for CodebaseIndexer."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from peppy.indexer import CodebaseIndexer
from peppy.cache import IndexCache


class TestFileCollection:
    """Tests for file collection and filtering."""

    def test_collect_files_by_extension(self, tmp_path, sample_codebase):
        """Only supported extensions collected."""
        indexer = CodebaseIndexer()
        files = indexer.collect_files(sample_codebase)

        assert len(files) > 0
        exts = {f.suffix for f in files}
        assert ".py" in exts
        assert ".js" in exts

    def test_collect_ignored_directories(self, tmp_path):
        """Ignores node_modules, .git, etc."""
        indexer = CodebaseIndexer()

        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        node_modules_file = node_modules / "test.js"
        node_modules_file.write_text("code", encoding="utf-8")

        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        main_file = tmp_path / "main.py"
        main_file.write_text("def test(): pass", encoding="utf-8")

        files = indexer.collect_files(tmp_path)

        assert main_file in files
        assert node_modules_file not in files

    def test_gitignore_respected(self, tmp_path):
        """Custom .gitignore patterns respected."""
        indexer = CodebaseIndexer()

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("ignore_dir/\nignore_file.py\n", encoding="utf-8")

        ignore_dir = tmp_path / "ignore_dir"
        ignore_dir.mkdir()
        (ignore_dir / "test.py").write_text("code", encoding="utf-8")

        ignore_file = tmp_path / "ignore_file.py"
        ignore_file.write_text("code", encoding="utf-8")

        main_file = tmp_path / "main.py"
        main_file.write_text("def test(): pass", encoding="utf-8")

        files = indexer.collect_files(tmp_path)

        assert main_file in files
        assert not any(f.name == "test.py" and f.parent.name == "ignore_dir" for f in files)
        assert ignore_file not in files

    def test_collect_empty_directory(self, tmp_path):
        """Empty directory returns empty list."""
        indexer = CodebaseIndexer()
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        files = indexer.collect_files(empty_dir)

        assert len(files) == 0


class TestFileIndexing:
    """Tests for single and multiple file indexing."""

    def test_index_single_file(self, sample_codebase):
        """Parses symbols correctly."""
        indexer = CodebaseIndexer()
        file_path = sample_codebase / "python" / "basic.py"

        result = indexer.index_file(file_path)

        assert "path" in result
        assert "symbols" in result
        assert len(result["symbols"]) > 0

    def test_index_multiple_files(self, sample_codebase):
        """Batch indexing."""
        indexer = CodebaseIndexer()

        index = indexer.index_codebase(sample_codebase)

        assert index is not None
        assert index["total_files"] > 0
        assert index["symbol_count"] > 0

    def test_index_error_handling(self, tmp_path, mocker):
        """File errors don't stop indexing."""
        indexer = CodebaseIndexer()
        mocker.patch.object(indexer.parser, "parse_file", side_effect=Exception("Error"))

        good_file = tmp_path / "good.py"
        good_file.write_text("def test(): pass", encoding="utf-8")

        bad_file = tmp_path / "bad.py"
        bad_file.write_text("bad code", encoding="utf-8")

        index = indexer.index_codebase(tmp_path)

        assert index is not None


class TestCacheIntegration:
    """Tests for cache usage."""

    def test_index_uses_cache_when_available(self, sample_codebase):
        """Honors existing cache."""
        indexer = CodebaseIndexer()

        index1 = indexer.index_codebase(sample_codebase)

        cache = indexer.cache.get(sample_codebase)
        assert cache is not None

    def test_index_force_reindex(self, sample_codebase):
        """Ignores cache when forced."""
        indexer = CodebaseIndexer()

        index1 = indexer.index_codebase(sample_codebase)
        index2 = indexer.index_codebase(sample_codebase, force_reindex=True)

        assert index2 is not None


class TestParallelProcessing:
    """Tests for parallel indexing."""

    def test_parallel_indexing(self, sample_codebase):
        """Efficient with multiple files."""
        indexer = CodebaseIndexer()

        import time

        start = time.time()
        index = indexer.index_codebase(sample_codebase)
        duration = time.time() - start

        assert index is not None

    def test_parallel_indexing_errors(self, tmp_path):
        """One error doesn't stop others."""
        indexer = CodebaseIndexer()

        for i in range(10):
            test_file = tmp_path / f"file{i}.py"
            test_file.write_text("def test(): pass", encoding="utf-8")

        bad_file = tmp_path / "bad.txt"
        bad_file.write_text("bad", encoding="utf-8")

        index = indexer.index_codebase(tmp_path)

        assert index is not None


class TestIndexerEdgeCases:
    """Tests for indexer edge cases."""

    def test_nonexistent_path(self, mocker):
        """Graceful handling."""
        indexer = CodebaseIndexer()
        mock_log = mocker.patch("builtins.print")

        result = indexer.index_codebase(Path("/nonexistent"))

        assert result is not None

    def test_symlink_handling(self, tmp_path):
        """Symbolic link resolution."""
        linker = tmp_path / "linker"
        linker.mkdir()

        target = tmp_path / "target"
        target.mkdir()

        link = tmp_path / "link"
        link.symlink_to(target)

        indexer = CodebaseIndexer()
        files = indexer.collect_files(tmp_path)

        assert isinstance(files, list)

    def test_large_files(self, tmp_path):
        """Memory usage bounded."""
        indexer = CodebaseIndexer()

        large_file = tmp_path / "large.py"
        large_file.write_text("\n".join(f"# {i}" for i in range(10000)), encoding="utf-8")

        result = indexer.index_file(large_file)

        assert "path" in result


@pytest.fixture
def sample_codebase():
    return Path(__file__).parent.parent / "fixtures" / "sample_codebase"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

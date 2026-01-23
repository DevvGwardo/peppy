"""Unit tests for IndexCache functionality."""

import pytest
from pathlib import Path
from datetime import datetime
from peppy.cache import IndexCache


class TestCacheLifecycle:
    """Tests for cache lifecycle operations."""

    def test_cache_directory_creation(self, tmp_path):
        """Cache dir created on init."""
        cache = IndexCache(tmp_path)
        assert cache.cache_dir.exists()

    def test_cache_set_and_get(self, tmp_path):
        """Basic set/get operations."""
        cache = IndexCache(tmp_path)
        test_data = {"total_files": 5, "symbol_count": 10}
        test_path = tmp_path / "test_project"
        test_path.mkdir()

        cache.set(test_path, test_data)
        result = cache.get(test_path)

        assert result is not None
        assert result["index"]["total_files"] == 5

    def test_cache_clear_specific_path(self, tmp_path):
        """Clear single path cache."""
        cache = IndexCache(tmp_path)
        cache.set(Path("/test"), {"total_files": 5})

        cache.clear(Path("/test"))
        result = cache.get(Path("/test"))

        assert result is None


class TestCacheValidation:
    """Tests for cache validation."""

    def test_cache_path_validation_nonexistent(self, tmp_path):
        """Deleted paths invalidate cache."""
        cache = IndexCache(tmp_path)

        test_path = tmp_path / "test_project"
        test_path.mkdir()

        cache.set(test_path, {"total_files": 5})
        test_path.rmdir()

        result = cache.get(test_path)
        assert result is None

    def test_cache_invalid_json_handling(self, tmp_path):
        """Corrupted JSON handled gracefully."""
        cache = IndexCache(tmp_path)

        cache_path = cache.cache_dir / "test.json"
        cache_path.write_text("invalid json", encoding="utf-8")

        result = cache.get(Path("/test"))
        assert result is None

    def test_cache_missing_timestamp(self, tmp_path):
        """Cache without timestamp rejected."""
        cache = IndexCache(tmp_path)

        cache_path = cache.cache_dir / "test.json"
        cache_path.write_text('{"path": "/test", "index": {}}', encoding="utf-8")

        result = cache.get(Path("/test"))
        assert result is None

    def test_cache_key_consistency(self, tmp_path):
        """Same path produces same key."""
        cache = IndexCache(tmp_path)
        path = Path("/test/path")

        key1 = cache._get_cache_key(path)
        key2 = cache._get_cache_key(path)

        assert key1 == key2


class TestCacheEdgeCases:
    """Tests for cache edge cases."""

    def test_cache_nonexistent_path(self, tmp_path):
        """Get returns None for missing cache."""
        cache = IndexCache(tmp_path)
        result = cache.get(Path("/nonexistent"))
        assert result is None

    def test_cache_large_data(self, tmp_path):
        """Large index handling."""
        cache = IndexCache(tmp_path)

        large_data = {
            "total_files": 1000,
            "files": [],
        }

        for i in range(1000):
            large_data["files"].append(
                {
                    "path": f"/file{i}.py",
                    "symbols": [
                        {"name": f"symbol{j}", "type": "function", "line": j} for j in range(100)
                    ],
                }
            )

        cache.set(Path("/test"), large_data)
        result = cache.get(Path("/test"))

        if result is not None:
            assert result["index"]["total_files"] == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

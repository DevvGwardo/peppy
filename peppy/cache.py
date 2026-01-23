"""Caching functionality for codebase indices."""

import json
import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class IndexCache:
    """Manages caching of codebase indices."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache files. Defaults to .peppy_cache in home dir.
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".peppy_cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, path: Path) -> str:
        """Generate a cache key for a given path.

        Args:
            path: The codebase path

        Returns:
            A hash string to use as cache key
        """
        # Use absolute path for consistent hashing
        abs_path = path.resolve()
        return hashlib.md5(str(abs_path).encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the cache file path for a given key.

        Args:
            cache_key: The cache key

        Returns:
            Path to the cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def get(self, path: Path) -> Optional[Dict[str, Any]]:
        """Retrieve cached index for a path.

        Args:
            path: The codebase path

        Returns:
            Cached index data or None if not found/expired
        """
        cache_key = self._get_cache_key(path)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                data = json.load(f)

            # Check if cache is still valid
            cached_time = datetime.fromisoformat(data.get("timestamp", ""))
            codebase_path = Path(data.get("path", ""))

            # Simple validation: check if path still exists
            if not codebase_path.exists():
                return None

            return data

        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            # Cache is corrupted or invalid
            return None

    def set(self, path: Path, index_data: Dict[str, Any]) -> None:
        """Store index data in cache.

        Args:
            path: The codebase path
            index_data: The index data to cache
        """
        cache_key = self._get_cache_key(path)
        cache_path = self._get_cache_path(cache_key)

        # Add metadata
        cache_entry = {
            "path": str(path.resolve()),
            "timestamp": datetime.now().isoformat(),
            "index": index_data,
        }

        try:
            with open(cache_path, "w") as f:
                json.dump(cache_entry, f, indent=2)
        except OSError as e:
            # Failed to write cache, but don't fail the operation
            print(f"Warning: Failed to write cache: {e}")

    def clear(self, path: Optional[Path] = None) -> None:
        """Clear cache for a specific path or all caches.

        Args:
            path: Optional path to clear cache for. If None, clears all caches.
        """
        if path is None:
            # Clear all caches
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except OSError:
                    pass
        else:
            # Clear specific cache
            cache_key = self._get_cache_key(path)
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                try:
                    cache_path.unlink()
                except OSError:
                    pass

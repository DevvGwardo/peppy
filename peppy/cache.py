"""Caching functionality for codebase indices."""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class IndexCache:
    """Manages caching of codebase indices."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl_seconds: Optional[int] = None):
        if cache_dir is None:
            cache_dir = Path.home() / ".peppy_cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _get_cache_key(self, path: Path) -> str:
        abs_path = path.resolve()
        return hashlib.sha256(str(abs_path).encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        return self.cache_dir / f"{cache_key}.json"

    def _compute_signature(self, path: Path, index: Optional[Dict[str, Any]] = None) -> Optional[str]:
        files = (index or {}).get("files", [])
        if not files:
            return None

        count = 0
        total_size = 0
        max_mtime = 0.0
        for file_info in files:
            file_path = Path(file_info.get("path", ""))
            if not file_path.is_absolute():
                file_path = path / file_path
            try:
                st = file_path.stat()
            except OSError:
                return None
            count += 1
            total_size += st.st_size
            if st.st_mtime > max_mtime:
                max_mtime = st.st_mtime

        raw = f"{count}:{int(max_mtime)}:{total_size}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, path: Path) -> Optional[Dict[str, Any]]:
        cache_key = self._get_cache_key(path)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            cached_time = datetime.fromisoformat(data.get("timestamp", ""))
            codebase_path = Path(data.get("path", ""))
            if not codebase_path.exists():
                return None

            if self.ttl_seconds is not None and datetime.now() - cached_time > timedelta(seconds=self.ttl_seconds):
                return None

            index = data.get("index")
            if not isinstance(index, dict):
                return None

            cached_signature = data.get("signature")
            if cached_signature:
                current_signature = self._compute_signature(codebase_path, index=index)
                if not current_signature or current_signature != cached_signature:
                    return None

            return data

        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            return None

    def set(self, path: Path, index_data: Dict[str, Any]) -> None:
        cache_key = self._get_cache_key(path)
        cache_path = self._get_cache_path(cache_key)

        resolved_path = path.resolve()
        cache_entry = {
            "path": str(resolved_path),
            "timestamp": datetime.now().isoformat(),
            "signature": self._compute_signature(resolved_path, index=index_data),
            "index": index_data,
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, indent=2)
        except OSError as e:
            print(f"Warning: Failed to write cache: {e}")

    def clear(self, path: Optional[Path] = None) -> None:
        if path is None:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except OSError:
                    pass
        else:
            cache_key = self._get_cache_key(path)
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                try:
                    cache_path.unlink()
                except OSError:
                    pass

import json
import os
import time
import threading
from typing import Any, Dict, Optional


class MetadataCache:
    """Простой файловый кэш для метаданных треков."""

    def __init__(self, cache_file: str = "cache/metadata.json", ttl_hours: int = 24):
        self.cache_file = cache_file
        self.ttl_seconds = ttl_hours * 3600 if ttl_hours else 0
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._ensure_dir()
        self._load()

    def _ensure_dir(self) -> None:
        cache_dir = os.path.dirname(self.cache_file)
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    def _load(self) -> None:
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._cache = data
        except Exception:
            # Если файл повреждён — просто начинаем с пустого кэша
            self._cache = {}

    def _save(self) -> None:
        with self._lock:
            self._save_unlocked()

    def _save_unlocked(self) -> None:
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception:
            # Кэш — вспомогательный, при ошибке записи просто пропускаем
            pass

    def _is_expired(self, ts: float) -> bool:
        if not self.ttl_seconds:
            return False
        return (time.time() - ts) > self.ttl_seconds

    def make_key(
        self,
        track_id: Any,
        album_name: Optional[str],
        total_tracks: Optional[int],
        total_discs: Optional[int],
        version: Optional[str],
    ) -> str:
        # Привязываем к ключу всё, что влияет на метаданные
        parts = [
            str(track_id or ""),
            str(album_name or ""),
            str(total_tracks or ""),
            str(total_discs or ""),
            str(version or ""),
        ]
        return "|".join(parts)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None

            ts = entry.get("ts", 0)
            if self._is_expired(ts):
                # Удаляем протухшие данные
                self._cache.pop(key, None)
                self._save_unlocked()
                return None

            metadata = entry.get("metadata")
            return dict(metadata) if isinstance(metadata, dict) else None

    def set(self, key: str, metadata: Dict[str, Any]) -> None:
        with self._lock:
            self._cache[key] = {"metadata": metadata, "ts": time.time()}
            self._save_unlocked()

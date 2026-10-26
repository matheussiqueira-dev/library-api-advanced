import time


class TTLCache[V]:
    """Small in-process cache with per-entry expiry and a hard size cap."""

    def __init__(self, ttl_seconds: float, max_entries: int) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: dict[str, tuple[float, V]] = {}

    def get(self, key: str) -> V | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at <= time.monotonic():
            del self._entries[key]
            return None
        return value

    def set(self, key: str, value: V) -> None:
        now = time.monotonic()
        if key not in self._entries and len(self._entries) >= self.max_entries:
            for stale in [k for k, (exp, _) in self._entries.items() if exp <= now]:
                del self._entries[stale]
            if len(self._entries) >= self.max_entries:
                # Dicts keep insertion order, so the first key is the oldest entry.
                del self._entries[next(iter(self._entries))]
        self._entries[key] = (now + self.ttl_seconds, value)

    def clear(self) -> None:
        self._entries.clear()

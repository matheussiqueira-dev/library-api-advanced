import math
import time
from collections import deque
from typing import Awaitable, Callable, Deque, Dict, Optional

from fastapi import HTTPException, Request, status

from app.core.config import settings


class SlidingWindowRateLimiter:
    """In-memory sliding-window limiter keyed by client address.

    State lives in the process: each serverless instance or worker keeps its own
    counters, so this is a per-instance safety net. Pair it with an edge rule
    (for example a Vercel WAF rate-limit rule) for a global budget.
    """

    def __init__(self, max_requests: int, window_seconds: float, max_keys: int = 10_000) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._hits: Dict[str, Deque[float]] = {}

    def hit(self, key: str) -> Optional[float]:
        """Record a request. Return the seconds to wait when over the limit, else None."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        hits = self._hits.get(key)
        if hits is None:
            if len(self._hits) >= self.max_keys:
                self._evict(cutoff)
            hits = self._hits[key] = deque()
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= self.max_requests:
            return hits[0] + self.window_seconds - now
        hits.append(now)
        return None

    def reset(self) -> None:
        self._hits.clear()

    def _evict(self, cutoff: float) -> None:
        for key in [k for k, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
            del self._hits[key]
        if len(self._hits) >= self.max_keys:
            del self._hits[next(iter(self._hits))]


def client_ip(request: Request) -> str:
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limited(limiter: SlidingWindowRateLimiter) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        retry_after = limiter.hit(client_ip(request))
        if retry_after is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Try again later.",
                headers={"Retry-After": str(max(1, math.ceil(retry_after)))},
            )

    return dependency


write_limiter = SlidingWindowRateLimiter(
    settings.RATE_LIMIT_WRITES_PER_WINDOW, settings.RATE_LIMIT_WINDOW_SECONDS
)
lookup_limiter = SlidingWindowRateLimiter(
    settings.RATE_LIMIT_LOOKUPS_PER_WINDOW, settings.RATE_LIMIT_WINDOW_SECONDS
)

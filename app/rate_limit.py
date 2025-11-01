import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Depends, HTTPException, status

# Fixed window rate limiter implementation
# Each key is allowed max_requests per window_seconds
class FixedWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    # Record a hit for the given key and enforce rate limit
    def hit(self, key: str) -> None:
        now = time.time()
        q = self._hits[key]
        # Purge old hits outside the window
        cutoff = now - self.window
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "rate_limit_exceeded", "message": "Rate limit exceeded"},
            )
        q.append(now)

# Factory to create a dependency that uses the limiter
def limiter_dependency_factory(limiter: FixedWindowLimiter):
    def _dep(key: str) -> None:
        limiter.hit(key)

    return _dep

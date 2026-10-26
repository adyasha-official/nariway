"""Tiny in-memory sliding-window limiter. Fine for one process; use Redis when scaling out."""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_hits: dict[str, deque[float]] = defaultdict(deque)


def reset() -> None:
    _hits.clear()


def limit(name: str, max_calls: int, per_seconds: int):
    def dep(request: Request) -> None:
        key = f"{name}:{request.client.host if request.client else 'unknown'}"
        now = time.monotonic()
        q = _hits[key]
        while q and now - q[0] > per_seconds:
            q.popleft()
        if len(q) >= max_calls:
            raise HTTPException(429, "Too many requests. Please wait a moment and try again.")
        q.append(now)

    return dep

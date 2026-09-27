"""Small in-process rate-limit middleware; use provider WAF limits in production too."""

import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, requests: int, window_seconds: int) -> None:
        super().__init__(app)
        self.requests = requests
        self.window_seconds = window_seconds
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/health"):
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self._windows[client]
        while window and window[0] <= now - self.window_seconds:
            window.popleft()
        if len(window) >= self.requests:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": {"code": "RATE_LIMITED", "message": "Try again later"}
                },
                headers={"Retry-After": str(self.window_seconds)},
            )
        window.append(now)
        return await call_next(request)


import time
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(
        self,
        app,
        max_requests=20,
        window_seconds=60,
    ):
        super().__init__(app)

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = Lock()

        self.limited_paths = {
            "/chat",
            "/ask",
            "/diagnose",
            "/generate-fix",
        }

    async def dispatch(self, request, call_next):

        if request.url.path not in self.limited_paths:
            return await call_next(request)

        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        current_time = time.monotonic()

        with self.lock:
            request_times = self.requests[client_ip]

            while (
                request_times
                and current_time - request_times[0]
                >= self.window_seconds
            ):
                request_times.popleft()

            if len(request_times) >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            "Rate limit exceeded. "
                            "Please try again later."
                        )
                    },
                )

            request_times.append(current_time)

        return await call_next(request)

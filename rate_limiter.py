import asyncio
import time

class RateLimiter:
    def __init__(self, delay: float):
        self.delay = max(0.0, delay)
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def wait(self):
        async with self._lock:
            now = time.monotonic()
            remaining = self.delay - (now - self._last)
            if remaining > 0:
                await asyncio.sleep(remaining)
            self._last = time.monotonic()

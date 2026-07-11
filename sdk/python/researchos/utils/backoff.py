"""Exponential backoff with jitter for retry logic."""

import random
import time


class ExponentialBackoff:
    """Exponential backoff with configurable jitter.

    Usage:
        backoff = ExponentialBackoff(base_delay=1.0, max_delay=60.0)
        delay = backoff.get_delay()  # first call returns ~1s
        backoff.reset()              # reset after success
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self._attempt = 0

    def get_delay(self) -> float:
        """Return the delay in seconds for the current attempt."""
        delay = min(self.base_delay * (2 ** self._attempt), self.max_delay)
        if self.jitter:
            delay = delay * (0.5 + random.random())
        self._attempt += 1
        return delay

    def reset(self) -> None:
        """Reset the attempt counter (call after a successful operation)."""
        self._attempt = 0

    def sleep(self) -> None:
        """Sleep for the current delay duration."""
        time.sleep(self.get_delay())

    @property
    def attempt(self) -> int:
        """Current attempt number (0-based)."""
        return self._attempt

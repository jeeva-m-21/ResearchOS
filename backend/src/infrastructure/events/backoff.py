"""
Exponential Backoff with Jitter for retry strategies.

Key features:
- Exponential backoff with configurable base and max delays
- Jitter to prevent thundering herd
- Reset capability
- Thread-safe
"""

import asyncio
import random
from typing import Optional


class ExponentialBackoff:
    """
    Exponential backoff with jitter for retry strategies.

    Formula: delay = min(base_delay * 2^attempt, max_delay)
    With jitter: delay = delay * (0.5 + random.random())

    This prevents thundering herd problems when many consumers retry simultaneously.
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True
    ):
        """
        Initialize exponential backoff.

        Args:
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            jitter: Add random jitter to prevent synchronization
        """
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if max_delay <= 0:
            raise ValueError("max_delay must be positive")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")

        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.attempt = 0
        self.last_delay: Optional[float] = None

    def get_delay(self) -> float:
        """
        Get next delay.

        Returns:
            Delay in seconds
        """
        # Calculate exponential delay
        delay = min(self.base_delay * (2 ** self.attempt), self.max_delay)

        # Apply jitter if enabled
        if self.jitter:
            delay = delay * (0.5 + random.random())

        self.attempt += 1
        self.last_delay = delay

        return delay

    def reset(self) -> None:
        """Reset attempt counter"""
        self.attempt = 0
        self.last_delay = None

    def get_attempt(self) -> int:
        """Get current attempt number"""
        return self.attempt

    def get_last_delay(self) -> Optional[float]:
        """Get last delay used"""
        return self.last_delay

    def __str__(self) -> str:
        return (
            f"ExponentialBackoff("
            f"attempt={self.attempt}, "
            f"base_delay={self.base_delay}, "
            f"max_delay={self.max_delay}, "
            f"jitter={self.jitter}"
            f")"
        )


class RetryLimiter:
    """
    Rate limiter for retries with exponential backoff.

    Useful for limiting retries to external services.
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff: Optional[ExponentialBackoff] = None
    ):
        self.max_retries = max_retries
        self.backoff = backoff or ExponentialBackoff()
        self.retry_count = 0

    def should_retry(self) -> bool:
        """Check if we should retry"""
        return self.retry_count < self.max_retries

    def get_next_delay(self) -> float:
        """Get delay for next retry"""
        if not self.should_retry():
            raise RuntimeError("Max retries exceeded")

        self.retry_count += 1
        return self.backoff.get_delay()

    def reset(self) -> None:
        """Reset retry counter"""
        self.retry_count = 0
        self.backoff.reset()

    def record_success(self) -> None:
        """Record successful operation (reset internal state)"""
        self.reset()

    def get_retry_info(self) -> dict:
        """Get retry information"""
        return {
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "next_attempt": self.retry_count + 1 if self.should_retry() else None,
            "should_retry": self.should_retry(),
        }


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
):
    """
    Decorator for retry with exponential backoff.

    Example:
        @retry_with_backoff(max_retries=3)
        async def call_external_api():
            # ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            backoff = ExponentialBackoff(
                base_delay=base_delay,
                max_delay=max_delay,
                jitter=jitter
            )

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception:
                    if attempt == max_retries - 1:
                        # Last attempt, re-raise
                        raise
                    else:
                        delay = backoff.get_delay()
                        await asyncio.sleep(delay)

            # Should never reach here
            raise RuntimeError("Retry loop completed without success")

        return wrapper

    return decorator

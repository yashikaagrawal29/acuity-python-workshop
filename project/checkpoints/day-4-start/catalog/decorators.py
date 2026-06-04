"""Reusable decorators (Day 1 Lab 3).

These get reused on every later day:
- Day 2: `@retry` wraps the HTTP `APIClient`
- Day 3: tests verify both decorators behave under failure
- Day 4: `@tool` (in agent.py) is built from the same registration pattern
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., object])


def log_calls(func: F) -> F:
    """Log every call: function name, args, return value (or exception)."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("call %s args=%s kwargs=%s", func.__name__, args, kwargs)
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            logger.exception("%s raised %s", func.__name__, exc)
            raise
        logger.info("return %s -> %r", func.__name__, result)
        return result

    return wrapper  # type: ignore[return-value]


def retry(
    times: int = 3,
    delay: float = 0.1,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[F], F]:
    """Retry `func` up to `times` attempts, sleeping `delay` seconds between."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: BaseException | None = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    logger.warning(
                        "%s attempt %d/%d failed: %s",
                        func.__name__, attempt, times, exc,
                    )
                    if attempt < times:
                        time.sleep(delay)
            assert last_exc is not None
            raise last_exc

        return wrapper  # type: ignore[return-value]

    return decorator

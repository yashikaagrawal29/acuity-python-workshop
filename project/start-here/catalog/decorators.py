"""Reusable decorators (Day 1 Lab 3) — reused on Days 2, 3, 4.

`functools.wraps` is non-negotiable: Day-3 tests assert that the wrapped
function keeps its `__name__`. Fill the `# TODO`s.

Done-signal: the TestDecorators class in `tests/test_lab03.py`.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., object])


def log_calls(func: F) -> F:
    """Log every call: name + args, then the return value (or the exception)."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # TODO: log the call; run it; log the return.
        #       On exception: log it and re-raise (don't swallow).
        # hint (notebook §7-8): result = func(*args, **kwargs); return result   (wraps keeps __name__)
        ...

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
            # TODO: loop up to `times`; on a caught exception, log a warning and
            #       sleep(delay) between attempts; re-raise the last one if all fail.
            # hint (notebook §9): for attempt in range(1, times + 1): try: return func(...) except ...: if attempt == times: raise
            ...

        return wrapper  # type: ignore[return-value]

    return decorator

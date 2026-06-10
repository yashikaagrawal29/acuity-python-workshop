from __future__ import annotations

import pytest

from catalog.decorators import log_calls, retry


def test_log_calls_keeps_name_and_logs_return(caplog):
    caplog.set_level("INFO")

    @log_calls
    def add(a, b):
        return a + b

    assert add.__name__ == "add"
    assert add(2, 3) == 5
    assert "call add" in caplog.text
    assert "return add" in caplog.text


def test_log_calls_reraises_exceptions(caplog):
    caplog.set_level("ERROR")

    @log_calls
    def boom():
        raise ValueError("bad")

    with pytest.raises(ValueError, match="bad"):
        boom()
    assert "raised bad" in caplog.text


def test_retry_retries_then_succeeds():
    attempts = {"count": 0}

    @retry(times=3, delay=0, exceptions=(ValueError,))
    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("try again")
        return "ok"

    assert flaky() == "ok"
    assert attempts["count"] == 3


def test_retry_reraises_last_exception_when_exhausted():
    @retry(times=2, delay=0, exceptions=(ValueError,))
    def always_fails():
        raise ValueError("still failing")

    with pytest.raises(ValueError, match="still failing"):
        always_fails()


def test_retry_does_not_catch_unlisted_exception_type():
    attempts = {"count": 0}

    @retry(times=3, delay=0, exceptions=(ValueError,))
    def raises_type_error():
        attempts["count"] += 1
        raise TypeError("wrong type")

    with pytest.raises(TypeError, match="wrong type"):
        raises_type_error()
    assert attempts["count"] == 1

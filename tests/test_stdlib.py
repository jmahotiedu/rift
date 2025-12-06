"""Standard library tests."""

from __future__ import annotations

import pytest

from rift.__main__ import run


def test_len(capsys: pytest.CaptureFixture[str]) -> None:
    run("print(len(\"hello\"));")
    assert capsys.readouterr().out.strip() == "5"


def test_str(capsys: pytest.CaptureFixture[str]) -> None:
    run("print(str(42));")
    assert capsys.readouterr().out.strip() == "42"


def test_type(capsys: pytest.CaptureFixture[str]) -> None:
    run("print(type(1)); print(type(\"x\")); print(type(true));")
    out = capsys.readouterr().out
    assert "number" in out and "string" in out and "bool" in out


def test_clock_returns_number(capsys: pytest.CaptureFixture[str]) -> None:
    ok = run("let t = clock(); print(t > 0);")
    assert ok is True
    assert "true" in capsys.readouterr().out.lower()

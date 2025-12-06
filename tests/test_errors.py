"""Error reporting tests."""

from __future__ import annotations

import pytest

from rift.__main__ import run
from rift.scanner import Scanner


def test_scan_error_unclosed_string() -> None:
    s = Scanner('"hello')
    s.scan_tokens()
    assert len(s.errors) > 0
    assert any("unterminated" in str(e).lower() or "string" in str(e).lower() for e in s.errors)


def test_parse_error_returns_false() -> None:
    assert run("let a = ;") is False
    assert run("print(1 2);") is False


def test_resolver_error_use_before_decl() -> None:
    # Using a variable in its own initializer
    ok = run("let x = x + 1;")
    assert ok is False


def test_runtime_error_not_callable() -> None:
    assert run("let x = 1; x();") is False

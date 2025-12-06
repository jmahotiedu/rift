"""Closure tests."""

from __future__ import annotations

import pytest

from rift.__main__ import run


def test_closure_counter(capsys: pytest.CaptureFixture[str]) -> None:
    src = """
    fn makeCounter() {
      let count = 0;
      fn inc() {
        count = count + 1;
        return count;
      }
      return inc;
    }
    let c = makeCounter();
    print(c());
    print(c());
    print(c());
    """
    ok = run(src)
    assert ok is True
    out = capsys.readouterr().out
    assert "1" in out and "2" in out and "3" in out


def test_closure_captures_outer() -> None:
    ok = run("fn outer(x) { fn inner() { return x; } return inner; } let f = outer(42); print(f());")
    assert ok is True

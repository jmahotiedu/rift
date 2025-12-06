"""End-to-end interpreter tests."""

from __future__ import annotations

import pytest

from rift.__main__ import run


def test_run_print(capsys: pytest.CaptureFixture[str]) -> None:
    run("print(1 + 2);")
    captured = capsys.readouterr()
    assert captured.out.strip() == "3"


def test_run_let_and_print(capsys: pytest.CaptureFixture[str]) -> None:
    run("let x = 10; print(x + 5);")
    captured = capsys.readouterr()
    assert captured.out.strip() == "15"


def test_run_function(capsys: pytest.CaptureFixture[str]) -> None:
    run("fn add(a, b) { return a + b; } print(add(2, 3));")
    captured = capsys.readouterr()
    assert captured.out.strip() == "5"


def test_run_invalid_syntax_returns_false() -> None:
    ok = run("let x = ;")
    assert ok is False


def test_run_runtime_error_returns_false() -> None:
    # Calling a non-callable triggers RiftRuntimeError
    ok = run("let x = 1; x();")
    assert ok is False


def test_fibonacci_example(capsys: pytest.CaptureFixture[str]) -> None:
    from pathlib import Path
    examples_dir = Path(__file__).resolve().parent.parent / "examples"
    fib_path = examples_dir / "fibonacci.rf"
    if not fib_path.exists():
        pytest.skip("examples/fibonacci.rf not found")
    run(fib_path.read_text())
    captured = capsys.readouterr()
    assert "55" in captured.out  # fib(10) = 55

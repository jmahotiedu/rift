"""Class and inheritance tests."""

from __future__ import annotations

import pytest

from rift.__main__ import run


def test_class_init_and_method(capsys: pytest.CaptureFixture[str]) -> None:
    src = """
    class Box {
      init(v) {
        this.value = v;
      }
      get() {
        return this.value;
      }
    }
    let b = Box(10);
    print(b.get());
    """
    ok = run(src)
    assert ok is True
    assert capsys.readouterr().out.strip() == "10"


def test_inheritance(capsys: pytest.CaptureFixture[str]) -> None:
    src = """
    class A {
      init() {}
      m() { return "A"; }
    }
    class B < A {
      m() { return "B"; }
    }
    let b = B();
    print(b.m());
    """
    ok = run(src)
    assert ok is True
    assert capsys.readouterr().out.strip() == "B"


def test_super_method_dispatch(capsys: pytest.CaptureFixture[str]) -> None:
    src = """
    class Animal {
      init(name) { this.name = name; }
      speak() { return this.name + " noise"; }
    }

    class Dog < Animal {
      speak() { return super.speak() + " bark"; }
    }

    let d = Dog("sam");
    print(d.speak());
    """
    ok = run(src)
    assert ok is True
    assert capsys.readouterr().out.strip() == "sam noise bark"

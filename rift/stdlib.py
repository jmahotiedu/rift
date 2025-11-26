from __future__ import annotations

import time
from typing import TYPE_CHECKING

from rift.callable import NativeFunction
from rift.environment import Environment
from rift.instance import RiftInstance

if TYPE_CHECKING:
    pass


def _clock() -> float:
    return time.time()


def _len_fn(value: object) -> object:
    if isinstance(value, str):
        return float(len(value))
    raise ValueError("len() argument must be a string")


def _str_fn(value: object) -> str:
    return _stringify(value)


def _num_fn(value: object) -> float:
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"cannot convert {value!r} to a number")
    raise ValueError("num() argument must be a string")


def _input_fn(prompt: object) -> str:
    return input(_stringify(prompt))


def _type_fn(value: object) -> str:
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, RiftInstance):
        return value.klass.name
    return "function"


def _stringify(value: object) -> str:
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        text = str(value)
        if text.endswith(".0"):
            text = text[:-2]
        return text
    return str(value)


def define_natives(environment: Environment) -> None:
    environment.define("clock", NativeFunction("clock", _clock, 0))
    environment.define("len", NativeFunction("len", _len_fn, 1))
    environment.define("str", NativeFunction("str", _str_fn, 1))
    environment.define("num", NativeFunction("num", _num_fn, 1))
    environment.define("input", NativeFunction("input", _input_fn, 1))
    environment.define("type", NativeFunction("type", _type_fn, 1))


# re-export for use elsewhere
stringify = _stringify

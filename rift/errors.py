from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rift.tokens import Token


@dataclass
class ScanError(Exception):
    line: int
    column: int
    msg: str

    def __str__(self) -> str:
        return f"[line {self.line}, col {self.column}] Scan error: {self.msg}"


@dataclass
class ParseError(Exception):
    token: Token
    msg: str

    def __str__(self) -> str:
        return f"[line {self.token.line}] Parse error at {self.token.lexeme!r}: {self.msg}"


@dataclass
class RiftRuntimeError(Exception):
    token: Token
    msg: str

    def __str__(self) -> str:
        return f"[line {self.token.line}] Runtime error: {self.msg}"


class ReturnException(Exception):
    """Control flow mechanism for function returns."""

    def __init__(self, value: object) -> None:
        super().__init__()
        self.value = value

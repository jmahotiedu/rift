from __future__ import annotations

from typing import TYPE_CHECKING

from rift.errors import RiftRuntimeError
from rift.tokens import Token

if TYPE_CHECKING:
    from rift.callable import RiftClass


class RiftInstance:
    def __init__(self, klass: RiftClass) -> None:
        self.klass = klass
        self.fields: dict[str, object] = {}

    def get(self, name: Token) -> object:
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        method = self.klass.find_method(name.lexeme)
        if method is not None:
            return method.bind(self)

        raise RiftRuntimeError(name, f"undefined property '{name.lexeme}'")

    def set(self, name: Token, value: object) -> None:
        self.fields[name.lexeme] = value

    def __repr__(self) -> str:
        return f"<{self.klass.name} instance>"

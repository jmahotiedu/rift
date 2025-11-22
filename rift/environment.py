from __future__ import annotations

from rift.errors import RiftRuntimeError
from rift.tokens import Token


class Environment:
    def __init__(self, enclosing: Environment | None = None) -> None:
        self.values: dict[str, object] = {}
        self.enclosing = enclosing

    def define(self, name: str, value: object) -> None:
        self.values[name] = value

    def get(self, name: Token) -> object:
        if name.lexeme in self.values:
            return self.values[name.lexeme]
        if self.enclosing is not None:
            return self.enclosing.get(name)
        raise RiftRuntimeError(name, f"undefined variable '{name.lexeme}'")

    def assign(self, name: Token, value: object) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return
        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return
        raise RiftRuntimeError(name, f"undefined variable '{name.lexeme}'")

    def get_at(self, distance: int, name: str) -> object:
        return self._ancestor(distance).values[name]

    def assign_at(self, distance: int, name: Token, value: object) -> None:
        self._ancestor(distance).values[name.lexeme] = value

    def _ancestor(self, distance: int) -> Environment:
        env: Environment = self
        for _ in range(distance):
            assert env.enclosing is not None
            env = env.enclosing
        return env

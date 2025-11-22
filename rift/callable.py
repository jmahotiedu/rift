from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Callable

from rift.environment import Environment
from rift.errors import ReturnException

if TYPE_CHECKING:
    from rift.interpreter import Interpreter
    from rift.instance import RiftInstance
    from rift import ast_nodes as ast


class RiftCallable(Protocol):
    def call(self, interpreter: Interpreter, arguments: list[object]) -> object: ...
    def arity(self) -> int: ...


class RiftFunction:
    def __init__(
        self,
        declaration: ast.FunctionStmt,
        closure: Environment,
        is_initializer: bool = False,
    ) -> None:
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        env = Environment(self.closure)
        for param, arg in zip(self.declaration.params, arguments):
            env.define(param.lexeme, arg)
        try:
            interpreter._execute_block(self.declaration.body, env)
        except ReturnException as ret:
            # init always returns 'this'
            if self.is_initializer:
                return self.closure.get_at(0, "this")
            return ret.value
        if self.is_initializer:
            return self.closure.get_at(0, "this")
        return None

    def arity(self) -> int:
        return len(self.declaration.params)

    def bind(self, instance: RiftInstance) -> RiftFunction:
        env = Environment(self.closure)
        env.define("this", instance)
        return RiftFunction(self.declaration, env, self.is_initializer)

    def __repr__(self) -> str:
        return f"<fn {self.declaration.name.lexeme}>"


class RiftClass:
    def __init__(
        self,
        name: str,
        superclass: RiftClass | None,
        methods: dict[str, RiftFunction],
    ) -> None:
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        from rift.instance import RiftInstance

        instance = RiftInstance(self)
        initializer = self.find_method("init")
        if initializer is not None:
            initializer.bind(instance).call(interpreter, arguments)
        return instance

    def arity(self) -> int:
        initializer = self.find_method("init")
        if initializer is not None:
            return initializer.arity()
        return 0

    def find_method(self, name: str) -> RiftFunction | None:
        if name in self.methods:
            return self.methods[name]
        if self.superclass is not None:
            return self.superclass.find_method(name)
        return None

    def __repr__(self) -> str:
        return f"<class {self.name}>"


class NativeFunction:
    def __init__(self, name: str, func: Callable[..., object], arity_count: int) -> None:
        self.name = name
        self.func = func
        self._arity = arity_count

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        return self.func(*arguments)

    def arity(self) -> int:
        return self._arity

    def __repr__(self) -> str:
        return f"<native fn {self.name}>"

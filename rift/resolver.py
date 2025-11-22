from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from rift import ast_nodes as ast
from rift.errors import ParseError
from rift.tokens import Token

if TYPE_CHECKING:
    from rift.interpreter import Interpreter


class _FunctionType(Enum):
    NONE = auto()
    FUNCTION = auto()
    METHOD = auto()
    INITIALIZER = auto()


class _ClassType(Enum):
    NONE = auto()
    CLASS = auto()
    SUBCLASS = auto()


class Resolver:
    def __init__(self, interpreter: Interpreter) -> None:
        self.interpreter = interpreter
        self.scopes: list[dict[str, bool]] = []
        self._current_function = _FunctionType.NONE
        self._current_class = _ClassType.NONE
        self.errors: list[ParseError] = []

    def resolve(self, statements: list[ast.Stmt]) -> None:
        for stmt in statements:
            self._resolve_stmt(stmt)

    def _resolve_stmt(self, stmt: ast.Stmt) -> None:
        match stmt:
            case ast.BlockStmt(statements):
                self._begin_scope()
                self.resolve(statements)
                self._end_scope()
            case ast.LetStmt(name, initializer):
                self._declare(name)
                if initializer is not None:
                    self._resolve_expr(initializer)
                self._define(name)
            case ast.FunctionStmt(name, _, _):
                self._declare(name)
                self._define(name)
                self._resolve_function(stmt, _FunctionType.FUNCTION)
            case ast.ExpressionStmt(expression):
                self._resolve_expr(expression)
            case ast.IfStmt(condition, then_branch, else_branch):
                self._resolve_expr(condition)
                self._resolve_stmt(then_branch)
                if else_branch is not None:
                    self._resolve_stmt(else_branch)
            case ast.PrintStmt(expression):
                self._resolve_expr(expression)
            case ast.ReturnStmt(keyword, value):
                if self._current_function == _FunctionType.NONE:
                    self.errors.append(ParseError(keyword, "cannot return from top-level code"))
                if value is not None:
                    if self._current_function == _FunctionType.INITIALIZER:
                        self.errors.append(
                            ParseError(keyword, "cannot return a value from an initializer")
                        )
                    self._resolve_expr(value)
            case ast.WhileStmt(condition, body):
                self._resolve_expr(condition)
                self._resolve_stmt(body)
            case ast.ClassStmt(name, superclass, methods):
                enclosing_class = self._current_class
                self._current_class = _ClassType.CLASS
                self._declare(name)
                self._define(name)

                if superclass is not None:
                    if superclass.name.lexeme == name.lexeme:
                        self.errors.append(
                            ParseError(superclass.name, "a class cannot inherit from itself")
                        )
                    self._current_class = _ClassType.SUBCLASS
                    self._resolve_expr(superclass)
                    self._begin_scope()
                    self.scopes[-1]["super"] = True

                self._begin_scope()
                self.scopes[-1]["this"] = True

                for method in methods:
                    ft = _FunctionType.METHOD
                    if method.name.lexeme == "init":
                        ft = _FunctionType.INITIALIZER
                    self._resolve_function(method, ft)

                self._end_scope()
                if superclass is not None:
                    self._end_scope()
                self._current_class = enclosing_class

    def _resolve_expr(self, expr: ast.Expr) -> None:
        match expr:
            case ast.VariableExpr(name):
                if self.scopes and self.scopes[-1].get(name.lexeme) is False:
                    self.errors.append(
                        ParseError(name, "cannot read variable in its own initializer")
                    )
                self._resolve_local(expr, name)
            case ast.AssignExpr(name, value):
                self._resolve_expr(value)
                self._resolve_local(expr, name)
            case ast.BinaryExpr(left, _, right):
                self._resolve_expr(left)
                self._resolve_expr(right)
            case ast.UnaryExpr(_, operand):
                self._resolve_expr(operand)
            case ast.LogicalExpr(left, _, right):
                self._resolve_expr(left)
                self._resolve_expr(right)
            case ast.CallExpr(callee, arguments, _):
                self._resolve_expr(callee)
                for arg in arguments:
                    self._resolve_expr(arg)
            case ast.GetExpr(obj, _):
                self._resolve_expr(obj)
            case ast.SetExpr(obj, _, value):
                self._resolve_expr(value)
                self._resolve_expr(obj)
            case ast.GroupingExpr(expression):
                self._resolve_expr(expression)
            case ast.LiteralExpr(_):
                pass
            case ast.ThisExpr(keyword):
                if self._current_class == _ClassType.NONE:
                    self.errors.append(
                        ParseError(keyword, "cannot use 'this' outside of a class")
                    )
                self._resolve_local(expr, keyword)
            case ast.SuperExpr(keyword, _):
                if self._current_class == _ClassType.NONE:
                    self.errors.append(
                        ParseError(keyword, "cannot use 'super' outside of a class")
                    )
                elif self._current_class != _ClassType.SUBCLASS:
                    self.errors.append(
                        ParseError(keyword, "cannot use 'super' in a class with no superclass")
                    )
                self._resolve_local(expr, keyword)

    def _resolve_function(self, function: ast.FunctionStmt, fn_type: _FunctionType) -> None:
        enclosing = self._current_function
        self._current_function = fn_type
        self._begin_scope()
        for param in function.params:
            self._declare(param)
            self._define(param)
        self.resolve(function.body)
        self._end_scope()
        self._current_function = enclosing

    def _resolve_local(self, expr: ast.Expr, name: Token) -> None:
        for i in range(len(self.scopes) - 1, -1, -1):
            if name.lexeme in self.scopes[i]:
                self.interpreter.resolve(expr, len(self.scopes) - 1 - i)
                return

    def _declare(self, name: Token) -> None:
        if not self.scopes:
            return
        scope = self.scopes[-1]
        if name.lexeme in scope:
            self.errors.append(
                ParseError(name, f"variable '{name.lexeme}' already declared in this scope")
            )
        scope[name.lexeme] = False

    def _define(self, name: Token) -> None:
        if not self.scopes:
            return
        self.scopes[-1][name.lexeme] = True

    def _begin_scope(self) -> None:
        self.scopes.append({})

    def _end_scope(self) -> None:
        self.scopes.pop()

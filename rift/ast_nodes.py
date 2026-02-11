from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rift.tokens import Token


# -- expressions --

@dataclass
class BinaryExpr:
    left: Expr
    operator: Token
    right: Expr


@dataclass
class UnaryExpr:
    operator: Token
    operand: Expr


@dataclass
class LiteralExpr:
    value: object


@dataclass
class GroupingExpr:
    expression: Expr


@dataclass
class VariableExpr:
    name: Token


@dataclass
class AssignExpr:
    name: Token
    value: Expr


@dataclass
class LogicalExpr:
    left: Expr
    operator: Token
    right: Expr


@dataclass
class CallExpr:
    callee: Expr
    arguments: list[Expr]
    paren: Token


@dataclass
class GetExpr:
    object: Expr
    name: Token


@dataclass
class SetExpr:
    object: Expr
    name: Token
    value: Expr


@dataclass
class ThisExpr:
    keyword: Token


@dataclass
class SuperExpr:
    keyword: Token
    method: Token


Expr = (
    BinaryExpr
    | UnaryExpr
    | LiteralExpr
    | GroupingExpr
    | VariableExpr
    | AssignExpr
    | LogicalExpr
    | CallExpr
    | GetExpr
    | SetExpr
    | ThisExpr
    | SuperExpr
)


# -- statements --

@dataclass
class ExpressionStmt:
    expression: Expr


@dataclass
class PrintStmt:
    expression: Expr


@dataclass
class LetStmt:
    name: Token
    initializer: Expr | None


@dataclass
class BlockStmt:
    statements: list[Stmt]


@dataclass
class IfStmt:
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt | None


@dataclass
class WhileStmt:
    condition: Expr
    body: Stmt


@dataclass
class FunctionStmt:
    name: Token
    params: list[Token]
    body: list[Stmt]


@dataclass
class ReturnStmt:
    keyword: Token
    value: Expr | None


@dataclass
class ClassStmt:
    name: Token
    superclass: VariableExpr | None
    methods: list[FunctionStmt]


Stmt = (
    ExpressionStmt
    | PrintStmt
    | LetStmt
    | BlockStmt
    | IfStmt
    | WhileStmt
    | FunctionStmt
    | ReturnStmt
    | ClassStmt
)

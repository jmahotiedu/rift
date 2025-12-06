"""Parser tests."""

from __future__ import annotations

from rift import ast_nodes as ast
from rift.parser import Parser
from rift.scanner import Scanner


def test_parse_print() -> None:
    s = Scanner("print(1 + 2);")
    s.scan_tokens()
    p = Parser(s.tokens)
    stmts = p.parse()
    assert len(stmts) == 1
    assert isinstance(stmts[0], ast.PrintStmt)


def test_parse_let() -> None:
    s = Scanner("let x = 10;")
    s.scan_tokens()
    p = Parser(s.tokens)
    stmts = p.parse()
    assert len(stmts) == 1
    assert isinstance(stmts[0], ast.LetStmt)
    assert stmts[0].name.lexeme == "x"


def test_parse_if() -> None:
    s = Scanner("if (true) { print(1); } else { print(2); }")
    s.scan_tokens()
    p = Parser(s.tokens)
    stmts = p.parse()
    assert len(stmts) == 1
    assert isinstance(stmts[0], ast.IfStmt)
    assert stmts[0].else_branch is not None


def test_parse_function() -> None:
    s = Scanner("fn add(a, b) { return a + b; }")
    s.scan_tokens()
    p = Parser(s.tokens)
    stmts = p.parse()
    assert len(stmts) == 1
    assert isinstance(stmts[0], ast.FunctionStmt)
    assert stmts[0].name.lexeme == "add"
    assert len(stmts[0].params) == 2

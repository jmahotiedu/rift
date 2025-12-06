"""Scanner/tokenizer tests."""

from __future__ import annotations

from rift.scanner import Scanner
from rift.tokens import TokenType


def test_scan_numbers() -> None:
    s = Scanner("1 42 3.14")
    tokens = s.scan_tokens()
    assert len(tokens) >= 4  # 3 numbers + EOF
    assert tokens[0].type == TokenType.NUMBER and tokens[0].literal == 1.0
    assert tokens[1].type == TokenType.NUMBER and tokens[1].literal == 42.0
    assert tokens[2].type == TokenType.NUMBER and tokens[2].literal == 3.14
    assert tokens[-1].type == TokenType.EOF


def test_scan_keywords_and_identifiers() -> None:
    s = Scanner("let x = 1; if true { }")
    tokens = s.scan_tokens()
    types = [t.type for t in tokens]
    assert TokenType.LET in types
    assert TokenType.IDENTIFIER in types
    assert TokenType.IF in types
    assert TokenType.TRUE in types
    assert TokenType.LEFT_BRACE in types
    assert TokenType.RIGHT_BRACE in types


def test_scan_string() -> None:
    s = Scanner('"hello"')
    tokens = s.scan_tokens()
    assert len(tokens) == 2
    assert tokens[0].type == TokenType.STRING and tokens[0].literal == "hello"


def test_scan_operators() -> None:
    s = Scanner("== != <= >=")
    tokens = s.scan_tokens()
    assert tokens[0].type == TokenType.EQUAL_EQUAL
    assert tokens[1].type == TokenType.BANG_EQUAL
    assert tokens[2].type == TokenType.LESS_EQUAL
    assert tokens[3].type == TokenType.GREATER_EQUAL

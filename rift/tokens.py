from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # single-char tokens
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    DOT = auto()
    MINUS = auto()
    PLUS = auto()
    SEMICOLON = auto()
    SLASH = auto()
    STAR = auto()
    PERCENT = auto()

    # one or two char tokens
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()

    # literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # keywords
    AND = auto()
    CLASS = auto()
    ELSE = auto()
    FALSE = auto()
    FN = auto()
    FOR = auto()
    IF = auto()
    LET = auto()
    NIL = auto()
    OR = auto()
    PRINT = auto()
    RETURN = auto()
    SUPER = auto()
    THIS = auto()
    TRUE = auto()
    WHILE = auto()

    EOF = auto()


KEYWORDS: dict[str, TokenType] = {
    "and": TokenType.AND,
    "class": TokenType.CLASS,
    "else": TokenType.ELSE,
    "false": TokenType.FALSE,
    "fn": TokenType.FN,
    "for": TokenType.FOR,
    "if": TokenType.IF,
    "let": TokenType.LET,
    "nil": TokenType.NIL,
    "or": TokenType.OR,
    "print": TokenType.PRINT,
    "return": TokenType.RETURN,
    "super": TokenType.SUPER,
    "this": TokenType.THIS,
    "true": TokenType.TRUE,
    "while": TokenType.WHILE,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    literal: object
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.lexeme!r}, {self.literal!r})"

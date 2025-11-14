from __future__ import annotations

from rift.tokens import KEYWORDS, Token, TokenType
from rift.errors import ScanError


class Scanner:
    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens: list[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.errors: list[ScanError] = []

    def scan_tokens(self) -> list[Token]:
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.column))
        return self.tokens

    def _scan_token(self) -> None:
        c = self._advance()
        match c:
            case "(":
                self._add_token(TokenType.LEFT_PAREN)
            case ")":
                self._add_token(TokenType.RIGHT_PAREN)
            case "{":
                self._add_token(TokenType.LEFT_BRACE)
            case "}":
                self._add_token(TokenType.RIGHT_BRACE)
            case ",":
                self._add_token(TokenType.COMMA)
            case ".":
                self._add_token(TokenType.DOT)
            case "-":
                self._add_token(TokenType.MINUS)
            case "+":
                self._add_token(TokenType.PLUS)
            case ";":
                self._add_token(TokenType.SEMICOLON)
            case "*":
                self._add_token(TokenType.STAR)
            case "%":
                self._add_token(TokenType.PERCENT)
            case "!":
                self._add_token(TokenType.BANG_EQUAL if self._match("=") else TokenType.BANG)
            case "=":
                self._add_token(TokenType.EQUAL_EQUAL if self._match("=") else TokenType.EQUAL)
            case "<":
                self._add_token(TokenType.LESS_EQUAL if self._match("=") else TokenType.LESS)
            case ">":
                self._add_token(
                    TokenType.GREATER_EQUAL if self._match("=") else TokenType.GREATER
                )
            case "/":
                if self._match("/"):
                    # single-line comment: consume until end of line
                    while not self._is_at_end() and self._peek() != "\n":
                        self._advance()
                else:
                    self._add_token(TokenType.SLASH)
            case " " | "\r" | "\t":
                pass
            case "\n":
                self.line += 1
                self.column = 1
            case '"':
                self._string()
            case _:
                if c.isdigit():
                    self._number()
                elif c.isalpha() or c == "_":
                    self._identifier()
                else:
                    self.errors.append(
                        ScanError(self.line, self.column - 1, f"unexpected character {c!r}")
                    )

    def _string(self) -> None:
        start_line = self.line
        start_col = self.column - 1
        value_chars: list[str] = []

        while not self._is_at_end() and self._peek() != '"':
            ch = self._peek()
            if ch == "\n":
                self.line += 1
                self.column = 0
            if ch == "\\":
                self._advance()
                esc = self._advance() if not self._is_at_end() else ""
                match esc:
                    case "n":
                        value_chars.append("\n")
                    case "t":
                        value_chars.append("\t")
                    case "\\":
                        value_chars.append("\\")
                    case '"':
                        value_chars.append('"')
                    case _:
                        value_chars.append("\\" + esc)
            else:
                value_chars.append(self._advance())

        if self._is_at_end():
            self.errors.append(ScanError(start_line, start_col, "unterminated string"))
            return

        self._advance()  # closing "
        self._add_token(TokenType.STRING, "".join(value_chars))

    def _number(self) -> None:
        while not self._is_at_end() and self._peek().isdigit():
            self._advance()

        # fractional part
        if not self._is_at_end() and self._peek() == "." and self._peek_next().isdigit():
            self._advance()  # consume .
            while not self._is_at_end() and self._peek().isdigit():
                self._advance()

        self._add_token(TokenType.NUMBER, float(self.source[self.start : self.current]))

    def _identifier(self) -> None:
        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        text = self.source[self.start : self.current]
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        self._add_token(token_type)

    def _advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        self.column += 1
        return c

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _add_token(self, token_type: TokenType, literal: object = None) -> None:
        text = self.source[self.start : self.current]
        col = self.column - len(text)
        self.tokens.append(Token(token_type, text, literal, self.line, col))

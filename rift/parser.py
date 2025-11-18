from __future__ import annotations

from rift.tokens import Token, TokenType
from rift.errors import ParseError
from rift import ast_nodes as ast


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0
        self.errors: list[ParseError] = []

    def parse(self) -> list[ast.Stmt]:
        statements: list[ast.Stmt] = []
        while not self._is_at_end():
            stmt = self._declaration()
            if stmt is not None:
                statements.append(stmt)
        return statements

    # -- declarations --

    def _declaration(self) -> ast.Stmt | None:
        try:
            if self._match(TokenType.CLASS):
                return self._class_declaration()
            if self._match(TokenType.FN):
                return self._function("function")
            if self._match(TokenType.LET):
                return self._let_declaration()
            return self._statement()
        except ParseError:
            self._synchronize()
            return None

    def _class_declaration(self) -> ast.ClassStmt:
        name = self._consume(TokenType.IDENTIFIER, "expected class name")

        superclass: ast.VariableExpr | None = None
        if self._match(TokenType.LESS):
            self._consume(TokenType.IDENTIFIER, "expected superclass name")
            superclass = ast.VariableExpr(self._previous())

        self._consume(TokenType.LEFT_BRACE, "expected '{' before class body")
        methods: list[ast.FunctionStmt] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            methods.append(self._function("method"))
        self._consume(TokenType.RIGHT_BRACE, "expected '}' after class body")
        return ast.ClassStmt(name, superclass, methods)

    def _function(self, kind: str) -> ast.FunctionStmt:
        name = self._consume(TokenType.IDENTIFIER, f"expected {kind} name")
        self._consume(TokenType.LEFT_PAREN, f"expected '(' after {kind} name")
        params: list[Token] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(params) >= 255:
                    self._error(self._peek(), "cannot have more than 255 parameters")
                params.append(self._consume(TokenType.IDENTIFIER, "expected parameter name"))
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RIGHT_PAREN, f"expected ')' after {kind} parameters")
        self._consume(TokenType.LEFT_BRACE, f"expected '{{' before {kind} body")
        body = self._block_statements()
        return ast.FunctionStmt(name, params, body)

    def _let_declaration(self) -> ast.LetStmt:
        name = self._consume(TokenType.IDENTIFIER, "expected variable name")
        initializer: ast.Expr | None = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "expected ';' after variable declaration")
        return ast.LetStmt(name, initializer)

    # -- statements --

    def _statement(self) -> ast.Stmt:
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.FOR):
            return self._for_statement()
        if self._match(TokenType.LEFT_BRACE):
            return ast.BlockStmt(self._block_statements())
        return self._expression_statement()

    def _if_statement(self) -> ast.IfStmt:
        self._consume(TokenType.LEFT_PAREN, "expected '(' after 'if'")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "expected ')' after if condition")
        then_branch = self._statement()
        else_branch: ast.Stmt | None = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()
        return ast.IfStmt(condition, then_branch, else_branch)

    def _print_statement(self) -> ast.PrintStmt:
        self._consume(TokenType.LEFT_PAREN, "expected '(' after 'print'")
        value = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "expected ')' after print argument")
        self._consume(TokenType.SEMICOLON, "expected ';' after print statement")
        return ast.PrintStmt(value)

    def _return_statement(self) -> ast.ReturnStmt:
        keyword = self._previous()
        value: ast.Expr | None = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "expected ';' after return value")
        return ast.ReturnStmt(keyword, value)

    def _while_statement(self) -> ast.WhileStmt:
        self._consume(TokenType.LEFT_PAREN, "expected '(' after 'while'")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "expected ')' after while condition")
        body = self._statement()
        return ast.WhileStmt(condition, body)

    def _for_statement(self) -> ast.Stmt:
        # desugar for into while
        self._consume(TokenType.LEFT_PAREN, "expected '(' after 'for'")

        initializer: ast.Stmt | None
        if self._match(TokenType.SEMICOLON):
            initializer = None
        elif self._match(TokenType.LET):
            initializer = self._let_declaration()
        else:
            initializer = self._expression_statement()

        condition: ast.Expr | None = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "expected ';' after loop condition")

        increment: ast.Expr | None = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "expected ')' after for clauses")

        body = self._statement()

        # build while from parts
        if increment is not None:
            body = ast.BlockStmt([body, ast.ExpressionStmt(increment)])
        if condition is None:
            condition = ast.LiteralExpr(True)
        body = ast.WhileStmt(condition, body)
        if initializer is not None:
            body = ast.BlockStmt([initializer, body])

        return body

    def _expression_statement(self) -> ast.ExpressionStmt:
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "expected ';' after expression")
        return ast.ExpressionStmt(expr)

    def _block_statements(self) -> list[ast.Stmt]:
        statements: list[ast.Stmt] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            stmt = self._declaration()
            if stmt is not None:
                statements.append(stmt)
        self._consume(TokenType.RIGHT_BRACE, "expected '}' after block")
        return statements

    # -- expressions (pratt / precedence climbing) --

    def _expression(self) -> ast.Expr:
        return self._assignment()

    def _assignment(self) -> ast.Expr:
        expr = self._or()

        if self._match(TokenType.EQUAL):
            equals = self._previous()
            value = self._assignment()

            if isinstance(expr, ast.VariableExpr):
                return ast.AssignExpr(expr.name, value)
            elif isinstance(expr, ast.GetExpr):
                return ast.SetExpr(expr.object, expr.name, value)
            self._error(equals, "invalid assignment target")

        return expr

    def _or(self) -> ast.Expr:
        expr = self._and()
        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._and()
            expr = ast.LogicalExpr(expr, operator, right)
        return expr

    def _and(self) -> ast.Expr:
        expr = self._equality()
        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._equality()
            expr = ast.LogicalExpr(expr, operator, right)
        return expr

    def _equality(self) -> ast.Expr:
        expr = self._comparison()
        while self._match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self._previous()
            right = self._comparison()
            expr = ast.BinaryExpr(expr, operator, right)
        return expr

    def _comparison(self) -> ast.Expr:
        expr = self._term()
        while self._match(TokenType.GREATER, TokenType.GREATER_EQUAL,
                          TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self._previous()
            right = self._term()
            expr = ast.BinaryExpr(expr, operator, right)
        return expr

    def _term(self) -> ast.Expr:
        expr = self._factor()
        while self._match(TokenType.MINUS, TokenType.PLUS):
            operator = self._previous()
            right = self._factor()
            expr = ast.BinaryExpr(expr, operator, right)
        return expr

    def _factor(self) -> ast.Expr:
        expr = self._unary()
        while self._match(TokenType.SLASH, TokenType.STAR, TokenType.PERCENT):
            operator = self._previous()
            right = self._unary()
            expr = ast.BinaryExpr(expr, operator, right)
        return expr

    def _unary(self) -> ast.Expr:
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            right = self._unary()
            return ast.UnaryExpr(operator, right)
        return self._call()

    def _call(self) -> ast.Expr:
        expr = self._primary()

        while True:
            if self._match(TokenType.LEFT_PAREN):
                expr = self._finish_call(expr)
            elif self._match(TokenType.DOT):
                name = self._consume(TokenType.IDENTIFIER, "expected property name after '.'")
                expr = ast.GetExpr(expr, name)
            else:
                break

        return expr

    def _finish_call(self, callee: ast.Expr) -> ast.CallExpr:
        arguments: list[ast.Expr] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    self._error(self._peek(), "cannot have more than 255 arguments")
                arguments.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
        paren = self._consume(TokenType.RIGHT_PAREN, "expected ')' after arguments")
        return ast.CallExpr(callee, arguments, paren)

    def _primary(self) -> ast.Expr:
        if self._match(TokenType.FALSE):
            return ast.LiteralExpr(False)
        if self._match(TokenType.TRUE):
            return ast.LiteralExpr(True)
        if self._match(TokenType.NIL):
            return ast.LiteralExpr(None)
        if self._match(TokenType.NUMBER, TokenType.STRING):
            return ast.LiteralExpr(self._previous().literal)
        if self._match(TokenType.THIS):
            return ast.ThisExpr(self._previous())
        if self._match(TokenType.SUPER):
            keyword = self._previous()
            self._consume(TokenType.DOT, "expected '.' after 'super'")
            method = self._consume(TokenType.IDENTIFIER, "expected superclass method name")
            return ast.SuperExpr(keyword, method)
        if self._match(TokenType.IDENTIFIER):
            return ast.VariableExpr(self._previous())
        if self._match(TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "expected ')' after expression")
            return ast.GroupingExpr(expr)

        raise self._error(self._peek(), "expected expression")

    # -- helpers --

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _error(self, token: Token, message: str) -> ParseError:
        err = ParseError(token, message)
        self.errors.append(err)
        return err

    def _synchronize(self) -> None:
        self._advance()
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            if self._peek().type in (
                TokenType.CLASS, TokenType.FN, TokenType.LET,
                TokenType.FOR, TokenType.IF, TokenType.WHILE,
                TokenType.PRINT, TokenType.RETURN,
            ):
                return
            self._advance()

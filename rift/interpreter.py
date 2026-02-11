from __future__ import annotations

from rift import ast_nodes as ast
from rift.callable import NativeFunction, RiftClass, RiftFunction
from rift.environment import Environment
from rift.errors import ReturnException, RiftRuntimeError
from rift.instance import RiftInstance
from rift.stdlib import define_natives, stringify
from rift.tokens import Token, TokenType


class Interpreter:
    def __init__(self) -> None:
        self.globals = Environment()
        self._environment = self.globals
        self._locals: dict[int, int] = {}  # expr id -> depth
        define_natives(self.globals)

    def interpret(self, statements: list[ast.Stmt]) -> None:
        for stmt in statements:
            self._execute(stmt)

    def resolve(self, expr: ast.Expr, depth: int) -> None:
        self._locals[id(expr)] = depth

    def _execute(self, stmt: ast.Stmt) -> None:
        match stmt:
            case ast.ExpressionStmt(expression):
                self._evaluate(expression)
            case ast.PrintStmt(expression):
                value = self._evaluate(expression)
                print(stringify(value))
            case ast.LetStmt(name, initializer):
                initial_value: object = None
                if initializer is not None:
                    initial_value = self._evaluate(initializer)
                self._environment.define(name.lexeme, initial_value)
            case ast.BlockStmt(statements):
                self._execute_block(statements, Environment(self._environment))
            case ast.IfStmt(condition, then_branch, else_branch):
                if self._is_truthy(self._evaluate(condition)):
                    self._execute(then_branch)
                elif else_branch is not None:
                    self._execute(else_branch)
            case ast.WhileStmt(condition, body):
                while self._is_truthy(self._evaluate(condition)):
                    self._execute(body)
            case ast.FunctionStmt(name, _, _):
                function = RiftFunction(stmt, self._environment)
                self._environment.define(name.lexeme, function)
            case ast.ReturnStmt(_, value):
                ret_val: object = None
                if value is not None:
                    ret_val = self._evaluate(value)
                raise ReturnException(ret_val)
            case ast.ClassStmt(name, superclass_expr, methods):
                superclass: RiftClass | None = None
                if superclass_expr is not None:
                    resolved_superclass = self._evaluate(superclass_expr)
                    if not isinstance(resolved_superclass, RiftClass):
                        raise RiftRuntimeError(
                            superclass_expr.name, "superclass must be a class"
                        )
                    superclass = resolved_superclass

                self._environment.define(name.lexeme, None)

                if superclass is not None:
                    self._environment = Environment(self._environment)
                    self._environment.define("super", superclass)

                method_map: dict[str, RiftFunction] = {}
                for method in methods:
                    is_init = method.name.lexeme == "init"
                    fn = RiftFunction(method, self._environment, is_init)
                    method_map[method.name.lexeme] = fn

                klass = RiftClass(name.lexeme, superclass, method_map)

                if superclass is not None:
                    assert self._environment.enclosing is not None
                    self._environment = self._environment.enclosing

                self._environment.assign(name, klass)

    def _execute_block(self, statements: list[ast.Stmt], environment: Environment) -> None:
        previous = self._environment
        try:
            self._environment = environment
            for stmt in statements:
                self._execute(stmt)
        finally:
            self._environment = previous

    def _evaluate(self, expr: ast.Expr) -> object:
        match expr:
            case ast.LiteralExpr(value):
                return value
            case ast.GroupingExpr(expression):
                return self._evaluate(expression)
            case ast.UnaryExpr(operator, operand):
                right = self._evaluate(operand)
                match operator.type:
                    case TokenType.MINUS:
                        self._check_number_operand(operator, right)
                        return -float(right)  # type: ignore[arg-type]
                    case TokenType.BANG:
                        return not self._is_truthy(right)
                return None
            case ast.BinaryExpr(left_node, operator, right_node):
                left = self._evaluate(left_node)
                right = self._evaluate(right_node)
                return self._eval_binary(operator, left, right)
            case ast.VariableExpr(name):
                return self._lookup_variable(name, expr)
            case ast.AssignExpr(name, value_expr):
                value = self._evaluate(value_expr)
                distance = self._locals.get(id(expr))
                if distance is not None:
                    self._environment.assign_at(distance, name, value)
                else:
                    self.globals.assign(name, value)
                return value
            case ast.LogicalExpr(left_node, operator, right_node):
                left = self._evaluate(left_node)
                if operator.type == TokenType.OR:
                    if self._is_truthy(left):
                        return left
                else:
                    if not self._is_truthy(left):
                        return left
                return self._evaluate(right_node)
            case ast.CallExpr(callee_expr, arguments, paren):
                callee = self._evaluate(callee_expr)
                args = [self._evaluate(a) for a in arguments]

                if not isinstance(callee, (RiftFunction, RiftClass, NativeFunction)):
                    raise RiftRuntimeError(paren, "can only call functions and classes")

                if len(args) != callee.arity():
                    raise RiftRuntimeError(
                        paren,
                        f"expected {callee.arity()} arguments but got {len(args)}",
                    )
                return callee.call(self, args)
            case ast.GetExpr(obj_expr, name):
                obj = self._evaluate(obj_expr)
                if isinstance(obj, RiftInstance):
                    return obj.get(name)
                raise RiftRuntimeError(name, "only instances have properties")
            case ast.SetExpr(obj_expr, name, value_expr):
                obj = self._evaluate(obj_expr)
                if not isinstance(obj, RiftInstance):
                    raise RiftRuntimeError(name, "only instances have fields")
                value = self._evaluate(value_expr)
                obj.set(name, value)
                return value
            case ast.ThisExpr(keyword):
                return self._lookup_variable(keyword, expr)
            case ast.SuperExpr(keyword, method):
                distance = self._locals.get(id(expr))
                assert distance is not None
                superclass = self._environment.get_at(distance, "super")
                assert isinstance(superclass, RiftClass)
                # 'this' is always one scope inside 'super'
                instance = self._environment.get_at(distance - 1, "this")
                assert isinstance(instance, RiftInstance)
                m = superclass.find_method(method.lexeme)
                if m is None:
                    raise RiftRuntimeError(
                        method, f"undefined property '{method.lexeme}'"
                    )
                return m.bind(instance)
        return None  # unreachable

    def _eval_binary(self, op: Token, left: object, right: object) -> object:
        match op.type:
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return left + right
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                raise RiftRuntimeError(
                    op, "operands must be two numbers or two strings"
                )
            case TokenType.MINUS:
                self._check_number_operands(op, left, right)
                return float(left) - float(right)  # type: ignore[arg-type]
            case TokenType.STAR:
                self._check_number_operands(op, left, right)
                return float(left) * float(right)  # type: ignore[arg-type]
            case TokenType.SLASH:
                self._check_number_operands(op, left, right)
                if float(right) == 0:  # type: ignore[arg-type]
                    raise RiftRuntimeError(op, "division by zero")
                return float(left) / float(right)  # type: ignore[arg-type]
            case TokenType.PERCENT:
                self._check_number_operands(op, left, right)
                if float(right) == 0:  # type: ignore[arg-type]
                    raise RiftRuntimeError(op, "modulo by zero")
                return float(left) % float(right)  # type: ignore[arg-type]
            case TokenType.GREATER:
                self._check_number_operands(op, left, right)
                return float(left) > float(right)  # type: ignore[arg-type]
            case TokenType.GREATER_EQUAL:
                self._check_number_operands(op, left, right)
                return float(left) >= float(right)  # type: ignore[arg-type]
            case TokenType.LESS:
                self._check_number_operands(op, left, right)
                return float(left) < float(right)  # type: ignore[arg-type]
            case TokenType.LESS_EQUAL:
                self._check_number_operands(op, left, right)
                return float(left) <= float(right)  # type: ignore[arg-type]
            case TokenType.EQUAL_EQUAL:
                return self._is_equal(left, right)
            case TokenType.BANG_EQUAL:
                return not self._is_equal(left, right)
        return None  # unreachable

    def _lookup_variable(self, name: Token, expr: ast.Expr) -> object:
        distance = self._locals.get(id(expr))
        if distance is not None:
            return self._environment.get_at(distance, name.lexeme)
        return self.globals.get(name)

    @staticmethod
    def _is_truthy(value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True

    @staticmethod
    def _is_equal(a: object, b: object) -> bool:
        return a == b

    @staticmethod
    def _check_number_operand(operator: Token, operand: object) -> None:
        if isinstance(operand, float):
            return
        raise RiftRuntimeError(operator, "operand must be a number")

    @staticmethod
    def _check_number_operands(operator: Token, left: object, right: object) -> None:
        if isinstance(left, float) and isinstance(right, float):
            return
        raise RiftRuntimeError(operator, "operands must be numbers")

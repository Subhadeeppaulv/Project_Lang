"""Tree-walking interpreter for Lang.

Evaluates the AST directly (no bytecode). This is the MVP execution
model: simple to read and extend, trade-off is raw speed. Swap in a
bytecode VM later once the language itself has stabilized.
"""

import time
from typing import Any, List

from . import lang_ast as ast
from . import lexer as T


class LangRuntimeError(Exception):
    def __init__(self, message: str, token=None):
        super().__init__(message)
        self.token = token


class _ReturnSignal(Exception):
    """Internal control-flow signal used to unwind out of a function call."""
    def __init__(self, value):
        self.value = value


class Environment:
    """A lexical scope. Chains to its parent for closures / nested blocks."""

    def __init__(self, parent: "Environment" = None):
        self.parent = parent
        self.values = {}

    def define(self, name: str, value: Any):
        self.values[name] = value

    def get(self, name_token):
        name = name_token.lexeme
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name_token)
        raise LangRuntimeError(f"Undefined variable '{name}'.", name_token)

    def assign(self, name_token, value):
        name = name_token.lexeme
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name_token, value)
            return
        raise LangRuntimeError(f"Undefined variable '{name}'.", name_token)


class LangCallable:
    def arity(self) -> int:
        raise NotImplementedError

    def call(self, interpreter, arguments):
        raise NotImplementedError


class NativeFunction(LangCallable):
    """A built-in function implemented in Python. arity=-1 means variadic."""

    def __init__(self, name, arity, fn):
        self.name = name
        self._arity = arity
        self.fn = fn

    def arity(self):
        return self._arity

    def call(self, interpreter, arguments):
        return self.fn(*arguments)

    def __repr__(self):
        return f"<native fn {self.name}>"


class LangFunction(LangCallable):
    """A user-defined Lang function. Captures its defining scope (closure)."""

    def __init__(self, declaration: ast.FuncDecl, closure: Environment):
        self.declaration = declaration
        self.closure = closure

    def arity(self):
        return len(self.declaration.params)

    def call(self, interpreter, arguments):
        env = Environment(self.closure)
        for param, arg in zip(self.declaration.params, arguments):
            env.define(param.lexeme, arg)
        try:
            interpreter.execute_block(self.declaration.body, env)
        except _ReturnSignal as r:
            return r.value
        return None

    def __repr__(self):
        return f"<func {self.declaration.name.lexeme}>"


def _stringify(value) -> str:
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _native_num(x):
    f = float(x)
    return int(f) if f.is_integer() else f


class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.env = self.globals
        self._install_builtins()

    def _install_builtins(self):
        self.globals.define("print", NativeFunction(
            "print", -1, lambda *args: print(" ".join(_stringify(a) for a in args))
        ))
        self.globals.define("len", NativeFunction("len", 1, lambda x: len(x)))
        self.globals.define("str", NativeFunction("str", 1, lambda x: _stringify(x)))
        self.globals.define("num", NativeFunction("num", 1, _native_num))
        self.globals.define("clock", NativeFunction("clock", 0, lambda: time.time()))

    def interpret(self, statements: List[ast.Stmt]):
        for stmt in statements:
            self._execute(stmt)

    # ---- statement execution ----
    def _execute(self, stmt: ast.Stmt):
        method = getattr(self, f"_exec_{type(stmt).__name__}")
        method(stmt)

    def execute_block(self, statements, env: Environment):
        previous = self.env
        try:
            self.env = env
            for stmt in statements:
                self._execute(stmt)
        finally:
            self.env = previous

    def _exec_ExpressionStmt(self, stmt: ast.ExpressionStmt):
        self._evaluate(stmt.expression)

    def _exec_LetStmt(self, stmt: ast.LetStmt):
        value = None
        if stmt.initializer is not None:
            value = self._evaluate(stmt.initializer)
        self.env.define(stmt.name.lexeme, value)

    def _exec_Block(self, stmt: ast.Block):
        self.execute_block(stmt.statements, Environment(self.env))

    def _exec_If(self, stmt: ast.If):
        for condition, block in stmt.branches:
            if _is_truthy(self._evaluate(condition)):
                self._execute(block)
                return
        if stmt.else_branch is not None:
            self._execute(stmt.else_branch)

    def _exec_While(self, stmt: ast.While):
        while _is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.body)

    def _exec_FuncDecl(self, stmt: ast.FuncDecl):
        func = LangFunction(stmt, self.env)
        self.env.define(stmt.name.lexeme, func)

    def _exec_Return(self, stmt: ast.Return):
        value = None
        if stmt.value is not None:
            value = self._evaluate(stmt.value)
        raise _ReturnSignal(value)

    # ---- expression evaluation ----
    def _evaluate(self, expr: ast.Expr):
        method = getattr(self, f"_eval_{type(expr).__name__}")
        return method(expr)

    def _eval_Literal(self, expr: ast.Literal):
        return expr.value

    def _eval_Grouping(self, expr: ast.Grouping):
        return self._evaluate(expr.expression)

    def _eval_Variable(self, expr: ast.Variable):
        return self.env.get(expr.name)

    def _eval_Assign(self, expr: ast.Assign):
        value = self._evaluate(expr.value)
        self.env.assign(expr.name, value)
        return value

    def _eval_Logical(self, expr: ast.Logical):
        left = self._evaluate(expr.left)
        if expr.operator.type == T.OR:
            if _is_truthy(left):
                return left
        else:  # AND
            if not _is_truthy(left):
                return left
        return self._evaluate(expr.right)

    def _eval_Unary(self, expr: ast.Unary):
        right = self._evaluate(expr.right)
        if expr.operator.type == T.MINUS:
            _check_number(expr.operator, right)
            return -right
        if expr.operator.type == T.NOT:
            return not _is_truthy(right)

    def _eval_Binary(self, expr: ast.Binary):
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)
        op = expr.operator.type

        if op == T.PLUS:
            if isinstance(left, str) or isinstance(right, str):
                return _stringify(left) + _stringify(right)
            _check_numbers(expr.operator, left, right)
            return left + right
        if op == T.MINUS:
            _check_numbers(expr.operator, left, right)
            return left - right
        if op == T.STAR:
            _check_numbers(expr.operator, left, right)
            return left * right
        if op == T.SLASH:
            _check_numbers(expr.operator, left, right)
            if right == 0:
                raise LangRuntimeError("Division by zero.", expr.operator)
            return left / right
        if op == T.PERCENT:
            _check_numbers(expr.operator, left, right)
            return left % right
        if op == T.GREATER:
            _check_numbers(expr.operator, left, right)
            return left > right
        if op == T.GREATER_EQUAL:
            _check_numbers(expr.operator, left, right)
            return left >= right
        if op == T.LESS:
            _check_numbers(expr.operator, left, right)
            return left < right
        if op == T.LESS_EQUAL:
            _check_numbers(expr.operator, left, right)
            return left <= right
        if op == T.EQUAL_EQUAL:
            return left == right
        if op == T.BANG_EQUAL:
            return left != right

    def _eval_Call(self, expr: ast.Call):
        callee = self._evaluate(expr.callee)
        arguments = [self._evaluate(arg) for arg in expr.arguments]

        if not isinstance(callee, LangCallable):
            raise LangRuntimeError("Can only call functions.", expr.paren)

        if callee.arity() != -1 and len(arguments) != callee.arity():
            raise LangRuntimeError(
                f"Expected {callee.arity()} arguments but got {len(arguments)}.",
                expr.paren,
            )
        return callee.call(self, arguments)


def _is_truthy(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return True


def _check_number(operator, operand):
    if isinstance(operand, (int, float)) and not isinstance(operand, bool):
        return
    raise LangRuntimeError("Operand must be a number.", operator)


def _check_numbers(operator, left, right):
    _check_number(operator, left)
    _check_number(operator, right)

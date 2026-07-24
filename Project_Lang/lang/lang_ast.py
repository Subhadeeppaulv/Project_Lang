"""AST node definitions for Lang.

Two families of nodes: Expr (things that evaluate to a value) and
Stmt (things that are executed for effect).
"""

from dataclasses import dataclass
from typing import List, Optional, Any


# ---- Expressions ----

class Expr:
    pass


@dataclass
class Literal(Expr):
    value: Any


@dataclass
class Grouping(Expr):
    expression: Expr


@dataclass
class Unary(Expr):
    operator: Any  # Token
    right: Expr


@dataclass
class Binary(Expr):
    left: Expr
    operator: Any  # Token
    right: Expr


@dataclass
class Logical(Expr):
    left: Expr
    operator: Any  # Token (AND / OR)
    right: Expr


@dataclass
class Variable(Expr):
    name: Any  # Token


@dataclass
class Assign(Expr):
    name: Any  # Token
    value: Expr


@dataclass
class Call(Expr):
    callee: Expr
    paren: Any  # Token, kept for error line-reporting
    arguments: List[Expr]


# ---- Statements ----

class Stmt:
    pass


@dataclass
class ExpressionStmt(Stmt):
    expression: Expr


@dataclass
class LetStmt(Stmt):
    name: Any  # Token
    initializer: Optional[Expr]


@dataclass
class Block(Stmt):
    statements: List[Stmt]


@dataclass
class If(Stmt):
    branches: List  # list of (condition: Expr, body: Block) — covers if + elif*
    else_branch: Optional[Block]


@dataclass
class While(Stmt):
    condition: Expr
    body: Block


@dataclass
class FuncDecl(Stmt):
    name: Any  # Token
    params: List[Any]  # list of Tokens
    body: List[Stmt]


@dataclass
class Return(Stmt):
    keyword: Any  # Token, for error reporting
    value: Optional[Expr]

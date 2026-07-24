"""Recursive-descent parser for Lang.

Converts a flat list of Tokens into an AST (see lang_ast.py) following
this grammar:

    program     -> declaration* EOF
    declaration -> letDecl | funcDecl | statement
    letDecl     -> "let" IDENTIFIER ( "=" expression )? ";"
    funcDecl    -> "func" IDENTIFIER "(" params? ")" block
    statement   -> exprStmt | ifStmt | whileStmt | returnStmt | block
    exprStmt    -> expression ";"
    ifStmt      -> "if" "(" expression ")" block
                   ( "elif" "(" expression ")" block )*
                   ( "else" block )?
    whileStmt   -> "while" "(" expression ")" block
    returnStmt  -> "return" expression? ";"
    block       -> "{" declaration* "}"
    expression  -> assignment
    assignment  -> IDENTIFIER "=" assignment | logic_or
    logic_or    -> logic_and ( "or" logic_and )*
    logic_and   -> equality ( "and" equality )*
    equality    -> comparison ( ( "==" | "!=" ) comparison )*
    comparison  -> term ( ( "<" | ">" | "<=" | ">=" ) term )*
    term        -> factor ( ( "+" | "-" ) factor )*
    factor      -> unary ( ( "*" | "/" | "%" ) unary )*
    unary       -> ( "not" | "-" ) unary | call
    call        -> primary ( "(" arguments? ")" )*
    primary     -> NUMBER | STRING | "true" | "false" | "nil"
                   | IDENTIFIER | "(" expression ")"
"""

from typing import List

from . import lexer as T
from . import lang_ast as ast


class ParseError(Exception):
    def __init__(self, message: str, token):
        super().__init__(f"[line {token.line}] ParseError at '{token.lexeme}': {message}")
        self.token = token


class Parser:
    def __init__(self, tokens: List[T.Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> List[ast.Stmt]:
        statements = []
        while not self._at_end():
            statements.append(self._declaration())
        return statements

    # ---- helpers ----
    def _peek(self):
        return self.tokens[self.current]

    def _previous(self):
        return self.tokens[self.current - 1]

    def _at_end(self):
        return self._peek().type == T.EOF

    def _advance(self):
        if not self._at_end():
            self.current += 1
        return self._previous()

    def _check(self, type_):
        if self._at_end():
            return False
        return self._peek().type == type_

    def _match(self, *types):
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, type_, message):
        if self._check(type_):
            return self._advance()
        raise ParseError(message, self._peek())

    def _synchronize(self):
        self._advance()
        while not self._at_end():
            if self._previous().type == T.SEMICOLON:
                return
            if self._peek().type in (T.FUNC, T.LET, T.IF, T.WHILE, T.RETURN):
                return
            self._advance()

    # ---- declarations ----
    def _declaration(self):
        if self._match(T.LET):
            return self._let_decl()
        if self._match(T.FUNC):
            return self._func_decl()
        return self._statement()

    def _let_decl(self):
        name = self._consume(T.IDENTIFIER, "Expected variable name.")
        initializer = None
        if self._match(T.EQUAL):
            initializer = self._expression()
        self._consume(T.SEMICOLON, "Expected ';' after variable declaration.")
        return ast.LetStmt(name, initializer)

    def _func_decl(self):
        name = self._consume(T.IDENTIFIER, "Expected function name.")
        self._consume(T.LPAREN, "Expected '(' after function name.")
        params = []
        if not self._check(T.RPAREN):
            while True:
                params.append(self._consume(T.IDENTIFIER, "Expected parameter name."))
                if not self._match(T.COMMA):
                    break
        self._consume(T.RPAREN, "Expected ')' after parameters.")
        self._consume(T.LBRACE, "Expected '{' before function body.")
        body = self._block()
        return ast.FuncDecl(name, params, body)

    # ---- statements ----
    def _statement(self):
        if self._match(T.IF):
            return self._if_statement()
        if self._match(T.WHILE):
            return self._while_statement()
        if self._match(T.RETURN):
            return self._return_statement()
        if self._match(T.LBRACE):
            return ast.Block(self._block())
        return self._expression_statement()

    def _if_statement(self):
        branches = []
        self._consume(T.LPAREN, "Expected '(' after 'if'.")
        cond = self._expression()
        self._consume(T.RPAREN, "Expected ')' after condition.")
        self._consume(T.LBRACE, "Expected '{' after condition.")
        branches.append((cond, ast.Block(self._block())))

        while self._match(T.ELIF):
            self._consume(T.LPAREN, "Expected '(' after 'elif'.")
            cond = self._expression()
            self._consume(T.RPAREN, "Expected ')' after condition.")
            self._consume(T.LBRACE, "Expected '{' after condition.")
            branches.append((cond, ast.Block(self._block())))

        else_branch = None
        if self._match(T.ELSE):
            self._consume(T.LBRACE, "Expected '{' after 'else'.")
            else_branch = ast.Block(self._block())

        return ast.If(branches, else_branch)

    def _while_statement(self):
        self._consume(T.LPAREN, "Expected '(' after 'while'.")
        cond = self._expression()
        self._consume(T.RPAREN, "Expected ')' after condition.")
        self._consume(T.LBRACE, "Expected '{' before loop body.")
        body = ast.Block(self._block())
        return ast.While(cond, body)

    def _return_statement(self):
        keyword = self._previous()
        value = None
        if not self._check(T.SEMICOLON):
            value = self._expression()
        self._consume(T.SEMICOLON, "Expected ';' after return value.")
        return ast.Return(keyword, value)

    def _block(self):
        statements = []
        while not self._check(T.RBRACE) and not self._at_end():
            statements.append(self._declaration())
        self._consume(T.RBRACE, "Expected '}' after block.")
        return statements

    def _expression_statement(self):
        expr = self._expression()
        self._consume(T.SEMICOLON, "Expected ';' after expression.")
        return ast.ExpressionStmt(expr)

    # ---- expressions (lowest to highest precedence) ----
    def _expression(self):
        return self._assignment()

    def _assignment(self):
        expr = self._logic_or()
        if self._match(T.EQUAL):
            equals = self._previous()
            value = self._assignment()
            if isinstance(expr, ast.Variable):
                return ast.Assign(expr.name, value)
            raise ParseError("Invalid assignment target.", equals)
        return expr

    def _logic_or(self):
        expr = self._logic_and()
        while self._match(T.OR):
            op = self._previous()
            right = self._logic_and()
            expr = ast.Logical(expr, op, right)
        return expr

    def _logic_and(self):
        expr = self._equality()
        while self._match(T.AND):
            op = self._previous()
            right = self._equality()
            expr = ast.Logical(expr, op, right)
        return expr

    def _equality(self):
        expr = self._comparison()
        while self._match(T.EQUAL_EQUAL, T.BANG_EQUAL):
            op = self._previous()
            right = self._comparison()
            expr = ast.Binary(expr, op, right)
        return expr

    def _comparison(self):
        expr = self._term()
        while self._match(T.LESS, T.LESS_EQUAL, T.GREATER, T.GREATER_EQUAL):
            op = self._previous()
            right = self._term()
            expr = ast.Binary(expr, op, right)
        return expr

    def _term(self):
        expr = self._factor()
        while self._match(T.PLUS, T.MINUS):
            op = self._previous()
            right = self._factor()
            expr = ast.Binary(expr, op, right)
        return expr

    def _factor(self):
        expr = self._unary()
        while self._match(T.STAR, T.SLASH, T.PERCENT):
            op = self._previous()
            right = self._unary()
            expr = ast.Binary(expr, op, right)
        return expr

    def _unary(self):
        if self._match(T.NOT, T.MINUS):
            op = self._previous()
            right = self._unary()
            return ast.Unary(op, right)
        return self._call()

    def _call(self):
        expr = self._primary()
        while True:
            if self._match(T.LPAREN):
                expr = self._finish_call(expr)
            else:
                break
        return expr

    def _finish_call(self, callee):
        arguments = []
        if not self._check(T.RPAREN):
            while True:
                arguments.append(self._expression())
                if not self._match(T.COMMA):
                    break
        paren = self._consume(T.RPAREN, "Expected ')' after arguments.")
        return ast.Call(callee, paren, arguments)

    def _primary(self):
        if self._match(T.FALSE):
            return ast.Literal(False)
        if self._match(T.TRUE):
            return ast.Literal(True)
        if self._match(T.NIL):
            return ast.Literal(None)
        if self._match(T.NUMBER, T.STRING):
            return ast.Literal(self._previous().literal)
        if self._match(T.IDENTIFIER):
            return ast.Variable(self._previous())
        if self._match(T.LPAREN):
            expr = self._expression()
            self._consume(T.RPAREN, "Expected ')' after expression.")
            return ast.Grouping(expr)
        raise ParseError("Expected expression.", self._peek())

"""
Lexer for the Lang programming language.

Converts raw source text into a stream of Tokens for the parser.

KEYWORDS ARE CONFIGURABLE
--------------------------
Every language keyword lives in the single `KEYWORDS` dict below. To rename
Lang's syntax later (e.g. `let` -> `var`, `func` -> `def`), this is the ONLY
place you need to change it — nothing else in the codebase cares about the
spelling, only the token TYPE (e.g. LET, FUNC).
"""

from dataclasses import dataclass
from typing import Any, List


class LexError(Exception):
    def __init__(self, message: str, line: int):
        super().__init__(f"[line {line}] LexError: {message}")
        self.line = line


# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------

# Single/multi-character symbols
PLUS, MINUS, STAR, SLASH, PERCENT = "PLUS", "MINUS", "STAR", "SLASH", "PERCENT"
EQUAL, EQUAL_EQUAL, BANG_EQUAL = "EQUAL", "EQUAL_EQUAL", "BANG_EQUAL"
LESS, LESS_EQUAL, GREATER, GREATER_EQUAL = "LESS", "LESS_EQUAL", "GREATER", "GREATER_EQUAL"
LPAREN, RPAREN, LBRACE, RBRACE = "LPAREN", "RPAREN", "LBRACE", "RBRACE"
COMMA, SEMICOLON = "COMMA", "SEMICOLON"

# Literals
IDENTIFIER, STRING, NUMBER = "IDENTIFIER", "STRING", "NUMBER"

# Keyword token types
LET, FUNC, IF, ELIF, ELSE, WHILE, RETURN = "LET", "FUNC", "IF", "ELIF", "ELSE", "WHILE", "RETURN"
TRUE, FALSE, NIL, AND, OR, NOT = "TRUE", "FALSE", "NIL", "AND", "OR", "NOT"

EOF = "EOF"

# Maps source-code spelling -> token type.
# >>> Rename the left-hand keys below to customize Lang's syntax. <<<
KEYWORDS = {
    "let": LET,
    "func": FUNC,
    "if": IF,
    "elif": ELIF,
    "else": ELSE,
    "while": WHILE,
    "return": RETURN,
    "true": TRUE,
    "false": FALSE,
    "nil": NIL,
    "and": AND,
    "or": OR,
    "not": NOT,
}


@dataclass
class Token:
    type: str
    lexeme: str
    literal: Any
    line: int

    def __repr__(self):
        return f"Token({self.type}, {self.lexeme!r}, {self.literal!r})"


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self) -> List[Token]:
        while not self._at_end():
            self.start = self.current
            self._scan_token()
        self.tokens.append(Token(EOF, "", None, self.line))
        return self.tokens

    # -- helpers --
    def _at_end(self):
        return self.current >= len(self.source)

    def _advance(self):
        c = self.source[self.current]
        self.current += 1
        return c

    def _peek(self):
        return "\0" if self._at_end() else self.source[self.current]

    def _peek_next(self):
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _match(self, expected):
        if self._at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def _add_token(self, type_, literal=None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(type_, text, literal, self.line))

    # -- core scan --
    def _scan_token(self):
        c = self._advance()

        if c in " \r\t":
            return
        if c == "\n":
            self.line += 1
            return
        if c == "#":
            while self._peek() != "\n" and not self._at_end():
                self._advance()
            return

        simple = {
            "+": PLUS, "-": MINUS, "*": STAR, "%": PERCENT,
            "(": LPAREN, ")": RPAREN, "{": LBRACE, "}": RBRACE,
            ",": COMMA, ";": SEMICOLON,
        }
        if c in simple:
            self._add_token(simple[c])
            return

        if c == "/":
            self._add_token(SLASH)
            return
        if c == "=":
            self._add_token(EQUAL_EQUAL if self._match("=") else EQUAL)
            return
        if c == "!":
            if self._match("="):
                self._add_token(BANG_EQUAL)
                return
            raise LexError("Unexpected character '!'. Did you mean 'not'?", self.line)
        if c == "<":
            self._add_token(LESS_EQUAL if self._match("=") else LESS)
            return
        if c == ">":
            self._add_token(GREATER_EQUAL if self._match("=") else GREATER)
            return
        if c == '"':
            self._string()
            return

        if c.isdigit():
            self._number()
            return
        if c.isalpha() or c == "_":
            self._identifier()
            return

        raise LexError(f"Unexpected character {c!r}", self.line)

    def _string(self):
        value_chars = []
        while self._peek() != '"' and not self._at_end():
            ch = self._advance()
            if ch == "\n":
                self.line += 1
            if ch == "\\" and not self._at_end():
                esc = self._advance()
                mapping = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                value_chars.append(mapping.get(esc, esc))
            else:
                value_chars.append(ch)
        if self._at_end():
            raise LexError("Unterminated string", self.line)
        self._advance()  # closing quote
        self._add_token(STRING, "".join(value_chars))

    def _number(self):
        while self._peek().isdigit():
            self._advance()
        is_float = False
        if self._peek() == "." and self._peek_next().isdigit():
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()
        text = self.source[self.start:self.current]
        self._add_token(NUMBER, float(text) if is_float else int(text))

    def _identifier(self):
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.source[self.start:self.current]
        type_ = KEYWORDS.get(text, IDENTIFIER)
        self._add_token(type_)

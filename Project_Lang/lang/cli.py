"""Command-line interface for Lang.

Usage:
    lang                  Start an interactive REPL.
    lang script.lang       Run a Lang source file.
"""

import sys

from .lexer import Lexer, LexError
from .parser import Parser, ParseError
from .interpreter import Interpreter, LangRuntimeError

VERSION = "0.1.0"


def run(source: str, interpreter: Interpreter):
    try:
        tokens = Lexer(source).scan_tokens()
        statements = Parser(tokens).parse()
    except (LexError, ParseError) as e:
        print(e, file=sys.stderr)
        return
    try:
        interpreter.interpret(statements)
    except LangRuntimeError as e:
        line = e.token.line if e.token else "?"
        print(f"[line {line}] RuntimeError: {e}", file=sys.stderr)


def run_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    interpreter = Interpreter()
    run(source, interpreter)


def run_repl():
    print(f"Lang {VERSION} — interactive REPL. Ctrl-D or Ctrl-C to exit.")
    interpreter = Interpreter()
    while True:
        try:
            line = input("lang> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line.strip():
            continue
        # Let the REPL be forgiving about trailing semicolons.
        source = line if line.strip().endswith((";", "}")) else line + ";"
        run(source, interpreter)


def main():
    args = sys.argv[1:]
    if len(args) == 0:
        run_repl()
    elif len(args) == 1:
        run_file(args[0])
    else:
        print("Usage: lang [script.lang]", file=sys.stderr)
        sys.exit(64)


if __name__ == "__main__":
    main()

# Project Lang

A small, tree-walking interpreted programming language, implemented in Python.

Lang is deliberately minimal: variables, functions with closures, control flow, and a handful
of built-ins. It's meant as a clean foundation to extend — not a finished product.

```
func fib(n) {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}

let i = 0;
while (i < 10) {
    print(fib(i));
    i = i + 1;
}
```

## Install

```bash
git clone https://github.com/Subhadeeppaulv/Project_Lang.git
cd Project_Lang
pip install -e .
```

This installs a `lang` command on your PATH via the `[project.scripts]` entry point in
`pyproject.toml`. Without installing, you can also run it directly with:

```bash
python3 -m lang
```

## Usage

**Run a script:**

```bash
lang examples/fizzbuzz.lang
```

**Interactive REPL:**

```bash
lang
```

## Website & docs

The full language guide, with runnable examples for every feature, lives at
**[subhadeeppaulv.github.io/Project_Lang](https://subhadeeppaulv.github.io/Project_Lang/)**
(source in [`docs/`](docs/)). The same content is summarized below.

## Language tour

| Feature      | Syntax |
|---|---|
| Variables    | `let x = 10;` |
| Reassignment | `x = x + 1;` |
| Functions    | `func add(a, b) { return a + b; }` |
| Conditionals | `if (x > 0) { ... } elif (x == 0) { ... } else { ... }` |
| Loops        | `while (x < 10) { ... }` |
| Types        | numbers, strings, `true` / `false`, `nil` |
| Logic        | `and`, `or`, `not` |
| Comments     | `# a comment` |

Built-in functions: `print(...)` (variadic), `len(x)`, `str(x)`, `num(x)`, `clock()`.

Every block uses `{ }`, every statement ends in `;`, and every condition is parenthesized —
this keeps the grammar unambiguous and the parser simple (see `lang/parser.py` for the
full grammar in EBNF).

More examples in [`examples/`](examples/): `hello.lang`, `fizzbuzz.lang`, `fibonacci.lang`,
`closures.lang`.

## Project structure

```
lang/
  lexer.py         Source text -> tokens
  lang_ast.py       AST node definitions
  parser.py        Tokens -> AST (recursive descent)
  interpreter.py   Tree-walking evaluator, environments, closures, built-ins
  cli.py           REPL + script runner
examples/          Sample .lang programs
tests/             Unit tests (unittest)
docs/              The project website (served via GitHub Pages from this folder)
```

## Customizing the syntax

Every keyword — `let`, `func`, `if`, `elif`, `else`, `while`, `return`, `true`, `false`,
`nil`, `and`, `or`, `not` — is defined in **one place**: the `KEYWORDS` dict at the top of
`lang/lexer.py`. Nothing else in the codebase depends on the spelling, only on the token
type (e.g. `LET`). To rename `let` to `var`, change one line:

```python
KEYWORDS = {
    "var": LET,   # was "let": LET
    ...
}
```

## Running tests

```bash
python3 -m unittest discover -s tests -v
```

## Roadmap

Current state is a v0 MVP: a working tree-walking interpreter with the essentials.
Natural next steps, roughly in order of value:

- [ ] Lists / arrays and a `for` loop
- [ ] String indexing and slicing
- [ ] Better error messages (source snippets, not just line numbers)
- [ ] A standard library (`math`, `io`, etc.)
- [ ] Module / import system
- [ ] Static scope resolution pass (currently variable lookup walks the environment chain
      at runtime — fine for an MVP, but a resolver pass would catch errors earlier and
      speed up execution)
- [ ] Bytecode VM, once the language surface is stable (tree-walking is the right call for
      v0 — don't reach for this until real usage shows it's the bottleneck)

## Contributing

Issues and PRs welcome once this is public. Keep the grammar in `parser.py`'s docstring in
sync with any syntax changes — it's the source of truth for the language.

## Acknowledgments

Designed and built by **Subhadeep Paul**, with development assistance from **Claude
(Anthropic)**.

## License

MIT — see [LICENSE](LICENSE).

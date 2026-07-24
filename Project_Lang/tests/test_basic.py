import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lang.lexer import Lexer
from lang.parser import Parser
from lang.interpreter import Interpreter


def run_lang(source: str) -> str:
    tokens = Lexer(source).scan_tokens()
    statements = Parser(tokens).parse()
    interpreter = Interpreter()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        interpreter.interpret(statements)
    return buf.getvalue()


class TestLang(unittest.TestCase):
    def test_arithmetic(self):
        self.assertEqual(run_lang("print(1 + 2 * 3);").strip(), "7")

    def test_variables_and_reassignment(self):
        self.assertEqual(run_lang("let x = 10; x = x + 5; print(x);").strip(), "15")

    def test_string_concat(self):
        out = run_lang('print("Hello, " + "world!");')
        self.assertEqual(out.strip(), "Hello, world!")

    def test_if_elif_else(self):
        src = """
        let n = 7;
        if (n % 15 == 0) { print("FizzBuzz"); }
        elif (n % 3 == 0) { print("Fizz"); }
        elif (n % 5 == 0) { print("Buzz"); }
        else { print(n); }
        """
        self.assertEqual(run_lang(src).strip(), "7")

    def test_while_loop(self):
        out = run_lang("let i = 0; while (i < 5) { print(i); i = i + 1; }")
        self.assertEqual(out.strip().split("\n"), ["0", "1", "2", "3", "4"])

    def test_function_and_recursion(self):
        src = """
        func fact(n) {
            if (n <= 1) { return 1; }
            return n * fact(n - 1);
        }
        print(fact(5));
        """
        self.assertEqual(run_lang(src).strip(), "120")

    def test_closures(self):
        src = """
        func make_counter() {
            let count = 0;
            func increment() {
                count = count + 1;
                return count;
            }
            return increment;
        }
        let c = make_counter();
        print(c());
        print(c());
        print(c());
        """
        self.assertEqual(run_lang(src).strip().split("\n"), ["1", "2", "3"])

    def test_logical_operators(self):
        out = run_lang("print(true and false); print(true or false); print(not true);")
        self.assertEqual(out.strip().split("\n"), ["false", "true", "false"])

    def test_comments_are_ignored(self):
        out = run_lang("# this is a comment\nprint(1); # trailing comment\n")
        self.assertEqual(out.strip(), "1")

    def test_scoping(self):
        src = """
        let x = "outer";
        {
            let x = "inner";
            print(x);
        }
        print(x);
        """
        self.assertEqual(run_lang(src).strip().split("\n"), ["inner", "outer"])


if __name__ == "__main__":
    unittest.main()

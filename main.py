#!/usr/bin/env python
import Data
import Lexer
import Parser
import traceback
from Error import ErrorHandler
import Exec
import sys

from sty import fg

# Import module for colouring.
# Prettifying the ast
from Utils import prettify_ast

# Dont forget to close the file
with open("tests/test.adk", "r") as f:
    text = f.read()

cli_mode = "cli-mode" in sys.argv

saved_scope = None
while True:
    text = input("aardvark: ")
    is_test = False
    file = "<main>"
    if text == "$clear":
        print("\033[2J\033[H")
        continue

    if text.startswith("$test"):
        test_name = text.split(" ")[-1]
        print(f"Running test {test_name}...")
        is_test = True
        with open(f"tests/{test_name}.adk", "r") as f:
            text = f.read()
        file = f"{test_name}.adk"
    errorhandler = ErrorHandler(text, file, py_error=True)

    try:
        lexer = Lexer.Lexer("#", "#*", "*#", errorhandler, False)
        lexer.tokenize(text)

        # print("".join([ str(x) for x in lexer.output ]))
        parser = Parser.Parser(errorhandler, lexer)
        ast = parser.parse()
        if not cli_mode:
            print(
                prettify_ast(ast)
            )  # Helps me see the ast so I don't have to go through Parser forever.
        executor = Exec.Executor(text, ast["body"], errorhandler)

        if saved_scope:
            executor.Global = saved_scope

        return_val = executor.run()
        saved_scope = executor.Global

        print(return_val)
    except Exception as e:
        if "py_error is True" not in str(e):
            traceback.print_exc()

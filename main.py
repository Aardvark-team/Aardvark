#!/usr/bin/env python
import Data
import Lexer
import Parser
import traceback
from Error import ErrorHandler
import Exec
import sys
from Types import Null
from sty import fg
import os

# Import module for colouring.
# Prettifying the ast
from Utils import prettify_ast

sys.setrecursionlimit(3000)


class Version:
    def __init__(self, major=0, minor=0, patch=0, type="stable", serial=1):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.serial = max(serial, 1)
        self.type = type.lower()

    def __str__(self):
        s = f"{self.major}.{self.minor}"
        if self.patch:
            s += f".{self.patch}"
        if self.type != "stable":
            s += f" {self.type.capitalize()} {self.serial}"
        return s

    def __repr__(self):
        return str(self)


version = Version(1, 0, 0, "test")
python = sys.version_info
python = Version(
    python.major, python.minor, python.micro, python.releaselevel, python.serial
)


def runTest(code, values={}, ret=None, testfunct=None):
    x = run(code)
    # print(x['error'])
    if x["error"] or x["Global"] == None:
        raise ValueError(f'Error: {x["error"]}')
    scope = x["Global"]
    if ret != None and x["return"] != ret:
        raise ValueError(f'Error, {ret} != {x["return"]}')
    for i in values:
        if scope[i] != values[i]:
            raise ValueError(f"Error, {scope[i]} != {values[i]} for variable {i}")
    if testfunct:
        testfunct(x)
    return True


def run(text, file="<main>", printToks=False, printAST=False, Global=None):
    errorhandler = ErrorHandler(text, file, py_error=True)
    ret = Null
    error = False
    try:
        lexer = Lexer.Lexer("#", "#*", "*#", errorhandler, False)
        toks = lexer.tokenize(text)
        if printToks:
            print(prettify_ast(toks))
        parser = Parser.Parser(errorhandler, lexer)
        ast = parser.parse()
        if printAST:
            print(prettify_ast(ast))
        executor = Exec.Executor(file, text, ast["body"], errorhandler)
        if Global:
            executor.Global = Global
        ret = executor.run()
        Global = executor.Global
    except Exception as e:
        error = str(e.args)
        if "py_error is True" not in str(e):
            traceback.print_exc()
    return {"return": ret, "Global": Global, "error": error}


# runTest('''
#   x = 5
#   (x = 7) if true
#   if x == 2*3+1 (x = x + 1)
#   if x == 8 {
#     x = 9
#   }
#   y = (5) if x < 100 else if x > 100 & x < 1000 (8) else (10)
# ''', {'x': 9, 'y': 5})


def runFile(file, *args, **kwargs):
    with open(file) as f:
        text = f.read()
        return run(text, file, *args, **kwargs)


if __name__ == "__main__":
    cmdargs = sys.argv[1:]
    options = []
    for i in cmdargs:
        if i.startswith("-"):
            options.append(i)
    if len(cmdargs) == 0 or len(cmdargs) == len(options):
        mode = "live"
    else:
        mode = cmdargs[0]

    if len(cmdargs) > 0 and cmdargs[0] == "--version":
        print(f"Aardvark {version} \n[Python {python}]\n{sys.platform.upper()}")

    elif mode == "live":
        print(f"Aardvark {version} \n[Python {python}]\n{sys.platform.upper()}")
        printast = "-ast" in sys.argv
        printtoks = "-toks" in sys.argv
        debugmode = "-debug" in sys.argv
        saved_scope = None
        while True:
            file = "<main>"
            text = input("aardvark: ")
            if debugmode:
                if text == "$clear":
                    print("\033[2J\033[H")
                    continue
                if text.startswith("$test"):
                    test_name = text.split(" ")[-1]
                    file = f"tests/{test_name}.adk"
                    with open(file) as f:
                        text = f.read()
                    print(f"Running test {test_name}...")

            errorhandler = ErrorHandler(text, file, py_error=True)

            x = run(
                text,
                file,
                printtoks,
                printast,
                Global=saved_scope if saved_scope else None,
            )
            if "no-ret" not in x:
                print(x["return"])
            saved_scope = x["Global"]

    elif mode == "run":
        printast = "-ast" in sys.argv
        printtoks = "-toks" in sys.argv
        runFile(cmdargs[1], printtoks, printast)

    elif mode == "help":
        print(f"Aardvark {version} \n[Python {python}]\n{sys.platform.upper()}")
        print(
            """Usage: adk cmd [-opts...]

Commands:
  run <file> [-opts...]
  live [-opts...]
  --version

Options:
  -ast   —  Prints the AST
  -toks  —  Prints the tokens
  -debug —  Enables $test and $clear in live mode

Versions:
  Aardvark versions have 2 parts, the number, and the release type.
  The number can be split into 3 parts: major, minor, and patch.
  The number is based on semantic versioning.
  The release type can be split into 2 parts: type and release number.
  There are 6 release types: test, alpha, beta, canidate, stable, and production.
  Tests are not usually released, they are used internally to mean that we aren't done with it.
  Alpha is for releases that don't have the full functionality.
  Beta is for releases that have most functionality, but are very buggy.
  Candidate is for releases that are thought to be stable.
  A candidate is promoted to stable after successful testing
  A stable can be promoted to production if it is well enough refined.
    
    """
        )
    elif mode.startswith('./'):
      printast = "-ast" in sys.argv
      printtoks = "-toks" in sys.argv
      runFile(mode[2:], printtoks, printast)
    else:
        print(sys.argv)
        print("Usage: adk cmd [-opts...]")

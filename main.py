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

class Version:
  def __init__(self, major=0, secondary=0, minor=0, revision=0, type='stable', serial=1):
    self.major = major
    self.secondary = secondary
    self.minor = minor
    self.revision = revision
    self.serial = max(serial, 1)
    if type.lower() not in ['test', 'alpha', 'beta', 'canidate', 'stable', 'production']:
      raise ValueError('Invalid release type!')
    self.type = type.lower()
  def __str__(self):
    s = f"{self.major}.{self.secondary}"
    if self.minor:
      s += f'.{self.minor}'
    if self.revision:
      s += f'.{self.revision}'
    if self.type != 'stable':
      s += f' {self.type.capitalize()} {self.serial}'
    return s
  def __repr__(self):
    return str(self)

version = Version(1, 0, 0, 0, 'test')
python = sys.version_info
python = Version(python.major, python.minor, python.micro, 0, python.releaselevel, python.serial)
def run(text, file, printToks=False, printAST=False, Global=None):
    errorhandler = ErrorHandler(text, file, py_error=True)
    ret = Null
    try:
        lexer = Lexer.Lexer("#", "#*", "*#", errorhandler, False)
        toks = lexer.tokenize(text)
        if printToks:
            print(
                prettify_ast(toks)
            )
        parser = Parser.Parser(errorhandler, lexer)
        ast = parser.parse()
        if printAST:
            print(prettify_ast(ast))
        executor = Exec.Executor(file, text, ast["body"], errorhandler)
        if Global:
          executor.Global = saved_scope
        ret = executor.run()
    except Exception as e:
        if "py_error is True" not in str(e):
            traceback.print_exc()
    return {
      'return': ret,
      'Global': Global
    }

  
def runFile(file, *args, **kwargs):
  with open(file) as f:
      text = f.read()
      return run(text, file, *args, **kwargs)


cmdargs = sys.argv[1:]
if len(cmdargs) == 0: 
  mode = 'live'
else:
  mode = cmdargs[0]

if mode == 'live':
  print(f'Aardvark {version} \n[Python {python}]\n{sys.platform.upper()}')
  printast = "-ast" in sys.argv
  printtoks = "-toks" in sys.argv
  debugmode = '-debug' in sys.argv
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
  
      x = run(text, file, printtoks, printast, Global=saved_scope if saved_scope else None)
      print(x['return'])
      saved_scope = x['Global']

elif mode == 'run':
  printast = "-ast" in sys.argv
  printtoks = "-toks" in sys.argv
  runFile(cmdargs[1], printtoks, printast)

elif mode == 'help':
  print('''Usage: ./adk cmd [-opts...]

Commands:
  run <file> [-opts...]
  live [-opts...]

Options:
  -ast   —  Prints the AST
  -toks  —  Prints the tokens
  -debug —  Enables $test and $clear in live mode''')
#elif len()
else:
  print('Usage: ./adk cmd [-opts...]')
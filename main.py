import Data
import Lexer
import Parser
import traceback
from Error import ErrorHandler
import Exec

# Prettifying the ast
import json

# Dont forget to close the file
with open("tests/test.adk", "r") as f:
	text = f.read()

while True:
  text = input("aardvark: ")
  is_test = False
  
  if text == "clear":
    print("\033[2J\033[H")
    continue
  
  if text.startswith("test-"):
    test_name = text[5:]
    print(f"Running test {test_name}...")
    is_test = True
    with open(f"tests/{test_name}.adk", "r") as f: text = f.read()
  
  lexer = Lexer.Lexer("#", "</", "/>", False) #</ and /> are just placeholders for what we decide multiline comments should be.
  lexer.tokenize(text)
  
  # print("".join([ str(x) for x in lexer.output ]))
  
  parser = Parser.Parser(ErrorHandler(
        text, 
        "<main>",
        py_error = True
    ), lexer)
  
  try:
    ast = parser.parse()
    print(json.dumps(ast, indent=2))
    Executor = Exec.Executor(text, ast['body']).run()
  except Exception as e:
    if "py_error is True" not in str(e): traceback.print_exc()

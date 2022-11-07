from Error import Highlight, styles
from sty import fg

Operators = {}


def missingOperand(left, errorhandler, line, ast, placeholder):
  did_you_mean = Highlight(line, {
      'background': None,
      'linenums': None
  })
  if left:
    did_you_mean = styles['suggestion'] + placeholder + ' ' + fg.rs + did_you_mean
  else:
     did_you_mean = did_you_mean + styles['suggestion'] + ' ' + placeholder + fg.rs
  start = ast['positions']['start']
  end = ast['positions']['end']
  errorhandler.throw('Syntax', 'Expected Operand.', {
    'lineno': start['line'],
    'marker': {
      'start': start['col'] - 1 if left else end['col'] + 2,
      'length': 1
    },
    'underline': {
      'start': start['col'] - 1 if left else start['col'],
      'end': end['col'] if left else end['col'] + 1
    },
    'did_you_mean': did_you_mean
  })

def operator(name):
  def decor(funct):
    Operators[name] = funct
    def wrapper_func():
        funct()
    return wrapper_func
  return decor

@operator('+')
def add(x, y, errorhandler, line, ast): 
    if x == None:
      missingOperand(True, errorhandler, line, ast, f'<{str(type(y or 0).__name__)}>')
    if y == None:
      missingOperand(False, errorhandler, line, ast, f'<{str(type(x or 0).__name__)}>')
    #TODO: add if y and x equal none
    return x + y
  
@operator('-')
def sub(x, y, errorhandler, line, ast):
    if x == None:
      missingOperand(True, errorhandler, line, ast, f'<{str(type(y or 0).__name__)}>')
    if y == None:
      missingOperand(False, errorhandler, line, ast, f'<{str(type(x or 0).__name__)}>')
    #TODO: add if y and x equal none
    return x - y
  
@operator('*')
def mult(x, y, errorhandler, line, ast):
    if x == None:
      missingOperand(True, errorhandler, line, ast, f'<{str(type(y or 0).__name__)}>')
    if y == None:
      missingOperand(False, errorhandler, line, ast, f'<{str(type(x or 0).__name__)}>')
    #TODO: add if y and x equal none
    return x * y

@operator('/')
def div(x, y, errorhandler, line, ast):
    if x == None:
      missingOperand(True, errorhandler, line, ast, f'<{str(type(y or 0).__name__)}>')
    if y == None:
      missingOperand(False, errorhandler, line, ast, f'<{str(type(x or 0).__name__)}>')
    #TODO: add if y and x equal none
    return x / y

@operator('==')
def logicalequals(x, y, errorhandler, line, ast):
    if x == None:
      missingOperand(True, errorhandler, line, ast, f'<{str(type(y or 0).__name__)}>')
    if y == None:
      missingOperand(False, errorhandler, line, ast, f'<{str(type(x or 0).__name__)}>')
    #TODO: add if y and x equal none
    return x == y

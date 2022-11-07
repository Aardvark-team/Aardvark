#Recusively execute code.
import Error
from Lexer import Token
import sys
from Operators import Operators

class Object:
  def __init__(self, inherit={}, init=None):
    self.vars = {}
    self.vars.update(inherit)
    if init:
      init(self)
    self._index = 0
  def set(self, name, value):
    self.vars[name] = value
  def __setitem__(self, name, value):
    return self.set(name, value)
  def get(self, name, default = None):
    return self.vars.get(name, default)
  def __getitem__(self, name):
    return self.get(name)
  def delete(self, name):
    del self.vars[name]
  def __delattr__(self, name):
    return self.delete()
  def __delitem__(self, name):
    return self.delete()
  def __iter__(self):
    return self.vars
  def __next__(self):
    if self._index >= len(self.vars) - 1:
      self.index = 0
      raise StopIteration
    else: 
      self._index += 1
      return self.vars.keys()[self._index]


class Scope(Object):
  def __init__(self, vars = {}, parent=None):
    self.vars = vars
    self.parent = parent or None
    self._index = 0
  def set(self, name, value):
    self.vars[name] = value
  def __setitem__(self, name, value):
    return self.set(name, value)
  def get(self, name, default = None):
    if self.parent:
      return self.vars.get(name, self.parent.get(name, default)) #To allow access to higher scopes.
    else:
      return self.vars.get(name, default)
  def __getitem__(self, name):
    return self.get(name)
  def delete(self, name):
    del self.vars[name]
  def __delattr__(self, name):
    return self.delete()
  def __delitem__(self, name):
    return self.delete()
  def __iter__(self):
    return self
  def __next__(self):
    if self._index >= len(self.vars) - 1:
      self.index = 0
      raise StopIteration
    else: 
      self._index += 1
      return self.vars.keys()[self._index]

class Executor:
  def __init__(self, code, ast):
    self.code = code
    self.codelines = code.split('\n')
    self.ast = ast
    self.Global = Scope({
      'stdout': Object({
        'write': lambda *args: print(*args, end=""), #Just simple for now
      }),
      'stdin': Object({
        #Many of our stdin functions can't be implemented in python.
        'prompt': lambda x: input(x), #Also simple
      }),
      'stderr': Object({
        'write': lambda *args: print(*args, end="", file=sys.stderr)
      })
    }) #Define builtins here
    self.errorhandler = Error.ErrorHandler(
        code, 
        "<main>",
        py_error = True
    )
    def makefunct(self, name, code, scope):
      def x(**kwargs):
        scope = Scope(kwargs, parent = scope)
        self.Exec(code, scope)
      scope[name] = x
  def getVar(self, scope, varname: str, start):
    if scope.get(varname, False):
        return scope[varname]
    else:
        self.errorhandler.throw('Value', f'Undefined variable "{varname}"', {
          'lineno':start['line'],
          'marker': {
            'start': start['col'] + 1,
            'length': len(varname)
          },
          'underline': {
            'start': start['col'],
            'end': start['col'] + len(varname)
          }
        })
  def ExecExpr(self, expr: dict, scope: Scope):
    match expr:
      case {'type': 'VariableDefinition'}:
        scope[expr['name']] = self.ExecExpr(expr['value'], scope) #Simple implementation.
      case {'type': 'NumberLiteral'}:
        return expr['value'] #Numbers not objects yet, didn't have time to add
      case {'type': 'StringLiteral'}:
        return expr['value']
      case {'type': 'VariableAccess'}:
        return self.getVar(scope, expr['value'], expr['positions']['start'])
      case {'type': 'Object'}:
        obj = Object()
        for k, v in expr['pairs'].items():
          obj[k] = self.ExecExpr(v, scope)
        return obj
      case { 'type': 'Set' }:
        return {self.ExecExpr(item, scope) for item in expr['items']}
      case { 'type': 'Array' }:
        return [self.ExecExpr(item, scope) for item in expr['items']]
      case { 'type': 'DeleteStatement' }:
          self.getVar(scope, expr['target']['value'], expr['target']['positions']['start'])
          del scope[expr['name']]
      case { 'type': 'FunctionCall' }:
          funct = self.getVar(scope, expr['name'], expr['tokens']['name'].start)
          return funct(*[self.ExecExpr(arg, scope) for arg in expr['arguments']])
      case { 'type': 'MethodCall' }:
          obj = self.ExecExpr(expr['value'], scope)
          funct = self.getVar(obj, expr['property'], expr['positions']['start'])
          return funct(*[self.ExecExpr(arg, scope) for arg in expr['arguments']])
      case { 'type': 'Operator' }:
          if expr['operator'] not in Operators:
            notImplemented(self.errorhandler, f'Operator "{expr["operator"]}" not yet implemented.', expr)
          left = self.ExecExpr(expr['left'], scope)
          op = Operators[expr['operator']]
          right = self.ExecExpr(expr['right'], scope)
          return op(left, right, self.errorhandler, self.codelines[expr['positions']['start']['line']], expr)
      case { 'type': 'IfStatement' }:
        pass
      case None:
        return None
      case _:
          notImplemented(self.errorhandler, expr['type'], expr)
      
  def Exec(self, ast: dict, scope: Scope):
    ret_val = None
    for item in ast:
      ret_val = self.ExecExpr(item, scope)

    return ret_val
    
  def run(self):
    return self.Exec(self.ast, self.Global)


def notImplemented(errorhandler, item, expr):
    start = expr['positions']['start']
    end = expr['positions']['end']
    errorhandler.throw('NotImplemented', f'{item} is not yet implemented.', {
      'lineno': start['line'],
      'underline': {
        'start': end['col']+1,
        'end': end['col']+1
      },
      'marker': {
        'start': start['col'] + 1,
        'length': end['col'] - start['col'] + 1
      }
    })
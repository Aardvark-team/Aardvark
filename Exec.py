#Recusively execute code.
import Error
from Lexer import Token
import sys
from Operators import Operators
import random
from nltk import edit_distance

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
  def __repr__(self):
    return self.vars.__repr__()
  def __str__(self):
    return self.vars.__str__()


class Scope(Object):
  def __init__(self, vars = {}, parent=None):
    self.vars = vars
    self.parent = parent or None
    self._index = 0
    self._returned_value = None
    self._has_returned = False
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
  def __repr__(self):
    return self.vars.__repr__()
  def __str__(self):
    return self.vars.__str__()
    
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
    )#function x(y, z) stdout.write(y, z, '\n')
  def makeFunct(self, name, params, code, scope):
      def x(*args, **kwargs):
        id = random.randint(0, 1000)
        functscope = Scope(parent = scope)
        for i in range(len(params)):
          param = params[i]
          arg = args[i]
          if param['value_type'] != None:
            notImplemented(self.errorhandler, 'Type Checking', param)
          functscope[param['name']] = arg
          print(f'defined {param["name"]} as {arg} {id}')
        self.Exec(code, functscope)
        return functscope._returned_value
      if name:
        scope[name] = x
      return x
  def getVar(self, scope, varname: str, start, error=True):
    if scope.get(varname, False):
        return scope[varname]
    elif error:
        line = self.codelines[start['line']-1]
        did_you_mean = line[:start['col']-1] + findClosest(varname, scope) + line[start['col']+len(varname)-1:]
        return self.errorhandler.throw('Value', f'Undefined variable "{varname}"', {
          'lineno':start['line'],
          'marker': {
            'start': start['col']-1,
            'length': len(varname)-1
          },
          'underline': {
            'start': start['col']-2,
            'end': start['col'] + len(varname)
          },
          'did_you_mean': Error.Highlight(did_you_mean, {'linenums':False})
        })
  def ExecExpr(self, expr: dict, scope: Scope, undefinedError=True):
    match expr:
      case {'type': 'VariableDefinition'}:
        if expr['value_type']:
            notImplemented(self.errorhandler, 'Type Checking', expr)
        scope[expr['name']] = self.ExecExpr(expr['value'], scope) #Simple implementation.
      case {'type': 'NumberLiteral'}:
        return expr['value'] #Numbers not objects yet, didn't have time to add
      case {'type': 'StringLiteral'}:
        return expr['value']
      case {'type': 'VariableAccess'}:
        return self.getVar(scope, expr['value'], expr['positions']['start'], undefinedError)
      case {'type': 'PropertyAccess'}:
        obj = self.ExecExpr(expr['value'], scope, undefinedError)
        if not isinstance(obj, Object) and undefinedError:
          return self.errorhandler.throw('Value', f'{expr["value"]} has no property {property}.')
        elif not isinstance(obj, Object): #If errors are surpressed, return None
          return None
        return self.getVar(obj, expr['property'], expr['positions']['start'], undefinedError)
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
        if expr['operator'] == '?':
          left = self.ExecExpr(expr['left'], scope, False)
          op = Operators[expr['operator']]
          right = self.ExecExpr(expr['right'], scope)
          return op(left, right, self.errorhandler, self.codelines[expr['positions']['start']['line']-1], expr)
        elif expr['operator'] in Operators:
          left = self.ExecExpr(expr['left'], scope)
          op = Operators[expr['operator']]
          right = self.ExecExpr(expr['right'], scope)
          return op(left, right, self.errorhandler, self.codelines[expr['positions']['start']['line']-1], expr)
        else:
          return notImplemented(self.errorhandler, f'Operator "{expr["operator"]}" not yet implemented.', expr)
      case { 'type': 'IfStatement' }:
        if bool(self.ExecExpr(expr['condition'], scope)):
          ifscope = Scope(parent = scope)
          self.Exec(expr['body'], ifscope)
        elif expr['else_body']:
          ifscope = Scope(parent = scope)
          self.Exec(expr['else_body'], ifscope)
      case { 'type': 'FunctionDefinition' }:
        funct = self.makeFunct(expr['name'], expr['parameters'], expr['body'], scope)
        return funct
      case { 'type': 'ReturnStatement' }:
        scope._returned_value = self.ExecExpr(expr['value'], scope)
        scope._has_returned = True
      case None:
        return None
      case _:
          notImplemented(self.errorhandler, expr['type'], expr)
      
  def Exec(self, ast, scope: Scope):
    ret_val = None
    for item in ast:
      ret_val = self.ExecExpr(item, scope)
      if scope._has_returned: break
    return ret_val
    
  def run(self):
    return self.Exec(self.ast, self.Global)


def notImplemented(errorhandler, item, expr):
    start = expr['positions']['start']
    end = expr['positions']['end']
    errorhandler.throw('NotImplemented', f'{item} is not yet implemented.', {
      'lineno': start['line'],
      'underline': {
        'start': 0,
        'end': end['col']
      },
      'marker': {
        'start': start['col']-1,
        'length': end['col'] - start['col'] + 1
      }
    })

def findClosest(var, scope):
  lowest = 99999999999999
  ret = '<identifier>'
  for item in list(scope.vars.keys()):
    dist = edit_distance(var, item)
    if dist < lowest: 
      ret = item
      lowest = dist
  return ret
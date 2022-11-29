# Note, doing an operataion on a obj changes its type back to the python version.
# So, I added a function to convert it to its Aardvark version.
# Note, we need to add unit test.
# Recusively execute code.
import Error
from Lexer import Token
import sys
from Operators import Operators
import random
from nltk import edit_distance
from Types import Null, Object, Scope, Number, String, Boolean, pyToAdk, Function

def get_call_scope(scope):
    call_scope = [ "scope " + str(id(scope)) ]
    if scope.parent: call_scope += get_call_scope(scope.parent)

    return call_scope

class Executor:
  def __init__(self, code, ast, errorhandler):
    self.code = code
    self.codelines = code.split('\n')
    self.ast = ast
    self.traceback = []
    self.Global = Scope({
      'stdout': Object({
        'write': lambda *args: print(*args, end=""), #Just simple for now
      }, name="stdout"),
      'stdin': Object({
        #Many of our stdin functions can't be implemented in python.
        'prompt': lambda x: input(x), #Also simple
        'readLine': lambda: input()
      }, name="stdin"),
      'stderr': Object({
        'write': lambda *args: print(*args, end="", file=sys.stderr)
      }, name="stderr"),
      'slice': lambda str, start, end: str[start:end],
      'typeof': lambda obj: type(obj).__name__,
      'dir': lambda x=None: x.vars if x else self.Global.vars,
      'null': Null,
      'Math': Object({
        
      })
    }) #Define builtins here
    #TODO: implement more builtins.
    self.errorhandler = errorhandler
  def defineVar(self, name, value, scope):
    if name in scope.getAll() and name not in list(scope.vars.keys()):
      self.defineVar(name, value, scope.parent)
    else:
      scope[name] = value
  def makeFunct(self, expr, parent):
      name = expr['name']
      params = expr['parameters']
      code = expr['body']
      AS = expr['as']
      def x(*args, **kwargs):
        functscope = Scope({}, parent = parent, is_func = True)
        if AS:
          functscope[AS] = x
        for i in range(len(params)):
          param = params[i]
          arg = args[i]
          if param['value_type'] != None:
            notImplemented(self.errorhandler, 'Type Checking', param)
          self.defineVar(param['name'], arg, functscope)
        #self.traceback.append({
        #  'name': f'{name}()',
        #  'line':
        #})
        ret = self.Exec(code, functscope)
        #self.traceback = self.traceback[:-1]
        #print('ret', ret, functscope._returned_value)

        #print(" -> ".join(get_call_scope(functscope)), functscope._returned_value)
        return functscope._returned_value
      if name:
        parent[name] = Function(x)
      return Function(x)
    
  def getVar(self, scope, varname: str, start, error=True, message='Undefined variable "{name}"'):
    val = scope.get(varname, None)
    success = val != None

    if success:
        return pyToAdk(val)
    elif error:
        line = self.codelines[start['line']-1]
        #print('Availiable vars in current scope (not including parent scopes):', ', '.join(scope.vars.keys()))
        did_you_mean = line[:start['col'] - 1] + findClosest(varname, scope) + line[start['col'] + len(varname) - 1:]
        return self.errorhandler.throw('Value', message.format(name=varname), {
          'lineno':start['line'],
          'marker': {
            'start': start['col'],
            'length': len(varname)
          },
          'underline': {
            'start': start['col'] - 2,
            'end': start['col'] + len(varname)
          },
          'did_you_mean': Error.Highlight(did_you_mean, {'linenums': False})
        })
      
  def ExecExpr(self, expr: dict, scope: Scope, undefinedError=True):
    match expr:
      case {'type': 'NumberLiteral'}:
        return Number(expr['value'])
      case {'type': 'StringLiteral'}:
        return String(expr['value'])
      case {'type': 'BooleanLiteral'}:
        return Boolean(expr['value'])
      case {'type': 'VariableAccess'}:
        return self.getVar(scope, expr['value'], expr['positions']['start'], undefinedError)
      case {'type': 'PropertyAccess'}:
        obj = self.ExecExpr(expr['value'], scope, undefinedError)
        objname = obj.name if 'name' in dir(obj) else Error.getAstText(expr['value'], self.codelines)
        return self.getVar(obj, expr['property'], expr['tokens']['property'].start, undefinedError, message=f"Undefined property \"{{name}}\" of \"{objname}\"")
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
          funct = self.getVar(scope, expr['name'], expr['positions']['start'])
          return pyToAdk(funct(*[self.ExecExpr(arg, scope) for arg in expr['arguments']]))
      case { 'type': 'MethodCall' }:
          obj = self.ExecExpr(expr['value'], scope)
          if not isinstance(obj, Object):
            #for rn, only objects have properties
            return self.errorhandler.throw('Value', f'{obj} has no property {expr["property"]}.', {
              'lineno': expr['positions']['start']['line'],
             'marker': {
               'start': expr['positions']['start']['col']-1,
               'length': len(expr['value'])
               },
             'underline': {
               'start': expr['positions']['start']['col']-2,
               'end': expr['positions']['start']['col'] + len(expr['value'])
             }
            })
          elif not isinstance(obj, Object): #If errors are surpressed, return None
            return None
          funct = self.getVar(obj, expr['property'], expr['tokens']['property'].start, message=f"Undefined property \"{{name}}\" of \"{obj.name}\"")
          return pyToAdk(funct(*[self.ExecExpr(arg, scope) for arg in expr['arguments']]))
      case {'type' : 'Operator', 'operator': '='}:
        right = self.ExecExpr(expr['right'], scope)
        self.defineVar(expr['left']['value'], right, scope)
        return right
      case {'type' : 'Operator', 'operator': '?'}:
          left = self.ExecExpr(expr['left'], scope, False)
          op = Operators[expr['operator']]
          right = self.ExecExpr(expr['right'], scope)
          return op(left, right, self.errorhandler, self.codelines[expr['positions']['start']['line']-1], expr)
      case { 'type': 'Operator', 'operator': operator}:
        if operator in Operators:
          left = self.ExecExpr(expr['left'], scope)
          op = Operators[operator]
          right = self.ExecExpr(expr['right'], scope)
          return pyToAdk(op(left, right, self.errorhandler, self.codelines[expr['positions']['start']['line'] - 1], expr))
        else:
          return notImplemented(self.errorhandler, f'Operator "{expr["operator"]}" not yet implemented.', expr)
      case { 'type': 'IfStatement' }:
        ifscope = Scope({}, parent = scope)
        if bool(self.ExecExpr(expr['condition'], scope)):
          return self.Exec(expr['body'], ifscope)
        elif expr['else_body']:
          return self.Exec(expr['else_body'], ifscope)
      case { 'type': 'WhileLoop' }:
        while bool(self.ExecExpr(expr['condition'], scope)):
          whilescope = Scope({}, parent = scope)
          ret = self.Exec(expr['body'], whilescope)
        return ret
      case { 'type': 'ForLoop' }:
        for item in self.ExecExpr(expr['iterable']):
          forscope = Scope({}, parent = scope)
          # i=0
          # for d in expr['delecarations']:
          #   if d['type'] = 'variable':
          #     item[]
          #   i+=1
          #TODO: Define the varaibles.
          ret = self.Exec(expr['body'], forscope)
        return ret
      case { 'type': 'FunctionDefinition' }:
        funct = self.makeFunct(expr, scope)
        return funct
      case {'type': 'DeferStatement'}:
        scope.addReturnAction(lambda: self.ExecExpr(expr['value'], scope))
      case { 'type': 'ReturnStatement' }:
        val = self.ExecExpr(expr['value'], scope)
        success = scope.set_return_value(val)
        if scope == self.Global or not success:
            self.Global._triggerReturnAction()
            sys.exit(int(val))
        return scope._returned_value
      case {'type': 'Multiply'}:
        #for (num)x mult
        return self.ExecExpr(expr['number'], scope) * self.getVar(scope, expr['variable'], expr['tokens']['variable'].start)
      case {'type': 'Index'}:
        return self.ExecExpr(expr['value'], scope)[self.ExecExpr(expr['property'], scope)]
      case None:
        return Null
      case _:
          if expr == Null: return Null
          notImplemented(self.errorhandler, expr['type'], expr)
        
  def Exec(self, ast, scope: Scope):
    ret_val = Null
    if type(ast).__name__ != 'list':
      ast = [ast]
    for item in ast:
      ret_val = self.ExecExpr(item, scope)
      if scope._has_returned or scope._returned_value: break
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
  for item in list(scope.getAll().keys()):
    dist = edit_distance(var, item)
    if dist < lowest: 
      ret = item
      lowest = dist
  return ret
# Note, doing an operataion on a obj changes its type back to the python version.
# So, I added a function to convert it to its Aardvark version.
# Note, we need to add unit test.
# Recusively execute code.
import Error
from Lexer import Token
import sys
from Operators import Operators
import random
import math
from nltk import edit_distance
from Types import Null, Object, Scope, Number, String, Boolean, pyToAdk, Function, Set, Array
import importlib

def get_call_scope(scope):
    call_scope = [ "scope " + str(id(scope)) ]
    if scope.parent: call_scope += get_call_scope(scope.parent)

    return call_scope

class Executor:
  def __init__(self, file, code, ast, errorhandler):
    self.file = file
    self.code = code
    self.codelines = code.split('\n')
    self.ast = ast
    self.traceback = [ ]
    self.switch = None
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
      'python': Object({ 
        'import': pyToAdk(lambda mod: importlib.import_module(mod)) #NOT WORKING
      }),
      'slice': lambda str, start, end: str[start:end],
      'typeof': lambda obj: type(obj).__name__,
      'dir': lambda x=None: x.vars if x else self.Global.vars,
      'sort': lambda iterable, reverse=False, key=(lambda x: x): sorted(iterable, reverse=reverse, key=key) ,
      'null': Null,
      'help': help,
      'sequence': lambda start, step, times: [(start + x * step) for x in range(times)],
      'Math': Object({
        'pi': math.pi,
        'π': math.pi,
        'e': math.e,
        'tau': math.tau,
        'round': round,
        'abs': abs,
        'factorial': math.factorial,
        'floor': math.floor,
        'ceil': math.ceil,
        'log': math.log,
      })
    }) #Define builtins here
    #TODO: implement more builtins.
    self.errorhandler = errorhandler
  def defineVar(self, name, value, scope):
    if name in scope.getAll() and name not in list(scope.vars.keys()):
      self.defineVar(name, value, scope.parent)
    else:
      scope.vars[name] = pyToAdk(value)
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
          arg = args[i] if i < len(args) else self.ExecExpr(param.get('default'), parent)
          if param['value_type'] != None:
            notImplemented(self.errorhandler, 'Type Checking', param)
          self.defineVar(param['name'], arg, functscope)
        ret = self.Exec(code, functscope)
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
          'did_you_mean': Error.Highlight(did_you_mean, {'linenums': False}),
          'traceback': self.traceback
        })
  
  def enterScope(self, var, scope):
    match var:
        case {'type': 'PropertyAccess'}:
          scope = self.enterScope(var['value'], scope)
          return self.getVar(scope, var['property'], var['positions']['start'])
        case _:
          return self.ExecExpr(var, scope)
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
        return Set({self.ExecExpr(item, scope) for item in expr['items']})
      case { 'type': 'Array' }:
        return Array([self.ExecExpr(item, scope) for item in expr['items']])
      case { 'type': 'DeleteStatement' }:
          self.getVar(scope, expr['target']['value'], expr['target']['positions']['start'])
          del scope[expr['name']]
      case { 'type': 'FunctionCall' }:
          funct = self.ExecExpr(expr['function'], scope)
          self.traceback.append({
            'name': Error.getAstText(expr['function'], self.codelines) + '()', 
            'line': expr['positions']['start']['line'], 
            'col': expr['positions']['start']['col'], 
            'filename': self.file
          })
          ret = funct(*[self.ExecExpr(arg, scope) for arg in expr['arguments']], **{k:ExecExpr(v, scope) for k, v in list(expr['keywordArguments'])})
          self.traceback = self.traceback[:-1]
          return pyToAdk(ret)
      case {'type' : 'Operator', 'operator': '='}:
        value = self.ExecExpr(expr['right'], scope)
        var = expr['left']
        defscope = scope
        if var['type'] == 'PropertyAccess':
          defscope = self.enterScope(var['value'], scope)
          var = var['property']
        elif var['type'] == 'VariableAccess':
          var = var['value']
        else:
          self.errorhandler.throw('Assign', 'Cannot set value of a literal.', {
            'lineno': var['positions']['start']['line'],
            'underline': {
              'start': var['positions']['start']['col'],
              'end': var['positions']['end']['col']
            },
            'marker': {
              'start': var['positions']['start']['col'],
              'length': var['positions']['end']['col'] - var['positions']['start']['col']
            }
          })
        self.defineVar(var, value, defscope)
        return value
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
        ret = []
        while bool(self.ExecExpr(expr['condition'], scope)):
          whilescope = Scope({}, parent = scope)
          ret.append(self.Exec(expr['body'], whilescope))
        return ret
      case { 'type': 'ForLoop' }:
        iterable = self.ExecExpr(expr['iterable'], scope)
        ret = []
        for item in iterable:
          forscope = Scope({}, parent = scope)
          item = iter(item)
          for d in expr['declarations']:
            if d['type'] == 'variable':
              self.defineVar(d['names'][0], next(item), scope)
            elif d['type'] == 'destructure':
              i = next(item)
              self.defineVar(d['names'][0], i, scope)
              self.defineVar(d['names'][1], iterable[i], scope)

          ret.append(self.Exec(expr['body'], forscope))
        return ret
      case {'type': 'CaseStatement'}:
        if self.switch == self.ExecExpr(expr['compare'], scope):
          casescope = Scope({}, parent = scope)
          self.Exec(expr['body'], casescope)
      case {'type': 'SwitchStatement'}:
        switchscope = Scope({}, parent = scope)
        self.switch = pyToAdk(self.ExecExpr(expr['value'], scope))
        self.Exec(expr['body'], scope)
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
            if val == Null: val = 0
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




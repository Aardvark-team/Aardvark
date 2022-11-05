#Recusively execute code.
import Error

class Object:
  def __init__(self, inherit={}, init=None):
    self.vars = {}.update(inherit)
    if init:
      init(self)
    self._index = 0
  def set(self, name, value):
    self.vars[name] = value
  def __setitem__(self, name, value):
    return self.set(name, value)
  def get(self, name):
    return self.vars.get(name, None)
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
    if self._index >= len(self.vars):
      self.index = 0
      raise StopIteration
    else: 
      self._index += 1
      return self.vars[self._index]

class Scope(Object):
  def __init__(self, parent=None):
    self.vars = {}
    self.parent = parent or None
    self._index = 0
    super.__init__(super())
  def set(self, name, value):
    self.vars[name] = value
  def __setitem__(self, name, value):
    return self.set(name, value)
  def get(self, name):
    return self.vars.get(name, self.parent.get(name)) #To allow access to higher scopes.
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
    if self._index >= len(self.vars):
      self.index = 0
      raise StopIteration
    else: 
      self._index += 1
      return self.vars[self._index]

class Executor:
  def __init__(self, code, ast):
    self.code = code
    self.codelines = code.split('\n')
    self.ast = ast
    self.Global = Scope({
      'stdout': Object({
        'write': lambda *args: print(*args, end=""), #Just simple for now
      })
    })
    self.ehandler = Error.ErrorHandler(
        code, 
        "<main>",
        py_error = True
    )
  def ExecExpr(self, expr: dict, scope: Scope):
    if expr.get('type') == 'VariableDefinition':
      scope[expr['name']] = ExecExpr(expr['value']) #Just a rough implementaton.
    elif expr.get('type') == 'NumberLiteral':
      return expr['value'] #Numbers not objects yet, didn't have time to add
    elif expr.get('type') == 'StringLiteral':
      return expr['value']
    elif expr.get('type') == 'VariableAccess':
      return scope[expr['value']]
    elif expr.get('type') == 'FunctionCall':
      if expr['name'] in scope:
        scope[expr['name']]([self.ExecExpr(arg) for arg in expr['arguments']])
      else:
        self.ehandler.throw('Value', f'Undefined variable {expr["name"]}', {
          'lineno':expr['positions']['start']['line'],
          'marker': {
            'start': 0,
            'length': 0
          },
          'underline': {
            'start': expr['positions']['start']['col'] + 1,
            'end': expr['positions']['start']['col'] - expr['positions']['end']['col']
          }
        })
  def Exec(self, ast: dict, scope: Scope):
    for item in ast:
      self.ExecExpr(item, scope)
  def run(self):
    self.Exec(self.ast, self.Global)
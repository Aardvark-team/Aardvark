import types
class Type:
  def get(self, name, default = None):
    return self.vars.get(name, default)
  def getAll(self):
    return self.vars
    
class Object(Type):
  def __init__(self, inherit={}, init=None, name=""):
    self.name = name;
    self.vars = {}
    self.vars.update(inherit)
    if init:
      init(self)
    self._index = 0
  def set(self, name, value):
    self.vars[name] = value
  def __setitem__(self, name, value):
    return self.set(name, value)
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
      return list(self.vars.keys())[self._index]
  def __repr__(self):
    return self.vars.__repr__()
  def __str__(self):
    return self.vars.__str__()


class Scope(Object):
  def __init__(self, vars, parent=None, is_func = False):
    self.vars = vars
    self.parent = parent or None
    self._index = 0 #for next() implementation.
    self._returned_value = Null
    self._has_returned = False
    self._is_function_scope = is_func
    self.returnActions = []
    
  def set(self, name, value):
    self.vars[name] = value
  
  def __setitem__(self, name, value):
    return self.set(name, value)
    
  def getAll(self):
    """Gets all variables useable in the current scope."""
    if self.parent:
      return self.vars | self.parent.getAll()
    else:
      return self.vars
    
  def get(self, name, default = None):
    if self.parent:
      return self.vars.get(name, self.parent.get(name, default))
    
    return self.vars.get(name, default)
    
  def _triggerReturnAction(self):
    for act in self.returnActions:
      act()
      
  def addReturnAction(self, item):
    self.returnActions.append(item)
    
  def set_return_value(self, value):
    if not self._is_function_scope:
      return self.parent.set_return_value(value) if self.parent != None else False

    # print(id(self), "Returned", value)
    self._returned_value = value
    self._has_returned = True
    self.__triggerReturnAction()
    return True
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
      return list(self.vars.keys())[self._index]
  def __repr__(self):
    return self.vars.__repr__()
  def __str__(self):
    return self.vars.__str__()
    
class __Null(Type):
  def __repr__(self): return 'null'
  def __str__(self): return 'null'
  def __bool__(self): return False
  def __call__(self): return self
    
class String(str, Type):
  def __init__(self, value):
    self.vars = {
      'length': len(value),
      'split': lambda sep=" ": self.value.split(sep.value if isinstance(sep, String) else sep),
      'slice': lambda start, end: self.value[start.value:end.value],
    }
    str.__init__(value)
  def __sub__(self, other):
    return self.removesuffix(other)

class Number(Type, float):
  def __init__(self, value):
    self.vars = {
      'digits': [Number(int(x)) if x not in '.-' else x for x in list(str(value))] if len(str(value)) > 1 else [value]
      #methods and attributes here
    }
    float.__init__(value)
  def __repr__(self):
    if self % 1 == 0:
      return str(int(self))
    else: return str(float(self))
  def __str__(self):
    if self % 1 == 0:
      return str(int(self))
    else: return str(float(self))
  def __index__(self):
    return int(self)

class Boolean(int, Type):
  def __init__(self, value):
    if value != 0: value = 1
    self.vars = {
      #methods and attributes here
    }
    int.__init__(value)
  def __repr__(self):
    if self == 1: return 'true'
    return 'false'
  def __str__(self):
    if self == 1: return 'true'
    return 'false'
  def __bool__(self):
    return self == 1

class Function(Type):
  def __init__(self, funct):
    self.funct = funct
    Type.__init__(self)
  def __call__(self, *args):
    return self.funct(*args)

#TODO: Add: Array, Set, more...
Null = __Null()

def pyToAdk(py):
  if py == None: return Null
  elif isinstance(py, bool): return Boolean(py)
  elif isinstance(py, int) or isinstance(py, float): return Number(py)
  elif isinstance(py, str): return String(py)
  elif isinstance(py, types.FunctionType): return Function(py)
  else: return py
import types
import io
import time
import os


class Type:
    def get(self, name, default=None):
        return self.vars.get(name, default)

    def getAll(self):
        return self.vars
      
    def set(self, name, value):
        self.vars[name] = value

    def __setitem__(self, name, value):
        return self.set(name, value)

    def __getitem__(self, name):
        return self.get(name)


class Object(Type):
    def __init__(self, inherit={}, name="", _class=None, call=None, setitem=None, getitem=None):
        self._class = _class
        self.name = name
        self.vars = {}
        for i in inherit:
          self.vars[i] = pyToAdk(inherit[i])
        self._call = call
        self._setitem = setitem #TODO
        self._getitem = getitem #TODO
        #etc... Add later TODO
        self._index = 0

    def set(self, name, value):
        self.vars[name] = value
      
    def __call__(self, *args, **kwargs):
      if self._call:
        return self._call(self, self._class.AS, *args, **kwargs)
        
    def __setitem__(self, name, value):
        if self._setitem:
          return self._setitem(self, self._class.AS)
        return self.set(name, value)

    def __getitem__(self, name):
        if self._getitem:
          return self._getitem(self, self._class.AS)
        return self.get(name)

    def delete(self, name):
        del self.vars[name]

    def __delattr__(self, name):
        return self.delete(name)

    def __delitem__(self, name):
        return self.delete(name)

    def __iter__(self):
        return iter(self.vars)

    def __next__(self):
        if self._index >= len(self.vars) - 1:
            self.index = 0
            raise StopIteration
        else:
            self._index += 1
            return list(self.vars.keys())[self._index]

    def __repr__(self):
        if self._class:
            return self._class.childstr()
        return self.vars.__repr__()

    def __str__(self):
        if self._class:
            return self._class.childstr()
        return self.vars.__str__()


class Scope(Object):
    def __init__(self, vars, parent=None, is_func=False):
        self.vars = vars
        self.parent = parent or None
        self._index = 0  # for next() implementation.
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

    def get(self, name, default=None):
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
        self._triggerReturnAction()
        return True

    def __getitem__(self, name):
        return self.get(name)

    def delete(self, name):
        del self.vars[name]

    def __delattr__(self, name):
        return self.delete(name)

    def __delitem__(self, name):
        return self.delete(name)

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
    def __repr__(self):
        return "null"

    def __str__(self):
        return "null"

    def __bool__(self):
        return False

    def __call__(self):
        return self


class String(str, Type):
    def __init__(self, value):
        value = str(value)
        self.vars = {
            "length": len(value),
            "split": lambda sep=" ": self.split(sep),
            "slice": lambda start, end: self[start : end],
            "startsWith": lambda prefix: self.startswith(x),
            "endsWith": lambda suffix: self.endswith(x),
            "replace": lambda x, y="": self.replace(x, y),
            "contains": lambda x: x in y,
        }
        str.__init__(value)

    def __sub__(self, other):
        return self.removesuffix(other)


class Number(Type, float):
    def __init__(self, value):
        if type(value) not in [float, int]:
          try:
            value = float(value)
          except:
            value = float(int(value))
        float.__init__(value)
        self.vars = {
            "digits": [int(x) if x in "0123456789" else x for x in str(value)]
            if len(str(value)) > 1
            else [value],
            # methods and attributes here
        }
        try:
            self.vars["prime"] = self >= 1 and all(self % i for i in range(2, int(self**0.5) + 1))
        except OverflowError:
            self.vars["prime"] = True
        #TODO: add prime factorization function to math.
    def __repr__(self):
        if self % 1 == 0:
            return str(int(self))
        else:
            return str(float(self))

    def __str__(self):
        if self % 1 == 0:
            return str(int(self))
        else:
            return str(float(self))

    def __index__(self):
        return int(self)

    def __getitem__(self, *args):
        return self.vars["digits"].__getitem__(*args)
    def __call__(self, x):
        return self * x


class Boolean(int, Type):
    def __init__(self, value):
        value = bool(value)
        if value != 0:
            value = 1
        self.vars = {
            # methods and attributes here
        }
        int.__init__(value)

    def __repr__(self):
        if self == 1:
            return "true"
        return "false"

    def __str__(self):
        if self == 1:
            return "true"
        return "false"

    def __bool__(self):
        return self == 1


class Function(Type):
    def __init__(self, funct):
        self.vars = {} # Funtions have no default attributes.
        self.funct = funct
        Type.__init__(self)

    def __call__(self, *args, **kwargs):
        return pyToAdk(self.funct(*args, **kwargs))

      
class Array(Type, list):
    def __init__(self, value):
        value = list(value)
        self.vars = {
            'contains': lambda x: x in self,
            'add': self.append,
            'remove': self.remove
            # methods and attributes here
        }
        list.__init__([])
        for i in value:
          self.append(pyToAdk(i))

      
class Set(Type, list):
    def __init__(self, value):
        value = list(value)
        self.vars = {
            'contains': lambda x: x in self,
            'add': self.append,
            'remove': self.remove
            # methods and attributes here
        }
        list.__init__([])
        for i in value:
          if i not in self:
            self.append(pyToAdk(i))
          #x = set{1, 2, 3}
    def __repr__(self):
      s = ''
      for i in self:
        s += str(i) + ', '
      s = s[:-2]
      return f'set{{{s}}}'
      
    def __str__(self):
      s = ''
      for i in self:
        s += str(i) + ', '
      s = s[:-2]
      return f'set{{{s}}}'

class File(Type):
  def __init__(self, obj):
    #NOT FINISHED
    # print(dir(value))
    self.name = obj.name
    self.mode = obj.mode
    self.obj = obj
    self.vars = {
      'read': self.read,
      'write': self.write,
      'readAll': self.readAll,
      'readLine': self.readLine,
      'writeLines': self.writeLines,
      'erase': self.erase,
      'move': self.move,
      'delete': self.delete,
      'name': self.name,
      'mode': self.mode
    }
  def read(self, chars=1):
    return self.obj.read(chars)
  def readLine(self):
    return self.obj.readline()
  def readAll(self):
    return self.obj.read()
  def write(self, *args):
    return self.obj.write(' '.join([str(a) for a in args]))
  def writeLines(self, *lines):
    return self.obj.writelines(*str(lines))
  def delete(self):
    os.remove(self.name)
  def erase(self):
    open(self.name, 'w').close()
  def move(self, new):
    os.rename(self.name, new)

class Class(Type):
    def __init__(self, name, parent=None, extends=[], AS=None):
      self.name = name
      self.vars = {}
      self.parent = parent
      self.AS = AS
      for e in extends:
        self.vars.update(e.vars)
      #Just to make it act like a scope
      self._returned_value = Null
      self._has_returned = False
      self._is_function_scope = False
      self.returnActions = []
    def addReturnAction(self, item):
        pass
    def set_return_value(self, value):
        return False
    def childstr(self):
      return f'<instance of {self.name}>'
    def __repr__(self):
        return str(self)
    def __str__(self):
        return f'<Class {self.name}>'
    def __call__(self, *args, **kwargs):
        obj = Object(self.vars, _class=self, call=self.getSpecial('call'), getitem=self.getSpecial('getitem'), setitem=self.getSpecial('setitem'))
        init = self.getSpecial('constructor')
        if init:
          init(obj, self.AS, *args, **kwargs)
        return obj
    def getSpecial(self, sp):
        return self.get('$'+sp)
    def getAll(self):
        """Gets all variables useable in the current scope."""
        if self.parent:
            return self.vars | self.parent.getAll()
        else:
            return self.vars

    def get(self, name, default=None):
        if self.parent:
            return self.vars.get(name, self.parent.get(name, default))

        return self.vars.get(name, default)

# TODO: Add: File, Stream, Bitarray
Null = __Null()

Types = [Object, Scope, Type, __Null, Number, String, Function, Boolean, Set, Array, File, Class]


def dict_from_other(old):
    context = {}
    for setting in dir(old):
        if not setting.startswith("_"):
            v = getattr(old, setting)
            if not isinstance(v, types.ModuleType):
                context[setting] = getattr(old, setting)
    return context

def pyToAdk(py):
    try:
        if type(py) in Types:
            return py
        elif py == None:
            return Null
        elif isinstance(py, bool):
            return Boolean(py)
        elif isinstance(py, int) or isinstance(py, float):
            return Number(py)
        elif isinstance(py, str):
            return String(py)
        elif isinstance(py, list):
            return Array(py)
        elif isinstance(py, set):
            return Set(py)
        elif isinstance(py, dict):
            return Object(py)
        elif isinstance(py, type):
            return Class(py.__name__)
        elif isinstance(py, types.ModuleType):
            return Object(dict_from_other(py))
        elif callable(py):
            return Function(py)
        elif isinstance(py, io.TextIOBase) or isinstance(py, io.BufferedIOBase) or isinstance(py, io.RawIOBase) or isinstance(py, io.IOBase):
          return File(py)
        else:
            return Object(dict_from_other(py))
    except RecursionError:
      return py

def adkToPy(adk):
  if type(adk) not in Types:
      return adk
  elif adk == Null:
    return None
  #TODO: finish later

# print(type(open('main.py')))
# print(dir(io.TextIOWrapper))
# File(io.TextIOWrapper)
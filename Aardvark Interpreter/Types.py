import types
import io
import time
import os
import sys
import inspect
from functools import cmp_to_key


def convert_number(number: str, base: int, charmap: str):
    value = 0
    for i, char in enumerate(number):
        if charmap.index(char) >= base:
            raise Exception(f"character '{char}' is not in base {base}")
        value += charmap.index(char) * base ** (len(number) - 1 - i)

    return value


def get_number(number: str, base: int, charmap: str):
    mult = 1

    while number.startswith("-") or number.startswith("+"):
        if number.startswith("+"):
            number = number[1:]
        else:
            number = number[1:]
            mult *= -1

    parts = number.split(".")

    num = convert_number(parts[0], base, charmap)
    if len(parts) > 1:
        num += convert_number(parts[1], base, charmap) / (base ** len(parts[1]))

    return num * mult


class Type:
    vars = {}

    @classmethod
    def get(self, name, default=None):
        if getattr(self, "parent", None):
            return self.vars.get(name, self.parent.get(name, default))
        else:
            return self.vars.get(name, default)

    @classmethod
    def getAll(self):
        if getattr(self, "parent", None):
            return self.vars | self.parent.getAll()
        else:
            return self.vars

    @classmethod
    def set(self, name, value):
        self.vars[name] = value

    def __setitem__(self, name, value):
        return self.set(name, value)

    def __getitem__(self, name):
        return self.get(name)


class Object(Type):
    def __init__(
        self,
        inherit={},
        name="",
        _class=None,
        call=None,
        setitem=None,
        getitem=None,
        deleteitem=None,
        delete=None,
        string=None,
    ):
        self._class = _class
        self.name = name
        self.vars = {}
        self.getters = {}
        self.setters = {}
        for i in inherit:
            self.vars[i] = pyToAdk(inherit[i])
        self._call = call
        self._setitem = setitem
        self._getitem = getitem
        self._deleteitem = deleteitem
        self._delete = delete
        self._string = string
        # Just to make it act like a scope
        self._returned_value = Null
        self._has_returned = False
        self._has_been_broken = False
        self._has_been_continued = False
        self._completed = False
        self._is_function_scope = False
        self.returnActions = []
        self.addReturnAction = lambda x: None
        self.set_return_value = lambda x: False
        self._has_been_broken = False
        self._scope_type = "Object"
        # etc... Add later TODO
        self._index = 0

    def define_getter(self, name: str, getter):
        self.getters[name] = getter

    def define_setter(self, name: str, setter):
        self.setters[name] = setter

    def set(self, name, value):
        if name in self.setters:
            self.setters[name](value)
            return
        elif name in self.getters:
            del self.getters[name]
        self.vars[name] = value

    def get(self, name, default=None):
        if name in self.getters:
            return self.getters[name]()

        return self.vars.get(name, default)

    def __call__(self, *args, **kwargs):
        if "_call" in dir(self) and self._call:
            return self._call(*args, **kwargs)

    def __setitem__(self, name, value):
        if self._setitem:
            return self._setitem(name, value)
        return self.set(name, value)

    def __getitem__(self, name):
        if self._getitem:
            return self._getitem(name)
        return self.get(name, Null)

    def __del__(self):
        if self._delete:
            self._delete()

    def delete(self, name):
        del self.vars[name]

    def __delitem__(self, name):
        if self._deleteitem:
            return self._deleteitem(name)
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
        return str(self)

    def __str__(self):
        if self._string:
            return self._string()
        if self._class:
            return self._class.childstr()
        return self.vars.__str__()

    def __add__(self, other):
        return Object(self.vars | other.vars)


class Scope(Object):
    def __init__(self, vars, parent: "Scope | None" = None, scope_type=None):
        self.vars = vars
        self.parent = parent or None
        self._index = 0  # for next() implementation.
        self._returned_value = Null
        self._has_returned = False
        self._has_been_broken = False
        self._has_been_continued = False
        self._completed = False
        self._scope_type = scope_type
        self.returnActions = []
        self.getters = {}
        self.setters = {}

    def define_getter(self, name: str, getter):
        self.getters[name] = getter

    def define_setter(self, name: str, setter):
        self.setters[name] = setter

    def set(self, name, value):
        if name in self.setters:
            self.setters[name](value)
            return
        elif name in self.getters:
            del self.getters[name]
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

        if name in self.getters:
            return self.getters[name]()

        return self.vars.get(name, default)

    def _triggerReturnAction(self):
        for act in self.returnActions:
            act()

    def addReturnAction(self, item, stype="function"):
        if self._scope_type != stype:
            return self.parent.setReturnAction(item, stype) if self.parent else False

        self.returnActions.append(item)
        return True

    def complete(self, stype="function", ret=None, action=lambda s: None):
        if self._scope_type != stype:
            x = self.parent.complete(stype, ret, action) if self.parent else False
            if x:
                self._completed = True
                return x

        self._returned_value = ret if ret != None else Null
        if self._scope_type == "loop":
            self._has_been_broken = True
        if self._scope_type == "function":
            self._has_returned = True
        action(self)
        self._completed = True
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

    def __del__(self):
        pass


class _Undefined(Type):
    def __repr__(self):
        return "null"

    def __str__(self):
        return "null"

    def __bool__(self):
        return False


class _Null(Type):
    def __repr__(self):
        return "null"

    def __str__(self):
        return "null"

    def __bool__(self):
        return False

    # def __call__(self):
    #     return self

    def __eq__(self, other):
        return type(other) == _Null

    def __ne__(self, other):
        return type(other) != _Null

    def __setattr__(self, name: str, value):
        return super().__setattr__(name, value)


class String(str, Type):
    vars = {
        "from_ordinal": lambda x: chr(x),
    }

    def __init__(self, value):
        value = str(value)
        self.vars = {
            "length": len(value),
            "split": lambda sep=" ": self.split(sep),
            "slice": lambda start, end, step=1: String(
                self[start : (end if end > 0 else len(value) + end) : step]
            ),
            "startsWith": lambda prefix: self.startswith(prefix),
            "endsWith": lambda suffix: self.endswith(suffix),
            "replace": lambda x, y="": self.replace(x, y),
            "contains": lambda x: x in self,
            "join": self.join,
            "indexOf": self.find,
            "rstrip": self.rstrip,
            "lstrip": self.lstrip,
            "strip": self.strip,
            "copy": lambda: String(value),
            "ordinal": lambda: ord(self),
            "from_ordinal": lambda x: chr(x),
        }
        str.__init__(self)

    def __sub__(self, other):
        return self.removesuffix(other)

    def __round__(self):
        return self.lower()

    @classmethod
    def get(self, name, default=None):
        if type(name) in [Number, int] or (
            type(name) in [str, String] and name.isdigit()
        ):
            index = int(name)
            if index >= len(self):
                return default
            return self[index]
        return self.vars.get(name, default)

    @classmethod
    def getAll(self):
        return self.vars | (
            {x: self[x] for x in range(len(self))} if type(self) != type else {}
        )

    def from_ordinal(self, x):
        return chr(x)


class Number(Type):
    def __init__(
        self,
        value=0,
        base=10,
        map=String("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    ):
        if type(value) in [str, String]:
            try:
                value = get_number(value, base, map)
            except Exception as e:
                value = int(value, base)
        self.value = value
        float.__init__(self)
        self.vars = {
            "digits": (
                [int(x) if x in "0123456789" else x for x in str(value)]
                if len(str(value)) > 1
                else [value]
            ),
            # methods and attributes here
        }
        try:
            self.vars["prime"] = value >= 1 and all(
                self % i for i in range(2, int(self.value**0.5) + 1)
            )
        except OverflowError:
            self.vars["prime"] = True

    def __repr__(self):
        return str(self)

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

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return str(self.value)

    def __abs__(self):
        return Number(abs(self.value))

    def __neg__(self):
        return Number(-self.value)

    def __pos__(self):
        return Number(+self.value)

    def __invert__(self):
        return ~int(self.value)

    def __truediv__(self, other):
        if isinstance(other, Number):
            return self.value / other.value
        else:
            return self.value / other

    def __floordiv__(self, other):
        if isinstance(other, Number):
            return self.value // other.value
        else:
            return self.value // other

    def __mod__(self, other):
        if isinstance(other, Number):
            return self.value % other.value
        else:
            return self.value % other

    def __pow__(self, other, modulo=None):
        if isinstance(other, Number):
            return pow(self.value, other.value, modulo)
        else:
            return pow(self.value, other, modulo)

    def __eq__(self, other):
        if isinstance(other, Number):
            return self.value == other.value
        else:
            return self.value == other

    def __lt__(self, other):
        if isinstance(other, Number):
            return self.value < other.value
        else:
            return self.value < other

    def __le__(self, other):
        if isinstance(other, Number):
            return self.value <= other.value
        else:
            return self.value <= other

    def __gt__(self, other):
        if isinstance(other, Number):
            return self.value > other.value
        else:
            return self.value > other

    def __ge__(self, other):
        if isinstance(other, Number):
            return self.value >= other.value
        else:
            return self.value >= other

    def __invert__(self):
        return Number(~int(self.value))

    def __add__(self, other):
        return Number(
            self.value + other.value
            if isinstance(other, Number)
            else self.value + other
        )

    def __radd__(self, other):
        return Number(other + self.value)

    def __sub__(self, other):
        return Number(
            self.value - other.value
            if isinstance(other, Number)
            else self.value - other
        )

    def __rsub__(self, other):
        return Number(other - self.value)

    def __mul__(self, other):
        return (
            Number(self.value * other.value)
            if isinstance(other, Number)
            else self.value * other
        )

    def __rmul__(self, other):
        return (
            Number(self.value * other.value)
            if isinstance(other, Number)
            else self.value * other
        )

    # Implement other arithmetic and bitwise operations similarly

    def __iadd__(self, other):
        self.value += other.value if isinstance(other, Number) else other
        return self

    def __isub__(self, other):
        self.value -= other.value if isinstance(other, Number) else other
        return self

    def __imul__(self, other):
        self.value *= other.value if isinstance(other, Number) else other
        return self

    def __hash__(self):
        return hash(self.value)

    def __round__(self):
        return round(self.value)

    def __bool__(self):
        return bool(self.value)


class Boolean(int, Type):
    def __init__(self, value):
        value = bool(value)
        if value != 0:
            value = 1
        self.vars = {
            # methods and attributes here
        }
        int.__init__(self)

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
    def __init__(self, funct, is_macro=False):
        self.vars = {}  # Functions have no default attributes.
        self.funct = funct
        # print("Is Macro: " + str(is_macro))
        self.is_macro = is_macro
        self._locals = {}  # TODO
        Type.__init__(self)

    def __call__(self, *args, **kwargs):
        return pyToAdk(self.funct(*args, **kwargs))


class Array(Type, list):
    def __init__(self, value):
        value = list(value)
        list.__init__(self)
        self.value = []
        for i in value:
            i = pyToAdk(i)
            self.append(i)
            self.value.append(i)
        self.vars = {
            "contains": lambda x: x in self,
            "add": self._append,
            "remove": self._remove,
            "length": len(self),
            "reverse": self._reverse,
            "backwards": self._backwards,
            "filter": self._filter,
            "map": lambda func: Array([func(i) for i in self]),
            "reduce": self._reduce,
            "slice": lambda start, end, step=1: Array(self.value[start:end:step]),
            "sort": self._sort,
            "copy": lambda: Array(self.value.copy()),
            # methods and attributes here
        }

    def __sub__(self, other):
        self._remove(other)

    def __str__(self):
        return (
            "["
            + ", ".join(
                [str(val) if type(val) != str else f'"{val}"' for val in self.value]
            )
            + "]"
        )

    def __repr__(self):
        return str(self)

    def _filter(self, key):
        new = []
        for i in self.value:
            if key(i):
                new.append(i)
        return new

    def _reverse(self):
        self.reverse()
        self.value.reverse()

    def _backwards(self):
        return reversed(self.value)

    def _sort(self, key=lambda x, y: x - y, reverse=False):
        self.sort(key=cmp_to_key(key), reverse=reverse)
        self.value.sort(key=cmp_to_key(key), reverse=reverse)

    def _reduce(self, func, start=0):
        for i in self.value:
            start = func(start, i)
        return start

    def _append(self, *args, **kwargs):
        self.append(*args, **kwargs)
        self.value.append(*args, **kwargs)
        self.vars["length"] = len(self)

    def _remove(self, *args, **kwargs):
        self.remove(*args, **kwargs)
        self.value.remove(*args, **kwargs)
        self.vars["length"] = len(self)

    def __setitem__(self, name, value):
        if type(name) in [Number, int] or (
            type(name) in [str, String] and name.isdigit()
        ):
            index = int(name)
            if index >= len(self.value):
                return None
            self.value[int(name)] = value
            return value
        return self.set(name, value)

    def get(self, name, default=None):
        if type(name) in [Number, int] or (
            type(name) in [str, String] and name.isdigit()
        ):
            index = int(name)
            if index >= len(self.value):
                return default
            return self.value[index]
        return self.vars.get(name, default)

    def __getitem__(self, name):
        return self.get(name, Null)


class Set(Type, list):
    def __init__(self, value):
        value = list(value)
        list.__init__(self)
        self.value = []
        for i in value:
            i = pyToAdk(i)
            if i not in self:
                self.append(i)
                self.value.append(i)
        self.vars = {
            "contains": lambda x: x in self,
            "add": self._append,
            "remove": self._remove,
            "length": len(self),
            "reverse": self._reverse,
            "filter": self._filter,
            "slice": lambda start, end, step=1: Set(self.value[start:end:step]),
            # methods and attributes here
        }

    def __sub__(self, other):
        self._remove(other)
        # TODO: make this work.
        return self

    def _filter(self, key):
        new = []
        for i in self.value:
            if key(i):
                new.append(i)
        return new

    def _reverse(self):
        self.reverse()
        self.value.reverse()

    def __getitem__(self, *args, **kwargs):
        return self.value.__getitem__(*args, **kwargs)

    def _append(self, *args, **kwargs):
        if args[0] not in self:
            self.append(*args, **kwargs)
            self.value.append(*args, **kwargs)
        self.vars["length"] = len(self)

    def _remove(self, *args, **kwargs):
        self.remove(*args, **kwargs)
        self.value.remove(*args, **kwargs)
        self.vars["length"] = len(self)

    def __repr__(self):
        s = ""
        for i in self:
            s += str(i) + ", "
        s = s[:-2]
        return f"set{{{s}}}"

    def __str__(self):
        s = ""
        for i in self:
            s += str(i) + ", "
        s = s[:-2]
        return f"set{{{s}}}"


class File(Type):
    def __init__(self, obj):
        if obj == None:
            obj = open(os.devnull, "w+")
        self.name = obj.name
        self.mode = obj.mode
        self.obj = obj
        self.vars = {
            "read": self.read,
            "write": self.write,
            "readAll": self.readAll,
            "readLine": self.readLine,
            "readLines": self.readLines,
            "writeLines": self.writeLines,
            "log": self.log,
            "erase": self.erase,
            "move": self.move,
            "delete": self.delete,
            "name": self.name,
            "mode": self.mode,
            "flush": self.obj.flush,
        }
        if self.obj == sys.stdin:
            self.vars["prompt"] = input

    def read(self, chars=1):
        return self.obj.read(chars)

    def readLine(self):
        return self.obj.readline()

    def readLines(self, n=-1):
        return self.obj.readlines(n)

    def readAll(self):
        return self.obj.read()

    def log(self, *args, flush="auto", sep=" "):
        ret = self.obj.write(sep.join([str(a) for a in args]) + "\n")
        if flush == "instant":
            self.obj.flush()
        return ret

    def write(self, *args, flush="auto"):
        ret = self.obj.write("".join([str(a) for a in args]))
        if flush == "instant":
            self.obj.flush()
        return ret

    def writeLines(self, *lines):
        return self.obj.write("\n".join([str(line) for line in lines]))

    def delete(self):
        os.remove(self.name)

    def erase(self):
        open(self.name, "w").close()

    def move(self, new):
        os.rename(self.name, new)


class Class(Type):
    def __init__(self, name, build, extends=[], AS=None, parent=None):
        self.name = name
        self.build = build  # A function the class with,
        self.parent = parent
        self._as = AS
        self.vars = {}
        self.getters = {}
        self.setters = {}
        self.extends = extends
        # Just to make it act like a scope
        self._returned_value = Null
        self._has_returned = False
        self._has_been_broken = False
        self._has_been_continued = False
        self._completed = False
        self._is_function_scope = False
        self.returnActions = []
        self.addReturnAction = lambda x: None
        self.set_return_value = lambda x: False
        self._scope_type = "Class"
        if self._as:
            self.vars[self._as] = self
        build(self)

    def define_getter(self, name, getter):
        self.getters[name] = getter

    def define_setter(self, name, setter):
        self.setters[name] = setter

    def childstr(self):
        return f"<instance of {self.name}>"

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"<Class {self.name}>"

    def __call__(self, *args, **kwargs):
        obj = Object({}, _class=self)

        for extends in self.extends:
            extends.build(obj)

        if self._as:
            obj.vars[self._as] = obj
        # obj.parent = self.parent
        scope = Scope({}, self.parent)
        if self._as:
            scope[self._as] = scope
        self.build(scope)
        obj.vars = scope.vars
        for name, getter in self.getters.items():
            obj.define_getter(name, getter)
        for name, setter in self.setters.items():
            obj.define_setter(name, setter)
        obj._call = obj.vars.get("$call")
        obj._setitem = obj.vars.get("$setitem")
        obj._getitem = obj.vars.get("$getitem")
        obj._deleteitem = obj.vars.get("$deleteitem")
        obj._delete = obj.vars.get("$delete")
        obj._string = obj.vars.get("$string")
        init = obj.vars.get("$constructor")
        if init:
            init(*args, **kwargs)
        return obj

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


class Error(Type):
    def __init__(self, t="?", msg="Error"):
        self.type = t
        self.message = msg
        self.vars = {"type": t, "message": msg}

    def __repr(self):
        return str(self)

    def __str__(self):
        return f"<{self.type}Error>"


# TODO: Add: Stream, Bitarray
Null = _Null()

Types = [
    Object,
    Scope,
    Type,
    _Null,
    Number,
    String,
    Function,
    Boolean,
    Set,
    Array,
    File,
    Class,
    Error,
    _Undefined,
]


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
        if type(py) == type:
            return py
        elif py == None:
            return Null
        elif isinstance(py, bool):
            return Boolean(py)
        elif isinstance(py, int) or isinstance(py, float):
            return Number(py)
        elif isinstance(py, str):
            return String(py)
        elif isinstance(py, tuple):
            return Array(list(py))
        elif isinstance(py, list):
            return Array(py)
        elif isinstance(py, set):
            return Set(py)
        elif isinstance(py, dict):
            return Object(py)
        elif isinstance(py, type):
            return Function(py)
        elif isinstance(py, types.ModuleType):
            return Object(dict_from_other(py))
        elif (
            isinstance(py, io.TextIOBase)
            or isinstance(py, io.BufferedIOBase)
            or isinstance(py, io.RawIOBase)
            or isinstance(py, io.IOBase)
            or isinstance(py, io.TextIOWrapper)
        ):
            return File(py)
        elif inspect.isclass(py):
            return Object(dict_from_other(py), call=py)
        elif inspect.isfunction(py):
            return Function(py)
        elif callable(py):
            return Object(dict_from_other(py), call=py)
        else:
            return Object(dict_from_other(py))
    except RecursionError:
        return py


def adkToPy(adk):
    if type(adk) not in Types:
        return adk
    elif adk == Null:
        return None
    elif isinstance(adk, Object):
        return adk.vars
    elif isinstance(adk, Array):
        return adk.value
    # TODO: finish later

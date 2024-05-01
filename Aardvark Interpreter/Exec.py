import Error
import Lexer
import Parser
import sys
from Operators import Operators
import random
import math
from nlp import edit_distance
import Types
from Types import (
    Null,
    Object,
    Scope,
    Number,
    String,
    Boolean,
    pyToAdk,
    Function,
    Set,
    Array,
    File,
    Class,
    _Undefined,
    adkToPy,
)
import importlib
import time
import copy
from jsonrender import render

try:
    from bitarray import bitarray
except ImportError:
    bitarray = None
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Error import ErrorHandler

from pathlib import Path
from Utils import prettify_ast
import os


class AardvarkArgumentError(ValueError):
    def __init__(self, message, *args) -> None:
        super().__init__(message, *args)
        self.message = message


current_dir = os.getcwd()
searchDirs = [Path(__file__).parent / "../lib"]
if os.environ.get("AARDVARK_INSTALL", False):
    searchDirs.append(Path(os.environ["AARDVARK_INSTALL"] + "/lib/"))
for i in range(len(searchDirs)):
    searchDirs[i] = searchDirs[i].resolve()
adk_overloaded_classes = {}


def mergeObjects(*args):
    vars = args[0].vars.copy()
    for arg in args[1:]:
        vars.update(arg.vars.copy())
    return Object(vars)


def LinkFunct(start, link="next", reverse=False):
    curr = start
    l = []
    while True:
        l.append(curr)
        if callable(link):
            curr = link(curr)
        else:
            curr = curr[link]
        if not curr:
            break
    if reverse:
        l = list(reversed(l))
    return l


def get_call_scope(scope: Scope):
    call_scope = ["scope " + str(id(scope))]
    if scope.parent:
        call_scope += get_call_scope(scope.parent)

    return call_scope


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def dsigmoid(x):
    return sigmoid(x) * (1 - sigmoid(x))


def createGlobals(safe=False):
    Globals = Scope(
        {
            "stdout": File(sys.stdout),
            "stdin": File(sys.stdin),
            "stderr": File(sys.stderr),
            "slice": lambda str, start=0, end=0: str[start:end],
            "prettify": prettify_ast,
            "range": lambda *args: list(range(*args)),
            "typeof": lambda obj: (
                obj._class
                if type(obj) == Object and getattr(obj, "_class", False)
                else type(obj)
            ),
            "type_of": lambda obj: (
                obj._class
                if type(obj) == Object and getattr(obj, "_class", False)
                else type(obj)
            ),
            "keys": lambda x: list(x.getAll().keys()),
            "dir": lambda x=None: x.getAll() if x else Globals.vars,
            "sort": lambda iterable, reverse=False, key=(lambda x: x): sorted(
                iterable, reverse=reverse, key=key
            ),
            "null": Null,
            "help": help,
            "sequence": lambda start=0, step=1, times=1: [
                (start + x * step) for x in range(times)
            ],
            "Math": Object(
                {
                    "max": max,
                    "min": min,
                    "pi": math.pi,
                    "π": math.pi,
                    "e": math.e,
                    "tau": math.tau,
                    "round": round,
                    "abs": abs,
                    "factorial": math.factorial,
                    "floor": math.floor,
                    "ceil": math.ceil,
                    "log": math.log,
                    "comb": math.comb,
                    "copysign": math.copysign,
                    "lcm": math.lcm,
                    "pow": math.pow,
                    "tanh": math.tanh,
                    "sigmoid": sigmoid,
                    "dsigmoid": dsigmoid,
                }
            ),
            "String": String,
            "Number": Number,
            "Array": Array,
            "Set": Set,
            "Function": Function,
            "Boolean": Boolean,
            "File": File,
            "Object": Object,
            "Error": Types.Error,
            "Bits": bitarray,
            "link": LinkFunct,
            "exit": sys.exit,
            "keys": lambda x: Array(x.vars.keys()),
            "values": lambda x: Array(x.values()),
            "mergeObjects": mergeObjects,
            "copy": copy.copy,
            "json_render": render,
            "Path": Path,
        }
    )  # Define builtins here
    if not safe:
        Globals.set(
            "python",
            {
                "import": lambda mod: importlib.import_module(mod),
                "eval": lambda code: eval(
                    code,
                    {
                        "importlib": importlib,
                        "math": math,
                        "random": random,
                        "sys": sys,
                        "os": os,
                        "time": time,
                    },
                ),
            },
        )
    return Globals


class Executor:
    def __init__(
        self,
        path: str,
        code: str,
        ast,
        errorhandler: "ErrorHandler",
        filestack={},
        is_main=False,
        safe=False,
        included_by=None,
        is_strict=False,
    ):
        self.lexer_time = 0
        self.parser_time = 0
        self.executor_time = 0
        self.path = Path(path)
        self.code = code
        self.codelines = code.split("\n")
        self.ast = ast
        self.traceback = []
        self.switch = None
        self.is_strict = is_strict
        self.filestack = filestack
        self.Global = createGlobals(safe)
        self.included_by = included_by
        self.safe = safe
        self.searchDirs = searchDirs
        self.searchDirs.insert(0, self.path.parent)
        if not safe:

            def adk_open(path, *args, **kwargs):
                # Make path relative to the file being executed.
                if not Path(str(path)).is_absolute():
                    path = os.path.join(str(self.path.parent), str(path))

                return open(path, *args, **kwargs)

            self.Global.set("open", adk_open)
        self.Global["include"] = self.include
        self.Global["is_main"] = is_main
        self.Global["current_file"] = self.path
        self.errorhandler = errorhandler
        self.filestack[str(self.path)] = self.Global

    def include(self, name):
        # Search all search directories
        with_ext = name + ".adk"
        file = None
        text = None
        for d in self.searchDirs:
            test_path = d / name
            if test_path.is_dir():
                test_path_main = test_path / "main.adk"
                if test_path_main.exists():
                    file = test_path / "main.adk"
                    break
                test_path_index = test_path / "index.adk"
                if test_path_index.exists():
                    file = test_path / "index.adk"
                    break
            elif test_path.exists():
                file = test_path
                break
            test_path_with_ext = d / with_ext
            if test_path_with_ext.exists():
                file = test_path_with_ext
                break
        else:
            raise ValueError(f"Could not find library or file {name}.")

        if file:
            file = file.resolve()

        if str(file) in self.filestack:
            return self.filestack[str(file)]

        text = file.read_text(encoding="utf-8")
        lexer_start = time.time()
        errorhandler = Error.ErrorHandler(text, file, py_error=True)
        lexer = Lexer.Lexer("#", "#*", "*#", True, False)
        toks = lexer.tokenize(text)
        lexer_end = time.time()
        self.lexer_time += lexer_end - lexer_start
        parser = Parser.Parser(errorhandler, lexer, self.is_strict)
        ast = parser.parse()
        parser_end = time.time()
        self.parser_time += parser_end - lexer_end
        executor = Executor(
            file,
            text,
            ast["body"],
            errorhandler,
            filestack=self.filestack,
            safe=self.safe,
            included_by=self,
            is_strict=self.is_strict,
        )
        executor.run()
        self.executor_time += executor.executor_time
        self.lexer_time += executor.lexer_time
        self.parser_time += executor.parser_time
        self.filestack[str(file)] = executor.Global
        return executor.Global

    def defineVar(self, name, value, scope, is_static=False, expr=None):
        if type(scope) == Types.Object and name in scope.setters:
            scope.setters[name](value)
        elif name in scope.getAll() and name not in list(scope.vars.keys()):
            self.defineVar(name, value, scope.parent)
        elif (
            name in list(scope.vars.keys())
            and getattr(scope[name], "is_static", False)
            and type(scope[name]) != _Undefined
        ):
            start = expr["positions"]["start"]
            self.errorhandler.throw(
                "Assignment",
                f"Cannot reassign a static variable: {name}.",
                {
                    "traceback": self.traceback,
                    "lineno": start["line"],
                    "marker": {"start": start["col"], "length": len(name)},
                    "underline": {
                        "start": start["col"] - 2,
                        "end": start["col"] + len(name),
                    },
                },
            )
        else:
            if getattr(scope[name], "is_static", None) == True:
                is_static = True
            scope[name] = pyToAdk(value)
            scope[name].is_static = is_static

    def makeFunct(self, expr, parent: Scope, is_macro=False):
        special = expr.get("special", False)
        name = "$" + expr["name"] if special else expr["name"]
        params = expr["parameters"]
        code = expr["body"]
        AS = expr.get("as", None)

        def x(*args, **kwargs):
            if is_macro:
                functscope = args[0]
                args = args[1:]
            else:
                functscope = Scope({}, parent=parent, scope_type="function")
                if AS:
                    functscope[AS] = x
            for i in range(len(params)):
                param = params[i]
                if i > len(args) - 1 and param["name"] in kwargs:
                    arg = kwargs[param["name"]]
                elif param["name"] in kwargs:
                    arg = kwargs[param["name"]]
                    raise AardvarkArgumentError(
                        "Cannot receive positional argument and keyword argument for the same parameter!!"
                    )
                elif i < len(args):
                    arg = args[i]
                    if param["absorb"]:
                        arg = args[i:]
                else:
                    arg = self.ExecExpr(param.get("default"), parent)
                # if param["value_type"] != None:
                #     notImplemented(self.errorhandler, "Type Checking", param)
                functscope.vars[param["name"]] = arg
                if self.is_strict or param.get("is_static", False):
                    setattr(functscope.vars[param["name"]], "is_static", True)
                    # functscope.vars[param["name"]].is_static = True
                else:
                    setattr(functscope.vars[param["name"]], "is_static", False)
                    # functscope.vars[param["name"]].is_static = False
            ret = self.Exec(code, functscope)
            if is_macro:
                return ret
            if not functscope._returned_value and expr.get("inline", False):
                functscope._returned_value = ret
            return functscope._returned_value

        funct_value = Function(x, is_macro)
        if name:
            parent.set(name, funct_value)
        return funct_value

    def getVar(
        self,
        scope: Scope,
        varname: str,
        start=None,
        error=True,
        message='Undefined variable "{name}".',
        just_a_check=False,
    ):
        val = scope.get(varname, None)
        success = val != None
        if type(val) == _Undefined and not just_a_check:
            if success and error:
                message = 'Uninitialized variable "{name}". Add `?` to render uninitialized variables as null.'
                line = self.codelines[start["line"] - 1]
                did_you_mean = (
                    line[: start["col"] + len(varname) - 1]
                    + "?"
                    + line[start["col"] + len(varname) - 1 :]
                )
                return self.errorhandler.throw(
                    "Value",
                    message.format(name=varname),
                    {
                        "lineno": start["line"],
                        "marker": {"start": start["col"], "length": len(varname)},
                        "underline": {
                            "start": start["col"] - 2,
                            "end": start["col"] + len(varname),
                        },
                        "did_you_mean": Error.Highlight(
                            did_you_mean, {"linenums": False}
                        ),
                        "traceback": self.traceback,
                    },
                )
            success = False
        if success:
            return pyToAdk(val)
        elif error:
            line = self.codelines[start["line"] - 1]
            did_you_mean = (
                line[: start["col"] - 1]
                + findClosest(varname, scope)
                + line[start["col"] + len(varname) - 1 :]
            )
            # Check if the message is a function or lambda:
            if callable(message):
                message = message()
            return self.errorhandler.throw(
                "Value",
                message.format(name=varname),
                {
                    "lineno": start["line"],
                    "marker": {"start": start["col"], "length": len(varname)},
                    "underline": {
                        "start": start["col"] - 2,
                        "end": start["col"] + len(varname),
                    },
                    "did_you_mean": Error.Highlight(did_you_mean, {"linenums": False}),
                    "traceback": self.traceback,
                },
            )
        return Null

    def enterScope(self, var, scope: Scope, main):
        if var["type"] == "PropertyAccess":
            property = self.ExecExpr(var["property"], main)
            scope = self.enterScope(var["value"], scope, main)
            return self.getVar(scope, property, var["positions"]["start"])
        elif var["type"] == "Index":
            property = self.ExecExpr(var["property"], main)
            scope = self.enterScope(var["value"], scope, main)
            return self.getVar(scope, property, var["positions"]["start"])
        else:
            return self.ExecExpr(var, main)

    def ExecFunctionCall(self, expr: dict, scope: Scope):
        funct = self.ExecExpr(expr["function"], scope)
        if not getattr(funct, "is_macro", False):
            self.traceback.append(
                {
                    "name": Error.getAstText(expr["function"], self.codelines) + "()",
                    "line": expr["positions"]["start"]["line"],
                    "col": expr["positions"]["start"]["col"],
                    "filename": self.path.name,
                }
            )
        args = []
        kwargs = {
            k: self.ExecExpr(v, scope)
            for k, v in list(expr["keywordArguments"].items())
        }
        for arg in expr["arguments"]:
            if arg.get("type") == "Operator" and arg.get("operator") == "...":
                arg = self.ExecExpr(arg["left"] if arg["left"] else arg["right"], scope)
                if type(arg) == Object:
                    kwargs.update(arg.vars)
                else:
                    args = [*args, *arg]
            else:
                args.append(self.ExecExpr(arg, scope))
        try:
            if type(funct) == Function and funct.is_macro:
                ret = funct(
                    scope,
                    *args,
                    **kwargs,
                )
            else:
                ret = funct(
                    *args,
                    **kwargs,
                )
        except AardvarkArgumentError as e:
            self.errorhandler.throw(
                "Argument",
                e.message,
                {
                    "traceback": self.traceback,
                    "lineno": expr["positions"]["start"]["line"],
                    "marker": {
                        "start": expr["positions"]["start"]["col"],
                        "length": expr["positions"]["end"]["col"]
                        - expr["positions"]["start"]["col"],
                    },
                    "underline": {
                        "start": expr["positions"]["start"]["col"],
                        "end": expr["positions"]["end"]["col"],
                    },
                },
            )
        self.traceback = self.traceback[:-1]
        return ret

    def ExecExpr(self, expr: dict, scope: Scope, undefinedError=True, reference=False):
        if expr == None:
            return Null
        elif expr["type"] == "NumberLiteral":
            return Number(expr["value"])
        elif expr["type"] == "StringLiteral":
            return String(expr["value"])
        elif expr["type"] == "BooleanLiteral":
            return Boolean(expr["value"])
        elif expr["type"] == "VariableAccess":
            return self.getVar(
                scope, expr["value"], expr["positions"]["start"], undefinedError
            )
        elif expr["type"] == "PropertyAccess":
            obj = pyToAdk(self.ExecExpr(expr["value"], scope, undefinedError))
            get_objname = lambda: (
                obj.name
                if "name" in dir(obj)
                else Error.getAstText(expr["value"], self.codelines)
            )
            property = self.ExecExpr(expr["property"], scope, undefinedError)
            return self.getVar(
                obj,
                property,
                expr["property"]["positions"]["start"],
                undefinedError,
                message=lambda: f'Undefined property "{{name}}" of "{get_objname()}"',
            )
        elif expr["type"] == "Object":
            obj = Object()
            for k, v in expr["pairs"].items():
                if k == ("...",) and v[0] == "...":
                    obj.vars.update(self.ExecExpr(v[1], scope).vars)
                else:
                    obj[k] = self.ExecExpr(v, scope)
            return obj
        elif expr["type"] == "Set":
            return Set({self.ExecExpr(item, scope) for item in expr["items"]})
        elif expr["type"] == "Array":
            items = []
            for item in expr["items"]:
                if item.get("type") == "Operator" and item.get("operator") == "...":
                    item = self.ExecExpr(
                        item["left"] if item["left"] else item["right"], scope
                    )
                    items = [*items, *item]
                else:
                    items.append(self.ExecExpr(item, scope))
            return Array(items)
        elif expr["type"] == "DeleteStatement":
            self.getVar(
                scope, expr["target"]["value"], expr["target"]["positions"]["start"]
            )
            del scope[expr["name"]]
        elif expr["type"] == "FunctionCall":
            return self.ExecFunctionCall(expr, scope)
        elif expr["type"] == "Operator" and expr["operator"] == "?":
            left = self.ExecExpr(expr["left"], scope, False)
            if left == Null:
                return self.ExecExpr(expr["right"], scope) if expr["right"] else Null
            else:
                return left
            # return Operators["?"](
            #     left,
            #     right,
            #     self.errorhandler,
            #     self.codelines[expr["positions"]["start"]["line"] - 1],
            #     expr,
            #     scope,
            #     self,
            # )
        elif expr["type"] == "Operator":
            operator = expr["operator"]
            if operator in Operators:
                op = Operators[operator]
                if operator in [
                    "=",
                    "+=",
                    "-=",
                    "*=",
                    "/=",
                    "^=",
                    "%=",
                    "++",
                    "--",
                    "|",
                    "&",
                    "or",
                    "and",
                    "@",
                ]:
                    left = expr["left"]
                    right = expr["right"]
                else:
                    left = self.ExecExpr(expr["left"], scope)
                    right = self.ExecExpr(expr["right"], scope)

                if isinstance(left, Types.Object) and left._class:
                    if overloads := adk_overloaded_classes.get(id(left._class)):
                        if operator in overloads:
                            return overloads[operator](left, right)

                try:
                    return pyToAdk(
                        op(
                            left,
                            right,
                            self.errorhandler,
                            self.codelines[expr["positions"]["start"]["line"] - 1],
                            expr,
                            scope,
                            self,
                        )
                    )
                except TypeError as e:
                    self.errorhandler.throw(
                        "Value",
                        e.args[0],
                        {
                            "lineno": expr["positions"]["start"]["line"],
                            "underline": {
                                "start": expr["positions"]["start"]["col"],
                                "end": expr["positions"]["end"]["col"],
                            },
                            "marker": {
                                "start": expr["positions"]["start"]["col"],
                                "length": expr["positions"]["end"]["col"]
                                - expr["positions"]["start"]["col"],
                            },
                            "traceback": self.traceback,
                        },
                    )
            else:
                return notImplemented(
                    self.errorhandler,
                    f'Operator "{expr["operator"]}" not yet implemented.',
                    expr,
                )
        elif expr["type"] == "IfStatement":
            ifscope = Scope({}, parent=scope, scope_type="conditional")
            if bool(self.ExecExpr(expr["condition"], scope)):
                return self.Exec(expr["body"], ifscope)
            elif expr["else_body"]:
                return self.Exec(expr["else_body"], ifscope)
        elif expr["type"] == "WhileLoop":
            ret = []
            while bool(self.ExecExpr(expr["condition"], scope)):
                whilescope = Scope({}, parent=scope, scope_type="loop")
                ret.append(self.Exec(expr["body"], whilescope))
                if whilescope._completed and not whilescope._has_been_continued:
                    break
            return ret
        elif expr["type"] == "ForLoop":
            iterable = self.ExecExpr(expr["iterable"], scope)
            ret = []
            for item in iterable:
                forscope = Scope({}, parent=scope, scope_type="loop")
                decls = expr["declarations"]
                if len(decls) == 1:
                    d = decls[0]
                    if d["type"] == "variable":
                        self.defineVar(d["names"][0], item, forscope)
                    elif d["type"] == "destructure":
                        self.defineVar(d["names"][0], item, forscope)
                        self.defineVar(d["names"][1], iterable[item], forscope)
                else:
                    item = iter(item)
                    for d in decls:
                        if d["type"] == "variable":
                            self.defineVar(d["names"][0], next(item), forscope)
                        elif d["type"] == "destructure":
                            i = next(item)
                            self.defineVar(d["names"][0], i, forscope)
                            self.defineVar(d["names"][1], iterable[i], forscope)

                ret.append(self.Exec(expr["body"], forscope))
                if forscope._completed and not forscope._has_been_continued:
                    break
            return ret
        elif expr["type"] == "SPMObject":
            c = expr["pairs"]
            define = {}
            compare = {}
            for k in c:
                v = c[k]
                if v[0] == "Define":
                    define[v[1]] = (k,)
                if v[0] == "Compare":
                    compare[k] = self.ExecExpr(v[1], scope)
            return compare, define
        elif expr["type"] == "CaseStatement":
            casescope = Scope({}, parent=scope)
            if expr["special"]:
                self.defineVar(expr["special"], self.switch, casescope)
                scope._has_been_broken = True
                return self.Exec(expr["body"], casescope)
            elif expr["compare"]["type"] == "SPMObject":
                compare, define = self.ExecExpr(expr["compare"], scope)
                for c in compare:
                    if self.switch[c] != compare[c]:
                        return
                for d in define:
                    value = self.switch
                    # TODO: fix: nested switch does not work.
                    for i in define[d]:
                        value = value[i]
                    self.defineVar(d, value, casescope)
                scope._has_been_broken = True
                return self.Exec(expr["body"], casescope)
            else:
                compare = self.ExecExpr(expr["compare"], scope)
                if self.switch == compare:
                    scope._has_been_broken = True
                    return self.Exec(expr["body"], casescope)
        elif expr["type"] == "Assignments":
            for assignment in expr["assignments"]:
                value = (
                    self.ExecExpr(assignment["value"], scope)
                    if assignment["value"]
                    else _Undefined()
                )
                self.defineVar(
                    assignment["var_name"],
                    value,
                    scope,
                    assignment["is_static"],
                    expr,
                )
            return value
        elif expr["type"] == "SwitchStatement":
            switchscope = Scope({}, parent=scope, scope_type="match")
            self.switch = self.ExecExpr(expr["value"], scope)
            self.Exec(expr["body"], switchscope)
            if getattr(self, "switch", False):
                del self.switch
        elif expr["type"] == "FunctionDefinition":
            funct = self.makeFunct(expr, scope)
            return funct
        elif expr["type"] == "MacroDefinition":
            funct = self.makeFunct(expr, scope, is_macro=True)
            return funct
        elif expr["type"] == "ClassDefinition":
            classcope = Class(
                expr["name"],
                lambda s: self.Exec(expr["body"], s),
                [self.getVar(scope, e.value, e.start) for e in expr["extends"]],
                expr["as"],
                scope,
            )
            if expr["name"]:
                self.defineVar(expr["name"], classcope, scope)
            return classcope
        elif expr["type"] == "GetterSetterDefinition" and expr["kind"] == "getter":
            prop_name = expr["function"]["name"]
            expr["function"]["name"] = None
            expr["function"]["special"] = False

            scope.define_getter(prop_name, self.makeFunct(expr["function"], scope))
        elif expr["type"] == "GetterSetterDefinition" and expr["kind"] == "setter":
            prop_name = expr["function"]["name"]
            expr["function"]["name"] = None
            expr["function"]["special"] = False

            scope.define_setter(prop_name, self.makeFunct(expr["function"], scope))
        elif expr["type"] == "DeferStatement":
            scope.addReturnAction(lambda: self.ExecExpr(expr["value"], scope))
        elif expr["type"] == "ReturnStatement":
            val = self.ExecExpr(expr["value"], scope)
            success = scope.complete("function", val)
            if scope == self.Global or not success:
                self.Global._triggerReturnAction()
                if val == Null:
                    val = 0
                sys.exit(int(val))
            return scope._returned_value
        elif expr["type"] == "Multiply":
            # for (num)x mult
            return self.ExecExpr(expr["number"], scope) * self.getVar(
                scope, expr["variable"], expr["tokens"]["variable"].start
            )
        elif expr["type"] == "Index":
            try:
                return self.ExecExpr(expr["value"], scope)[
                    self.ExecExpr(expr["property"], scope)
                ]
            except IndexError:
                if undefinedError:
                    self.errorhandler.throw(
                        "Index",
                        "No such index.",
                        {
                            "lineno": expr["positions"]["start"]["line"],
                            "underline": {
                                "start": expr["positions"]["start"]["col"],
                                "end": expr["positions"]["end"]["col"],
                            },
                            "marker": {
                                "start": expr["property"]["positions"]["start"]["col"],
                                "length": expr["property"]["positions"]["end"]["col"]
                                - expr["property"]["positions"]["start"]["col"]
                                + 1,
                            },
                            "traceback": self.traceback,
                        },
                    )
                else:
                    return None
        elif expr["type"] == "IncludeStatement":
            file = expr["lib_name"]
            try:
                fscope = self.include(file)
            except ValueError:
                self.errorhandler.throw(
                    "Include",
                    f'Could not find library or file {expr["lib_name"]}.',
                    {
                        "lineno": expr["positions"]["start"]["line"],
                        "underline": {
                            "start": expr["positions"]["start"]["col"],
                            "end": expr["positions"]["end"]["line"],
                        },
                        "marker": {
                            "start": expr["tokens"]["lib_name"].start["col"],
                            "length": len(expr["lib_name"]),
                        },
                        "traceback": self.traceback,
                    },
                )
            if expr["included"] == "ALL":
                name = Path(expr["local_name"]).name.split(".")[0]
                self.defineVar(name, fscope, scope)
            else:
                for k, v in expr["included"].items():
                    self.defineVar(v["local"], fscope[k], scope)
        elif expr["type"] == "ThrowStatement":
            tothrow = self.ExecExpr(expr["tothrow"], scope)
            if type(tothrow) != Types.Error:
                self.errorhandler.throw(
                    "Error",
                    f'Can only throw Errors, not "{type(tothrow).__name__}"!',
                    {
                        "lineno": expr["tothrow"]["positions"]["start"]["line"],
                        "underline": {
                            "start": expr["tothrow"]["positions"]["start"]["col"],
                            "end": expr["tothrow"]["positions"]["end"]["col"],
                        },
                        "marker": {
                            "start": expr["tothrow"]["positions"]["start"]["col"],
                            "length": expr["tothrow"]["positions"]["end"]["col"]
                            - expr["tothrow"]["positions"]["start"]["col"]
                            + 1,
                        },
                        "traceback": self.traceback,
                    },
                )
            self.errorhandler.throw(
                tothrow.type,
                tothrow.message,
                {
                    "lineno": expr["positions"]["start"]["line"],
                    "underline": {
                        "start": expr["positions"]["start"]["col"],
                        "end": expr["positions"]["end"]["col"],
                    },
                    "marker": {
                        "start": expr["positions"]["start"]["col"],
                        "length": expr["positions"]["end"]["col"]
                        - expr["positions"]["start"]["col"]
                        + 1,
                    },
                    "traceback": self.traceback,
                },
            )
        elif expr["type"] == "TryCatch":
            stderr = sys.stderr
            sys.stderr = open(os.devnull, "w+")
            tryscope = Scope({}, parent=scope)
            try:
                self.Exec(expr["body"], tryscope)
            except Exception as e:
                sys.stderr = stderr
                if expr["catchbody"]:
                    notes = e.args
                    error = Types.Error(notes[1], notes[2])
                    catchscope = Scope({}, parent=scope)
                    if expr["catchvar"]:
                        catchscope[expr["catchvar"]] = error
                    self.Exec(expr["catchbody"], catchscope)
            sys.stderr = stderr
        elif expr["type"] == "ExtendingStatement" and expr["kind"] == "operator":
            ext_type, ext_name = expr["params"][0]
            other_name = expr["params"][1][1]

            to_overload = self.getVar(
                scope,
                ext_type.value,
                message=f"Cannot overload undeclared type '{ext_type.value}'",
            )

            if not isinstance(to_overload, Types.Class):
                self.errorhandler.throw(
                    "Exec",
                    "Cannot overload non-class types",
                    {
                        "lineno": expr["positions"]["start"]["line"],
                        "underline": {
                            "start": expr["positions"]["start"]["col"],
                            "end": expr["positions"]["end"]["col"],
                        },
                        "marker": {
                            "start": expr["positions"]["start"]["col"],
                            "length": expr["positions"]["end"]["col"]
                            - expr["positions"]["start"]["col"]
                            + 1,
                        },
                        "traceback": self.traceback,
                    },
                )

            def execute_inner(param1, param2):
                exec_scope = Scope({}, parent=scope, scope_type="function")
                exec_scope.set(ext_name.value, param1)
                exec_scope.set(other_name.value, param2)

                ret = self.Exec(expr["body"], exec_scope)

                if not exec_scope._returned_value:
                    exec_scope._returned_value = ret

                return exec_scope._returned_value

            adk_overloaded_classes[id(to_overload)] = adk_overloaded_classes.get(
                id(to_overload), {}
            )
            adk_overloaded_classes[id(to_overload)][expr["operator"]] = execute_inner
        elif expr["type"] == "BreakStatement":
            success = scope.complete("loop")
            if not success:
                self.errorhandler.throw(
                    "BreakOutside",
                    "Keyword 'break' can only be used inside loops",
                    {
                        "lineno": expr["positions"]["start"]["line"],
                        "underline": {
                            "start": expr["positions"]["start"]["col"],
                            "end": expr["positions"]["end"]["col"],
                        },
                        "marker": {
                            "start": expr["positions"]["start"]["col"],
                            "length": expr["positions"]["end"]["col"]
                            - expr["positions"]["start"]["col"],
                        },
                        "traceback": self.traceback,
                    },
                )
        elif expr["type"] == "ContinueStatement":

            def x(s):
                s._has_been_continued = True

            success = scope.complete("loop", action=x)
            if not success:
                self.errorhandler.throw(
                    "ContinueOutside",
                    "Keyword 'continue' can only be used inside loops",
                    {
                        "lineno": expr["positions"]["start"]["line"],
                        "underline": {
                            "start": expr["positions"]["start"]["col"],
                            "end": expr["positions"]["end"]["col"],
                        },
                        "marker": {
                            "start": expr["positions"]["start"]["col"],
                            "length": expr["positions"]["end"]["col"]
                            - expr["positions"]["start"]["col"],
                        },
                        "traceback": self.traceback,
                    },
                )
        elif expr["type"] == "TemplateString":
            string = expr["value"]
            replacements = reversed(expr["replacements"])
            for rep in replacements:
                value = rep["value"]
                codelines = rep["string"].split("\n")
                self.traceback.append(
                    {
                        "name": Error.getAstText(value, codelines),
                        "line": value["positions"]["start"]["line"],
                        "col": value["positions"]["start"]["col"],
                        "filename": self.path,
                    }
                )
                value = self.ExecExpr(value, scope)
                string = string[: rep["from"]] + str(value) + string[rep["to"] + 1 :]
            return String(string)
        else:
            if expr == Null:
                return Null
            notImplemented(self.errorhandler, expr["type"], expr)

    def Exec(self, ast, scope: Scope):
        if (
            scope._has_returned
            or scope._has_been_broken
            or scope._has_been_continued
            or scope._completed
        ):
            return Null
        ret_val = Null
        if type(ast).__name__ != "list":
            ast = [ast]
        for item in ast:
            ret_val = self.ExecExpr(item, scope)

            if (
                scope._has_returned
                or scope._has_been_broken
                or scope._has_been_continued
                or scope._completed
            ):
                break
        return pyToAdk(ret_val)

    def run(self):
        return self.Exec(self.ast, self.Global)


def notImplemented(errorhandler: "ErrorHandler", item, expr):
    start = expr["positions"]["start"]
    end = expr["positions"]["end"]
    errorhandler.throw(
        "NotImplemented",
        f"{item} is not yet implemented.",
        {
            "lineno": start["line"],
            "underline": {"start": 0, "end": end["col"]},
            "marker": {
                "start": start["col"] - 1,
                "length": end["col"] - start["col"] + 1,
            },
        },
    )


def findClosest(var: str, scope: Scope):
    var = str(var)
    lowest = 9999999999999999
    ret = "<identifier>"
    for item in list(scope.getAll().keys()):
        item = str(item)
        dist = edit_distance(var, item)
        if dist < lowest:
            ret = item
            lowest = dist
    return ret

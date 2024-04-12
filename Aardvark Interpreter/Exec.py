import Error
import Lexer
import Parser
import sys
import inspect
from Data import OrderOfOps
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
)
import importlib
from bitarray import bitarray


# from bitarray import bitarray
from pathlib import Path
from Utils import prettify_ast
import os


class AardvarkArgumentError(ValueError):
    def __init__(self, message, *args) -> None:
        super().__init__(message, *args)
        self.message = message


searchDirs = [
    os.environ["AARDVARK_INSTALL"] + "/lib/",
    "../lib/",
    "/home/runner/Aardvark/lib/",
    "/home/runner/Aardvark-py/lib/",
    "/home/runner/Aardvark-py-API/lib/",
]

current_dir = os.getcwd()


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


def get_call_scope(scope):
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
                obj._class.name
                if type(obj) == Object and getattr(obj, "_class", False)
                else type(obj).__name__
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
                    },
                ),
            },
        )
    return Globals


class Executor:
    def __init__(
        self,
        path,
        code,
        ast,
        errorhandler,
        filestack={},
        is_main=False,
        safe=False,
        included_by=None,
    ):
        self.path = Path(path)
        self.code = code
        self.codelines = code.split("\n")
        self.ast = ast
        self.traceback = []
        self.switch = None
        self.filestack = filestack
        self.Global = createGlobals(safe)
        self.included_by = included_by
        self.safe = safe
        if not safe:

            def adk_open(path, *args, **kwargs):
                # Make path relative to the file being executed.
                if not Path(path).is_absolute():
                    path = Path(Path(self.path).parent, path)

                return open(path, *args, **kwargs)

            self.Global.set("open", adk_open)
        self.Global["include"] = self.include
        self.Global["is_main"] = is_main
        self.errorhandler = errorhandler
        self.filestack[str(self.path)] = self.Global

    def include(self, name):
        locs = []
        path = Path(Path(self.path).parent, name).resolve()
        locs.append(str(path))
        locs.append(str(path) + ".adk")
        # allow importing folders that contain an main.adk
        locs.append(os.path.join(str(path), "index.adk"))
        locs.append(os.path.join(str(path), "main.adk"))

        if "/" not in name and "\\" not in name:
            for dir in searchDirs:
                locs.append(os.path.join(current_dir, dir, name))
                locs.append(os.path.join(current_dir, dir, name) + ".adk")
                locs.append(dir + name)
                locs.append(dir + name + ".adk")
        i = 0
        text = None
        while True:
            file = Path(locs[i])
            if file.is_dir():
                file = file.joinpath(file.name + ".adk")
            if file.exists():
                text = file.read_text(encoding="utf-8")
                break
            if i > len(locs) - 2:
                raise ValueError(f"Could not find library or file {name}.")
            i += 1
        file.resolve()
        # print(f"{self.path.name} included {file.name}")
        if str(file) in self.filestack:
            return self.filestack[str(file)]
        errorhandler = Error.ErrorHandler(text, file, py_error=True)
        lexer = Lexer.Lexer("#", "#*", "*#", errorhandler, False)
        toks = lexer.tokenize(text)
        parser = Parser.Parser(errorhandler, lexer)
        ast = parser.parse()
        executor = Executor(
            file,
            text,
            ast["body"],
            errorhandler,
            filestack=self.filestack,
            safe=self.safe,
            included_by=self,
        )
        executor.run()
        self.filestack[str(file)] = executor.Global
        # if file.name.split(".")[0] == "SyntaxHighlighter":
        #     if self.filestack[str(file)]["Highlight"] == None:
        #         print(self.included_by)
        return executor.Global

    def defineVar(self, name, value, scope, is_static=False, expr=None):
        if name in scope.getAll() and name not in list(scope.vars.keys()):
            self.defineVar(name, value, scope.parent)
        elif (
            name in list(scope.vars.keys())
            and getattr(scope[name], "is_static", False)
            and type(scope[name]) != _Undefined
        ):
            start = expr["positions"]["start"]
            self.errorhandler.throw(
                "Assignment",
                "Cannot reassign a static variable.",
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

    def makeFunct(self, expr, parent):
        special = expr["special"]
        name = "$" + expr["name"] if special else expr["name"]
        params = expr["parameters"]
        code = expr["body"]
        AS = expr["as"]

        def x(*args, **kwargs):
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
                functscope.vars[param["name"]].is_static = False  # Should this be True?
            ret = self.Exec(code, functscope)
            if not functscope._returned_value and expr["inline"]:
                functscope._returned_value = ret
            return functscope._returned_value

        if name:
            parent.set(name, Function(x))
        return Function(x)

    def getVar(
        self,
        scope,
        varname,
        start=None,
        error=True,
        message='Undefined variable "{name}".',
    ):
        val = scope.get(varname, None)
        success = val != None
        if type(val) == _Undefined:
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

    def enterScope(self, var, scope, main):
        match var:
            case {"type": "PropertyAccess"}:
                property = self.ExecExpr(var["property"], main)
                scope = self.enterScope(var["value"], scope, main)
                return self.getVar(scope, property, var["positions"]["start"])
            case {"type": "Index"}:
                property = self.ExecExpr(var["property"], main)
                scope = self.enterScope(var["value"], scope, main)
                return self.getVar(scope, property, var["positions"]["start"])
            case _:
                return self.ExecExpr(var, main)

    def ExecExpr(self, expr: dict, scope: Scope, undefinedError=True):
        match expr:
            case {"type": "NumberLiteral"}:
                return Number(expr["value"])
            case {"type": "StringLiteral"}:
                return String(expr["value"])
            case {"type": "BooleanLiteral"}:
                return Boolean(expr["value"])
            case {"type": "VariableAccess"}:
                return self.getVar(
                    scope, expr["value"], expr["positions"]["start"], undefinedError
                )
            case {"type": "PropertyAccess"}:
                obj = pyToAdk(self.ExecExpr(expr["value"], scope, undefinedError))
                objname = (
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
                    message=f'Undefined property "{{name}}" of "{objname}"',
                )
            case {"type": "Object"}:
                obj = Object()
                for k, v in expr["pairs"].items():
                    if k == ("...",) and v[0] == "...":
                        obj.vars.update(self.ExecExpr(v[1], scope).vars)
                    else:
                        obj[k] = self.ExecExpr(v, scope)
                return obj
            case {"type": "Set"}:
                return Set({self.ExecExpr(item, scope) for item in expr["items"]})
            case {"type": "Array"}:
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
            case {"type": "DeleteStatement"}:
                self.getVar(
                    scope, expr["target"]["value"], expr["target"]["positions"]["start"]
                )
                del scope[expr["name"]]
            case {"type": "FunctionCall"}:
                funct = self.ExecExpr(expr["function"], scope)
                self.traceback.append(
                    {
                        "name": Error.getAstText(expr["function"], self.codelines)
                        + "()",
                        "line": expr["positions"]["start"]["line"],
                        "col": expr["positions"]["start"]["col"],
                        "filename": Path(self.path).name,
                    }
                )
                args = []
                kwargs = {
                    k: self.ExecExpr(v, scope)
                    for k, v in list(expr["keywordArguments"].items())
                }
                for arg in expr["arguments"]:
                    if arg.get("type") == "Operator" and arg.get("operator") == "...":
                        arg = self.ExecExpr(
                            arg["left"] if arg["left"] else arg["right"], scope
                        )
                        if type(arg) == Object:
                            kwargs.update(arg.vars)
                        else:
                            args = [*args, *arg]
                    else:
                        args.append(self.ExecExpr(arg, scope))
                try:
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
            case {"type": "Operator", "operator": "?"}:
                left = self.ExecExpr(expr["left"], scope, False)
                right = self.ExecExpr(expr["right"], scope)
                return Operators["?"](
                    left,
                    right,
                    self.errorhandler,
                    self.codelines[expr["positions"]["start"]["line"] - 1],
                    expr,
                    scope,
                    self,
                )
            case {"type": "Operator", "operator": operator}:
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
            case {"type": "IfStatement"}:
                ifscope = Scope({}, parent=scope, scope_type="conditional")
                if bool(self.ExecExpr(expr["condition"], scope)):
                    return self.Exec(expr["body"], ifscope)
                elif expr["else_body"]:
                    return self.Exec(expr["else_body"], ifscope)
            case {"type": "WhileLoop"}:
                ret = []
                while bool(self.ExecExpr(expr["condition"], scope)):
                    whilescope = Scope({}, parent=scope, scope_type="loop")
                    ret.append(self.Exec(expr["body"], whilescope))
                    if whilescope._completed and not whilescope._has_been_continued:
                        break
                return ret
            case {"type": "ForLoop"}:
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
            case {"type": "SPMObject"}:
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
            case {"type": "CaseStatement"}:
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
            case {"type": "Assignments"}:
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
            case {"type": "SwitchStatement"}:
                switchscope = Scope({}, parent=scope, scope_type="match")
                self.switch = self.ExecExpr(expr["value"], scope)
                self.Exec(expr["body"], switchscope)
                if getattr(self, "switch", False):
                    del self.switch
            case {"type": "FunctionDefinition"}:
                funct = self.makeFunct(expr, scope)
                return funct
            case {"type": "ClassDefinition"}:
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
            case {"type": "DeferStatement"}:
                scope.addReturnAction(lambda: self.ExecExpr(expr["value"], scope))
            case {"type": "ReturnStatement"}:
                val = self.ExecExpr(expr["value"], scope)
                success = scope.complete("function", val)
                if scope == self.Global or not success:
                    self.Global._triggerReturnAction()
                    if val == Null:
                        val = 0
                    sys.exit(int(val))
                return scope._returned_value
            case {"type": "Multiply"}:
                # for (num)x mult
                return self.ExecExpr(expr["number"], scope) * self.getVar(
                    scope, expr["variable"], expr["tokens"]["variable"].start
                )
            case {"type": "Index"}:
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
                                    "start": expr["property"]["positions"]["start"][
                                        "col"
                                    ],
                                    "length": expr["property"]["positions"]["end"][
                                        "col"
                                    ]
                                    - expr["property"]["positions"]["start"]["col"]
                                    + 1,
                                },
                                "traceback": self.traceback,
                            },
                        )
                    else:
                        return None
            case {"type": "IncludeStatement"}:
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
            case {"type": "ThrowStatement"}:
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
            case {"type": "TryCatch"}:
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
            # case {'type': 'ExtendingStatement'}:
            #   pass
            case {"type": "BreakStatement"}:
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
            case {"type": "ContinueStatement"}:

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
            case {"type": "TemplateString"}:
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
                    string = (
                        string[: rep["from"]] + str(value) + string[rep["to"] + 1 :]
                    )
                return String(string)
            case None:
                return Null
            case _:
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


def notImplemented(errorhandler, item, expr):
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


def findClosest(var, scope):
    lowest = 9999999999999999
    ret = "<identifier>"
    for item in list(scope.getAll().keys()):
        dist = edit_distance(var, item)
        if dist < lowest:
            ret = item
            lowest = dist
    return ret

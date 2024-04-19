from Error import Highlight, styles
from sty import fg
from Types import Null, Object, Scope
import math
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Error import ErrorHandler
    from Exec import Executor

Operators = {}


def missingOperand(
    left, errorhandler: "ErrorHandler", line: str, ast, placeholder: str
):
    if left:
        line = (
            line[: ast["positions"]["start"]["col"]]
            + placeholder
            + " "
            + line[ast["positions"]["start"]["col"] :]
        )
    else:
        line = (
            line[: ast["positions"]["end"]["col"]]
            + " "
            + placeholder
            + line[ast["positions"]["end"]["col"] :]
        )
    did_you_mean = Highlight(line, {"background": None, "linenums": None})
    start = ast["positions"]["start"]
    end = ast["positions"]["end"]
    errorhandler.throw(
        "Syntax",
        "Expected non-null Operand.",
        {
            "lineno": start["line"],
            "marker": {"start": start["col"] if left else end["col"], "length": 1},
            "underline": {
                "start": start["col"] if left else start["col"],
                "end": end["col"] if left else end["col"],
            },
            "did_you_mean": did_you_mean,
        },
    )


def unexpectedOperand(left, errorhandler: "ErrorHandler", line: str, ast):
    if left:
        line = (
            line[: ast["left"]["positions"]["start"]["col"]]
            + line[ast["left"]["positions"]["end"]["col"] :]
        )
    else:
        line = (
            line[: ast["right"]["positions"]["start"]["col"]]
            + line[ast["right"]["positions"]["end"]["col"] :]
        )
    did_you_mean = Highlight(line, {"background": None, "linenums": None})
    start = ast["positions"]["start"]
    end = ast["positions"]["end"]
    errorhandler.throw(
        "Syntax",
        "Unexpected Operand.",
        {
            "lineno": start["line"],
            "marker": {"start": start["col"] if left else end["col"] + 1, "length": 1},
            "underline": {
                "start": start["col"] if left else start["col"],
                "end": end["col"] if left else end["col"],
            },
            "did_you_mean": did_you_mean,
        },
    )


class Operator:
    def __init__(self, handler, left, right):
        self.handler = handler
        self.left = left
        self.right = right

    def __call__(self, *args, **kwargs):
        return self.handler(*args, **kwargs)


def operator(*names, left=None, right=None):
    def decor(funct):
        for name in names:
            Operators[name] = Operator(funct, left, right)
        return funct

    return decor


@operator("+", left=True, right=True)
def add(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return x + y


@operator("-", left=None, right=True)
def sub(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    # This function also handles negative numbers, it sees -5 as 0-5
    if x == Null and type(y).__name__ != "Number":
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    elif x == Null:
        x = 0  # Can't return because we still have to check for y
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return x - y


@operator("*", left=True, right=True)
def mult(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return x * y


@operator("/", left=True, right=True)
def div(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return x / y


@operator("==", left=True, right=True)
def logicalequals(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    return x == y


@operator("<", left=True, right=True)
def logicallessthan(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return x < y


@operator(">", left=True, right=True)
def logicamorethan(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return x > y


@operator(">=", left=True, right=True)
def logicamorethanequal(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return x >= y


@operator("<=", left=True, right=True)
def logicallessthanequal(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none

    return x <= y


@operator("!=", left=True, right=True)
def logicalnotequal(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    return x != y


@operator("~", left=False, right=True)
def roundop(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x != Null:
        return unexpectedOperand(True, errorhandler, line, ast)
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return round(y)


@operator("?", left=True, right=True)
def Exists(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return y
    return x


@operator("!", "not", left=False, right=True)
def notop(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x != Null:
        return unexpectedOperand(True, errorhandler, line, ast)
    # TODO: add if y and x equal none
    return not y


@operator("%", left=True, right=True)
def modulo(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return x % y


@operator("&", "and", left=True, right=True)
def logicaland(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    x = exec.ExecExpr(x, scope)
    if not x:
        return False
    y = exec.ExecExpr(y, scope)
    return x and y


@operator("|", "or", left=True, right=True)
def logicalor(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    x = exec.ExecExpr(x, scope)
    if x:
        return True
    y = exec.ExecExpr(y, scope)
    return x or y


@operator("x|", "xor", left=True, right=True)
def logicalxor(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    try:
        return x ^ y
    except:
        pass
    return (x or y) and not (x and y)


@operator("in", left=True, right=True)
def inop(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    try:
        return x in y
    except:
        sys.exit()


# Working on making Aardvark lexer work (from the compiler version)
# Yep, `$test classes` it does work. As far as I know. I made unit tests btw and added stuff to that.
# ./adk run [file]
# It just runs python3 main.py file when you run that command. But its not working because theres an error at the bottom of this file.
# how do I run code here? oh it's compiled already? aha
# now you can try.
# ./adk by itself does a live thing kinda like when you run python3 by itself.
@operator("~=", left=True, right=True)
def aboutequal(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    return round(x) == round(y)


@operator("...", left=None, right=None)
def spread(
    x, y, errorhandler: "ErrorHandler", line: str, ast, scope: Scope, exec: "Executor"
):
    start = ast["positions"]["start"]
    end = ast["positions"]["end"]
    errorhandler.throw(
        "Operator",
        "Spread operator not available in this context.",
        {
            "lineno": start["line"],
            "marker": {"start": start["col"], "length": end["col"] - start["col"] + 1},
            "underline": {
                "start": start["col"],
                "end": end["col"],
            },
        },
    )


@operator("=", left=True, right=True)
def assign(
    x,
    y,
    errorhandler: "ErrorHandler",
    line: str,
    expr,
    scope: Scope,
    exec: "Executor",
    predone=False,
    allowLiteral=False,
):
    value = exec.ExecExpr(y, scope) if not predone else y
    var = x
    defscope = scope
    if var["type"] == "PropertyAccess":
        defscope = exec.enterScope(var["value"], scope, scope)
        var = exec.ExecExpr(var["property"], scope)
        # if exec.is_strict:
        #     exec.getVar(
        #         defscope,
        #         var,
        #         x["positions"]["start"],
        #         True,
        #         'Undefined variable "{name}". Use `let` to declare a variable.',
        #     )
        exec.defineVar(var, value, defscope, False, expr)
    elif var["type"] == "Index":
        defscope = exec.enterScope(var["value"], scope, scope)
        var = exec.ExecExpr(var["property"], scope)
        exec.defineVar(var, value, defscope, False, expr)
    elif var["type"] == "VariableAccess":
        var = var["value"]
        if exec.is_strict:
            exec.getVar(
                scope,
                var,
                x["positions"]["start"],
                True,
                'Undefined variable "{name}". Use `let` to declare a variable.',
                True,
            )
        exec.defineVar(var, value, defscope, False, expr)
    elif var["type"] == "Array":
        spread = None
        for i in range(len(var["items"])):
            val = var["items"][i]
            if val["type"] == "Spread":
                spread = val["value"]
            else:
                assign(val, value[i], errorhandler, line, expr, scope, exec, True)
        if spread:
            exec.defineVar(spread, value[i:], defscope, False, expr)
    elif not allowLiteral:
        errorhandler.throw(
            "Assignment",
            "Cannot set value of a literal or expression.",
            {
                "lineno": var["positions"]["start"]["line"],
                "underline": {
                    "start": var["positions"]["start"]["col"],
                    "end": var["positions"]["end"]["col"],
                },
                "marker": {
                    "start": var["positions"]["start"]["col"],
                    "length": var["positions"]["end"]["col"]
                    - var["positions"]["start"]["col"],
                },
                "traceback": exec.traceback,
            },
        )
    else:
        exec.ExecExpr(var, scope)
        return value
    return value


@operator("+=", left=True, right=True)
def plusequals(
    x, y, errorhandler: "ErrorHandler", line: str, expr, scope: Scope, exec: "Executor"
):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left + right, errorhandler, line, expr, scope, exec, True)


@operator("-=", left=True, right=True)
def minusequals(
    x, y, errorhandler: "ErrorHandler", line: str, expr, scope: Scope, exec: "Executor"
):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left - right, errorhandler, line, expr, scope, exec, True)


@operator("*=", left=True, right=True)
def multequals(
    x, y, errorhandler: "ErrorHandler", line: str, expr, scope: Scope, exec: "Executor"
):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left * right, errorhandler, line, expr, scope, exec, True)


@operator("/=", left=True, right=True)
def divideequals(
    x, y, errorhandler: "ErrorHandler", line: str, expr, scope: Scope, exec: "Executor"
):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left / right, errorhandler, line, expr, scope, exec, True)


@operator("^=", left=True, right=True)
def exponetequals(
    x, y, errorhandler: "ErrorHandler", line: str, expr, scope: Scope, exec: "Executor"
):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left**right, errorhandler, line, expr, scope, exec, True)


@operator("%=", left=True, right=True)
def moduloequals(
    x, y, errorhandler: "ErrorHandler", line: str, expr, scope: Scope, exec: "Executor"
):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left % right, errorhandler, line, expr, scope, exec, True)


@operator("++", left=True, right=True)
def plusplus(
    x, y, errorhandler: "ErrorHandler", line: str, expr, scope: Scope, exec: "Executor"
):
    if x:
        left = exec.ExecExpr(x, scope)
        assign(x, left + 1, errorhandler, line, expr, scope, exec, True, True)
        return left
    # Otherwise return the new value
    right = exec.ExecExpr(y, scope)
    return assign(y, right + 1, errorhandler, line, expr, scope, exec, True)


@operator("--", left=True, right=True)
def minusminus(
    x, y, errorhandler: "ErrorHandler", line: str, expr, scope: Scope, exec: "Executor"
):
    if x:
        left = exec.ExecExpr(x, scope)
        assign(x, left - 1, errorhandler, line, expr, scope, exec, True, True)
        return left
    # Otherwise return the new value
    right = exec.ExecExpr(y, scope)
    return assign(y, right - 1, errorhandler, line, expr, scope, exec, True)


@operator("@", left=False, right=True)
def reference(
    x, y, errorhandler: "ErrorHandler", line: str, expr, scope: Scope, exec: "Executor"
):
    if x:
        return unexpectedOperand(x, errorhandler, line, expr)
    errorhandler.throw(
        "Unimplemented",
        "The @ operator is not yet implemented.",
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
            "traceback": exec.traceback,
        },
    )
    return

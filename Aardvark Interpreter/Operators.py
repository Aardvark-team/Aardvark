from Error import Highlight, styles
from sty import fg
from Types import Null, Object, Scope
import math
import sys

Operators = {}
# stdout.write(+ 1)


def missingOperand(left, errorhandler, line, ast, placeholder):
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


def unexpectedOperand(left, errorhandler, line, ast):
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


def operator(*names):
    def decor(funct):
        for name in names:
            Operators[name] = funct
        return funct

    return decor


@operator("+")
def add(x, y, errorhandler, line, ast, scope, exec):
    # print("OP", x, '+', y)
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


@operator("-")
def sub(x, y, errorhandler, line, ast, scope, exec):
    # This function also handles negative numbers, it sees -5 as 0-5
    if x == Null and type(y).__name__ != "Number":
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    elif x == Null:
        # print('not x', x, ast)
        x = 0  # Can't return because we still have to check for y
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    # print("OP", x, '-', y, '=', x - y)
    return x - y


@operator("*")
def mult(x, y, errorhandler, line, ast, scope, exec):
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


@operator("/")
def div(x, y, errorhandler, line, ast, scope, exec):
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


@operator("==")
def logicalequals(x, y, errorhandler, line, ast, scope, exec):
    return x == y


@operator("<")
def logicallessthan(x, y, errorhandler, line, ast, scope, exec):
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


@operator(">")
def logicamorethan(x, y, errorhandler, line, ast, scope, exec):
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


@operator(">=")
def logicamorethanequal(x, y, errorhandler, line, ast, scope, exec):
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


@operator("<=")
def logicallessthanequal(x, y, errorhandler, line, ast, scope, exec):
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


@operator("!=")
def logicalnotequal(x, y, errorhandler, line, ast, scope, exec):
    return x != y


@operator("~")
def roundop(x, y, errorhandler, line, ast, scope, exec):
    if x != Null:
        return unexpectedOperand(True, errorhandler, line, ast)
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return round(y)


@operator("?")
def Exists(x, y, errorhandler, line, ast, scope, exec):
    if x == Null:
        return y
    return x


@operator("!", "not")
def roundop(x, y, errorhandler, line, ast, scope, exec):
    if x != Null:
        return unexpectedOperand(True, errorhandler, line, ast)
    # TODO: add if y and x equal none
    return not y


@operator("%")
def modulo(x, y, errorhandler, line, ast, scope, exec):
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


@operator("&", "and")
def logicaland(x, y, errorhandler, line, ast, scope, exec):
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
    if not x: return False
    y = exec.ExecExpr(y, scope)
    return x and y


@operator("|", "or")
def logicalor(x, y, errorhandler, line, ast, scope, exec):
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
    if x: return True
    y = exec.ExecExpr(y, scope)
    return x or y


@operator("x|", "xor")
def logicalxor(x, y, errorhandler, line, ast, scope, exec):
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


@operator("in")
def inop(x, y, errorhandler, line, ast, scope, exec):
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    try:return x in y
    except:
        # print('vals', x, y)
        sys.exit()


# Working on making Aardvark lexer work (from the compiler version)
# Yep, `$test classes` it does work. As far as I know. I made unit tests btw and added stuff to that.
# ./adk run [file]
# It just runs python3 main.py file when you run that command. But its not working because theres an error at the bottom of this file.
# how do I run code here? oh it's compiled already? aha
# now you can try.
# ./adk by itself does a live thing kinda like when you run python3 by itself.
@operator("~=")
def aboutequal(x, y, errorhandler, line, ast, scope, exec):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    return round(x) == round(y)


@operator("...")
def spread(x, y, errorhandler, line, ast, scope, exec):
    start = ast['positions']['start']
    end = ast['positions']['end']
    errorhandler.throw('Operator', 'Spread operator not available in this context.',
        {
            "lineno": start["line"],
            "marker": {"start": start["col"], "length": end['col'] - start['col'] + 1},
            "underline": {
                "start": start["col"],
                "end": end["col"],
            }
    })


@operator('=')
def assign(x, y, errorhandler, line, expr, scope, exec, predone=False):
    value = exec.ExecExpr(y, scope) if not predone else y
    var = x
    defscope = scope
    if var["type"] == "PropertyAccess":
        defscope = exec.enterScope(var["value"], scope, scope)
        var = var["property"]
        exec.defineVar(var, value, defscope)
    elif var["type"] == "Index":
        defscope = exec.enterScope(var["value"], scope, scope)
        var = exec.ExecExpr(var["property"], scope)
        exec.defineVar(var, value, defscope)
    elif var["type"] == "VariableAccess":
        var = var["value"]
        exec.defineVar(var, value, defscope)
    elif var['type'] == 'Array':
        spread = None
        for i in range(len(var['items'])):
            val = var['items'][i]
            if val['type'] == 'Spread':
                spread = val['value']
            else:
                assign(val, value[i], errorhandler, line, expr, scope, exec, True)
        if spread: 
            exec.defineVar(spread, value[i:], defscope) 
    else:
        errorhandler.throw(
            "Assignment",
            "Cannot set value of a literal.",
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
                "traceback": self.traceback,
            },
        )
    return value

@operator('+=')
def plusequals(x, y, errorhandler, line, expr, scope, exec):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left + right, errorhandler, line, expr, scope, exec, True)

@operator('-=')
def minusequals(x, y, errorhandler, line, expr, scope, exec):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left - right, errorhandler, line, expr, scope, exec, True)

@operator('*=')
def multequals(x, y, errorhandler, line, expr, scope, exec):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left * right, errorhandler, line, expr, scope, exec, True)

@operator('/=')
def divideequals(x, y, errorhandler, line, expr, scope, exec):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left / right, errorhandler, line, expr, scope, exec, True)

@operator('^=')
def exponetequals(x, y, errorhandler, line, expr, scope, exec):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left ** right, errorhandler, line, expr, scope, exec, True)

@operator('%=')
def moduloequals(x, y, errorhandler, line, expr, scope, exec):
    left = exec.ExecExpr(x, scope)
    right = exec.ExecExpr(y, scope)
    return assign(x, left % right, errorhandler, line, expr, scope, exec, True)

@operator('++')
def plusplus(x, y, errorhandler, line, expr, scope, exec):
    left = exec.ExecExpr(x, scope)
    return assign(x, left + 1, errorhandler, line, expr, scope, exec, True)

@operator('--')
def minusminus(x, y, errorhandler, line, expr, scope, exec):
    left = exec.ExecExpr(x, scope)
    return assign(x, left - 1, errorhandler, line, expr, scope, exec, True)
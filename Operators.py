from Error import Highlight, styles
from sty import fg
from Types import Null, Object, Scope

Operators = {}
# stdout.write(+ 1)


def missingOperand(left, errorhandler, line, ast, placeholder):
    if left:
        line = (
            line[: ast["positions"]["start"]["col"] - 1]
            + placeholder
            + " "
            + line[ast["positions"]["start"]["col"] - 1 :]
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
            "marker": {"start": start["col"] - 1 if left else end["col"], "length": 1},
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
            line[: ast["left"]["positions"]["start"]["col"] - 1]
            + line[ast["left"]["positions"]["end"]["col"] :]
        )
    else:
        line = (
            line[: ast["right"]["positions"]["start"]["col"] - 1]
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
def add(x, y, errorhandler, line, ast):
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
def sub(x, y, errorhandler, line, ast):
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
def mult(x, y, errorhandler, line, ast):
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
def div(x, y, errorhandler, line, ast):
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
def logicalequals(x, y, errorhandler, line, ast):
    return x == y


@operator("<")
def logicallessthan(x, y, errorhandler, line, ast):
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
def logicamorethan(x, y, errorhandler, line, ast):
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
def logicamorethanequal(x, y, errorhandler, line, ast):
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
def logicallessthanequal(x, y, errorhandler, line, ast):
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
def logicalnotequal(x, y, errorhandler, line, ast):
    return x != y


@operator("~")
def roundop(x, y, errorhandler, line, ast):
    if x != Null:
        return unexpectedOperand(True, errorhandler, line, ast)
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return round(y)


@operator("?")
def Exists(x, y, errorhandler, line, ast):
    if x == Null:
        return y
    return x


@operator("!", "not")
def roundop(x, y, errorhandler, line, ast):
    if x != Null:
        return unexpectedOperand(True, errorhandler, line, ast)
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return not y


@operator("%")
def modulo(x, y, errorhandler, line, ast):
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
def logicaland(x, y, errorhandler, line, ast):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return x and y


@operator("|", "or")
def logicalor(x, y, errorhandler, line, ast):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return x or y


@operator("x|", "xor")
def logicalxor(x, y, errorhandler, line, ast):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return (x or y) and not (x and y)


@operator("in")
def inop(x, y, errorhandler, line, ast):
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    # TODO: add if y and x equal none
    return x in y


@operator("~=")
def aboutequal(x, y, errorhandler, line, ast):
    if x == Null:
        return missingOperand(
            True, errorhandler, line, ast, f"<{str(type(y or 0).__name__)}>"
        )
    if y == Null:
        return missingOperand(
            False, errorhandler, line, ast, f"<{str(type(x or 0).__name__)}>"
        )
    return round(x) == round(y)

class TokenType:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


TokenTypes = {
    "String": TokenType("String"),
    "Number": TokenType("Number"),
    "Keyword": TokenType("Keyword"),
    "Operator": TokenType("Operator"),
    "Identifier": TokenType("Identifier"),
    "Delimiter": TokenType("Delimiter"),
    "Indent": TokenType("Indent"),
    "Comment": TokenType("Comment"),
    "LineBreak": TokenType("LineBreak"),
    "Boolean": TokenType("Boolean"),
}


Booleans = {"true", "false"}

NotIncluded = "`'\"~!@#$%^&*()-+=[]{}\\|:;,<.>/?"

PureOperators = {
    "=",  # equals
    "!",  # not,
    "~",  # about
    "<",  # less than
    ">",  # more than
    "==",  # equals
    "<=",  # less than or equal to
    ">=",  # more than or equal to
    "!=",  # not equal to
    "~=",  # about equal to
    "&",  # and
    "|",  # or
    "+",  # add
    "-",  # subtract
    "/",  # divide
    "*",  # multiplication
    "^",  # exponent
    "%",  # mod
    "@",  # at. reference
    "?",  # x.y? will be null if x.y doesn't exist or if it is null
    "->",  # Return Type,
    "<-",
    "++",  # Increment
    "--",  # Decrement
    "$=",  # Structural Pattern Matching
    "...",  # Spread
    "@=",  # Is the same reference
    "?=",  # Assign if null
    "+=",
    "-=",
    "*=",
    "/=",
    "^=",
    "%=",
    "=>",
    "=<",
    ">>=",
    ">>",
    "<<",
    "<<=",
    ">>>",
    ">>>=",
    "<<<",
    "<<<=",
    "$",
}
#!& should be valid, not and.
#!| should be valid, not or.
#!x| should be valid, not xor.
#!= should be valid, not equal.
Operators = PureOperators | {
    "not",  # not operator
    "and",  # and operator
    "or",  # or operator
    "xor",  # XOR
    "in",
    "is",
    "mod",
    "is not",
    "is not in",
    "not in",
    "is in",
    "references",
}
OrderOfOps = {
    0: ["...", "?"],
    1: ["~", "!", "@", "not"],
    2: ["^"],
    3: ["*", "/"],
    4: ["-"],
    5: ["-", "+", "%", "mod"],
    6: ["++", "--", "=", "+=", "-=", "*=", "/=", "^=", "%=", "?="],
    7: [
        "~=",
        "<",
        ">",
        "<=",
        ">=",
        "!=",
        "in",
        "is in",
        "==",
        "$=",
        "is",
        "is not",
        "is not in",
        "not in",
        "references",
    ],
    8: [
        "&",
        "|",
        "x|",
        "and",
        "or",
        "xor",
        "->",
        "<-",
        ">>",
        ">>=",
        "<<",
        "<<=",
        ">>>",
        ">>>=",
        "<<<",
        "<<<=",
    ],
}


def get_precedence(operator):
    for i in OrderOfOps:
        if operator in OrderOfOps[i]:
            return i


Quotes = {'"', "'", "`"}

Groups = (("(", ")"), ("[", "]"), ("{", "}"))

Whitespaces = {
    " ",  # Space
    "\t",  # Tab
    "​",  # zero width space
    " ",  # hair space
    " ",  # six per em space
    " ",  # thin space
    " ",  # punctuation space
    " ",  # four per em space
    " ",  # three per em space
    " ",  # figure space
    " ",  # en space
    " ",  # em space
    "⠀",  # braile blank
}

Delimiters = {
    ":",  # Colon, used for defining blocks and for types
    "(",  # lparen
    ")",  # rparen
    ",",  # comma
    "{",  # lbrace
    "}",  # rbrace
    "[",  # lbracket
    "]",  # rbracket
    ".",  # period,
}

Keywords = {
    "class",
    "extends",
    "extending",
    "function",
    "for",
    "while",
    "match",
    "switch",
    "case",
    "if",
    "else",  # Blocks
    "return",
    "delete",
    "include",
    "async",
    "await",
    "yield",
    "defer",  # Statements
    "as",
    "from",  # other
    "throw",
    "try",
    "catch",
    "break",
    "continue",
    "pause-until",
    "let",
    "static",
    "get",
    "set",
    "macro",
    "mutable",
    "construct",
    "with",
    "embed",
    "structure",
    "template",
    "loop",
    "lambda",
    "option",
    "expose",
}

# https://replit.com/@Programit/Redesign

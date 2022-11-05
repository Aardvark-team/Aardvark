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
    "Boolean": TokenType("Boolean")
}


class Group:

    def __init__(self, t):
        self.type = t
        self.tokens = [[]]

    def append(self, token, line=-1):
        self.tokens[line].append(token)

    def newline(self):
        self.tokens.append([])


Booleans = {"true", "false"}

PureOperators = {
    "=",  # is equal to
    "!",  #not, and factorial
    "<",  #less than
    ">",  #more than
    "<=",  #less than or equal to
    ">=",  #more than or equal to
    "!=",  #not equal to
    "&",  #and
    "|",  #or
    "x|",  #xor (exculsive or)
    "=",  #equal to
    "+",  #add
    "-",  #subtract
    "/",  #divide
    "*",  #multiplication
    "^",  #exponet 
    "%",  #mod
    "@",  #at. Kinda between a pointer and reference.
    "$",  #idk
    "?",  # x.y? will be null if x.y doesn't exist or if it is null
    "->",  # For defining a function return type
    "<-",  #idk, we can use it for something maybe.
}
#!& should be valid, not and.
#!| should be valid, not or.
#!x| should be valid, not xor.
#!= should be valid, not equal.
Operators = PureOperators | {
    'not',  #not operator
    'and',  #and operator
    'or',  #or operATOR
    'xor',  #XOR
}

Quotes = {'"', "'", '`'}

Groups = (('(', ')'), ('[', ']'), ('{', '}'))

Whitespaces = {
    ' ',  #Space
    '\t',  #Tab
    '​',  #zero width space
    ' ',  #hair space
    ' ',  #six per em space
    ' ',  #thin space
    ' ',  #punctuation space
    ' ',  #four per em space
    ' ',  #three per em space
    ' ',  #figure space
    ' ',  #en space
    ' ',  #em space
    '⠀',  #braile blank
}

Delimiters = {
    ":",  #Colon, used for defining blocks and for types
    "(",  #lparen
    ")",  #rparen
    ",",  #comma
    "{",  #lbrace
    "}",  #rbrace
    "[",  #lbracket
    "]",  #rbracket
    ".",  #period,
    ';',  #newline
}

Keywords = {
    'class',
    'extends',
    'type',
    'extending',
    'function',
    'for',
    'while',
    'if',
    'else',  #Blocks
    'return',
    'delete',
    'static',
    'include',
    'async',
    'yield',
    'let',  #Statements
    'as',
    'from',
    'in',
    'is',
    'copy',  #Other
}
#https://replit.com/@Programit/Redesign
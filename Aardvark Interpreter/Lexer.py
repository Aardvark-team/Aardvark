from Data import (
    TokenTypes,
    Operators,
    Keywords,
    Quotes,
    Whitespaces,
    PureOperators,
    Booleans,
    Delimiters,
    NotIncluded,
)
import Error


class Token:
    def __init__(
        self,
        toktype,
        start: int,
        end: int,
        line: int,
        columnstart: int,
        columnend: int,
        value=None,
        variation=None,
    ):
        if type(toktype) == str:
            toktype = TokenTypes[toktype]
        self.columnstart = columnstart
        self.columnend = columnend
        self.type = toktype
        self.length = end - start
        self.start = {"line": line, "col": columnstart}
        self.end = {"line": line, "col": columnend}
        self.start_index = start
        self.end_index = end
        self.value = value
        self.line = line
        self.variation = variation

    def __repr__(self):
        return (
            f"Token({self.type.name}, '{self.value}', from"
            f" {self.start['line']}:{self.start['col']} to"
            f" {self.end['line']}:{self.end['col']})"
        )


class Lexer:
    def __init__(
        self,
        singleline: str,
        multilines: str,
        multilinee: str,
        errorhandler: Error.ErrorHandler,
        useIndents=False,
        tokenizeComments=False,
        strict=True,
    ):
        self.errorhandler = errorhandler
        self.useIndents = useIndents
        self.comment = singleline
        self.commentstart = multilines
        self.commentend = multilinee
        self.tokenizeComments = tokenizeComments
        self.data = ""
        self.index = 0
        self.line = 1
        self.column = 1
        self.output = []
        self.empty = True
        self.AtEnd = False
        self.curChar = ""
        self.strict = strict

    def isWhitespace(self, char=None):
        char = char or self.curChar
        return char in Whitespaces

    def isNewline(self, char=None):
        char = char or self.curChar
        return char == "\n" or char == ";"

    def isString(self, char=None):
        char = char or self.curChar
        return char in Quotes

    def isDelimiter(self, char=None):
        char = char or self.curChar
        return char in Delimiters

    def detect(self, text):
        if self.curChar == text[0]:
            for i in range(len(text) - 1):
                if not self.peek(i + 1) == text[i + 1]:
                    return False
        else:
            return False
        return True

    def isNumber(self, char=None):
        char = char or self.curChar
        return char in "0123456789"

    def addToken(self, *args, **kwargs):
        self.output.append(Token(*args, **kwargs))
        self.empty = False

    def otherwise(self, char=None):
        char = char or self.curChar
        return not (
            self.isWhitespace(char)
            or self.isDelimiter(char)
            or self.isNewline(char)
            or char == self.comment
            or char in PureOperators
            or char in NotIncluded
        )

    def newline(self):
        # Self.empty means that we are on an empty line
        self.empty = True
        self.line += 1
        self.column = 1

    def reset(self):
        self.data = ""
        self.index = 0
        self.line = 1
        self.column = 1
        self.output = []
        self.empty = True
        self.AtEnd = False
        self.curChar = ""

    def tokenize(self, data: str):
        """
        Takes code and converts it to tokens.
        """
        if not data:
            self.output = []
            return []
        self.data += data
        self.curChar = self.data[self.index]
        while self.index < len(self.data):

            # Operators
            for op in sorted(PureOperators, key=len, reverse=True):
                if self.detect(op):
                    start = self.index
                    startcolumn = self.column
                    self.advance(len(op) - 1)
                    self.addToken(
                        "Operator",
                        start,
                        self.index,
                        self.line,
                        startcolumn,
                        self.column,
                        op,
                    )
                    self.advance()
                    if self.AtEnd:
                        break

            # Newlines (\n or ;)
            if self.isNewline():
                self.addToken(
                    "LineBreak",
                    start=self.index,
                    end=self.index,
                    line=self.line,
                    value=self.curChar,
                    variation=self.curChar,
                    columnstart=self.column,
                    columnend=self.column,
                )
                if self.curChar == "\n":
                    self.newline()  # Only incremnet the line if its a \n
                else:
                    self.empty = True

            # Indents
            elif self.isWhitespace() and self.empty and self.useIndents:
                value = ""
                start = self.index
                startcolumn = self.column
                while self.isWhitespace() and not self.AtEnd:
                    value += self.curChar
                    self.advance()
                if not self.isNewline():
                    self.advance(-1)
                    self.addToken(
                        "Indent",
                        start,
                        self.index,
                        self.line,
                        value=value,
                        columnstart=startcolumn,
                        columnend=self.column,
                    )
                else:
                    self.advance(-1)

            # Delimiters
            elif self.isDelimiter():
                self.addToken(
                    "Delimiter",
                    self.index,
                    self.index,
                    self.line,
                    self.column,
                    self.column,
                    self.curChar,
                )

            # Numbers
            elif self.isNumber():  # Has to be in 0123456789 for this to be true.
                start = self.index
                startcolumn = self.column
                value = ""
                seen_dot = False
                while (self.isNumber() or self.curChar == ".") and not self.AtEnd:
                    if (
                        seen_dot and self.curChar == "." and self.errorhandler
                    ):  # TODO: replace with native errors
                        if self.strict:
                            raise Exception(
                                "invalid syntax, floats can only have one '.'"
                            )
                        else:
                            value += self.curChar
                    if self.curChar == ".":
                        seen_dot = True
                    value += self.curChar
                    self.advance()
                self.advance(-1)
                if value[-1] == "." and self.errorhandler:
                    if self.strict:
                        didyoumean = (
                            self.data.split("\n")[self.line - 1][
                                : self.column - len(value)
                            ]
                            + value[:-1]
                            + self.data.split("\n")[self.line - 1][self.column :]
                        )
                        self.errorhandler.throw(
                            "Syntax",
                            "Numbers cannot end with a .",
                            {
                                "lineno": self.line,
                                "marker": {"start": self.column, "length": 1},
                                "underline": {
                                    "start": self.column - len(value),
                                    "end": self.column + 1,
                                },
                                "did_you_mean": didyoumean,
                            },
                        )
                self.addToken(
                    "Number",
                    start,
                    self.index,
                    self.line,
                    startcolumn,
                    self.column,
                    value,
                )

            # Multi-line comments
            elif self.detect(self.commentstart):
                value = ""
                start = self.index
                startcolumn = self.column
                while not self.detect(self.commentend) and not self.AtEnd:
                    value += self.curChar
                    self.advance()
                    if self.curChar == "\n":
                        self.line += 1
                        self.column = 1
                if self.tokenizeComments:
                    self.addToken(
                        "Comment",
                        start,
                        self.index,
                        self.line,
                        startcolumn,
                        self.column,
                        value,
                    )
                self.advance(len(self.commentend) - 1)  # To skip past the *#

            # Single line comments
            elif self.detect(self.comment):
                value = ""
                start = self.index
                startcolumn = self.column
                while self.curChar != "\n" and not self.AtEnd:
                    value += self.curChar
                    self.advance()
                if self.tokenizeComments:
                    self.addToken(
                        "Comment",
                        start,
                        self.index,
                        self.line,
                        startcolumn,
                        self.column,
                        value,
                    )
                self.advance(-1)  # To register the new line

            # Strings
            elif self.isString():
                variation = self.curChar
                value = ""
                begin = self.index
                startcolumn = self.column
                backslash = False
                while True:
                    self.advance()
                    if self.AtEnd:
                        if self.strict:
                            raise Exception("Error: Unexpected EOF")
                        else:
                            self.advance(-1)
                            break

                    if backslash:
                        if self.curChar == "\\":
                            value += "\\"
                        if self.curChar == "n":
                            value += "\n"
                        if self.curChar == variation:
                            value += variation
                        backslash = False
                    else:
                        if self.curChar == "\\":
                            backslash = True
                        elif self.curChar == variation:
                            break
                        else:
                            value += self.curChar

                self.addToken(
                    "String",
                    begin,
                    self.index,
                    self.line,
                    startcolumn,
                    self.column,
                    value,
                    variation,
                )

            # Identifiers, Keywords, and Operators.
            elif self.otherwise():
                value = ""
                start = self.index
                startcolumn = self.column
                while (self.otherwise() or self.isNumber()) and not self.AtEnd:
                    value += self.curChar
                    self.advance()
                self.advance(-1)
                if value in Operators:
                    self.addToken(
                        "Operator",
                        start,
                        self.index,
                        self.line,
                        startcolumn,
                        self.column,
                        value,
                    )
                elif value in Keywords:
                    self.addToken(
                        "Keyword",
                        start,
                        self.index,
                        self.line,
                        startcolumn,
                        self.column,
                        value,
                    )
                elif value in Booleans:
                    self.addToken(
                        "Boolean",
                        start,
                        self.index,
                        self.line,
                        startcolumn,
                        self.column,
                        value,
                    )
                else:
                    self.addToken(
                        "Identifier",
                        start,
                        self.index,
                        self.line,
                        columnstart=startcolumn,
                        columnend=self.column,
                        value=value,
                    )

            if self.AtEnd:
                break
            self.advance()  # Next character and continue the loop
        return self.output

    def advance(self, amt=1):
        self.index += amt
        self.column += amt
        if self.index < len(self.data):
            self.curChar = self.data[self.index]
        else:
            self.AtEnd = True

    def peek(self, amt=1):
        if self.index + amt < len(self.data):
            return self.data[self.index + amt]
        else:
            return None

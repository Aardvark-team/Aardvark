import Data
import Lexer
import Parser
import Error


class Formatter:
    def __init__(self, parser, ast, settings):
        self.parser = parser
        self.ast = ast
        self.code = parser.code
        self.codelines = parser.code.split("\n")

    def formatExpr(self, expr):
        match expr:
            case {"type": "NumberLiteral"}:
                return expr["value"]
            case {"type": "StringLiteral"}:
                return expr["value"]
            case {"type": "BooleanLiteral"}:
                return expr["value"]
            case {"type": "VariableAccess"}:
                return expr["value"]
            case {"type": "Set", "items": items}:
                inside = ", ".join(self.formatToList(items))
                return f"set{{{inside}}}"

            case _:
                start = expr["positions"]["start"]
                end = expr["positions"]["end"]
                return self.getText(start, end)

    def getText(self, start, end, codelines=None):
        codelines = codelines or self.codelines
        l = []
        for i in range(start["line"] - 1, end["line"]):
            if i == start["line"] - 1:
                l.append(codelines[i][start["col"] - 1 :])
            elif i == end["line"]:
                l.append(codelines[i][: end["col"]])
            else:
                l.append(codelines[i])
        return "\n".join(l)

    def format(self, ast=None):
        ast = ast or self.ast
        if type(ast) != list:
            ast = ast["body"]
        text = ""
        for expr in ast:
            text += str(self.formatExpr(expr))
        return text

    def formatToList(self, ast=None):
        ast = ast or self.ast
        if type(ast) != list:
            ast = ast["body"]
        out = []
        for expr in ast:
            out.append(str(self.formatExpr(expr)))
        return out


def format(text):
    errorhandler = Error.ErrorHandler(text, "<main>", py_error=True, silenced=True)
    lexer = Lexer.Lexer("#", "#*", "*#", errorhandler, False)
    lexer.tokenize(text)
    parser = Parser.Parser(errorhandler, lexer)
    ast = parser.parse()
    formatter = Formatter(parser, ast, {})
    return formatter.format()


if __name__ == "__main__":
    # Needs to handle comments and everything too.
    text = """
  function x(y:String,z){return set {y,z}}"""
    print(format(text))

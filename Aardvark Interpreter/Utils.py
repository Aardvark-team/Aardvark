# I always forgot what indent im using so
#   Indent: spaces - 4

from sty import fg
import Error
import Lexer
import json
import Types


class FunctDict:
    def __init__(self, d):
        self.data = d

    def __getitem__(self, name):
        return self.data[name]()

    def __setitem__(self, name, value):
        self.data[name] = value

    def get(self, name, default):
        if name in self.data:
            return self[name]
        return default


def prettify_ast(ast, level=0, indent="  "):
    styles = Error.styles
    ind = level * indent
    ast = Types.adkToPy(ast)

    if isinstance(ast, int) or isinstance(ast, float):
        return styles["Number"] + str(ast) + fg.rs

    elif isinstance(ast, str):
        return styles["String"] + f'"{ast}"' + fg.rs

    elif isinstance(ast, bool):
        return styles["Boolean"] + str(ast) + fg.rs

    elif ast == None:
        return styles["Keyword"] + str(ast) + fg.rs

    elif isinstance(ast, list):
        repr = ind + styles["Delimiter"] + "[\n" + fg.rs
        for item in ast:
            for l in prettify_ast(item, level + 1, indent).split("\n"):
                repr += l + "\n"

        return (
            (ind + styles["Delimiter"] + "[]" + fg.rs)
            if len(ast) == 0
            else (repr + ind + styles["Delimiter"] + "]" + fg.rs)
        )

    elif isinstance(ast, dict):
        repr = ind + styles["Delimiter"] + "{\n" + fg.rs

        for k, v in ast.items():
            val_rep = prettify_ast(v, level + 1, indent).split("\n")

            repr += ind + indent + styles["String"] + f'"{k}"' + fg.rs + ": "

            for i, l in enumerate(val_rep):
                if i == 0:
                    l = l.lstrip()
                if i == len(val_rep) - 1:
                    l = l.rstrip()
                repr += l + "\n"

        return (
            (styles["Delimiter"] + "{}" + fg.rs)
            if len(ast.keys()) == 0
            else (repr + ind + styles["Delimiter"] + "}" + fg.rs)
        )
    elif type(ast) == Lexer.Token:
        return ind + styles["default"] + str(ast) + fg.rs
    else:
        return ind + styles["default"] + str(ast) + fg.rs
    raise Exception("Couldn't prettify " + str(ast) + " type " + str(type(ast)))


if __name__ == "__main__":
    import Lexer
    import Parser
    from Error import ErrorHandler

    text = """function exampleAst() -> int {}"""

    lexer = Lexer.Lexer("#", "#*", "*#", None, False)
    lexer.tokenize(text)

    parser = Parser.Parser(ErrorHandler(text, "<main>", py_error=True), lexer)

    ast = parser.parse()

    print(ast)
    print(prettify_ast(ast))

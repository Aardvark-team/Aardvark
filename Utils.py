# I always forgot what indent im using so
#   Indent: spaces - 4

from sty import fg
from Error import styles
from Lexer import Token
import json


def prettify_ast(ast, level=0, indent="  "):
    ind = level * indent

    if type(ast) == int or type(ast) == float:
        return styles["Number"] + str(ast) + fg.rs

    if type(ast) == str:
        return styles["String"] + f'"{ast}"' + fg.rs

    if type(ast) == bool:
        return styles["Boolean"] + str(ast) + fg.rs

    if ast == None:
        return styles["Keyword"] + str(ast) + fg.rs

    if type(ast) == list:
        repr = ind + styles["Delimiter"] + "[\n" + fg.rs
        for item in ast:
            for l in prettify_ast(item, level + 1, indent).split("\n"):
                repr += l + "\n"

        return (
            (ind + styles["Delimiter"] + "[]" + fg.rs)
            if len(ast) == 0
            else (repr + ind + styles["Delimiter"] + "]" + fg.rs)
        )

    if type(ast) == dict:
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

    if type(ast) == Token:
        return ind + styles["default"] + str(ast) + fg.rs

    raise Exception("Couldn't prettify " + str(ast) + " type " + str(type(ast)))


if __name__ == "__main__":
    import Lexer
    import Parser
    from Error import ErrorHandler

    text = """function exampleAst() -> int {}"""

    lexer = Lexer.Lexer("#", "</", "/>", None, False)
    lexer.tokenize(text)

    # print("".join([ str(x) for x in lexer.output ]))

    parser = Parser.Parser(ErrorHandler(text, "<main>", py_error=True), lexer)

    ast = parser.parse()

    print(ast)
    print(prettify_ast(ast))

from Data import TokenTypes, OrderOfOps, get_precedence
import Error
from sty import fg
from Types import Null
import random
import json

type_helper = {}

type_helper["Operator"] = "<operator>"
type_helper["Boolean"] = "<true | false>"
type_helper["Identifier"] = "<identifier>"
type_helper["LineBreak"] = "\n"
type_helper["Number"] = "<Number>"
type_helper["String"] = "<String>"
type_helper["ValueType"] = "<String | Int>"


def shift_ast_columns(ast, amount):
    ast["positions"]["start"]["col"] += amount
    ast["positions"]["end"]["col"] += amount

    for k, v in ast.items():
        if type(v) == dict and v.get("type", None):
            shift_ast_columns(v, amount)


eats = 0
compares = 0


class Parser:

    def __init__(self, err_handler, lexer, is_strict=False):
        self.code = lexer.data
        self.is_strict = is_strict
        self.codelines = self.code.split("\n")
        self.tokens = lexer.output
        self.pos = 0
        self.err_handler = err_handler
        self.lexer = lexer
        self.pyError = {}

    ## UTILITY

    # Get the next token

    def peek(self, n=0):
        tok = self.tokens[self.pos + n] if self.pos + n < len(self.tokens) else None
        return tok

    # Compare the next token with type, value

    def compare(self, Type, value=None, n=0):
        if self.isEOF():
            return False

        tok = self.peek(n)
        if type(Type) == str:
            Type = TokenTypes[Type]
        if tok and tok.type == Type and (value is None or value == tok.value):
            return True
        return False

    # Advance to the next token

    def advance(self):
        self.pos += 1

    def eatLBs(self):
        while self.compare("LineBreak"):
            self.advance()

    # Unexpected EOF

    def eofError(self, Type=None, value=None, is_type=False):
        last_tok = self.tokens[self.pos - 1]
        curr_line = self.err_handler.code.split("\n")[last_tok.line - 1]
        line_len = len(curr_line)
        value_type = (
            value
            if value
            else type_helper.get(
                (Type.name if Type else "any") if not is_type else "ValueType",
                "[no suggestion]",
            )
        )
        if type(value_type) == list:
            value_type = random.choice(value_type)

        replacement = " " + value_type
        curr_line = curr_line[:line_len].rstrip()
        line_end = replacement
        if self.pyError.get("type") == "Unexpected EOF":
            self.pyError = {}
            raise SyntaxError("Unexpected EOF")
        else:
            self.err_handler.throw(
                "Syntax",
                "Unexpected EOF.",
                {
                    "lineno": last_tok.line,
                    "marker": {"start": line_len + 1, "length": 1},
                    "underline": {"start": 0, "end": line_len + 1},
                    "did_you_mean": Error.Highlight(
                        curr_line, {"background": None, "linenums": None}
                    )
                    + Error.styles["suggestion"]
                    + line_end
                    + fg.rs,
                },
            )

    # Consume the current token if the types match, else throw an error

    def eat(self, Type="any", value=None, is_type=False):
        if type(Type) == str:
            Type = TokenTypes[Type]

        if self.compare(Type, value):
            curr = self.peek()
            self.advance()

            return curr

        # Raise an error
        if self.isEOF():
            return self.eofError(Type, value, is_type)

        next_tok = self.peek()
        curr_line = self.codelines[next_tok.line - 1].rstrip()
        line_len = len(curr_line)

        value_type = (
            value
            if value
            else type_helper.get(
                Type.name if not is_type else "ValueType", "[no suggestion]"
            )
        )
        if type(value_type) == list:
            value_type = random.choice(value_type)

        replacement = " " + value_type
        end_pos = max(next_tok.start["col"] + len(replacement), next_tok.end["col"] + 1)

        curr_line = (
            curr_line[: next_tok.start["col"] - 2]
            + replacement
            + curr_line[next_tok.start["col"] - 1 :]
        )
        if (
            self.pyError.get("type") == "Unexpected token"
            and (
                not self.pyError.get("token_value")
                or str(next_tok.value) in self.pyError.get("token_value", [])
            )
            and (
                not self.pyError.get("token_type")
                or str(next_tok.type) in self.pyError.get("token_type", [])
            )
        ):
            self.pyError = {}
            raise SyntaxError("Unexpected token")

        self.err_handler.throw(
            "Syntax",
            f'Unexpected {str(next_tok.type)}: "{str(next_tok.value)}"',
            {
                "lineno": next_tok.line,
                "marker": {
                    "start": next_tok.start["col"],
                    "length": next_tok.length + 1,
                },
                "underline": {"start": 0, "end": line_len},
                "did_you_mean": curr_line,
            },
        )

    # Is at the end of file

    def isEOF(self):
        return self.pos >= len(self.tokens)

    # Parse expression split by delimiter, until token type is reached,
    # closer should look like ( Type of token, Value of token )

    def parseListLike(self, delim, closer):
        items = []
        while self.peek() and not self.compare(*closer):
            self.eatLBs()
            if len(items) > 0:
                if not self.compare("Delimiter", delim):
                    tok = self.peek()
                    self.err_handler.throw(
                        "Syntax",
                        f"Invalid syntax, perhaps you forgot a {delim}?",
                        {
                            "lineno": tok.start["line"],
                            "marker": {"start": tok.start["col"], "length": len(delim)},
                            "underline": {
                                "start": tok.start["col"] - 2,
                                "end": tok.start["col"] + 2,
                            },
                            "did_you_mean": self.codelines[tok.start["line"] - 1][
                                : tok.start["col"] - 1
                            ]
                            + delim
                            + self.codelines[tok.start["line"] - 1][
                                tok.end["col"] - 1 :
                            ],
                        },
                    )
                self.eat(TokenTypes["Delimiter"], delim)
            self.eatLBs()
            if self.compare(*closer):
                return items
            items.append(self.pStatement(eatLBs=True))
            self.eatLBs()
        return items

    # Eats a list of statements contained in { and }

    def eatBlockScope(self):
        self.eatLBs()
        self.eat(TokenTypes["Delimiter"], "{")
        body = []
        while self.peek() and not self.compare(TokenTypes["Delimiter"], "}"):
            if len(body) > 0 and self.peek(-1).type != TokenTypes["LineBreak"]:
                self.eat(TokenTypes["LineBreak"])
            while self.compare(TokenTypes["LineBreak"]):
                self.advance()
            if self.compare(TokenTypes["Delimiter"], "}"):
                break

            body.append(self.pStatement())
        close = self.eat(TokenTypes["Delimiter"], "}")

        return body, close.end

    ## PARSER MAIN

    # Primary:
    # 	[number]
    # 	  [string]
    # 	[identifier]
    #   [boolean]
    #   FunctionDefinition
    #   FunctionCall

    def pPrimary(self, require=False, exclude=[], eatLBs=False):
        tok = self.peek()
        ast_node = None

        if not tok or self.isEOF():
            if require:
                self.eofError(
                    TokenTypes[random.choice(["String", "Number", "Identifier"])]
                )
            else:
                return None
        if (
            self.compare("Operator", "$")
            and self.peek(1)
            and self.peek(1).type == TokenTypes["String"]
            and self.peek().end["col"] == self.peek(1).start["col"] - 1
        ):
            start = self.eat(TokenTypes["Operator"])
            templ = self.eat(TokenTypes["String"])

            templ_val = templ.value
            replacements = []
            text = ""
            ind = 0
            while ind < len(templ_val):
                if (
                    templ_val[ind] == "{"
                    and ind + 1 < len(templ_val)
                    and templ_val[ind + 1] == "{"
                ):
                    ind += 2
                    text += "{"
                elif templ_val[ind] == "{":
                    starti = ind
                    inner = ""
                    ind += 1
                    opener_count = 1

                    while ind < len(templ_val) and opener_count > 0:
                        if templ_val[ind] == "{":
                            opener_count += 1
                        elif templ_val[ind] == "}":
                            opener_count -= 1
                        if opener_count == 0:
                            break
                        inner += templ_val[ind]
                        ind += 1
                    if opener_count > 0:
                        self.err_handler.throw(
                            "Syntax",
                            f"Template string never closed.",
                            {
                                "lineno": templ.line,
                                "marker": {
                                    "start": templ.start["col"] + ind,
                                    "length": 1,
                                },
                                "underline": {
                                    "start": start.start["col"],
                                    "end": templ.end["col"],
                                },
                                # TODO: add a suggestion
                            },
                        )
                    if inner == "":
                        self.err_handler.throw(
                            "Syntax",
                            "Template string cannot be empty.",
                            {
                                "lineno": templ.line,
                                "marker": {
                                    "start": templ.start["col"] + ind,
                                    "length": 1,
                                },
                                "underline": {
                                    "start": start.start["col"],
                                    "end": templ.end["col"],
                                },
                            },
                        )

                    self.lexer.reset()
                    self.lexer.tokenize(inner)
                    inner_toks = self.lexer.output

                    saved_pos = self.pos
                    saved_code = self.err_handler.code
                    saved_toks = self.tokens

                    self.err_handler.code = inner
                    self.err_handler.codelines = [inner]
                    self.tokens = inner_toks
                    self.pos = 0
                    inner_ast = self.pExpression(require=True)

                    shift_ast_columns(inner_ast, templ.start["col"] + ind)

                    self.pos = saved_pos
                    self.tokens = saved_toks
                    self.err_handler.code = saved_code
                    self.err_handler.codelines = saved_code.split("\n")

                    replacements.append(
                        {"from": starti, "to": ind, "value": inner_ast, "string": inner}
                    )

                else:
                    text += templ_val[ind]

                ind += 1

            return {
                "type": "TemplateString",
                "value": templ.value,
                "replacements": replacements,
                "positions": {
                    "start": start.start,
                    "end": {"line": templ.end["line"], "col": templ.end["col"] - 2},
                },
            }

        elif self.compare("Keyword", "lambda") and self.compare("Delimiter", "(", 1):
            self.eat("Keyword", "lambda")
            ast_node = self.pFunctionDefinition(assignment=True, anonymous=True)
        if tok.type == TokenTypes["String"]:
            self.eat(tok.type)
            ast_node = {
                # StringLiteral, NumberLiteral, etc...
                "type": tok.type.name + "Literal",
                "value": tok.value,
                "positions": {"start": tok.start, "end": tok.end},
                "tokens": {"value": tok},
            }

        elif tok.type == TokenTypes["Number"]:
            self.eat(tok.type)
            value = tok.value
            if "." in tok.value:
                value = float(value)
            else:
                value = int(value)
            ast_node = {
                "type": "NumberLiteral",
                "value": value,
                "positions": {"start": tok.start, "end": tok.end},
                "tokens": {"value": tok},
            }
            if (
                self.compare("Identifier")
                and self.peek().start["col"] == ast_node["positions"]["end"]["col"] + 1
            ):
                value = self.pExpression(2, True)
                ast_node = {
                    "type": "Multiply",
                    "number": ast_node,
                    "value": value,
                    "positions": {
                        "start": ast_node["positions"]["start"],
                        "end": value["positions"]["end"],
                    },
                }

        elif tok.type == TokenTypes["Boolean"]:
            self.eat(tok.type)

            ast_node = {
                "type": "BooleanLiteral",
                "value": tok.value == "true",
                "positions": {"start": tok.start, "end": tok.end},
                "tokens": {"value": tok},
            }

        elif tok.type == TokenTypes["Delimiter"] and tok.value == "{":
            if self.is_strict:
                self.err_handler.throw(
                    "Strict",
                    "Objects are not allowed in strict mode.",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 1},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            ast_node = self.pObject()

        elif tok.type == TokenTypes["Delimiter"] and tok.value == "[":
            ast_node = self.pArray()
        elif self.compare("Keyword", "set") and self.compare("Delimiter", "{", 1):
            self.eat("Keyword")
            ast_node = self.pSet(tok)

        elif tok.type == TokenTypes["Identifier"]:
            self.eat(tok.type)
            ast_node = {
                "type": "VariableAccess",
                "value": tok.value,
                "positions": {"start": tok.start, "end": tok.end},
            }

        elif tok.type == TokenTypes["Delimiter"] and tok.value == "(":
            self.eat("Delimiter")
            ast_node = self.pStatement(eatLBs=True)
            self.eat("Delimiter", ")")

        # Dynamic include
        elif (
            tok.type == TokenTypes["Keyword"]
            and tok.value == "include"
            and self.peek(1).type == TokenTypes["Delimiter"]
            and self.peek(1).value == "("
            and self.peek(1).start["col"] == tok.end["col"] + 1
        ):
            if self.is_strict:
                self.err_handler.throw(
                    "Strict",
                    "Dynamic includes are not allowed in strict mode.",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 7},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            keyw = self.eat("Keyword")
            ast_node = self.pFunctionCall(
                {
                    "type": "VariableAccess",
                    "value": "include",
                    "positions": {"start": keyw.start, "end": keyw.end},
                }
            )

        elif self.compare("Keyword", "structure"):
            ast_node = self.pStructure()

        elif self.compare("Keyword", "template"):
            ast_node = self.pTemplate()

        elif self.compare("Keyword", "option"):
            ast_node = self.pOption()

        elif tok.type == TokenTypes["Keyword"] and tok.value == "function":
            if self.is_strict:
                self.err_handler.throw(
                    "Strict",
                    "Functions declared with `function` are not allowed in strict mode. Declare your functions with `let f(x) { ... }`",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 8},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            ast_node = self.pFunctionDefinition()

        elif tok.type == TokenTypes["Keyword"] and tok.value == "class":
            if self.is_strict:
                self.err_handler.throw(
                    "Strict",
                    "Classes are depreciated and are not allowed in strict mode.",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 4},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            ast_node = self.pClassDefinition()

        # elif self.compare("Keyword", "structure"):
        #     ast_node = self.pStructureDefinition()

        while ast_node:
            if eatLBs:
                self.eatLBs()
            while self.compare(TokenTypes["Delimiter"], "."):
                if eatLBs:
                    self.eatLBs()
                dot = self.eat(TokenTypes["Delimiter"])
                property = None
                self.eatLBs()
                if self.peek() == None:
                    return self.eofError(TokenTypes["Identifier"])
                if self.compare("Identifier"):
                    tok = self.eat("Identifier")
                    property = {
                        "type": "StringLiteral",
                        "value": tok.value,
                        "positions": {
                            "start": tok.start,
                            "end": tok.end,
                        },
                    }
                elif self.compare("String"):
                    tok = self.eat("String")
                    property = {
                        "type": "StringLiteral",
                        "value": tok.value,
                        "positions": {
                            "start": tok.start,
                            "end": tok.end,
                        },
                    }
                elif self.compare("Number"):
                    tok = self.eat("Number")
                    property = {
                        "type": "NumberLiteral",
                        "value": float(tok.value),
                        "positions": {
                            "start": tok.start,
                            "end": tok.end,
                        },
                    }
                elif self.compare("Operator", "$"):
                    self.eat("Operator")
                    tok = self.eat("Identifier")
                    property = {
                        "type": "VariableAccess",
                        "value": tok.value,
                        "positions": {
                            "start": tok.start,
                            "end": tok.end,
                        },
                    }
                elif self.compare("Delimiter", "("):
                    self.eat("Delimiter")
                    property = self.pStatement(eatLBs=True)
                    self.eat("Delimiter", ")")
                elif self.compare("Operator", "-"):
                    op = self.eat("Operator")
                    tok = self.eat("Number")
                    property = {
                        "type": "Operator",
                        "operator": "-",
                        "left": None,
                        "right": {
                            "type": "NumberLiteral",
                            "value": tok.value,
                            "positions": {
                                "start": tok.start,
                                "end": tok.end,
                            },
                        },
                        "positions": {
                            "start": op.start,
                            "end": tok.end,
                        },
                    }
                else:
                    self.err_handler.throw(
                        "Syntax",
                        "Unexpected End Of Expression",
                        {
                            "lineno": dot.end["line"],
                            "marker": {"start": dot.end["col"], "length": 2},
                            "underline": {
                                "start": dot.end["col"],
                                "end": len(self.codelines[dot.end["line"] - 1]),
                            },
                            "did_you_mean": Error.Highlight(
                                self.codelines[dot.end["line"] - 1],
                                {"background": None, "linenums": False},
                            )
                            + Error.styles["suggestion"]
                            + "<value>"
                            + fg.rs,
                        },
                    )
                if property == None:
                    self.err_handler.throw(
                        "Syntax",
                        "Cannot get empty property",
                        {
                            "lineno": dot.end["line"],
                            "marker": {"start": dot.end["col"], "length": 2},
                            "underline": {
                                "start": dot.end["col"],
                                "end": len(self.codelines[dot.end["line"] - 1]),
                            },
                            "did_you_mean": Error.Highlight(
                                self.codelines[dot.end["line"] - 1],
                                {"background": None, "linenums": False},
                            )
                            + Error.styles["suggestion"]
                            + "<value>"
                            + fg.rs,
                        },
                    )
                ast_node = {
                    "type": "PropertyAccess",
                    "property": property,
                    "value": ast_node,
                    "positions": {
                        "start": ast_node["positions"]["start"],
                        "end": property["positions"]["end"],
                    },
                }
                if eatLBs:
                    self.eatLBs()
                continue  # Check for others
            # Indexes
            if self.compare("Delimiter", "["):
                if self.is_strict:
                    self.err_handler.throw(
                        "Syntax",
                        "Indexing via brackets is not allowed in strict mode. Use `.()`.",
                        {
                            "lineno": ast_node["positions"]["start"]["line"],
                            "marker": {
                                "start": ast_node["positions"]["start"]["col"],
                                "length": 1,
                            },
                            "underline": {
                                "start": ast_node["positions"]["start"]["col"],
                                "end": ast_node["positions"]["end"]["col"],
                            },
                        },
                    )
                self.eat("Delimiter")
                property = self.pExpression(eatLBs=True)
                self.eat("Delimiter", "]")
                ast_node = {
                    "type": "PropertyAccess",
                    "property": property,
                    "value": ast_node,
                    "positions": {
                        "start": ast_node["positions"]["start"],
                        "end": (
                            property["positions"]["end"]
                            if property
                            else ast_node["positions"]["end"]
                        ),
                    },
                }
                continue  # Check for others
            # Structure creation from template.
            if self.compare("Delimiter", ":") and self.compare("Delimiter", "{", 1):
                self.eat("Delimiter")
                ast_node = self.pTemplateInit(ast_node)
            # Function calls
            if (
                self.compare(TokenTypes["Delimiter"], "(")
                and self.peek().start["col"] == ast_node["positions"]["end"]["col"] + 1
            ):
                ast_node = self.pFunctionCall(ast_node)
                continue  # Check for others
            # Inline ifs
            if self.compare(TokenTypes["Keyword"], "if") and "if" not in exclude:
                if_ast = self.pIfStatement(True)
                if_ast["body"] = ast_node
                ast_node = if_ast
            # inline fors
            if self.compare("Keyword", "for") and "for" not in exclude:
                for_ast = self.pForLoop(True)
                for_ast["body"] = ast_node
                ast_node = for_ast
            if self.compare("Keyword", "while") and "while" not in exclude:
                while_ast = self.pWhileLoop(True)
                while_ast["body"] = ast_node
                ast_node = while_ast

            return ast_node

        if require:
            # Throw an error
            self.err_handler.throw(
                "Syntax",
                "Unexpected End Of Expression",
                {
                    "lineno": tok.end["line"],
                    "marker": {"start": tok.end["col"], "length": 1},
                    "underline": {
                        "start": tok.end["col"],
                        "end": len(self.codelines[tok.end["line"] - 1]),
                    },
                    "did_you_mean": Error.Highlight(
                        self.codelines[tok.end["line"] - 1],
                        {"background": None, "linenums": False},
                    )
                    + Error.styles["suggestion"]
                    + " <statement>"
                    + fg.rs,
                },
            )
            raise Exception(
                f"Unexpected token {tok.type.name.upper()}, expected STRING, NUMBER,"
                " ARRAY, SET, FUNCTION CALL or IDENTIFIER."
            )

    # Expression:

    def pExpression(
        self, level=len(OrderOfOps) - 1, require=False, exclude=[], eatLBs=False
    ):
        # TODO: only make a list of values and operators and handle it at execution using Operators.py
        if level < 0:
            left = self.pPrimary(require=False, exclude=exclude, eatLBs=eatLBs)
        else:
            left = self.pExpression(
                level - 1, require=False, exclude=exclude, eatLBs=eatLBs
            )
        if eatLBs:
            self.eatLBs()
        if "$" not in exclude:
            exclude.append("$")
        while (
            self.compare("Operator")
            and level in OrderOfOps
            and self.peek().value in OrderOfOps[level]
            and self.peek().value not in exclude
        ):
            op = self.eat("Operator")
            if eatLBs:
                self.eatLBs()
            right = self.pExpression(
                level - 1, require=False, exclude=exclude, eatLBs=eatLBs
            )
            if not left and not right:
                # Just an operator by itself.
                self.err_handler.throw(
                    "Syntax",
                    "Why is there an operator there just by itself? It makes no sense.",
                    {
                        "lineno": op.start["line"],
                        "underline": {
                            "start": op.start["col"],
                            "end": op.end["col"] + 1,
                        },
                        "marker": {"start": op.start["col"], "length": len(op.value)},
                    },
                )

            left = {
                "type": "Operator",
                "left": left,
                "right": right,
                "operator": op.value,
                "positions": {
                    "start": (left or {}).get("positions", {}).get("start", op.start),
                    "end": (right or {})
                    .get("positions", {})
                    .get("end", op.end),  # to handle if there is no right
                },
            }
        if left == None and require:
            if level < 0:
                left = self.pPrimary(require=require, exclude=exclude, eatLBs=eatLBs)
            else:
                left = self.pExpression(
                    level - 1, require=require, exclude=exclude, eatLBs=eatLBs
                )
        return left

    # Object:
    # 	{ [string] : Expression (, [string] : Expression ) }

    def pObject(self, no_error=False):
        starter = self.eat(TokenTypes["Delimiter"], "{")
        obj = {}
        while (
            self.peek()
            and not self.compare(TokenTypes["Delimiter"], "}")
            and not (self.compare("Delimiter", ",") and self.peek(1).value == "}")
        ):
            self.eatLBs()
            if len(obj.keys()) > 0:
                if no_error and not self.compare("Delimiter", ","):
                    return False
                else:
                    self.eat("Delimiter", ",")

            self.eatLBs()
            if self.compare("Delimiter", "}"):
                break

            name = None
            name_pos = None

            if self.compare("Operator", "..."):
                self.eat("Operator")
                obj[("...",)] = ("...", self.pExpression(eatLBs=True))
                continue
            elif self.compare("Identifier") or self.compare("String"):
                if self.compare("String"):
                    tok = self.eat("String")
                else:
                    tok = self.eat("Identifier")
                name = tok.value
                name_pos = tok
            elif self.compare("Number"):
                tok = self.eat("Number")
                name = float(tok.value)
                name_pos = tok
            elif no_error:
                return False
            else:
                self.err_handler.throw(
                    "Syntax",
                    "Expected Object key.",
                    {
                        "lineno": self.peek().start["line"],
                        "underline": {
                            "start": self.peek().start["col"],
                            "end": self.peek().end["col"],
                        },
                        "marker": {
                            "start": self.peek().start["col"],
                            "length": len(self.peek().value),
                        },
                    },
                )

            self.eatLBs()
            if self.compare("Delimiter", ":"):
                self.eat(TokenTypes["Delimiter"], ":")
                self.eatLBs()
                value = self.pStatement(eatLBs=True)
                self.eatLBs()
            else:
                value = {
                    "type": "VariableAccess",
                    "value": name,
                    "positions": {"start": name_pos.start, "end": name_pos.end},
                }
            obj[name] = value
        if self.compare("Delimiter", ","):
            self.eat("Delimiter")
        closing_par = self.eat(TokenTypes["Delimiter"], "}")

        return {
            "type": "Object",
            "pairs": obj,
            "positions": {"start": starter.start, "end": closing_par.end},
        }

    # Array:
    # 	[ Expression ( , Expression ) ]

    def pArray(self):
        starter = self.eat(TokenTypes["Delimiter"], "[")
        items = self.parseListLike(",", (TokenTypes["Delimiter"], "]"))
        closing_par = self.eat(TokenTypes["Delimiter"], "]")

        return {
            "type": "Array",
            "items": items,
            "positions": {"start": starter.start, "end": closing_par.end},
        }

    # Set:
    # 	{ Expression ( , Expression ) }

    def pSet(self, starter):
        self.eat(TokenTypes["Delimiter"], "{")
        items = self.parseListLike(",", (TokenTypes["Delimiter"], "}"))
        closing_par = self.eat(TokenTypes["Delimiter"], "}")

        return {
            "type": "Set",
            "items": items,
            "positions": {"start": starter.start, "end": closing_par.end},
        }

    # FunctionCall:
    # 	[identifier] ( Expression ( , Expression ) )

    def pFunctionCall(self, ast_node):
        self.eat(TokenTypes["Delimiter"], "(")
        arguments = []
        keywordArguments = {}
        while (
            self.compare("Delimiter", ",")
            or (len(arguments) == 0 and len(keywordArguments) == 0)
            and not self.compare("Delimiter", ")")
        ):
            self.eatLBs()
            if self.compare("Delimiter", ","):
                self.eat("Delimiter", ",")
            self.eatLBs()
            KorV = self.pExpression(eatLBs=True)
            if KorV["type"] == "Operator" and KorV["operator"] == "=":
                if not (KorV["left"] and KorV["left"]["type"] == "VariableAccess"):
                    self.err_handler.throw(
                        "Syntax",
                        "Cannot use an expression as a key.",
                        {
                            "lineno": KorV["positions"]["start"]["line"],
                            "marker": {
                                "start": KorV["positions"]["start"]["col"],
                                "length": KorV["positions"]["end"]["col"]
                                - KorV["positions"]["start"]["col"],
                            },
                            "underline": {
                                "start": KorV["positions"]["start"]["col"],
                                "end": KorV["positions"]["end"]["col"],
                            },
                        },
                    )
                key = KorV["left"]["value"]
                value = KorV["right"]
                if key in keywordArguments:
                    self.err_handler.throw(
                        "Argument",
                        "Duplicate keyword arguments.",
                        {
                            "lineno": KorV["positions"]["start"]["line"],
                            "marker": {
                                "start": KorV["positions"]["start"]["col"],
                                "length": len(key),
                            },
                            "underline": {
                                "start": KorV["positions"]["start"]["col"],
                                "end": value["positions"]["end"]["col"],
                            },
                        },
                    )
                keywordArguments[key] = value
            else:
                arguments.append(KorV)
        self.eatLBs()
        closing_par = self.eat(TokenTypes["Delimiter"], ")")

        return {
            "type": "FunctionCall",
            "function": ast_node,
            "arguments": arguments,
            "keywordArguments": keywordArguments,
            "tokens": {},
            "positions": {
                "start": ast_node["positions"]["start"],
                "end": closing_par.end,
            },
        }

    # pFunctionDefinition:
    # 	function [identifier] ( [identifier] [identifier] ( , [identifier] [identifier] ) )

    def pFunctionDefinition(self, special=False, assignment=False, anonymous=False):
        starter = None
        name = None
        parameters = []
        is_static = False
        if not (special or assignment) and not anonymous:
            if self.compare("Keyword", "static"):
                starter = self.eat("Keyword", "static").start
                self.eat(TokenTypes["Keyword"], "function")
                is_static = True
            else:
                starter = self.eat("Keyword", "function").start
        if self.compare("Identifier"):
            name = self.eat(TokenTypes["Identifier"])
        if not starter and name:
            starter = name.start
        if self.compare("Delimiter", "("):
            openparen = self.eat(TokenTypes["Delimiter"], "(")
            if special and not starter:
                starter = openparen.start
            while self.peek() and not self.compare(TokenTypes["Delimiter"], ")"):
                var_type = None
                var_name = None
                absorb = False
                is_ref = False
                is_static = False
                var_default = None
                is_optional = False
                self.eatLBs()
                if len(parameters) > 0:
                    self.eat(TokenTypes["Delimiter"], ",")
                self.eatLBs()
                if self.compare("Operator", "..."):
                    self.eat("Operator")
                    absorb = True
                if self.compare("Operator", "@"):
                    self.eat()
                    is_ref = True
                if self.compare("Keyword", "static"):
                    self.eat()
                    is_static = True
                if self.compare("Delimiter", "["):
                    var_type = self.pArray()
                    var_name = self.eat("Identifier")
                if self.compare("Delimiter", "("):
                    var_type = self.pExpression(require=True)
                    var_name = self.eat("Identifier")
                else:
                    temp = self.eat("Identifier")
                    if self.compare("Identifier"):
                        var_type = {
                            "type": "VariableAccess",
                            "value": temp.value,
                            "positions": {"start": temp.start, "end": temp.end},
                        }
                        var_name = self.eat("Identifier")
                    else:
                        var_name = temp
                if self.compare("Operator", "?"):
                    self.eat("Operator")
                    is_optional = True
                self.eatLBs()
                if self.compare("Operator", "="):
                    self.eat("Operator")
                    self.eatLBs()
                    var_default = self.pExpression()
                # TODO: Add modes to not parse , or something
                self.eatLBs()

                parameters.append(
                    {
                        "type": "Parameter",
                        "name": var_name.value,
                        "value_type": var_type,
                        "default": var_default,
                        "absorb": absorb,
                        "is_ref": is_ref,
                        "is_static": is_static,
                        "is_optional": is_optional,
                        "positions": {
                            "start": (
                                var_type["positions"]["start"]
                                if var_type
                                else var_name.start
                            ),
                            "end": var_name.end,
                        },
                    }
                )
                if absorb:
                    break

            self.eat(TokenTypes["Delimiter"], ")")
        AS = None
        if self.compare(TokenTypes["Keyword"], "as"):
            self.eat(TokenTypes["Keyword"], "as")
            tok = self.eat(TokenTypes["Identifier"])
            AS = tok.value
            if not starter:
                starter = tok.start

        return_type = None
        if self.compare("Operator", "->"):
            self.eat(TokenTypes["Operator"], "->")
            return_type = self.pExpression()
            if not starter:
                starter = return_type["positions"]["start"]
        self.eatLBs()
        inline = None
        if assignment and self.compare("Operator", "="):
            self.eat("Operator")
            inline = True
            body = self.pStatement(require=True)
            lasti = body["positions"]["end"]
        else:
            if self.compare("Delimiter", "{"):
                old = self.pos
                inline = True
                body = self.pObject(True)
                if body == False:
                    self.pos = old
                    body, lasti = self.eatBlockScope()
                    inline = False
                else:
                    lasti = body["positions"]["end"]
            else:
                body = self.pStatement(require=True)
                lasti = body["positions"]["end"]
                inline = True

            # self.pyError = {"type": "Unexpected token", "token_value": [":", "$", ","]}
            # try:
            #     body, lasti = self.eatBlockScope()
            #     inline = False
            # except:
            #     self.pos = old
            #     body = self.pStatement(require=True)
            #     lasti = body["positions"]["end"]
            #     inline = True

        return {
            "type": "FunctionDefinition",
            "name": name.value if name else "",
            "is_anonymous": name is None,
            "parameters": parameters,
            "special": special,
            "is_static": is_static,
            "body": body,
            "as": AS,
            "inline": inline,
            "return_type": return_type,
            "positions": {"start": starter, "end": lasti},
        }

    # ExtendingStatement:
    #    extending Object

    def pExtendingStatement(self):
        starter = self.eat("Keyword", "extending")

        if not self.compare("Operator"):
            obj_name = self.eat("Identifier")

            if self.compare("Delimiter", "{"):
                obj = self.pObject()
            elif self.compare("Delimiter", "["):
                obj = self.pArray()
            elif self.compare("Identifier", "set"):
                self.eat("Identifier")
                obj = self.pSet(self.peek())
            else:
                raise Exception(
                    "Syntax error: Unexpected token " + str(self.peek().type).upper()
                )
            return {
                "type": "ExtendingStatement",
                "kind": "name",
                "name": obj_name.value,
                "object": obj,
                "positions": {"start": starter.start, "end": obj["positions"]["end"]},
            }

        operator = self.eat("Operator")
        params = []

        self.eat("Delimiter", "(")
        params.append((self.eat("Identifier"), self.eat("Identifier")))
        self.eat("Delimiter", ",")

        second_type = None
        if self.compare("Identifier") and self.peek(1).type == TokenTypes["Identifier"]:
            second_type = self.eat("Identifier")

        params.append((second_type, self.eat("Identifier")))
        self.eat("Delimiter", ")")

        body, end = self.eatBlockScope()

        return {
            "type": "ExtendingStatement",
            "kind": "operator",
            "operator": operator.value,
            "params": params,
            "body": body,
            "positions": {"start": operator.start, "end": end},
        }

    # ReturnStatement:
    # 	return Expression

    def pReturnStatement(self):
        starter = self.eat(TokenTypes["Keyword"], "return")
        return_value = self.pStatement(eatLBs=False)
        return {
            "type": "ReturnStatement",
            "value": return_value,
            "positions": {
                "start": starter.start,
                "end": (
                    return_value["positions"]["end"] if return_value else starter.end
                ),
            },
        }

    # WhileLoop:
    # 	while condition BlockScope
    # 	while condition Statement

    def pWhileLoop(self, inline=False):
        starter = self.eat(TokenTypes["Keyword"], "while")
        condition = self.pExpression(require=True)
        body = None
        lasti = condition["positions"]["end"]
        if not inline:
            self.eatLBs()
            if self.compare(TokenTypes["Delimiter"], "{"):
                body, lasti = self.eatBlockScope()
            else:
                statm = self.pStatement()
                body = [statm]
                lasti = statm["positions"]["end"]
        return {
            "type": "WhileLoop",
            "condition": condition,
            "body": body,
            "positions": {"start": starter.start, "end": lasti},
        }

    # IfStatement:
    # 	if condition BlockScope [ else BlockScope ]
    #   if condition BlockScope [ else Statement ]

    def pIfStatement(self, inline=False):
        starter = self.eat(TokenTypes["Keyword"], "if")
        condition = self.pExpression(require=True)
        body = None
        lasti = condition["positions"]["end"]
        self.eatLBs()
        if self.compare("Delimiter", "{") and not inline:
            body, lasti = self.eatBlockScope()
        elif not inline:
            statm = self.pStatement(True)
            body = [statm]
            lasti = statm["positions"]["end"]
        closing_pos = lasti
        else_body = None
        self.eatLBs()
        if self.compare(TokenTypes["Keyword"], "else"):
            self.eat(TokenTypes["Keyword"])
            self.eatLBs()
            if self.compare(TokenTypes["Delimiter"], "{"):
                else_body, lasti = self.eatBlockScope()
                closing_pos = lasti
            else:
                else_body = [self.pStatement()]
                closing_pos = else_body[0]["positions"]["end"]

        return {
            "type": "IfStatement",
            "condition": condition,
            "body": body,
            "else_body": else_body,
            "positions": {"start": starter.start, "end": closing_pos},
        }

    # Delete Keyword:

    def pDelete(self):
        starter = self.eat(TokenTypes["Keyword"], "delete")
        target = self.pExpression(require=True)
        return {
            "type": "DeleteStatement",
            "target": target,
            "positions": {"start": starter.start, "end": target["positions"]["end"]},
        }

    # For loop:

    def pForLoop(self, inline=False):
        starter = self.eat("Keyword", "for")
        declarations = []
        # { ..., declarations: [ { type: "destructure", names: [ "k", "v" ] } ] }
        while self.compare("Identifier"):
            x = self.eat(TokenTypes["Identifier"])
            if self.compare(TokenTypes["Delimiter"], ","):
                self.eat("Delimiter")
                declarations.append({"type": "variable", "names": [x.value]})
            elif self.compare(TokenTypes["Delimiter"], ":"):
                self.eat("Delimiter")
                declarations.append(
                    {
                        "type": "destructure",
                        "names": [x.value, self.eat("Identifier").value],
                    }
                )
                if self.compare("Delimiter", ","):
                    self.eat("Delimiter")
            else:
                declarations.append({"type": "variable", "names": [x.value]})
                break
        self.eat("Operator", "in")
        iterable = self.pExpression(exclude=["for"])  # Get the iterable.
        self.eatLBs()
        body = None
        lasti = iterable["positions"]["end"]
        if not inline:
            if self.compare("Delimiter", "{"):
                body, lasti = self.eatBlockScope()
            else:
                body = [self.pStatement(require=True)]
                lasti = body[0]["positions"]["end"]
        return {
            "type": "ForLoop",
            "declarations": declarations,
            "iterable": iterable,
            "body": body,
            "positions": {"start": starter.start, "end": lasti},
        }

    # ClassScope:
    #     { FunctionDefinition(is_class_method = True)* }

    def pClassScope(self):
        starter = self.eat("Delimiter", "{")
        body = []

        while not self.compare("Delimiter", "}") and self.peek():
            if len(body) > 0 and self.peek(-1).type != TokenTypes["LineBreak"]:
                self.eat(TokenTypes["LineBreak"])
            self.eatLBs()
            if self.compare("Operator", "$"):
                self.eat("Operator")
                body.append(self.pFunctionDefinition(True))
            body.append(self.pStatement())

        closer = self.eat("Delimiter", "}")

        return body, closer.end

    # ClassDefinition:
    #     class [identifier] [ extends [identifier] ] ClassScope

    def pClassDefinition(self):
        if self.compare("Keyword", "static"):
            starter = self.eat("Keyword", "static")
            self.eat(TokenTypes["Keyword"], "class")
            is_static = True
        else:
            is_static = False
            starter = self.eat("Keyword", "class")
        name = None
        extends = []
        AS = None

        if self.compare(TokenTypes["Identifier"]):
            name = self.eat(TokenTypes["Identifier"]).value

        if self.compare("Keyword", "extends"):
            self.eat("Keyword", "extends")
            extends.append(self.eat(TokenTypes["Identifier"]))
            while self.compare("Delimiter", ","):
                self.eat("Delimiter")
                extends.append(self.eat(TokenTypes["Identifier"]))

        if self.compare("Keyword", "as"):
            self.eat("Keyword", "as")
            AS = self.eat(TokenTypes["Identifier"]).value

        body, lasti = self.pClassScope()

        return {
            "type": "ClassDefinition",
            "name": name,
            "is_static": is_static,
            "is_anonymous": name is None,
            "extends": extends,
            "body": body,
            "as": AS,
            "positions": {
                "start": starter.start,
                "end": lasti,
            },
        }

    # IncludeStatement:
    #     include [identifier/string]
    #     include [identifier/string] as [identifier]
    #     include [identifier] [ as [identifier] ] from [identifier]
    #     from [identifier] include [identifier]
    #     from [identifier] include [identifier] as [identifier]

    def pIncludeStatement(self):
        if self.compare("Keyword", "include"):
            keyw = self.eat("Keyword", "include")
            if (
                self.compare("Delimiter", "(")
                and self.peek().start["col"] == keyw.end["col"] + 1
            ):
                # Dynamic include
                return self.pFunctionCall(
                    {
                        "type": "VariableAccess",
                        "value": "include",
                        "positions": {"start": keyw.start, "end": keyw.end},
                    }
                )
            if self.compare("String"):
                lib_or_start = self.eat("String")
            else:
                lib_or_start = self.eat("Identifier")
            included_parts = [[lib_or_start.value, lib_or_start.value]]

            # Include without as / from
            if self.isEOF() or self.compare("LineBreak"):
                return {
                    "type": "IncludeStatement",
                    "lib_name": lib_or_start.value,
                    "local_name": lib_or_start.value,
                    "included": "ALL",
                    "positions": {"start": keyw.start, "end": lib_or_start.end},
                    "tokens": {"lib_name": lib_or_start},
                }

            # Include as
            if self.compare("Keyword", "as"):
                self.eat("Keyword", "as")
                local_name = self.eat("Identifier")

                if self.isEOF() or self.compare("LineBreak"):
                    return {
                        "type": "IncludeStatement",
                        "lib_name": lib_or_start.value,
                        "local_name": local_name.value,
                        "included": "ALL",
                        "positions": {"start": keyw.start, "end": local_name.end},
                        "tokens": {"lib_name": lib_or_start},
                    }

                # We predicted the wrong type of include so replace the included parts
                included_parts[0][1] = local_name.value

            while not self.compare("Keyword", "from"):
                # We already have 1 included part so we can always eat a new comma
                self.eat("Delimiter", ",")
                name = self.eat("Identifier")
                local_name = name

                if self.compare("Keyword", "as"):
                    self.eat("Keyword", "as")
                    local_name = self.eat("Identifier")

                included_parts.append([name.value, local_name.value])

            self.eat("Keyword", "from")
            if self.compare("String"):
                lib_name = self.eat("String")
            else:
                lib_name = self.eat("Identifier")
            created_obj = {}

            for part_name, part_local in included_parts:
                created_obj[part_name] = {"local": part_local}
            end = lib_name.end
        else:
            keyw = self.eat("Keyword", "from")
            if self.compare("String"):
                lib_name = self.eat("String")
            else:
                lib_name = self.eat("Identifier")
            self.eat("Keyword", "include")
            created_obj = {}

            while self.compare("Delimiter", ",") or len(created_obj) == 0:
                if self.compare("Delimiter", ","):
                    self.eat("Delimiter")
                item = self.eat("Identifier")
                local_name = item
                end = item.end
                if self.compare("Keyword", "as"):
                    self.eat("Keyword")
                    local_name = self.eat("Identifier")
                    end = local_name.end
                created_obj[item.value] = {"local": local_name.value}

        return {
            "type": "IncludeStatement",
            "lib_name": lib_name.value,
            "local_name": lib_name.value,
            "included": created_obj,
            "positions": {"start": keyw.start, "end": end},
            "tokens": {"lib_name": lib_name},
        }

    def pSPMObject(self):
        starter = self.eat(TokenTypes["Delimiter"], "{")
        obj = {}
        while self.peek() and not self.compare(TokenTypes["Delimiter"], "}"):
            self.eatLBs()
            if len(obj.keys()) > 0:
                self.eat(TokenTypes["Delimiter"], ",")
            self.eatLBs()

            name = None

            if self.compare(TokenTypes["Identifier"]):
                name = self.eat(TokenTypes["Identifier"]).value
            elif self.compare("Number"):
                name = self.eat("Number").value
            elif self.compare("String"):
                name = self.eat("String").value
            elif (
                self.compare("Operator", "$")
                and self.peek(1).type == TokenTypes["Identifier"]
                and self.peek(1).start["col"] == self.peek().start["col"] + 1
            ):
                self.eat("Operator")
                name = self.eat("Identifier").value
                obj[name] = ("Define", name)
                self.eatLBs()
                continue
            self.eatLBs()
            self.eat(TokenTypes["Delimiter"], ":")
            self.eatLBs()
            if (
                self.compare("Operator", "$")
                and self.peek(1).type == TokenTypes["Identifier"]
                and self.peek(1).start["col"] == self.peek().start["col"] + 1
            ):
                self.eat("Operator")
                value = ("Define", self.eat("Identifier").value)
            else:
                value = ("Compare", self.pStatement())
            self.eatLBs()
            obj[name] = value

        closing_par = self.eat(TokenTypes["Delimiter"], "}")

        return {
            "type": "SPMObject",
            "pairs": obj,
            "positions": {"start": starter.start, "end": closing_par.end},
        }

    # Statement:
    #   Case

    def pCaseStatement(self):
        starter = self.eat("Keyword", "case")
        compare = None
        special = None
        if self.compare("Delimiter", "{"):
            compare = self.pSPMObject()
        elif self.compare("Operator", "$"):
            self.eat("Operator")
            special = self.eat("Identifier").value
        else:
            compare = self.pExpression()
        # ADD the case in y, case == 5 later

        if self.compare("Delimiter", "{"):
            body, lasti = self.eatBlockScope()
        else:
            body = [self.pStatement(require=True)]
            lasti = body[0]["positions"]["end"]
        return {
            "type": "CaseStatement",
            "compare": compare,
            "body": body,
            "special": special,
            "positions": {"start": starter.start, "end": lasti},
        }

    # Statement Switch

    def pSwitchCase(self):
        if self.compare("Keyword", "match"):
            starter = self.eat("Keyword", "match")
        else:
            starter = self.eat("Keyword", "switch")
        value = self.pExpression()
        self.eat("Delimiter", "{")
        body = []

        while not self.compare("Delimiter", "}"):
            if len(body) > 0 and self.peek(-1).type != TokenTypes["LineBreak"]:
                self.eat(TokenTypes["LineBreak"])
            self.eatLBs()
            if self.compare("Delimiter", "}"):
                break
            body.append(self.pCaseStatement())
            self.eatLBs()
        close = self.eat("Delimiter", "}")

        return {
            "type": "SwitchStatement",
            "body": body,
            "value": value,
            "positions": {"start": starter.start, "end": close.end},
        }

    def pDeferStatement(self):
        starter = self.eat("Keyword")
        if self.compare(TokenTypes["Delimiter"], "{"):
            value, lasti = self.eatBlockScope()
            closing_pos = lasti
        else:
            value = [self.pStatement()]
            closing_pos = value[0]["positions"]["end"]
        value = self.pStatement()
        return {
            "type": "DeferStatement",
            "value": value,
            "positions": {
                "start": starter.start,
                "end": closing_pos,
            },
        }

    def pTryCatch(self):
        keyw = self.eat("Keyword", "try")
        self.eatLBs()
        if self.compare("Delimiter", "{"):
            body, lasti = self.eatBlockScope()
        else:
            body = self.pStatement(True)
            lasti = body["positions"]["end"]

        self.eatLBs()
        node = {
            "type": "TryCatch",
            "body": body,
            "catchvar": None,
            "catchbody": None,
            "positions": {"start": keyw.start, "end": lasti},
        }
        if self.compare("Keyword", "catch"):
            self.eat("Keyword")
            self.eatLBs()
            var = None
            if self.compare("Identifier"):
                var = self.eat("Identifier").value
            if self.compare("Delimiter", "{"):
                body, lasti = self.eatBlockScope()
            else:
                body = self.pStatement(True)
                lasti = body["positions"]["end"]
            node["positions"]["end"] = lasti
            node["catchvar"] = var
            node["catchbody"] = body
        return node

    def pThrow(self):
        keyw = self.eat("Keyword", "throw")
        tothrow = self.pExpression()

        return {
            "type": "ThrowStatement",
            "tothrow": tothrow,
            "positions": {"start": keyw.start, "end": tothrow["positions"]["end"]},
        }

    def pBreak(self):
        keyw = self.eat("Keyword", "break")

        return {
            "type": "BreakStatement",
            "positions": {"start": keyw.start, "end": keyw.end},
        }

    def pContinue(self):
        keyw = self.eat("Keyword", "continue")

        return {
            "type": "ContinueStatement",
            "positions": {"start": keyw.start, "end": keyw.end},
        }

    def pAssignment(self, implied_let=False):
        starter = None
        if self.compare("Keyword", "let"):
            starter = self.eat("Keyword", "let")
        elif not (self.compare("Keyword", "mutable") or implied_let):
            raise SyntaxError("Expected 'let' or 'mutable'")
        assignments = []
        while True:
            is_static = False
            is_private = False
            is_mutable = False
            var_type = None
            var_name = None
            value = None
            if self.compare("Keyword", "mutable"):
                tok = self.eat("Keyword")
                is_mutable = True
                if not starter:
                    starter = tok
            if self.compare("Keyword", "static"):
                tok = self.eat("Keyword")
                if not starter:
                    starter = tok
                is_static = True
            if self.compare("Keyword", "private"):
                tok = self.eat("Keyword")
                if not starter:
                    starter = tok
                is_private = True
            if self.compare("Keyword", "static"):
                tok = self.eat("Keyword")
                if not starter:
                    starter = tok
                is_static = True
            if self.compare("Delimiter", "["):
                if not starter:
                    starter = self.peek()
                var_type = self.pArray()
            elif self.compare("Delimiter", "("):
                if not starter:
                    starter = self.peek()
                var_type = self.pExpression(require=True)
            elif self.compare("Delimiter", "{"):
                if not starter:
                    starter = self.peek()
                var_type = self.pObject()
            elif self.compare("Operator", "..."):
                dotdotdot = self.eat("Operator", "...")
                if not starter:
                    starter = dotdotdot
                var_name = "..."
                self.eat("Operator", "=")
                value = self.pExpression(require=True)
                assignments.append(
                    {
                        "is_static": is_static,
                        "is_private": is_private,
                        "is_mutable": is_mutable,
                        "var_type": None,
                        "var_name": var_name,
                        "is_dotdotdot": True,
                        "value": value,
                        "positions": {
                            "start": dotdotdot.start,
                            "end": value["positions"]["end"],
                        },
                    }
                )
                if not self.compare("Delimiter", ","):
                    break
                self.eat("Delimiter", ",")
                continue
            else:
                temp = self.eat("Identifier")
                if not starter:
                    starter = temp
                if self.compare("Identifier") or (
                    self.peek()
                    and self.peek(1).value == "?"
                    and self.peek(1)
                    and self.peek(1).type == TokenTypes["Identifier"]
                ):
                    var_type = {
                        "type": "VariableAccess",
                        "value": temp.value,
                        "positions": {"start": temp.start, "end": temp.end},
                    }
                else:
                    var_name = temp
            if not var_name and self.compare("Identifier"):
                var_name = self.eat("Identifier")
            if self.compare("Delimiter", "("):
                self.pos -= 1
                return self.pFunctionDefinition(assignment=True)
            if self.compare("Operator", "?"):
                op = self.eat("Operator", "?")
                var_type = {
                    "type": "Operator",
                    "operator": "?",
                    "left": var_type,
                    "right": None,
                    "positions": {
                        "start": (
                            var_type["positions"]["start"] if var_type else op.start
                        ),
                        "end": op.end,
                    },
                }
            if not var_name:
                var_name = self.eat("Identifier")
            # let static Number y = 9
            # let static [Number, String] = 7
            if self.compare("Operator", "="):
                self.eat("Operator", "=")
                value = self.pExpression(require=True)
            assignments.append(
                {
                    "is_static": is_static,
                    "is_private": is_private,
                    "is_mutable": is_mutable,
                    "var_type": var_type,
                    "var_name": var_name.value,
                    "is_dotdotdot": False,
                    "value": value,
                    "positions": {
                        "start": var_name.start,
                        "end": value["positions"]["end"] if value else var_name.end,
                    },
                }
            )
            if not self.compare("Delimiter", ","):
                break
            self.eat("Delimiter", ",")
        return {
            "type": "Assignments",
            "assignments": assignments,
            "positions": {
                "start": starter.start,
                "end": assignments[-1]["positions"]["end"],
            },
        }

    def pStructure(self):
        starter = self.eat("Keyword", "structure")
        if self.compare("Keyword", "template"):
            return self.pTemplate()
        name = None
        if self.compare("Identifier"):
            name = self.eat("Identifier").value
        self.eat("Delimiter", "{")
        assignments = []
        while not self.compare("Delimiter", "}") and self.peek():
            if len(assignments) > 0 and self.peek(-1).type != TokenTypes["LineBreak"]:
                self.eat("LineBreak")
            self.eatLBs()
            assignments.append(self.pAssignment(implied_let=True))
            self.eatLBs()

        closer = self.eat("Delimiter", "}")
        return {
            "type": "Structure",
            "name": name,
            "assignments": assignments,
            "positions": {"start": starter.start, "end": closer.end},
        }

    def pTemplate(self):
        starter = self.eat("Keyword", "template")
        name = None
        if self.compare("Identifier"):
            name = self.eat("Identifier").value
        self.eat("Delimiter", "{")
        assignments = []
        while not self.compare("Delimiter", "}") and self.peek():
            if len(assignments) > 0 and self.peek(-1).type != TokenTypes["LineBreak"]:
                self.eat("LineBreak")
            self.eatLBs()
            assignments.append(self.pAssignment(implied_let=True))
            self.eatLBs()

        closer = self.eat("Delimiter", "}")
        return {
            "type": "Template",
            "name": name,
            "assignments": assignments,
            "positions": {"start": starter.start, "end": closer.end},
        }

    def pOption(self):
        starter = self.eat("Keyword", "option")
        name = None
        if self.compare("Identifier"):
            name = self.eat("Identifier").value
        self.eat("Delimiter", "{")
        assignments = []
        while not self.compare("Delimiter", "}") and self.peek():
            if len(assignments) > 0 and self.peek(-1).type != TokenTypes["LineBreak"]:
                self.eat("LineBreak")
            self.eatLBs()
            assignments.append(self.pAssignment())
            self.eatLBs()

        closer = self.eat("Delimiter", "}")
        return {
            "type": "Option",
            "name": name,
            "assignments": assignments,
            "positions": {"start": starter.start, "end": closer.end},
        }

    def pTemplateInit(self, ast_node):
        starter = self.eat("Delimiter", "{")
        arguments = []
        keywordArguments = {}
        while (
            (self.compare("LineBreak") or self.compare("Delimiter", ","))
            or (len(arguments) == 0 and len(keywordArguments) == 0)
            and not self.compare("Delimiter", "}")
        ):
            self.eatLBs()
            if self.compare("Delimiter", ","):
                self.eat("Delimiter", ",")
            self.eatLBs()
            KorV = self.pExpression(eatLBs=True)
            if KorV["type"] == "Operator" and KorV["operator"] == "=":
                if not (KorV["left"] and KorV["left"]["type"] == "VariableAccess"):
                    self.err_handler.throw(
                        "Syntax",
                        "Cannot use an expression as a key.",
                        {
                            "lineno": KorV["positions"]["start"]["line"],
                            "marker": {
                                "start": KorV["positions"]["start"]["col"],
                                "length": KorV["positions"]["end"]["col"]
                                - KorV["positions"]["start"]["col"],
                            },
                            "underline": {
                                "start": KorV["positions"]["start"]["col"],
                                "end": KorV["positions"]["end"]["col"],
                            },
                        },
                    )
                key = KorV["left"]["value"]
                value = KorV["right"]
                if key in keywordArguments:
                    self.err_handler.throw(
                        "Argument",
                        "Duplicate keyword arguments.",
                        {
                            "lineno": KorV["positions"]["start"]["line"],
                            "marker": {
                                "start": KorV["positions"]["start"]["col"],
                                "length": len(key),
                            },
                            "underline": {
                                "start": KorV["positions"]["start"]["col"],
                                "end": value["positions"]["end"]["col"],
                            },
                        },
                    )
                keywordArguments[key] = value
            else:
                arguments.append(KorV)
        self.eatLBs()
        closing = self.eat("Delimiter", "}")
        return {
            "type": "TemplateInit",
            "template": ast_node,
            "arguments": arguments,
            "keywordArguments": keywordArguments,
            "positions": {"start": starter.start, "end": closing.end},
        }

    def pMacroDefinition(self):
        construct_keyword = self.eat("Keyword", "construct")
        name = self.eat("Identifier")
        parameters = []
        if self.compare("Delimiter", "("):
            openparen = self.eat(TokenTypes["Delimiter"], "(")
            while self.peek() and not self.compare(TokenTypes["Delimiter"], ")"):
                var_type = None
                var_name = None
                absorb = False
                var_default = None
                is_optional = False
                self.eatLBs()
                if len(parameters) > 0:
                    self.eat(TokenTypes["Delimiter"], ",")
                self.eatLBs()
                if self.compare("Operator", "..."):
                    self.eat("Operator")
                    absorb = True
                if self.compare("Delimiter", "["):
                    var_type = self.pArray()
                    var_name = self.eat("Identifier")
                if self.compare("Delimiter", "("):
                    var_type = self.pExpression(require=True)
                    var_name = self.eat("Identifier")
                else:
                    temp = self.eat("Identifier")
                    if self.compare("Identifier"):
                        var_type = {
                            "type": "VariableAccess",
                            "value": temp.value,
                            "positions": {"start": temp.start, "end": temp.end},
                        }
                        var_name = self.eat("Identifier")
                    else:
                        var_name = temp
                if self.compare("Operator", "?"):
                    self.eat("Operator")
                    is_optional = True
                self.eatLBs()
                if self.compare("Operator", "="):
                    self.eat("Operator")
                    self.eatLBs()
                    var_default = self.pExpression()
                self.eatLBs()

                parameters.append(
                    {
                        "type": "Parameter",
                        "name": var_name.value,
                        "value_type": var_type,
                        "default": var_default,
                        "absorb": absorb,
                        "is_optional": is_optional,
                        "positions": {
                            "start": (
                                var_type["positions"]["start"]
                                if var_type
                                else var_name.start
                            ),
                            "end": var_name.end,
                        },
                    }
                )
                if absorb:
                    break
            self.eat(TokenTypes["Delimiter"], ")")
        if self.compare("Delimiter", "{"):
            old = self.pos
            inline = True
            body = self.pObject(True)
            if body == False:
                self.pos = old
                body, lasti = self.eatBlockScope()
                inline = False
            else:
                lasti = body["positions"]["end"]
        else:
            body = self.pStatement(require=True)
            lasti = body["positions"]["end"]
            inline = True
        return {
            "type": "MacroDefinition",
            "name": name.value,
            "parameters": parameters,
            "body": body,
            "positions": {
                "start": construct_keyword.start,
                "end": lasti,
            },
        }

    # Statement:
    # 	VariableDefinition

    def pStatement(self, require=False, eatLBs=False):
        self.eatLBs()
        if self.compare("Keyword", "loop"):
            begin = self.eat("Keyword", "loop")
            if self.compare("Delimiter", "{"):
                body, lasti = self.eatBlockScope()
                inline = False
            else:
                body = self.pStatement(require=True)
                lasti = body["positions"]["end"]
                inline = True
            return {
                "type": "Loop",
                "body": body,
                "inline": inline,
                "positions": {
                    "start": begin.start,
                    "end": lasti,
                },
            }
        if self.compare("Keyword", "try"):
            if self.is_strict:
                tok = self.peek()
                self.err_handler.throw(
                    "Strict",
                    "try is not allowed in strict mode.",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 4},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            return self.pTryCatch()
        if self.compare("Keyword", "throw"):
            if self.is_strict:
                tok = self.peek()
                self.err_handler.throw(
                    "Strict",
                    "throw is not allowed in strict mode.",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 4},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            return self.pThrow()
        if self.compare("Keyword", "static") and self.compare("Keyword", "function", 1):
            if self.is_strict:
                tok = self.peek(1)
                self.err_handler.throw(
                    "Strict",
                    "Functions declared with `function` are not allowed in strict mode. Declare your functions with `let f(x) { ... }`",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 8},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            return self.pFunctionDefinition()
        if self.compare("Keyword", "function"):
            if self.is_strict:
                tok = self.peek()
                self.err_handler.throw(
                    "Strict",
                    "Functions declared with `function` are not allowed in strict mode. Declare your functions with `let f(x) { ... }`",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 8},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            return self.pFunctionDefinition()

        if self.compare("Keyword", "return"):
            return self.pReturnStatement()

        if self.compare("Keyword", "defer"):
            if self.is_strict:
                tok = self.peek()
                self.err_handler.throw(
                    "Strict",
                    "Defer is deprecated and not allowed in strict mode.",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 8},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            return self.pDeferStatement()

        if self.compare("Keyword", "if"):
            return self.pIfStatement()

        if self.compare("Keyword", "while"):
            return self.pWhileLoop()

        if self.compare("Keyword", "delete"):
            if self.is_strict:
                tok = self.peek()
                self.err_handler.throw(
                    "Strict",
                    "Delete is deprecated and not allowed in strict mode.",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 8},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            return self.pDelete()

        if self.compare("Keyword", "for"):
            return self.pForLoop()

        if self.compare("Keyword", "include"):
            return self.pIncludeStatement()

        if self.compare("Keyword", "from"):
            return self.pIncludeStatement()

        if self.compare("Keyword", "extending"):
            if self.is_strict:
                tok = self.peek()
                self.err_handler.throw(
                    "Strict",
                    "Extending is deprecated and not allowed in strict mode.",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 8},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            return self.pExtendingStatement()

        if self.compare("Keyword", "static") and self.compare("Keyword", "class", 1):
            if self.is_strict:
                tok = self.peek()
                self.err_handler.throw(
                    "Strict",
                    "Classes are deprecated and not allowed in strict mode.",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 8},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            return self.pClassDefinition()

        if self.compare("Keyword", "class"):
            if self.is_strict:
                tok = self.peek()
                self.err_handler.throw(
                    "Strict",
                    "Classes are deprecated and not allowed in strict mode.",
                    {
                        "lineno": tok.line,
                        "marker": {"start": tok.start["col"], "length": 8},
                        "underline": {"start": tok.start["col"], "end": tok.end["col"]},
                    },
                )
            return self.pClassDefinition()

        # if self.compare("Keyword", "structure"):
        #     return self.pStructureDefinition()

        if self.compare("Keyword", "match"):
            return self.pSwitchCase()
        if self.compare("Keyword", "switch"):
            return self.pSwitchCase()

        if self.compare("Keyword", "break"):
            return self.pBreak()

        if self.compare("Keyword", "continue"):
            return self.pContinue()

        if self.compare("Keyword", "else"):
            e = self.eat("Keyword", "else")
            self.err_handler.throw(
                "Syntax",
                "Unexpected else statement. Else statements are only valid after if statements.",
                {
                    "lineno": e.line,
                    "marker": {"start": e.start["col"] + 1, "length": len(e.value)},
                    "underline": {"start": 0, "end": e.end["col"] + 5},
                },
            )
        if self.compare("Keyword", "case"):
            e = self.eat("Keyword", "case")
            self.err_handler.throw(
                "Syntax",
                "Unexpected case statement. Case statements are only valid within match statements.",
                {
                    "lineno": e.line,
                    "marker": {"start": e.start["col"] + 1, "length": len(e.value)},
                    "underline": {"start": 0, "end": e.end["col"] + 5},
                },
            )
        if self.compare("Keyword", "let") or self.compare("Keyword", "mutable"):
            return self.pAssignment()

        if self.compare("Keyword", "get") or self.compare("Keyword", "set"):
            keyw = self.eat("Keyword")
            funct = self.pFunctionDefinition(True)
            return {
                "type": "GetterSetterDefinition",
                "kind": keyw.value + "ter",
                "function": funct,
                "positions": {
                    "start": keyw.start,
                    "end": funct["positions"]["end"],
                },
            }
        if self.compare("Keyword", "construct"):
            return self.pMacroDefinition()

        return self.pExpression(require=require, eatLBs=eatLBs)

    # Program:
    # 	Statement ( [linebreak] Statement )

    def pProgram(self):
        self.statements = []

        while not self.isEOF():
            if (
                len(self.statements) > 0
                and self.peek(-1).type != TokenTypes["LineBreak"]
            ):
                self.eat("LineBreak")
            while self.compare("LineBreak"):
                self.advance()
            if self.isEOF():
                break
            self.statements.append(self.pStatement(True))

        return {
            "type": "Program",
            "body": self.statements,
            "positions": {
                "start": (
                    0
                    if len(self.statements) == 0
                    else self.statements[0]["positions"]["start"]
                ),
                "end": (
                    0
                    if len(self.statements) == 0
                    else self.statements[-1]["positions"]["end"]
                ),
            },
        }

    def parse(self):
        # Return a single statement for now.
        return self.pProgram()


"""
When design is done, these should be true
|
|                      Operation                       | Lines
---------------------------------------------------------------
| Add 1 to every item in a list                        | 1
| Get all values from x, y to x2, y2 in a 2d array     | 1
"""

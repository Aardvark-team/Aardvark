from Data import TokenTypes, OrderOfOps
import Error
from sty import fg
from Types import Null

import random

type_helper = {}

type_helper["Operator"] = "<operator>"
type_helper["Boolean"] = "<true | false>"
type_helper["Identifier"] = "<identifier>"
type_helper["LineBreak"] = "\n"
type_helper["Number"] = "<Number>"
type_helper["String"] = "<String>"
type_helper["ValueType"] = "<String | Int>"


class Parser:
    def __init__(self, err_handler, lexer):
        self.code = lexer.data
        self.codelines = self.code.split("\n")
        self.tokens = lexer.output
        self.pos = 0
        self.err_handler = err_handler

    ## UTILITY

    # Get the next token
    def peek(self, n=0):
        return self.tokens[self.pos + n] if not self.isEOF() else None

    # Compare the next token with type, value
    def compare(self, Type, value=None):
        if self.isEOF():
            return False

        tok = self.peek()
        if type(Type) == str:
            Type = TokenTypes[Type]

        if tok and tok.type == Type and (value is None or value == tok.value):
            return True
        return False

    # Advance to the next token
    def advance(self):
        self.pos += 1

    # Unexpected EOF
    def eofError(self, Type, value=None, is_type=False):
        last_tok = self.tokens[self.pos - 1]
        curr_line = self.err_handler.code.split("\n")[last_tok.line - 1]
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
        curr_line = curr_line[:line_len].rstrip()
        line_end = replacement

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
    def eat(self, Type, value=None, is_type=False):
        # print("ATE:", Type)

        if type(Type) == str:
            Type = TokenTypes[Type]

        if self.compare(Type, value):
            curr = self.peek()
            self.advance()

            return curr

        # Raise an error
        # print(Type)
        if self.isEOF():
            return self.eofError(Type, value, is_type)

        next_tok = self.peek()
        curr_line = self.err_handler.code.split("\n")[next_tok.line - 1].rstrip()
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
            curr_line[: next_tok.start["col"] - 1].rstrip()
            + replacement
            + curr_line[end_pos - 1 :]
        )

        self.err_handler.throw(
            "Syntax",
            f"Unexpected token {str(next_tok.type)}",
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
            while self.compare(TokenTypes["LineBreak"]):
                self.advance()
            if len(items) > 0:
                if not self.compare('Delimiter', delim):
                  tok = self.peek()
                  self.err_handler.throw('Syntax', f'Invalid syntax, perhaps you forgot a {delim}?', {
                    'lineno': tok.start['line'],
                    'marker': {
                      'start': tok.start['col'],
                      'length': len(delim)
                    },
                    'underline': {
                      'start': tok.start['col']-2,
                      'end': tok.start['col']+2
                    },
                    'did_you_mean': self.codelines[tok.start['line']-1][:tok.start['col']-1] + delim + self.codelines[tok.start['line']-1][tok.end['col']-1:]
                  })
                self.eat(TokenTypes["Delimiter"], delim)
            while self.compare(TokenTypes["LineBreak"]):
                self.advance()

            items.append(self.pStatement())
        return items

    # Eats a list of statements contained in { and }
    def eatBlockScope(self):
        self.eat(TokenTypes["Delimiter"], "{")
        body = []

        while self.peek() and not self.compare(TokenTypes["Delimiter"], "}"):
            if len(body) > 0:
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
    def pPrimary(self, require=False):
        tok = self.peek()
        ast_node = None

        if self.isEOF():
            if require:
                self.eofError(
                    TokenTypes[random.choice(["String", "Number", "Identifier"])]
                )
            else:
                return None

        if tok.type == TokenTypes["Operator"] and tok.value == "!":
            self.eat("Operator", "!")
            right = self.pExpression()
            ast_node = {
                "type": "LogicalExpression",
                "operator": "!",
                "right": right,
                "positions": {"start": tok.start, "end": right["positions"]["end"]},
            }

        if tok.type in [TokenTypes["String"], TokenTypes["Number"]]:
            self.eat(tok.type)

            value = tok.value
            if tok.type == TokenTypes["Number"]:
                if "." in tok.value:
                    value = float(value)
                else:
                    value = int(value)
            else:
                value = value.replace("\\n", "\n")
            ast_node = {
                # StringLiteral, NumberLiteral, etc...
                "type": tok.type.name + "Literal",
                "value": value,
                "positions": {"start": tok.start, "end": tok.end},
                "tokens": {"value": tok},
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
            ast_node = self.pObject(tok)

        elif tok.type == TokenTypes["Delimiter"] and tok.value == "[":
            ast_node = self.pArray(tok)

        elif tok.type == TokenTypes["Identifier"]:
            self.eat(tok.type)

            if self.compare(TokenTypes["Delimiter"], "("):
                ast_node = self.pFunctionCall(tok)

            elif tok.value == "set" and self.compare(TokenTypes["Delimiter"], "{"):
                ast_node = self.pSet(tok)

            else:
                ast_node = {
                    "type": "VariableAccess",
                    "value": tok.value,
                    "positions": {"start": tok.start, "end": tok.end},
                }

        elif tok.type == TokenTypes["Delimiter"] and tok.value == "(":
            self.eat(tok.type)
            ast_node = self.pStatement()
            self.eat(TokenTypes["Delimiter"], ")")

        elif tok.type == TokenTypes["Keyword"] and tok.value == "function":
            ast_node = self.pFunctionDefinition()

        elif tok.type == TokenTypes["Keyword"] and tok.value == "class":
            ast_node = self.pClassDefinition()

        if ast_node:
            while self.compare(TokenTypes["Delimiter"], "."):
                self.eat(TokenTypes["Delimiter"])
                property_name = self.eat(TokenTypes["Identifier"])

                ast_node = {
                    "type": "PropertyAccess",
                    "property": property_name.value,
                    "value": ast_node,
                    "positions": {
                        "start": ast_node["positions"]["start"],
                        "end": property_name.end,
                    },
                    "tokens": {
                        "property": property_name,
                    },
                }

                if self.compare(TokenTypes["Delimiter"], "("):
                    self.eat(TokenTypes["Delimiter"])
                    arguments = self.parseListLike(",", (TokenTypes["Delimiter"], ")"))
                    last = self.eat(TokenTypes["Delimiter"], ")")
                    ast_node["arguments"] = arguments
                    ast_node["type"] = "MethodCall"
                    ast_node["positions"]["end"] = last.end
            # 5x, number-var mult
            if (
                self.compare("Identifier")
                and self.peek().start["col"] == ast_node["positions"]["end"]["col"] + 1
            ):
                var = self.eat(TokenTypes["Identifier"])
                ast_node = {
                    "type": "Multiply",
                    "number": ast_node,
                    "variable": var.value,
                    "positions": {
                        "start": ast_node["positions"]["start"],
                        "end": var.end,
                    },
                    "tokens": {
                        "variable": var,
                    },
                }
            elif self.compare("Identifier"):
                print(ast_node["positions"]["end"], self.peek().start)
            # Inline ifs
            if self.compare(TokenTypes["Keyword"], "if"):
                if_ast = self.pIfStatement(True)
                if_ast["body"] = ast_node
                ast_node = if_ast
            # Indexes
            if self.compare("Delimiter", "["):
                self.eat("Delimiter")
                property = self.pExpression()
                self.eat("Delimiter")
                ast_node = {
                    "type": "Index",
                    "property": property,
                    "value": ast_node,
                    "positions": {
                        "start": ast_node["positions"]["start"],
                        "end": property["positions"]["end"]
                        if property
                        else ast_node["positions"]["end"],
                    },
                }
            # Types
            if self.compare("Delimiter", ":"):
                self.eat("Delimiter")
                type = self.pExpression()
                ast_node["valuetype"] = type
                ast_node["positions"]["end"] = type["positions"]["end"]
            # TODO: add a, b, c

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
                f"Unexpected token {tok.type.name.upper()}, expected STRING, NUMBER, ARRAY, SET, FUNCTION CALL or IDENTIFIER."
            )

    # Expression:
    #
    def pExpression(self, level=len(OrderOfOps) - 1, require=False):
        if level < 0:
            left = self.pPrimary(require=require)
        else:
            left = self.pExpression(level - 1, require=require)
        if (
            self.peek()
            and self.compare(TokenTypes["Operator"])
            and level in OrderOfOps
            and self.peek().value in OrderOfOps[level]
        ):
            op = self.eat(TokenTypes["Operator"])
            right = self.pExpression(level, require=False)
            return {
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
        return left

    # Expression:
    # 	Additive
    # def pExpression(self):
    #    return self.pAdditive()

    # Object:
    # 	{ [string] : Expression (, [string] : Expression ) }
    def pObject(self, starter):
        self.eat(TokenTypes["Delimiter"], "{")
        obj = {}

        while self.peek() and not self.compare(TokenTypes["Delimiter"], "}"):
            if len(obj.keys()) > 0:
                self.eat(TokenTypes["Delimiter"], ",")

            name = None
            if self.compare(TokenTypes["Identifier"]):
                name = self.eat(TokenTypes["Identifier"]).value

            self.eat(TokenTypes["Delimiter"], ":")
            value = self.pStatement()

            obj[name] = value

        closing_par = self.eat(TokenTypes["Delimiter"], "}")

        return {
            "type": "Object",
            "pairs": obj,
            "positions": {"start": starter.start, "end": closing_par.end},
        }

    # Array:
    # 	[ Expression ( , Expression ) ]
    def pArray(self, starter):
        self.eat(TokenTypes["Delimiter"], "[")
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
    def pFunctionCall(self, name):
        self.eat(TokenTypes["Delimiter"], "(")
        arguments = self.parseListLike(",", (TokenTypes["Delimiter"], ")"))
        closing_par = self.eat(TokenTypes["Delimiter"], ")")

        return {
            "type": "FunctionCall",
            "name": name.value,
            "arguments": arguments,
            "tokens": {"name": name},
            "positions": {"start": name.start, "end": closing_par.end},
        }

    # pFunctionDefinition:
    # 	function [identifier] ( [identifier] [identifier] ( , [identifier] [identifier] ) )
    def pFunctionDefinition(self, is_class_method=False):
        starter = None
        name = None

        if not is_class_method:
            starter = self.eat(TokenTypes["Keyword"], "function")

        if self.compare("Identifier") or is_class_method:
            name = self.eat(TokenTypes["Identifier"])

        if is_class_method:
            starter = name

        self.eat(TokenTypes["Delimiter"], "(")

        parameters = []
        while self.peek() and not self.compare(TokenTypes["Delimiter"], ")"):
            var_type = None
            if len(parameters) > 0:
                self.eat(TokenTypes["Delimiter"], ",")
            var_name = self.eat(TokenTypes["Identifier"])
            if self.compare("Delimiter", ":"):
                self.eat("Delimiter")
                var_type = self.pExpression()

            parameters.append(
                {
                    "type": "Parameter",
                    "name": var_name.value,
                    "value_type": var_type,
                    "positions": {
                        "start": var_type["positions"]["start"]
                        if var_type
                        else var_name.start,
                        "end": var_name.end,
                    },
                }
            )

        self.eat(TokenTypes["Delimiter"], ")")
        AS = None
        if self.compare(TokenTypes["Keyword"], "as"):
            self.eat(TokenTypes["Keyword"], "as")
            AS = self.eat(TokenTypes["Identifier"]).value

        return_type = None
        if self.compare("Operator"):
            self.eat(TokenTypes["Operator"], "->")
            return_type = self.eat(TokenTypes["Identifier"], is_type=True)
        if self.compare("Delimiter", "{"):
            body, lasti = self.eatBlockScope()
        else:
            body = self.pStatement(require=True)
            lasti = body["positions"]["end"]

        return {
            "type": "FunctionDefinition",
            "name": name.value if name else "",
            "is_anonymous": name is None,
            "parameters": parameters,
            "body": body,
            "as": AS,
            "return_type": return_type.value if return_type else "void",
            "positions": {"start": starter.start, "end": lasti},
        }

    # ExtendingStatement:
    #    extending Object
    def pExtendingStatement(self):
        starter = self.eat("Keyword", "extending")
        obj_name = self.eat("Identifier")

        if self.compare("Delimiter", "{"):
            obj = self.pObject(self.peek())
        elif self.compare("Delimiter", "["):
            obj = self.pArray(self.peek())
        elif self.compare("Identifier", "set"):
            self.eat("Identifier")
            obj = self.pSet(self.peek())
        else:
            raise Exception(
                "Syntax error: Unexpected token " + str(self.peek().type).upper()
            )
        return {
            "type": "ExtendingStatement",
            "name": obj_name.value,
            "object": obj,
            "positions": {"start": starter.start, "end": obj["positions"]["end"]},
        }

    # ReturnStatement:
    # 	return Expression
    def pReturnStatement(self):
        starter = self.eat(TokenTypes["Keyword"], "return")
        return_value = self.pStatement()
        return {
            "type": "ReturnStatement",
            "value": return_value,
            "positions": {
                "start": starter.start,
                "end": return_value["positions"]["end"]
                if return_value
                else starter.end,
            },
        }

    # WhileLoop:
    # 	while condition BlockScope
    # 	while condition Statement
    def pWhileLoop(self):
        starter = self.eat(TokenTypes["Keyword"], "while")
        condition = self.pExpression()

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
        condition = self.pExpression()
        body = None
        lasti = condition["positions"]["end"]

        if self.compare(TokenTypes["Delimiter"], "{") and not inline:
            body, lasti = self.eatBlockScope()
        elif not inline:
            statm = self.pStatement(True)
            body = [statm]
            lasti = statm["positions"]["end"]
        closing_pos = lasti
        else_body = None
        if self.compare(TokenTypes["Keyword"], "else"):
            self.eat(TokenTypes["Keyword"])

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
        target = self.pExpression()
        return {
            "type": "DeleteStatement",
            "target": target,
            "positions": {"start": starter.start, "end": target["positions"]["end"]},
        }

    # For loop:
    def pForLoop(self):
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
        iterable = self.pExpression()  # Get the iterable.
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

        while not self.compare("Delimiter", "}"):
            while self.compare("LineBreak"):
                self.eat("LineBreak")

            body.append(self.pFunctionDefinition(is_class_method=True))

        closer = self.eat("Delimiter", "}")

        return {
            "type": "ClassScope",
            "body": body,
            "positions": {"start": starter.start, "end": closer.end},
        }

    # ClassDefinition:
    #     class [identifier] [ extends [identifier] ] ClassScope
    def pClassDefinition(self):
        starter = self.eat(TokenTypes["Keyword"], "class")
        name = None
        extends = []
        AS = None

        if self.compare(TokenTypes["Identifier"]):
            name = self.eat(TokenTypes["Identifier"]).value

        if self.compare("Keyword", "extends"):
            self.eat("Keyword", "extends")
            extends.append(self.eat(TokenTypes["Identifier"]).value)
            while self.compare("Delimiter", ","):
                self.eat("Delimiter")
                extends.append(self.eat(TokenTypes["Identifier"]).value)

        if self.compare("Keyword", "as"):
            self.eat("Keyword", "as")
            AS = self.eat(TokenTypes["Identifier"]).value

        class_scope = self.pClassScope()

        return {
            "type": "ClassDefinition",
            "name": name,
            "is_anonymous": name is None,
            "extends": extends,
            "class_scope": class_scope,
            "as": AS,
            "positions": {
                "start": starter.start,
                "end": class_scope["positions"]["end"],
            },
        }

    # IncludeStatement:
    #     include [identifier]
    #     include [identifier] as [identifier]
    #     include [identifier] [ as [identifier] ] from [identifier]
    #     from [identifier] include [identifier]
    #     from [identifier] include [identifier] as [identifier]
    def pIncludeStatement(self):
        if self.compare("Keyword", "include"):
            keyw = self.eat(TokenTypes["Keyword"], "include")
            lib_or_start = self.eat(TokenTypes["Identifier"])
            included_parts = [[lib_or_start.value, lib_or_start.value]]

            # Include without as / from
            if self.isEOF() or self.compare(TokenTypes["LineBreak"]):
                return {
                    "type": "IncludeStatement",
                    "lib_name": lib_or_start.value,
                    "local_name": lib_or_start.value,
                    "included": "ALL",
                    "positions": {"start": keyw.start, "end": lib_or_start.end},
                }

            # Include as
            if self.compare(TokenTypes["Keyword"], "as"):
                self.eat(TokenTypes["Keyword"], "as")
                local_name = self.eat(TokenTypes["Identifier"])

                if self.isEOF() or self.compare(TokenTypes["LineBreak"]):
                    return {
                        "type": "IncludeStatement",
                        "lib_name": lib_or_start.value,
                        "local_name": local_name.value,
                        "included": "ALL",
                        "positions": {"start": keyw.start, "end": local_name.end},
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
            lib_name = self.eat("Identifier")
            created_obj = {}

            for part_name, part_local in included_parts:
                created_obj[part_name] = {"local": part_local}
            end = lib_name.end
        else:
            keyw = self.eat("Keyword", "from")
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
        }

    # Statement:
    #   Case
    def pCaseStatement(self):
        starter = self.eat("Keyword", "case")
        compare = self.pExpression()
        # ADD the case in y, case == 5 later

        if self.compare("Delimiter", "{"):
            body, lati = self.eatBlockScope()
        else:
            body = [self.pStatement(require=True)]
            lasti = body[0]["positions"]["end"]
        return {
            "type": "CaseStatement",
            "compare": compare,
            "body": body,
            "positions": {"start": starter.start, "end": lasti},
        }

    # Statement Switch
    def pSwitchCase(self):
        starter = self.eat("Keyword", "switch")
        value = self.pExpression()
        self.eat("Delimiter", "{")
        body = []

        while not self.compare("Delimiter", "}"):
            while self.compare("LineBreak"):
                self.eat("LineBreak")
            body.append(self.pCaseStatement())
            while self.compare("LineBreak"):
                self.eat("LineBreak")

        close = self.eat("Delimiter", "}")

        return {
            "type": "SwitchStatement",
            "body": body,
            "value": value,
            "positions": {"start": starter.start, "end": close.end},
        }

    def pDeferStatement(self):
        starter = self.eat("Keyword")
        value = self.pExpression()
        return {
            "type": "DeferStatement",
            "value": value,
            "positions": {
                "start": starter.start,
                "end": value["positions"]["end"] if value else starter.end,
            },
        }

    # Statement:
    # 	VariableDefinition
    def pStatement(self, require=False):

        if self.compare(TokenTypes["Keyword"], "function"):
            return self.pFunctionDefinition()

        if self.compare(TokenTypes["Keyword"], "return"):
            return self.pReturnStatement()

        if self.compare(TokenTypes["Keyword"], "defer"):
            return self.pDeferStatement()

        if self.compare(TokenTypes["Keyword"], "if"):
            return self.pIfStatement()

        if self.compare(TokenTypes["Keyword"], "while"):
            return self.pWhileLoop()

        if self.compare(TokenTypes["Keyword"], "delete"):
            return self.pDelete()

        if self.compare(TokenTypes["Keyword"], "for"):
            return self.pForLoop()

        if self.compare(TokenTypes["Keyword"], "include"):
            return self.pIncludeStatement()

        if self.compare(TokenTypes["Keyword"], "from"):
            return self.pIncludeStatement()

        if self.compare(TokenTypes["Keyword"], "extending"):
            return self.pExtendingStatement()

        if self.compare(TokenTypes["Keyword"], "class"):
            return self.pClassDefinition()

        if self.compare(TokenTypes["Keyword"], "switch"):
            return self.pSwitchCase()

        return self.pExpression(require=require)

    # Program:
    # 	Statement ( [linebreak] Statement )
    def pProgram(self):
        statements = []

        while not self.isEOF():
            if len(statements) > 0:
                self.eat(TokenTypes["LineBreak"])
            while self.compare(TokenTypes["LineBreak"]):
                self.advance()
            if self.isEOF():
                break

            statements.append(self.pStatement())

        return {
            "type": "Program",
            "body": statements,
            "positions": {
                "start": 0
                if len(statements) == 0
                else statements[0]["positions"]["start"],
                "end": 0
                if len(statements) == 0
                else statements[-1]["positions"]["end"],
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

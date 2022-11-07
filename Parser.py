from Data import TokenTypes, OrderOfOps
from Error import Highlight, styles
from sty import fg

import random

type_helper = {}

type_helper["Operator"] = "<operator>"
type_helper["Boolean"] = "<true | false>"
type_helper["Identifier"] = "<identifier>"
type_helper["LineBreak"] = ""
type_helper["Number"] = "<number>"
type_helper["String"] = '<string>'
type_helper["ValueType"] = "<String | Int>"

class Parser:

    def __init__(self, err_handler, lexer):
        self.tokens = lexer.output
        self.pos = 0
        self.err_handler = err_handler

    ## UTILITY

    # Get the next token
    def peek(self, n=0):
        return self.tokens[self.pos + n] if not self.isEOF() else None

    # Compare the next token with type, value
    def compare(self, Type, value=None):
        if self.isEOF(): return False
        
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
        curr_line = self.err_handler.code.split("\n")[last_tok.line]
        line_len = len(curr_line)

        value_type = value if value else type_helper.get(Type.name if not is_type else "ValueType", "[no suggestion]")
        if type(value_type) == list: value_type = random.choice(value_type)

        replacement = " " + value_type
        curr_line = curr_line[:line_len + 1].rstrip()
        line_end = replacement
        
        self.err_handler.throw(
            "Syntax",
            "Unexpected EOF.",
            {
                'lineno': last_tok.line,
        
                'marker': {
                    'start': line_len + 1,
                    'length': 1
                },
        
                'underline': {
                    'start': 0,
                    'end': line_len + 1
                },

                'did_you_mean': Highlight(curr_line, {
                    "background": None,
                    "linenums": None
                }) + styles["suggestion"] + line_end + fg.rs
            }
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
        if self.isEOF(): return self.eofError(Type, value, is_type)
            
        next_tok = self.peek()
        curr_line = self.err_handler.code.split("\n")[next_tok.line].rstrip()
        line_len = len(curr_line)

        value_type = value if value else type_helper.get(Type.name if not is_type else "ValueType", "[no suggestion]")
        if type(value_type) == list: value_type = random.choice(value_type)

        replacement = " " + value_type
        end_pos = max(next_tok.start["col"] + len(replacement), next_tok.end["col"] + 1)

        curr_line = curr_line[:next_tok.start["col"]].rstrip() + \
                    replacement + \
                    curr_line[end_pos:]

        self.err_handler.throw(
            "Syntax",
            f"Unexpected token {str(next_tok.type)}",
            {
                'lineno': next_tok.line,
        
                'marker': {
                    'start': next_tok.start["col"] + 1,
                    'length': next_tok.length + 1
                },
        
                'underline': {
                    'start': 0,
                    'end': line_len
                },

                'did_you_mean': curr_line
            }
        )
    # Is at the end of file
    def isEOF(self):
        return self.pos >= len(self.tokens)

    # Parse expression split by delimiter, until token type is reached,
    # closer should look like ( Type of token, Value of token )
    def parseListLike(self, delim, closer):
        items = []
        while self.peek() and not self.compare(*closer):
            if len(items) > 0:
                self.eat(TokenTypes["Delimiter"], delim)

            items.append(self.pExpression())
        return items

    # Eats a list of statements contained in { and }
    def eatBlockScope(self):
        self.eat(TokenTypes["Delimiter"], "{")
        body = []

        while self.peek() and not self.compare(TokenTypes["Delimiter"], "}"):
            if len(body) > 0: self.eat(TokenTypes["LineBreak"])
            while self.compare(TokenTypes["LineBreak"]):
                self.advance()
            if self.compare(TokenTypes["Delimiter"], "}"): break

            body.append(self.pStatement())
        close = self.eat(TokenTypes["Delimiter"], "}")

        return body, close.end

    ## PARSER MAIN

    # Primary:
    # 	[number]
    #	  [string]
    # 	[identifier]
    #   [boolean]
    #   FunctionDefinition
    #   FunctionCall
    def pPrimary(self, require=False):
        tok = self.peek()
        ast_node = None
        
        if self.isEOF():
          if require:
            self.eofError(TokenTypes[random.choice(
                [ "String", "Number", "Identifier" ]
            )])
          else: return None

        if tok.type == TokenTypes["Operator"] and tok.value == "!":
            self.eat("Operator", "!")
            right = self.pExpression()
            ast_node = {
                "type": "LogicalExpression",
                "operator": "!",
                "right": right,
                "positions": {
                    "start": tok.start,
                    "end": right["positions"]["end"]
                }
            }

        if tok.type in [TokenTypes["String"], TokenTypes["Number"]]:
            self.eat(tok.type)

            value = tok.value
            if tok.type == TokenTypes["Number"]:
                if "." in tok.value: value = float(value)
                else: value = int(value)

            ast_node = {
                # StringLiteral, NumberLiteral, etc...
                "type": tok.type.name + "Literal",
                "value": value,
                "positions": {
                    "start": tok.start,
                    "end": tok.end
                }
            }

        elif tok.type == TokenTypes["Boolean"]:
            self.eat(tok.type)

            ast_node = {
                "type": "BooleanLiteral",
                "value": tok.value == "true",
                "positions": {
                    "start": tok.start,
                    "end": tok.end
                }
            }

        elif tok.type == TokenTypes["Delimiter"] and tok.value == "{":
            ast_node = self.pObject(tok)

        elif tok.type == TokenTypes["Delimiter"] and tok.value == "[":
            ast_node = self.pArray(tok)

        elif tok.type == TokenTypes["Identifier"]:
            self.eat(tok.type)

            if self.compare(TokenTypes["Delimiter"], "("):
                ast_node = self.pFunctionCall(tok)

            elif tok.value == "set" and self.compare(TokenTypes["Delimiter"],
                                                     "{"):
                ast_node = self.pSet(tok)

            else:
                ast_node = {
                    "type": "VariableAccess",
                    "value": tok.value,
                    "positions": {
                        "start": tok.start,
                        "end": tok.end
                    }
                }

        elif tok.type == TokenTypes["Delimiter"] and tok.value == "(":
            self.eat(tok.type)
            ast_node = self.pExpression()
            self.eat(TokenTypes["Delimiter"], ")")

        elif tok.type == TokenTypes['Keyword'] and tok.value == 'function':
            ast_node = self.pFunctionDefinition()
        
        elif tok.type == TokenTypes["Keyword"] and tok.value == "class":
            ast_node = self.pClassDefinition()

        if ast_node:
            if self.peek() and self.peek(
            ).type == TokenTypes["Operator"] and self.peek().value in [
                    "=", "<", ">", "<=", "=>", "!="
            ]:
                op = self.eat(TokenTypes["Operator"])
                right = self.pExpression()

                ast_node = {
                    "type": "LogicalExpression",
                    "operator": op.value,
                    "left": ast_node,
                    "right": right,
                    "positions": {
                        "start": ast_node["positions"]["start"],
                        "end": right["positions"]["end"]
                    }
                }

            while self.compare(TokenTypes["Delimiter"], "."):
                self.eat(TokenTypes["Delimiter"])
                property_name = self.eat(TokenTypes["Identifier"])

                ast_node = {
                    "type": "PropertyAccess",
                    "property": property_name.value,
                    "value": ast_node,
                    "positions": {
                        "start": ast_node["positions"]["start"],
                        "end": property_name.end
                    }
                }

                if self.compare(TokenTypes["Delimiter"], "("):
                    self.eat(TokenTypes["Delimiter"])
                    arguments = self.parseListLike(
                        ",", (TokenTypes["Delimiter"], ")"))
                    last = self.eat(TokenTypes["Delimiter"], ")")
                    ast_node["arguments"] = arguments
                    ast_node["type"] = "MethodCall"
                    ast_node["positions"]["end"] = last.end

            return ast_node
        if require:
          # Throw an error
          raise Exception(
              f"Unexpected token {tok.type.name.upper()}, expected STRING, NUMBER, ARRAY, SET, FUNCTION CALL or IDENTIFIER."
          )

      
    # Expression:
    #   
    def pExpression(self, level = len(OrderOfOps)-1, require=False):
        if level < 0: left = self.pPrimary(require=require)
        else: left = self.pExpression(level - 1, require=require)
        if self.peek() and self.compare(TokenTypes["Operator"]) and level in OrderOfOps and self.peek().value in OrderOfOps[level]:
            op = self.eat(TokenTypes["Operator"])
            right = self.pExpression(level, require = False)
            return {
              'type': 'Operator',
              'left': left,
              'right': right,
              'operator': op.value,
              'positions': {
                'start': (left or {}).get('positions', {}).get('start', op.start),
                'end': (right or {}).get('positions', {}).get('end', op.end) #to handle if there is no right
              }
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
            else:
                name = self.eat(TokenTypes["String"]).value

            self.eat(TokenTypes["Delimiter"], ":")
            value = self.pExpression()

            obj[name] = value

        closing_par = self.eat(TokenTypes["Delimiter"], "}")

        return {
            "type": "Object",
            "pairs": obj,
            "positions": {
                "start": starter.start,
                "end": closing_par.end
            }
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
            "positions": {
                "start": starter.start,
                "end": closing_par.end
            }
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
            "positions": {
                "start": starter.start,
                "end": closing_par.end
            }
        }

    # FunctionCall:
    #	[identifier] ( Expression ( , Expression ) )
    def pFunctionCall(self, name):
        self.eat(TokenTypes["Delimiter"], "(")
        arguments = self.parseListLike(",", (TokenTypes["Delimiter"], ")"))
        closing_par = self.eat(TokenTypes["Delimiter"], ")")

        return {
            "type": "FunctionCall",
            "name": name.value,
            "arguments": arguments,
            "tokens": {
              "name": name
            },
          
            "positions": {
                "start": name.start,
                "end": closing_par.end
            }
        }


    # pFunctionDefinition:
    # 	function [identifier] ( [identifier] [identifier] ( , [identifier] [identifier] ) )
    def pFunctionDefinition(self, is_class_method=False):
        starter = None
        name = None

        if not is_class_method:
            starter = self.eat(TokenTypes["Keyword"], "function")

        if self.compare('Identifier') or is_class_method:
            name = self.eat(TokenTypes["Identifier"])

        if is_class_method:
            starter = name

        self.eat(TokenTypes["Delimiter"], "(")

        parameters = []
        while self.peek() and not self.compare(TokenTypes["Delimiter"], ")"):
            if len(parameters) > 0:
                self.eat(TokenTypes["Delimiter"], ",")

            var_type = self.eat(TokenTypes["Identifier"], is_type = True)
            var_name = self.eat(TokenTypes["Identifier"])
            
            #if self.compare(TokenTypes['Identifier']):
            #    var_type = x
            #    var_name = self.eat(TokenTypes["Identifier"])
            #else:
            #    var_type = None
            #    var_name = x
            
            parameters.append({
                "type": "Parameter",
                "name": var_name.value,
                "value_type": var_type.value if var_type else None,
                "positions": {
                    "start": var_type.start if var_type else var_name.start,
                    "end": var_name.end
                }
            })

        self.eat(TokenTypes["Delimiter"], ")")
        AS = None
        if self.compare(TokenTypes['Keyword'], 'as'):
            self.eat(TokenTypes['Keyword'], 'as')
            AS = self.eat(TokenTypes["Identifier"]).value

        return_type = None
        if self.compare("Operator"):
            self.eat(TokenTypes["Operator"], "->")
            return_type = self.eat(TokenTypes["Identifier"], is_type = True)

        body, lasti = self.eatBlockScope()

        return {
            "type": "FunctionDefinition",
            "name": name.value if name else "",
            "is_anonymous": name is None,
            "parameters": parameters,
            "body": body,
            'as': AS,
            "return_type": return_type.value if return_type else "void",
            "positions": {
                "start": starter.start,
                "end": lasti
            }
        }

    # ExtendingStatement:
    #    extending Object
    def pExtendingStatement(self):
        starter = self.eat("Keyword", "extending")
        obj_name = self.eat("Identifier")

        if not self.compare("Delimiter", "{"):
            raise Exception("Syntax error: Unexpected token " +
                            str(self.peek().type).upper())

        obj = self.pObject(self.peek())
        return {
            "type": "ExtendingStatement",
            "name": obj_name.value,
            "object": obj,
            "positions": {
                "start": starter.start,
                "end": obj["positions"]["end"]
            }
        }

    # ReturnStatement:
    # 	return Expression
    def pReturnStatement(self):
        starter = self.eat(TokenTypes["Keyword"], "return")
        return_value = self.pExpression()
        return {
            "type": "ReturnStatement",
            "value": return_value,
            "positions": {
                "start": starter.start,
                "end": return_value["positions"]["end"]
            }
        }

    # VariableDefinition:
    #   let [identifier] = [expression]
    # 	let [identifier] [identifier] = [expression]
    def pVariableDefinition(self):
        keyword = self.eat(TokenTypes["Keyword"], "let")
        var_type = self.eat(TokenTypes["Identifier"], is_type = True) if self.compare(
            TokenTypes["Identifier"]) else None
        var_name = None

        if self.compare(TokenTypes["Operator"], "="):
            var_name = var_type
            var_type = None
        else:
            var_name = self.eat(TokenTypes["Identifier"])

        if not var_name:
            var_name = self.eat(TokenTypes["Identifier"])

        self.eat(TokenTypes["Operator"], "=")
        var_value = self.pExpression()

        return {
            "type": "VariableDefinition",
            "name": var_name.value,
            "value_type": var_type.value if var_type else None,
            "value": var_value,
            "positions": {
                "start": keyword.start,
                "end": var_value["positions"]["end"]
            }
        }

    # WhileLoop:
    #	while condition BlockScope
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
            "positions": {
                "start": starter.start,
                "end": lasti
            }
        }

    # IfStatement:
    #	if condition BlockScope [ else BlockScope ]
    #   if condition BlockScope [ else Statement ]
    def pIfStatement(self):
        starter = self.eat(TokenTypes["Keyword"], "if")
        condition = self.pExpression()

        if self.compare(TokenTypes["Delimiter"], "{"):
            body, lasti = self.eatBlockScope()
        else:
            statm = self.pStatement()
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
            "positions": {
                "start": starter.start,
                "end": closing_pos
            }
        }

    # Delete Keyword:
    def pDelete(self):
        starter = self.eat(TokenTypes["Keyword"], "delete")
        target = self.pExpression()
        return {
            "type": "DeleteStatement",
            "target": target,
            "positions": {
                "start": starter.start,
                "end": target["positions"]["end"]
            }
        }

    # For loop:
    def pForLoop(self):
        starter = self.eat('Keyword', 'for')
        declarations = []
        #{ ..., declarations: [ { type: "destructure", names: [ "k", "v" ] } ] }
        while self.compare('Identifier'):
            x = self.eat(TokenTypes['Identifier'])
            if self.compare(TokenTypes['Delimiter'], ','):
                self.eat('Delimiter')
                declarations.append({'type': 'variable', 'names': [x.value]})
            elif self.compare(TokenTypes['Delimiter'], ':'):
                self.eat('Delimiter')
                declarations.append({
                    'type':
                    'destructure',
                    'names': [x.value, self.eat('Identifier').value]
                })
                if self.compare('Delimiter', ','):
                    self.eat('Delimiter')
            else:
                declarations.append({'type': 'variable', 'names': [x.value]})
                break
        self.eat('Keyword', 'in')
        iterable = self.pExpression()  #Get the iterable.
        body, lasti = self.eatBlockScope()
        return {
            'type': 'ForLoop',
            'declarations': declarations,
            'iterable': iterable,
            'body': body,
            'positions': {
                'start': starter.start,
                'end': lasti
            }
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
            "positions": {
                "start": starter.start,
                "end": closer.end
            }
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
            while self.compare('Delimiter', ','):
                self.eat('Delimiter')
                extends.append(self.eat(TokenTypes["Identifier"]).value)
              
        if self.compare('Keyword', 'as'):
            self.eat('Keyword', 'as')
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
                "end": class_scope["positions"]["end"]
            }
        }

    # IncludeStatement:
    #     include [identifier]
    #     include [identifier] as [identifier]
    #     include [identifier] [ as [identifier] ] from [identifier]
    def pIncludeStatement(self):
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
                "positions": {
                    "start": keyw.start,
                    "end": lib_or_start.end
                }
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
                    "positions": {
                        "start": keyw.start,
                        "end": local_name.end
                    }
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

        return {
            "type": "IncludeStatement",
            "lib_name": lib_name.value,
            "local_name": lib_name.value,
            "included": created_obj,
            "positions": {
                "start": keyw.start,
                "end": lib_name.end
            }
        }

    # Statement:
    # 	VariableDefinition
    def pStatement(self):
        if self.compare(TokenTypes["Keyword"], "let"):
            return self.pVariableDefinition()

        if self.compare(TokenTypes["Keyword"], "function"):
            return self.pFunctionDefinition()

        if self.compare(TokenTypes["Keyword"], "return"):
            return self.pReturnStatement()

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

        if self.compare(TokenTypes["Keyword"], "extending"):
            return self.pExtendingStatement()

        if self.compare(TokenTypes["Keyword"], "class"):
            return self.pClassDefinition()

        return self.pExpression(require=True)

    # Program:
    #	Statement ( [linebreak] Statement )
    def pProgram(self):
        statements = []

        while not self.isEOF():
            if len(statements) > 0: self.eat(TokenTypes["LineBreak"])
            while self.compare(TokenTypes["LineBreak"]):
                self.advance()
            if self.isEOF(): break

            statements.append(self.pStatement())

        return {
            "type": "Program",
            "body": statements,
            "positions": {
                "start":
                0 if len(statements) == 0 else
                statements[0]["positions"]["start"],
                "end":
                0
                if len(statements) == 0 else statements[-1]["positions"]["end"]
            }
        }

    def parse(self):
        # Return a single statement for now.
        return self.pProgram()

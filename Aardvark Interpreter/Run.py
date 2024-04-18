import Data
import Lexer
import Parser
import traceback
from Error import ErrorHandler, Highlight, Aardvark_Error
import Exec
import sys
from Exec import Executor, createGlobals
from Types import Null, Scope
from Getch import getch
from sty import fg
import os
import shutil
import time

color_prompt = fg(255, 189, 122)
color_error = fg(229, 34, 34)
color_gray = fg(157, 162, 166)

installedLocation = os.getenv("AardvarkInstallLoc", "/home/runner/Aardvark-py/.adk/")
testdir = "/home/runner/Aardvark-py/tests/"
searchDirs = [os.path.join(installedLocation, "lib/")]

# Import module for colouring.
# Prettifying the ast
from Utils import prettify_ast

sys.setrecursionlimit(3500)


class Version:
    def __init__(self, major=0, minor=0, patch=0, type="stable", serial=1):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.serial = max(serial, 1)
        self.type = type.lower()

    def __str__(self):
        s = f"{self.major}.{self.minor}"
        if self.patch:
            s += f".{self.patch}"  # idk, maybe in the Chat tab?
        if self.type != "stable":  # Would it be easier to talk here?
            s += f" {self.type.capitalize()} {self.serial}"
        return s

    def __repr__(self):
        return str(self)


version = Version(1, 0, 0, "Interpretter (Python version)", 5)
python = sys.version_info
python = Version(
    python.major, python.minor, python.micro, python.releaselevel, python.serial
)


def runTest(code, values={}, ret=None, testfunct=None):
    x = run(code)
    if x["error"] or x["Global"] == None:
        raise ValueError(f'Error: {x["error"]}')
    scope = x["Global"]
    if ret != None and x["return"] != ret:
        raise ValueError(f'Error, {ret} != {x["return"]}')
    for i in values:
        if scope[i] != values[i]:
            raise ValueError(f"Error, {scope[i]} != {values[i]} for variable {i}")
    if testfunct:
        testfunct(x)
    return True


def run(
    text,
    file="<main>",
    printToks=False,
    printAST=False,
    Global=None,
    safe=False,
    is_strict=False,
    time_stats=False,
    bypass_eof=False
):
    lexer_time = 0
    parser_time = 0
    executor_time = 0
    ret = Null
    error = False
    try:
        lexer_start = time.time()
        errorhandler = ErrorHandler(text, file, py_error=True)
        lexer = Lexer.Lexer("#", "#*", "*#", True, False)
        toks = lexer.tokenize(text)
        if printToks:
            print(prettify_ast(toks))
        lexer_end = time.time()
        lexer_time = lexer_end - lexer_start
        parser = Parser.Parser(errorhandler, lexer, is_strict)
        ast = parser.parse()
        if printAST:
            print(prettify_ast(ast))
        parser_end = time.time()
        parser_time = parser_end - lexer_end
        executor = Exec.Executor(
            file, text, ast["body"], errorhandler, {}, True, safe, None, is_strict
        )
        if Global:
            executor.Global = Global
        ret = executor.run()
        executor_time = executor.executor_time
        lexer_time += executor.lexer_time
        parser_time += executor.parser_time
        if time_stats:
            print(
                f"Lexer: {lexer_time}\nParser: {parser_time}\nExecutor: {executor_time}"
            )
        Global = executor.Global
    except Aardvark_Error as e:
        error = str(e.args)
        if "Unexpected EOF." in error and bypass_eof:
            raise e
        print(e.output, file=sys.stderr)
    return {"return": ret, "Global": Global, "error": error}


# runTest('''
#   x = 5
#   (x = 7) if true
#   if x == 2*3+1 (x = x + 1)
#   if x == 8 {
#     x = 9
#   }
#   y = (5) if x < 100 else if x > 100 & x < 1000 (8) else (10)
# ''', {'x': 9, 'y': 5})


def runFile(file, *args, **kwargs):
    with open(file, encoding="utf-8") as f:
        text = f.read()
        return run(text, file, *args, **kwargs)


def highlighted_input(
    prompt: str, scope: Scope, input_history: list[str], eval_mode: bool = False
) -> (str, list[str]):
    buff = ""

    buff = ""
    picked_completion = 0
    last_completions = []

    escape_code = []
    auto_complete_scope = scope

    while True:
        valid_completions = []

        if buff != "":
            for line in input_history:
                if line.startswith(buff) and line != buff:
                    added = line[len(buff) :]
                    valid_completions.append(
                        (added, color_gray + added + fg.rs + f"\33[{len(added)}D")
                    )

        errorhandler = ErrorHandler(buff, "<main>", py_error=True)
        lexer = Lexer.Lexer("#", "</", "/>", True, True, True, False)
        tokens = lexer.tokenize(buff)

        attribTokens = tokens
        attributeStack = []
        currentCycle = 0
        cycleArray = input_history
        while (
            len(attribTokens) > 2
            and attribTokens[-1].type == Data.TokenTypes["Identifier"]
            and attribTokens[-2].value == "."
            and attribTokens[-2].type == Data.TokenTypes["Delimiter"]
        ):
            attributeStack.append(attribTokens[-1])
            attribTokens = attribTokens[:-2]
            if (
                len(attribTokens) >= 1
                and attribTokens[-1].type == Data.TokenTypes["Identifier"]
                and (
                    len(attribTokens) < 2
                    or attribTokens[-2].value != "."
                    or attribTokens[-2].type != Data.TokenTypes["Delimiter"]
                )
            ):
                attributeStack.append(attribTokens[-1])
                break

        if len(attributeStack) >= 1:
            current = scope
            attributeStack.reverse()
            for id in attributeStack[:-1]:
                val = current.get(id.value)
                if val:
                    current = val
            auto_complete_scope = current

        if len(tokens) >= 1 and tokens[-1].type == Data.TokenTypes["Identifier"]:
            for vname in auto_complete_scope.vars:
                if vname.startswith(tokens[-1].value) and vname != tokens[-1].value:
                    added = vname[len(tokens[-1].value) :]
                    valid_completions.insert(
                        0,
                        (added, color_gray + added + fg.rs + f"\33[{len(added)}D"),
                    )

        if len(last_completions) != len(valid_completions):
            picked_completion = 0
        else:
            for lc, rc in zip(last_completions, valid_completions, strict=True):
                if lc[0] != rc[0]:
                    picked_completion = 0
                    break
        valid_completions.sort(key=lambda x: len(x[0]))
        last_completions = valid_completions
        if picked_completion >= len(valid_completions):
            picked_completion = 0
        elif picked_completion < 0:
            picked_completion = len(valid_completions) - 1

        current_completion = ""
        if len(valid_completions) != 0:
            current_completion = valid_completions[picked_completion][1]

        print(
            "\33[2K\r"
            + prompt
            + Highlight(buff, {"linenums": False})
            + current_completion,
            end="",
            flush=True,
        )
        key = getch()
        time.sleep(0.02)  # Why?
        key_code = ord(key)
        if key_code == 27:
            escape_code = [27]
        elif key_code == 13:
            escape_code = []
            break
        elif key_code == 127 and len(buff) > 0:
            escape_code = []
            buff = buff[:-1]
        elif key_code == 3:
            raise KeyboardInterrupt()
        elif key_code == 9:
            escape_code = []
            if len(valid_completions) != 0:
                buff += valid_completions[picked_completion][0]

        # ARROW KEYS NOT TRIGGERING
        # It registers as [A and [B
        elif key_code == 38:
            print("\n\nHere\n\n")
            currentCycle += 1
            buff = cycleArray[len(cycleArray) - (currentCycle - 1)]
            if buff != "":
                cycleArray.append(buff)
                currentCycle += 1
        elif key_code == 40 and currentCycle > 0:
            currentCycle -= 1
            if currentCycle == 0:
                buff = ""
            else:
                buff = cycleArray[len(cycleArray) - (currentCycle - 1)]

        elif key.isprintable() and key_code not in [91, 65, 66]:
            # Doesn't allow me to print [, A, or B
            buff += key
        else:
            escape_code.append(key_code)

            if escape_code == [27, 91, 65]:
                picked_completion -= 1
            elif escape_code == [27, 91, 66]:
                picked_completion += 1

        if eval_mode:
            print()
            message = None

            custom_builtins = {}
            for name in dir(builtins):
                custom_builtins[name] = getattr(builtins, name)
            custom_builtins["print"] = fake_print
            custom_builtins["exit"] = fake_exit
            custom_builtins["quit"] = fake_exit

            try:
                res = eval(buff, {"__builtins__": custom_builtins}, eval_locals)
                message = color_gray + str(res)
            except Exception as e:
                message = color_gray + str(e).replace("\n", "")

            print("\33[2K\r" + str(message).replace("\n", "") + fg.rs, end="\33[1A")

    print("\33[2K\r" + prompt + Highlight(buff, {"linenums": False}))

    input_history.append(buff)

    return buff, input_history + [buff]


def runLive(
    debugmode=False,
    noret=False,
    printToks=False,
    printAST=False,
    experimental=False,
    safe=False,
    is_strict=False,
):
    print(f"Aardvark {version} \n[Python {python}]\n{sys.platform.upper()}")
    saved_scope = None
    input_history = []

    while True:
        file = "<main>"
        if experimental:
            text, input_history = highlighted_input(
                ">>> ",
                saved_scope if saved_scope else createGlobals(safe),
                input_history,
            )
        else:
            text = input(">>> ")
        if debugmode:
            if text == "$clear":
                print("\033[2J\033[H")
                continue
            if text.startswith("$test"):
                test_name = text.split(" ")[-1]
                file = testdir + f"{test_name}.adk"
                with open(file) as f:
                    text = f.read()
                print(f"Running test {test_name}...")

        while True:
            try:
                x = run(
                    text,
                    file,
                    printToks,
                    printAST,
                    Global=saved_scope if saved_scope else None,
                    safe=safe,
                    is_strict=is_strict,
                    bypass_eof=True
                )
                break
            except Aardvark_Error as e: # EOF
                openc = text.count("{") - text.count("}")
                if experimental:
                    newl, input_history = highlighted_input(
                        "... " + " " * openc * 2,
                        saved_scope if saved_scope else createGlobals(safe),
                        input_history,
                    )
                else:
                    newl = input("... " + " " * openc * 2)
                text += "\n" + newl
        if not noret:
            print(x["return"])
        saved_scope = x["Global"]

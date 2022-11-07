#This is a proof-of-concept for Aardvark error design.
#It is not a complete implementation.
#It is only a proof-of-concept.
#GHOSTWRITER wrote lines 2 and 3.

from sty import bg, fg, ef, rs
from Data import *
import Lexer
import sys

styles = {
    "String": fg(152, 195, 121) + ef.rs,
    "Function": fg(97, 175, 239) + ef.rs,
    "Number": fg(229, 192, 123) + ef.rs,
    "Keyword": fg(224, 108, 117) + ef.rs,
    "Operator": fg(86, 182, 194) + ef.bold,
    "Boolean": fg(229, 192, 123) + ef.rs,
    "background": bg(36, 39, 55) + ef.rs,
    "Comment": fg(92, 99, 112) + ef.italic,
    "Delimiter": fg(245, 245, 255) + ef.rs,
    "default": fg(171, 178, 191) + ef.rs,
    "suggestion": fg(255, 165, 0)
}


def genLine(line, digits):
    return ' ' * (digits - len(str(line))) + f'{line} │ '


def Highlight(code: str, opts={}):
    lexer = Lexer.Lexer("#", "</", "/>", True, True)
    lexer.tokenize(code)
    line = opts.get('startline', 1)
    output = (styles['background'] if opts.get('background', True) else ''
              ) + styles['default'] + (genLine(line, opts.get(
                  'leftpadding', 4)) if opts.get('linenums', True) else '')
    toknum = 0
    last = 0
    for token in lexer.output:
        if token.start_index > last + 1:
            output += styles['default'] + code[last + 1:token.start_index]
        #To restore things the lexer left out.
        if str(token.type) == 'String':
            output += styles[str(token.type)] + token.variation + str(
                token.value) + token.variation
        #To give strings their quotes back.
        elif token.value == '\n':
            line += 1
            output += styles['default'] + '\n' + (genLine(
                line, opts.get('leftpadding', 4)) if opts.get(
                    'linenums', True) else '')
        #To render the line numbers when there is a newline.
        elif str(token.type) == 'Identifier' and toknum < len(
                lexer.output) - 1 and str(
                    lexer.output[toknum + 1].type
                ) == 'Delimiter' and lexer.output[toknum + 1].value == '(':
            output += styles['Function'] + str(token.value)
        #For function calls
        elif str(token.type) in styles:
            output += styles[str(token.type)] + str(token.value)
        #Everything else that has a defined color.
        else:
            output += styles['default'] + str(token.value)
        #The random stuff that uses a default color
        toknum += 1
        last = token.end_index
    output += rs.all
    return output

def get_trace_line(index, line):
    header = "    at "
    fileloc = f" ― {line['filename']}:{line['line']}:{line['col']}"
    
    if index == 0:
        return header + line["name"] + fileloc
    return " " * len(header) + line["name"] + fileloc

def print_error(type: str, pos, msg, didyoumean, err_trace, code):
    padding = len(str(pos["lineend"])) + 1#To dynamicly adjust padding based on the larger line#
    lineno = pos["lineno"]
    didyoumean_par = didyoumean

    if pos["linestart"] < 0: pos["linestart"] = 0
    
    code = Highlight(code, {
        'startline': pos["linestart"]+1,
        'leftpadding': padding,
        'background': False
    })

    underline_start = max(pos.get("underline", {}).get("start"), 0)
    underline_end = max(pos.get("underline", {}).get("end"), 0)
    marker_pos = max(pos.get("marker", {}).get("start"), 0)
    marker_length = max(pos.get("marker", {}).get("length"), 0)
                        
    underline_str = len(code.split("\n")[-1]) * " "

    underline_str = underline_str[:underline_start] + \
                    "―" * (underline_end - underline_start) + \
                    underline_str[underline_end:]

    if marker_pos != None:
        underline_str = underline_str[:marker_pos - 1] + \
                        "^" * marker_length + \
                        underline_str[marker_pos - 1 + marker_length:]

    underline_str = underline_str.rstrip()
    error_underline = f'{" "*(padding+3)}{ef.bold + fg(225, 30, 10)}{underline_str}―>{ef.rs} {fg(225, 30, 10)}{msg}'
    
    code_lines = code.split("\n")
    code_lines[lineno] = code_lines[lineno] + "\n" + error_underline + styles["default"]

    if didyoumean_par != None:
        lines_mean = code_lines.copy()
        lines_mean[lineno] = f"{' ' * (padding - len(str(pos['lineno']+1)))}{styles['default']}{pos['lineno']+1} │ {didyoumean}"
        #Highlight(didyoumean, {
        #    'startline': pos["lineno"]+1,
        #    'leftpadding': padding,
        #    'background': False
        #})
        didyoumean = "\n".join(lines_mean[pos["linestart"]:pos["lineend"] + 1])
    
    code = "\n".join(code_lines[pos["linestart"]:pos["lineend"] + 1])
    
    traceback = ""
    if err_trace != None:
        traceback = "\n".join([
            get_trace_line(i, item) for i, item in enumerate(err_trace)
        ]) + "\n\n"

    if didyoumean_par != None: didyoumean = f'''\n
{fg.blue}ⓘ  did you mean:{styles["default"]}
{didyoumean}{fg.rs}'''
    else: didyoumean = fg.rs
    
    output = f'''{fg(225, 30, 10)}ⓧ  {type}Error in {pos["filename"]}:{pos["lineno"]+1}:{marker_pos if marker_pos != None else underline_start}
{traceback}{styles["default"]}{code}{didyoumean}'''
    print(output, file=sys.stderr)


#Everything is fixed now.
# print(Highlight(open('main.adk').read())) #Works file

class ErrorHandler:
    def __init__(self, code, filename, py_error=False):
        self.code = code
        self.filename = filename
        self.py_error = py_error

    def throw(self, type, message, options = {}):
        options["filename"] = self.filename
        options["linestart"] = options["lineno"] - 1
        options["lineend"] = options["lineno"] + 1
        
        print_error(
            type,
            options,
            message,
            options.get("did_you_mean", None),
            options.get("traceback", None),
            self.code
        )

        if not self.py_error:
            exit(1)
        else:
            raise Exception("py_error is True.")

if __name__ == "__main__":
    examplecode = '#print Hello World\nstdout|.write("Hello World\\n")\n#after'
    code_stack = [
        {
            "name": "this()",
            "line": 2,
            "col": 4,
            "filename": "main.adk"
        },
        {
            "name": "is_an()",
            "line": 5,
            "col": 3,
            "filename": "other.adk"
        },
        {
            "name": "example()",
            "line": 8,
            "col": 8,
            "filename": "test.adk"
        }
    ]
    
    print_error(
        'Syntax', #You can change how this works or make a class for Error or really whatever you think is best, this is still only a proof of concept. Later, I'm going to start writing the compiler.
        {
            # ok
            'linestart': 1,#Line of the code's start
            'lineend': 2,#Line of the code's end
            'lineno': 1,#Line the error is on
            'filename': 'main.adk',#File the error is in.
    
            # I cleaned up some of the positions so now they are in separate objects
            'marker': {
                'start': 8,
                'length': 6
            },
    
            'underline': {
                'start': 0,
                'end': 30
            }
        },
        '".write" is invalid. No object to get attribute of.',
        'stdout.write("Hello World\\n")',
        None,
        examplecode
    )
    #Wait, just noticed, the -- aren't working how they are suppossed to anyways.
    # This is not a real implementation, its just a proof-of-concept.
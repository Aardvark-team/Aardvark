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


def genLine(linenum, digits):
    return ' ' * (digits - len(str(linenum))) + f'{styles["default"]}{linenum} │ '


def Highlight(code: str, opts={}):
    lexer = Lexer.Lexer("#", "</", "/>", True, True)
    lexer.tokenize(code)
    line = opts.get('startline', 1)
    output = (styles['background'] if opts.get('background', False) else ''
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
    padding = len(str(pos["lineend"])) + 1#To dynamicly adjust padding based on the larger line num
    lineno = pos["lineno"]
    didyoumean_par = didyoumean

    if pos["linestart"] < 0: pos["linestart"] = 0

    code = Highlight(code, {
        'startline': 1,
        'leftpadding': padding,
        'background': False
    })

    underline_start = pos.get("underline", {}).get("start")
    underline_end = pos.get("underline", {}).get("end")
    marker_pos = pos.get("marker", {}).get("start")
    marker_length = pos.get("marker", {}).get("length")

    underline = (underline_start - 1) * ' ' + "―" * (underline_end - underline_start + 1)
    marker = (marker_pos - 1) * ' ' + '^' * (marker_length)
    underline_str = ""

    # whats this big for loop
    # This code helped me fix a few bugs
    #It basicly is just a different implementation of what the code was already suppossed to do, and it fixed a couple bugs
    # oh okay
  #idk why the old code didn't work, and I was stuck and couldn't find the problem, so I just rewrote it.
    
    for i in range(len(max(underline, marker))): #Look over both strings, ^ takes precedense over -
        if i >= len(underline) and i < len(marker):
          underline_str += marker[i]
        elif i >= len(marker):
          underline_str += underline[i]
        elif i < len(marker) and i < len(underline):
          if marker[i] != ' ':
            underline_str += marker[i]
          elif underline[i] != ' ':
            underline_str += underline[i]
          else: underline_str += ' '
        else: break
    #Token lines and columns now start at 1
    #This above code fixed a couple bugs.
    if marker_pos != None:
        underline_str = underline_str[:max(marker_pos - 1, 0)] + \
                        "^" * marker_length + \
                        underline_str[marker_pos - 1 + marker_length:]

    underline_str = underline_str.rstrip()
    error_underline = f'{" "*(padding+3)}{ef.bold + fg(225, 30, 10)}{underline_str}―>{ef.rs} {fg(225, 30, 10)}{msg}'
    
    code_lines = code.split("\n")
    code_lines[lineno-1] = code_lines[lineno-1] + "\n" + error_underline + styles["default"]

    linestart = pos["linestart"] - (1 if pos["linestart"] > 0 else 0)
    lineend = pos["lineend"] + (1 if pos["lineend"] + 1 < len(code_lines) else 0)
    
    if didyoumean_par != None:
        lines_mean = code_lines.copy()
        lines_mean[lineno-1] = f"{' ' * (padding - len(str(lineno)))}{styles['default']}{lineno} │ {didyoumean}"
        #Highlight(didyoumean, {
        #    'startline': pos["lineno"]+1,
        #    'leftpadding': padding,
        #    'background': False
        #})
        didyoumean = "\n".join(lines_mean[linestart:lineend])

    code = "\n".join(code_lines[linestart:lineend])
    
    traceback = ""
    if err_trace != None:
        traceback = "\n".join([
            get_trace_line(i, item) for i, item in enumerate(err_trace)
        ]) + "\n\n"

    if didyoumean_par != None: didyoumean = f'''\n
{fg.blue}ⓘ  did you mean:{styles["default"]}
{didyoumean}{fg.rs}'''
    else: didyoumean = fg.rs
    
    output = f'''{fg(225, 30, 10)}ⓧ  {type}Error in {pos["filename"]}:{pos["lineno"]}:{marker_pos if marker_pos != None else underline_start}
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
        options["linestart"] = options["lineno"] - (1 if options["lineno"] > 0 else 0)
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
    print(examplecode)
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
            'lineend': 3,#Line of the code's end
            'lineno': 2,#Line the error is on
            'filename': 'main.adk',#File the error is in.
    
            # I cleaned up some of the positions so now they are in separate objects
            'marker': {
                'start': 8,
                'length': 6
            },
    
            'underline': {
                'start': 1,
                'end': 30
            }
        },
        '".write" is invalid. No object to get attribute of.',
        Highlight('stdout.write("Hello World\\n")', {'linenums': False}),
        code_stack,
        examplecode
    )
    #Wait, just noticed, the -- aren't working how they are suppossed to anyways.
    # This is not a real implementation, its just a proof-of-concept.
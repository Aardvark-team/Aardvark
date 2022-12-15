from sty import fg
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def match_pattern(pattern, arr):
    if len(arr) != len(pattern):
        return False

    for part, item in zip(pattern, arr):
        if (part.startswith("[") and part.endswith("]")) or part == item:
            continue
        break
    else:
        return True

    return False


class ArgumentContext:
    def __init__(self, argp, positional, switches, keywords):
        self.positional = positional
        self.keywords = keywords
        self.switches = switches
        self.__argp = argp

    def help(self, message=None):
        self.__argp.print_help(message, printer=print)

    def __repr__(self):
        return f"Context(\n  positional={self.positional},\n  keywords={self.keywords},\n  switches={self.switches}\n)"
    def getSwitch(self, switch):
        return self.switches.get(switch, False)


class ArgumentParser:
    def __init__(self, name):
        self.__positional = []
        self.__switches = []
        self.__keywords = []
        self.__name = name
        self.__arg_descriptions = {}
        self.__pre_parse_callbacks = []
        
    def preparse(self, callback):
        self.__pre_parse_callbacks.append(callback)
        return callback
        
    def command(self, name=None, desc=None):
        if type(name) == str:
            name = name.split(" ")
        if name == None:
            name = []

        def action(callback):
            self.__positional.append([name, callback, desc])

        return action

    def keyword(self, name, desc=None):
        self.__keywords.append(name)
        if desc:
            self.__arg_descriptions[name] = desc

    def switch(self, name, desc=None):
        self.__switches.append(name)
        if desc:
            self.__arg_descriptions[name] = desc

    def print_help(self, message=None, printer=eprint):
        if printer == eprint:
            eprint(fg.red, end="")
        if message:
            printer(message, end="\n\n")

        printer(f"Usage: {self.__name} [command] [-switches, -keyword args]\n")

        printer("Commands:")
        for command, c, desc in self.__positional:
            if len(command) == 0:
                continue

            printer(
                f"  {command[0].ljust(10, ' ')}  {'' if not desc else f' - {desc}'}"
            )

        printer("\nSwitches and keyword arguments:")
        for name in self.__keywords + self.__switches:
            desc = self.__arg_descriptions.get(name)
            printer(
                f"  {f'-{name}, --{name}'.ljust(20, ' ')}  {'' if not desc else f' - {desc}'}"
            )

        if printer == eprint:
            eprint(fg.rs, end="")

    def parse(self, string):
        positional = []
        switches = {}
        keywords = {}
        
        for callback in self.__pre_parse_callbacks:
            if callback(string):
                return
                
        i = 0
        while i < len(string):
            if string[i].startswith("-"):
                name = string[i].lstrip("-")

                if name in self.__keywords:
                    if i + 1 >= len(string):
                        self.print_help(f"Missing value for keyword argument '{name}'.")
                        exit(1)

                    keywords[name] = string[i + 1]

                    i += 1
                elif name in self.__switches:
                    switches[name] = True
                else:
                    self.print_help(f"Unknown keyword argument '{name}'.")
                    exit(1)
            else:
                positional.append(string[i])
            i += 1
        for pattern, callback, _ in self.__positional:
            if match_pattern(pattern, positional):
                callback(ArgumentContext(self, positional, switches, keywords))
                break
        else:
            self.print_help(f"Unknown command '{' '.join(positional)}'.")
            exit(1)


if __name__ == "__main__":
    argp = ArgumentParser("adk")
    argp.switch("version", "Print the current version.")

    @argp.command()
    def main(ctx):
        print(ctx)
        if ctx.switches.get("version"):
            print("Version info")
        else:
            ctx.help()

    @argp.command("compile [file]", "Compile a file.")
    def compile(ctx):
        print(ctx)
        print("compiling file...")

    @argp.command("help", "Show this menu.")
    def help(ctx):
        print(ctx)
        ctx.help()
        
            
    argp.parse(sys.argv[1:])

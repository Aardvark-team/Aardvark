#!/usr/bin/env python
from Run import *
import sys

if __name__ == "__main__":
    import ArgumentParser
    argp = ArgumentParser.ArgumentParser("adk")
    argp.switch("version", "Print the current version.")
    argp.switch("toks", "Print tokens. If not present, toks are not printed.")
    argp.switch("ast", "Print AST. If not present, ast is not printed.")
    argp.switch('debug', 'Allow $test and $clear commands.')
    argp.switch('no-ret', 'if set, return values are not printed in live mode.')
    
    @argp.command()
    def main(ctx):
        if ctx.getSwitch("version"):
            print("Version info")
        else:
            runLive(ctx.getSwitch('debug'), ctx.getSwitch('no-ret'), ctx.getSwitch('toks'), ctx.getSwitch('ast'))

    @argp.command("run [file]", "Compile a file.")
    def Run(ctx):
        runFile(ctx.positional[1], ctx.getSwitch('toks'), ctx.getSwitch('ast'))

    @argp.command('live', 'Start an interactable language shell.') #''Run a live thing (idk what to call it)')
    def live(ctx):
        runLive(ctx.getSwitch('debug'), ctx.getSwitch('no-ret'), ctx.getSwitch('toks'), ctx.getSwitch('ast'))
        
    @argp.command("help", "Show this menu.")
    def help(ctx):
        ctx.help()

    @argp.command("setup-lib [lib]", "Show this menu.")
    def setup_lib(ctx):
        dirloc = ctx.positional[1]
        dir = dirloc.split("/")[-1]
        if os.path.isfile(dirloc):
            name = ".".join(dir.split(".")[:-1])
            os.makedirs(searchDirs[0]+name)
            shutil.copy(dirloc, searchDirs[0]+name)
        elif not os.path.isdir(dirloc):
            print(f'ERROR: "{dirloc}" not found.')
        else:
            shutil.copytree(dirloc, searchDirs[0] + dir)

    @argp.command("[file]", "Default action if only a file is passed.")
    def run_file(ctx):
        file = ctx.positional[0]

        if "/" in file or "." in file:
            runFile(file, ctx.getSwitch('toks'), ctx.getSwitch('ast'))
        else:
            ctx.help(error = True, message = f"Unknown command '{file}'.")

    """
    # The command above does the same thing without any preparse things.
    # argp.command basically takes a pattern to match the array with.
    
    @argp.preparse
    def dotslash(args):
        opts = []
        other = []
        for arg in args:
            if arg.startswith('-'):
                opts.append(arg.lstrip('-'))
            else:
                other.append(arg)
        if len(other) == 1 and other[0].startswith('./'):
            runFile(other[0].removeprefix('./'), 'toks' in opts, 'ast' in opts)
            return True
    """

            
    argp.parse(sys.argv[1:])
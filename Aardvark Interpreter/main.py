#!/usr/bin/env python
from Run import *
import sys
import os
import subprocess

if __name__ == "__main__":
    import ArgumentParser
    from sty import fg, ef, rs

    argp = ArgumentParser.ArgumentParser("adk")
    argp.switch("version", "Print the current version.")
    argp.switch("toks", "Print tokens. If not present, toks are not printed.")
    argp.switch("ast", "Print AST. If not present, ast is not printed.")
    argp.switch("debug", "Allow $test and $clear commands.")
    argp.switch("no-ret", "if set, return values are not printed in repl mode.")
    argp.switch("e", "Use experimental repl.")
    argp.switch("safe", "Use safe mode.")
    argp.switch("help", "Displays the help menu.")
    argp.switch("canary", "Install the canary version of aardvark.")

    @argp.command()
    def main(ctx):
        if ctx.getSwitch("version"):
            print("Version info")
        elif ctx.getSwitch("help"):
            ctx.help()
        else:
            runLive(
                ctx.getSwitch("debug"),
                ctx.getSwitch("no-ret"),
                ctx.getSwitch("toks"),
                ctx.getSwitch("ast"),
                ctx.getSwitch("e"),
                ctx.getSwitch("safe"),
            )

    @argp.command("run [file]", "Compile a file.")
    def Run(ctx):
        if ctx.getSwitch("help"):
            print(
                f"{ef.bold+fg.red}Usage: {fg.rs}adk run <file> [--safe, -ast, -toks]{rs.bold_dim+fg.rs}\n"
            )
        else:
            runFile(
                ctx.positional[1],
                ctx.getSwitch("toks"),
                ctx.getSwitch("ast"),
                safe=ctx.getSwitch("safe"),
            )

    @argp.command("repl", "Start an interactable language shell.")
    def live(ctx):
        if ctx.getSwitch("help"):
            print(
                f"{ef.bold+fg.red}Usage: {fg.rs}adk repl [--safe, -ast, -toks, -no-ret, -e, --debug]{rs.bold_dim+fg.rs}\nRun {ef.bold}adk help{rs.bold_dim+fg.rs} for more info.\n"
            )
        else:
            runLive(
                ctx.getSwitch("debug"),
                ctx.getSwitch("no-ret"),
                ctx.getSwitch("toks"),
                ctx.getSwitch("ast"),
                ctx.getSwitch("e"),
                ctx.getSwitch("safe"),
            )

    @argp.command("help", "Shows help menu.")
    def help(ctx):
        ctx.help()

    @argp.command("setup-lib [lib]", "Creates a new library.")
    def setup_lib(ctx):
        dirloc = ctx.positional[1]
        dir = dirloc.split("/")[-1]
        if os.path.isfile(dirloc):
            name = ".".join(dir.split(".")[:-1])
            os.makedirs(searchDirs[0] + name)
            shutil.copy(dirloc, searchDirs[0] + name)
        elif not os.path.isdir(dirloc):
            print(f'ERROR: "{dirloc}" not found.')
        else:
            shutil.copytree(dirloc, searchDirs[0] + dir)

    @argp.command("upgrade", "Upgrade aardvark")
    def upgrade_command(ctx):
        adk_folder = os.environ["AARDVARK_INSTALL"]

        if ctx.getSwitch("canary"):
            commmands = [
                "git init",
                "git remote add origin https://github.com/Aardvark-team/Aardvark/",
                "git fetch origin",
                "git reset --hard origin/main"
            ]

            for command in commmands:
                subprocess.run(command, cwd=adk_folder, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            print(fg.green + "Updated aardvark successfully!" + fg.rs)
        else:
            print(fg.red + "This installer can only download Aardvark canary for now." + fg.rs)

    @argp.command("[file]", "Default action if only a file is passed.")
    def run_file(ctx):
        file = ctx.positional[0]

        if "/" in file or "." in file:
            runFile(file, ctx.getSwitch("toks"), ctx.getSwitch("ast"))
        else:
            ctx.help(error=True, message=f"Unknown command '{file}'.")

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

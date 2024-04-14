#!/usr/bin/env python
from Run import *
import sys
import os
import shutil
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
    argp.switch("pick", "Choose which version of aardvark to install.")

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
        elif ctx.getSwitch("pick"):
            commmands = [
                "git init",
                "git remote add origin https://github.com/Aardvark-team/Aardvark/",
                "git fetch origin",
            ]

            for command in commmands:
                subprocess.run(command, cwd=adk_folder, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            print(f"{ef.bold}? {ef.rs}Please choose a version from the following list:")
            proc = subprocess.Popen("git tag --sort=creatordate", cwd=adk_folder, shell=True, stdout=subprocess.PIPE)
            stdout, _ = proc.communicate()
            tags = list(filter(bool, stdout.decode("utf-8").split("\n")))
            tags.reverse()
            tags.insert(0, "canary")

            last_char = ""
            position = 0
            count = 2
            last_tag_count = 0

            while True:
                position = min(len(tags) - 1, max(0, position))
                
                if position <= count:
                    start_index = 0
                    end_index = count * 2 + 1
                elif position + count >= len(tags):
                    start_index = max(0, len(tags) - count * 2 - 1)
                    end_index = len(tags)
                else:
                    start_index = max(0, position - count)
                    end_index = min(position + count + 1, len(tags))
                
                curr_tags = tags[start_index:end_index]

                if last_tag_count > 0:
                    print(f"\033[{last_tag_count}A", end="", flush=True)

                for i, tag in enumerate(curr_tags):
                    print(f"\33[2K\r ({'o' if i == position - start_index else ' '}) {tag}")

                last_tag_count = len(curr_tags)
                key = getch()

                if key == b'\x03' or key == b'\x1B':
                    print(fg.red + "Cancelled." + fg.rs)
                    break

                if key == b'\r':
                    git_target = tags[position]
                    target = git_target

                    if target == "canary":
                        git_target = "origin/main"

                    subprocess.run(f"git reset --hard {git_target}", cwd=adk_folder, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(fg.green + f"Updated to aardvark {target} successfully!" + fg.rs)
                    break

                if last_char == b'\x00' and key == b'P':
                    position += 1

                if last_char == b'\x00' and key == b'H':
                    position -= 1

                last_char = key
        else:
            commmands = [
                "git init",
                "git remote add origin https://github.com/Aardvark-team/Aardvark/",
                "git fetch origin",
            ]

            for command in commmands:
                subprocess.run(command, cwd=adk_folder, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            proc = subprocess.Popen("git tag --sort=creatordate", cwd=adk_folder, shell=True, stdout=subprocess.PIPE)
            stdout, _ = proc.communicate()
            tags = list(filter(bool, stdout.decode("utf-8").split("\n")))
            target = tags[len(tags) - 1]

            subprocess.run(f"git reset --hard {target}", cwd=adk_folder, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(fg.green + f"Updated to aardvark {target} successfully!" + fg.rs)

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

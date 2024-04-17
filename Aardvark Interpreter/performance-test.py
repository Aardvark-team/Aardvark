import Run

import cProfile
from pathlib import Path
import os

current_directory = Path(__file__).resolve().parent

path = current_directory / "../Aardvark Compiler/new-Parser.adk"
path = path.resolve()


def test():
    Run.runFile(path)


cProfile.run("test()", sort="tottime")

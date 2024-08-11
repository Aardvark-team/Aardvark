import Run

# import cProfile
from pathlib import Path
import os

current_directory = Path(__file__).resolve().parent

path = current_directory / "../Aardvark Compiler/Parser-test.adk"
path = path.resolve()


def test():
    for i in range(10):
        Run.runFile(path)


test()
# cProfile.run("test()", sort="tottime")
#

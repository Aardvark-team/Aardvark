from distutils.core import Extension, setup
from Cython.Build import cythonize

# define an extension that will be cythonized and compiled
ext = Extension(
    name="Run",
    sources=[
        "Run.py",
        "Parser.py",
        "Lexer.py",
        "Exec.py",
        "Data.py",
        "Operators.py",
        "Types.py",
        "nlp.py",
        "Getch.py",
        "sty.py",
        "Utils.py",
        "ArgumentParser.py",
        "Error.py",
    ],
)
setup(ext_modules=cythonize(ext))

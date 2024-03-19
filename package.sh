#!/bin/sh


# Steps to run:
# 1. Go one directory up
# 2. Duplicate the Aardvark directory.
# 3. Rename the duplicate "adk"
# 4. Run this script:

zip -r adk.zip adk -x "adk/.git/*" "adk/__pycache__/*" "adk/.gitignore" "adk/Aardvark Interpreter/__pycache__/*" "adk/Tensovark/__pycache__/*" "adk/package.sh"
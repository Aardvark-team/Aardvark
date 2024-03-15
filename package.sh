#!/bin/sh
zip -r adk.zip adk -x "adk/.git/*" "adk/__pycache__/*" "adk/.gitignore" "adk/Aardvark Interpreter/__pycache__/*" "adk/Tensovark/__pycache__/*" "adk/package.sh"
# Installation
### UNIX
You can install Aardvark with this command:
```sh
sh <(curl -fsSL https://raw.githubusercontent.com/Aardvark-team/Aardvark/main/install.sh)
```

### Windows
```powershell
& $([scriptblock]::Create((iwr https://raw.githubusercontent.com/Aardvark-team/Aardvark/main/install.ps1)))
```
You can add `-branch canary` to install the lastest changes (windows installer only).

This will add a `.adk` folder to your home directory which includes the Aardvark source.
It will also add `~/.adk/bin` to your PATH, which gives you access to the commands `adk` and `adkc`.

# Aardvark-py Version 1.0 Test
This first implementation of Aardvark is written in Python. 
This is an interpreted language meant to be easy and extensible.
The real version will be compiled. You can see our progress on development in the Aardvark Compiler folder.

## Using the command
Run `adk help` in the terminal to get started.

# Documentation
Documentation is avaliable on the documentation repo: https://github.com/Aardvark-team/Documentation

More, information, some of which is outdated can be found on our old documentation website: https://aardvark-docs.replit.app/.

# Why Python?
We don't care what language it is written in, we just wanted to make a version of the language as soon as possible so that we can get to work on the self-hosted compiler.

# AdkCode
AdkCode is an online Aardvark code editor with the ability to run code. It is currently updated to Aardvark  Test 5.1
You can try AdkCode [here](https://adkcode.replit.app/).

##### NOTE: filesystem access will be denied and certian abilities restricted within this enviroment.

# VSCode extension
Clone [the extension repository](https://github.com/Aardvark-team/Aardvark-vscode-extension) and then add that to your `~/.vscode/extensions/` folder (UNIX) or `%USERPROFILE%\.vscode\extensions` (Windows).
For now it only provides syntax highlighting and a run button.

# Contributing 
View the list of things that need to be implemented [here](https://github.com/orgs/Aardvark-team/projects/3).

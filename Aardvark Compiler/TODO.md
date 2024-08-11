### TODO: make this TODO

## Lexer:
Turns text to tokens
#### All done! (in my testing at least)

## Parser:
Turns tokens to AST
Mostly done

## Optimizer:
 Takes AST and evaluates it, removing things that are unnecessary. 
 This will probably require multiple passes.
 All variables with only one reference (creation) will be deleted.
 All functions whose value can be determined at compile time will be run, and the function call replaced with that value. This will make it seem a lot faster.
 All ifs that can be determined false at compile time will be removed, and all ifs that can be determined true at compile time will be run without the if statement
 etc...
 Emits low level AST
## Compiler:
Turns low level AST to LLVM AST, and compiles with llvm platform optimization.
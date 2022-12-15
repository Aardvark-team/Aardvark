### TODO: make this TODO

## Lexer:
Turns text to tokens
#### All done! (in my testing at least)

## Parser:
Turns tokens to AST
 - [ ] Start building

## Optimizer:
 Takes AST and evaluates it, removing things that are unnessasary. 
 This will probably require multiple passes.
 All variables with only one reference will be deleted.
 All functions whose value can be determined at compile time will be run, and the function call replaced with that value. This will make it seem a lot faster.
 All ifs that can be determined false at compile time will be removed, and all ifs that can be determined true at compile time will be run without the if statement
 etc...

## Compiler:
Turns AST to LLVM AST, and compiles with maximum llvm optimization.
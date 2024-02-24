# The ADK Command
## Code Management
`adk compile <filename>.adk [output=filename]` Compiles <filename.adk> and produces an executable file `filename`.
`adk run <filename>.adk` Compiles and runs the program in-place
`adk check <filename>.adk` Does optimizations and error checking, but does not run the code or produce an executable
`--format` An option to format, lint, and optimize the code while compiling, running, or checking. Much faster than separate `adk format` because the AST can be reused instead of having to reparse the whole thing.
`adk format <filename>.adk` Formats the code.

## Package Management
`adk install <package-name>` Installs package <package-name>
`adk uninstall <package-name>` Uninstalls package <package-name>
`adk update <package-name>` Updates package <package-name>

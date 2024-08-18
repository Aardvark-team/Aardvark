# <Name goes here> Language Reference

This language is defined upon the principals of a modular design.

To define a variable, simply use `let`. All variables are preceded by `$` during use. This makes it easy to distinguish in many contexts. Example:

```
@include "std"

let x = 5 # Variable definition
$x # Variable use

let y = {
    a = 5
    b = 6
    c = 7
}
$y."c" # 7
let z = "b"
$y.$z # 6

let n = 0
function f(0) then
    ret 0
end
overload f(1) then
    ret 1
end
overload f(n) then # Overload for any other n
    ret f($n-1) + f($n-2)
end
```

Everything is defined manually:

```
@define `if @expression=$expression then @code=$code end` then
    @embed asm then

    end
end
```

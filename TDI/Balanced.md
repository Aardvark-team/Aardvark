## Symbols and Operators:

### Undecided Use

- `&` Unknown, no mathematical uses (compile-time directives??)
- `:` Unknown, no mathematical use (intervals??)
- `~` No stand-alone purpose. Used before logical operators to convert them to bitwise operators

### Mathematical Operators:

- `!` a! (Factorial) OR !a (Subfactorial)
- `\` a \ b (Set subtraction, also character escape in strings)
- `|` a | b (Such that) OR |a| (absolute value)
- `*` a \* b (Multiplication)
- `-` a - b (Subtraction) OR -a (negation)
- `+` a + b (Addition) OR +a (identity)
- `/` a / b (Division)
- `<` a < b (Less than)
- `<=` a <= b (Less than or equal to)
- `>` a > b (Greater than)
- `>=` a >= b (Greater than or equal to)
- `=` a = b (Equality)
- `!=` ≠ = ¬(a = b) (Not equal)
- `in` a ∈ b (Contains)
- `has` a ∋ b (Has)
- `not` ¬a (complement/negation)
- `or` a ∨ b (Logical or)
- `and` a ∧ b (Logical and)
- `xor` a ⊕ b (Logical exclusive or, symmetric Difference when a and b are sets)
- `~not` Bitwise negation
- `~or` Bitwise or
- `~and` Bitwise and
- `~xor` Bitwise exclusive or
- `mod` a mod b
- `union` a ∪ b (Union, also combines arrays)
- `intersect` a ∩ b (Intersection)
- `<=>` a <=> b (If and only if)
- `>>` a >> b (Right shift)
- `<<` a << b (Left shift)
- `>>>` a >>> b (Rotate right)
- `<<<` a <<< b (Rotate left)
- `%` a% = a/100 (Percentage)
- `^` a ^ b (Exponentiation)

### Special Operators:

- `@` @a (Reference)
- `?` a? OR a?b (If a exists, returns a, otherwise returns b or null)
- `...` ...a (Spread operator)
- `..*` a..*b (Spreads b of a) Example: `[1..*5] = [1, 1, 1, 1, 1]`
- `any` any a (The set of all possible values of type a)
- `as` a as b (Raw type cast)

### Special:

- `;` Optional end line
- `.` Property or member access
- `_` Underscore, used for number base and in variable names
- `::` Interval, Example: `::[1, 2)` ? ? ? ? Is this the best operator for it?
- `'` String
- `"` String
- `` ` `` String
- `,` Comma
- `$` Special
- `#` Comment
- `:=` Reassignment

### Control Flow Keywords:

- `include` - `include x`, `include x, y, z`, `include x as y`, `include x as y with C` (compile-time)
- `if` - `if condition { ... } else { ... }`
- `loop` - `loop { ... }`, `name loop { ... }`, `loop name { ... }`
- `break` - `break`, `break name`
- `continue` - `continue`, `continue name`
- `return` - `return`, `return value`
- `yield` - `yield`, `yield value` # Yields a value from the generator.
- `let` - `let name = value`, `let name = value, name2 = value`
- `mutable` - `mutable name = value`, `mutable name = value, name2 = value`
- `check` Checks if a condition is true
- `construct` Creates a construct (compile-time)
- `infer` Sets type inference for builtin things. (compile-time)
- `with` [x = 5, y = 6] with [x = 3, z = 10] = [x = 3, y = 6, z = 10]
- `implements` Can also be used as an operator
- `await` - stops execution until an expression is truthy. A promise is truthy when it is fulfilled.
- `reserve` - reserves a keyword for use as operators or in constructs.
- Something for compile-time execution.

## Control Flow:

```
let x = 5
x = 7 # Error

mutable y = 5
y := 7 # Fine

if x = 5 {
    stdout.write("x is 5\n")
} else {
    stdout.write("x is not 5\n")
}

loop {
    stdout.write("Hello, World!\n")
    break
}

name loop {
    break name
}
```

## Comparison:

The only builtin conditional construct is `if`. There is no `while` or `for`, instead we have `loop`, which can be used in place of either of them.

- `check` allows you to check if an expression is true or false. Assignment is not allowed in comparison contexts. We support operator chaining.

```
mutable x = 5 # Assignment
x := 7 # Reassignment

check x = 8 # Comparison: false

check 0 < x < 10 # Comparison: true

let y = check x = 7 # Assignment to a Comparison: true

if x = 7 { # Comparison: true

}
if 3 > x > -7 { # Comparison: false

}
```

## Type annotations:

Type annotations are strictly enforced by the compiler.

```
let number x = 5

let f(number x) -> number = x + 1
```

## Compile-time execution:

## Specific Restraints:

The purpose of a type system is to be able to restrict values and how they are used.

```
mutable number x in {x | 0 < x < 10} = 5

x := 3 # Fine
x := 11 # Error

let my_restraint = {x | 0 < x < 10}
let my_restraint = any number x where 0 < x < 10 # another way?? Should we support this?
let my_restraint = any number x | 0 < x < 10 # yet another way?? Should we support this?
# Intervals??

mutable my_restraint y = 5
y := 11 # Error
```

## Structures:

Structures can be either unlabeled or labeled.

```
# An unlabeled structure
let array = [1, 2, 3]
array.0 # 1

# A labeled structure
let Hudson = [
    name = "Hudson"
    mutable age = 16
]

Hudson.0 # "Hudson"
Hudson.name # "Hudson"
```

Structure types:

```
type three_numbers = [number, number, number] # This is a template for an unlabeled structure.
type three_numbers = [number..*3]
let three_numbers x = [1, 2, 3]

# A labeled structure type
type Person = [
    let string name = "Placeholder" # This one has a default value
    mutable number age
] # A template is a template for a structure. It can be used like a type.


let Person Hudson = [name="Hudson", age=16]
let Person Spencer = ["Spencer", 14] # More concise
let x = Person [name = "Hudson", age = 16]
# `with` is a keyword can be used to construct a structure based off of a template.
```

## Functions:

```
let f(number x) -> number = x + 1

# Functions can also be passed around like values.

let g((function(number) -> number) f, x: number) -> number = f(x)
```

## Types, Restraints, and Unions:

```
# We need a way to create a union of two types, values, etc...
# Values as types like in Typescript and Python's `typing.Literal`

let my_union = {5, 6, 7} union any string

# Types are not first class

let y in my_union = 9 # Error

let z in my_union = "Hello" # Fine
```

## Generics:

Generics allow you to write flexible and reusable code by enabling functions and data structures to handle a variety of types without knowing the specific type in advance. This capability facilitates the use of a single implementation to operate on multiple types, adapting to the needs of different contexts.

```
let identity($type x in my_union) -> $type = x

if x in any string {
    # x is a string.
}
```

## Loops:

```
mutable x = 0
outer loop { # A named loop. The name is optional
    mutable y = 0
    inner loop {
        y := y + 1
        if x * y = 25
            break outer
        if y >= 10
            break inner
    }
    x := x + 1
    if x >= 10
        break outer
}
```

## Info:

In the document, I listed operators, including some for set union and intersection. Type inference can be used anywhere; the examples included type annotations mainly for demonstration purposes. The type system described there allowed me to define the entire string type in two lines; it wouldn't be very difficult create other types of strings or really any other types.

The compiler will be somewhat computationally expensive, but using advanced caching and parallelization strategies, we can keep the total compile-time to a minimum.

We will have plenty of standard library features. Our language will have inter-interoperability with other programming languages via an extension system. Here is an example:

```

include C

include stdio with C # includes C's stdio library

```

Inside the C library, some special functions are defined that tell the compiler how to use C programs within this language. The same can be done with any other language, thus giving us the largest standard library of any language since we can borrow from any of them.

The errors are handled at compile time. A member of our team designed an absolutely beautiful error message system that truly just blows everything else out of the water.

Our target audience is just about everyone. We want to design a language that goes back to the base of what it means to code. It would be most easily learned by beginners, because its design does not resemble other languages.

The priorities of the language are as follows:

1. Ease and simplicity. A child should be able to understand it and a professional should find even the toughest of tasks a breeze to complete.

2. Helpfulness. The language should make the programmer's job as easy as possible by finding issues before they occur.

3. Performance and speed. Our goal is to be the fastest programming language in the world. To do so, we are building a first-of-its-find optimization system that is able to store dynamic resources in faster, static, cached memory. In addition, we do clock-cycle-level performance optimizations around the whole program. Everything is optimized.

Memory management is handled automatically. There should generally be no need for manual memory management. However, it is allowed if the programmer feels a need to do so.

## stdlib.types

```
type character = ({x | 0 <= x <= 127} U {x | 192 <= x <= 223} U {x | 224 <= x <= 239} U {x | 240 <= x <= 247} U {x | 128 <= x <= 191}) \ {x | 248 <= x <= 255}

type string = [...utf8_character]

type null # A type with only one value: null
let null null # Define the value null with a type of null.

type boolean = {0, 1}
let boolean true = 1
let boolean false = 0

infer check = boolean # Sets type inference for condition results to type boolean
infer "" = string # Sets type inference for double quoted strings to type string
infer '' = string # Sets type inference for single quoted strings to type string
infer `` = string # Sets type inference for backtick strings to type string
infer void = null # Sets type inference for void function return values to type null

```

### Usage:

```
from stdlib.types include string, null, true, false, boolean, character
from stdlib.io include stdout, stdin, stderr, prompt

let x = "Hello"

stdout.log(x) # Hello

let y = prompt("What is your name? ")
```

## Await/Async

All builtin io functions are async.

## Operator Overloading

Operator behavior for types other than those that are builtin is not defined by default.

## Creating Operators

```
# Here we will create an operator called nor

reserve "nor"

let a nor b = not (a or b)
```

## Constructs

```
reserve while
construct while (expression condition) (body code) {
    loop {
        if not condition()
            break
        code()
    }
}
```

Valid construct types:

- `expression` – An expression. Given as a function.
- `body` – A code block. Given as a function.
- `""` – Anything within double quotes.
- `''` – Anything within single quotes.
- ` `` ` – Anything within backticks.
- `identifier` – A variable name.
- `definition` – A variable definition as would be seen with let. Given as a function that takes one argument: the value to set it to.

Anything within [] will be optional in the construct. Example:

```
construct [(identifier name)] while (expression condition) (body code) {
    $name loop {
        if not condition()
            break
        code()
    }
}
```

This code allows the user to optionally give the loop a name.

## Structures of types.

```
option Choice = [
    Rock
    Paper
    Scissors
] # Defines 3 types, all grouped under the structure Choice

option Shape = [
    Circle = [number]
    Square = [number]
    Rectangle = [number, number]
]
let Shape.Circle circle = [5]
```

## Type compatibility

## Exact numbers

The `exact` type implements the base `number` type but uses a different implementation for operations that keeps all values exact.

```
from stdlib.exact include exact
from math.constants include π
from math.trigonometry include sin, cos, tan

infer number = exact # Makes all numbers exact by default, unless specified otherwise

stdout.log(5/2) # 5/2

stdout.log(cos(π/6)) # sqrt(3)/2
```

## Arbitrary-precision numbers

TODO: figure out how to do this

## Finding valid types

Let's say we have a to_string function that any type may overload to add support.

```
let to_string(string x) {...}
let to_string(number x) {...}
# etc...
```

And we have `stdout.log` that wants to take anything that can be converted to a string:

```
let log(x) {
    let string_x = to_string(x)
}
```

How can we type `x` such that it represents any type that is valid in `to_string`?
TODO: adjust generic system to support this.

#### Function parameter type deconstruction???

??????? should this exist??

```
type (t) = to_string
# t is the type of the first parameter of to_string
```

## Sets of types (like unions)

```
type t = {string, boolean, 5} # Can be either string, boolean, or 5

mutable t x = "Hello"

x := true # Fine
x := 6 # Error
```

## Function signatures

```
let add(number x, number y) -> number = x + y
let subtract(number x, number y) -> number = x - y

let add multiply = lambda(x, y) x * y # Defines a function that
```

## String to int

```
let string_to_integer(string x) -> number {
    mutable index = 0
    mutable result = 0
    loop {
        let exponent = length(x) - index - 1

        if (x.(index) = "0")
            result := result + 0 * 10^exponent
        else if (x.(index) = "1")
            result := result + 1 * 10^exponent
        else if (x.(index) = "2")
            result := result + 2 * 10^exponent
        else if (x.(index) = "3")
            result := result + 3 * 10^exponent
        else if (x.(index) = "4")
            result := result + 4 * 10^exponent
        else if (x.(index) = "5")
            result := result + 5 * 10^exponent
        else if (x.(index) = "6")
            result := result + 6 * 10^exponent
        else if (x.(index) = "7")
            result := result + 7 * 10^exponent
        else if (x.(index) = "8")
            result := result + 8 * 10^exponent
        else if (x.(index) = "9")
            result := result + 9 * 10^exponent
        else
            return 0

        index := index + 1

        if index = length(x)
            return result
    }
}

from stdlib.io include prompt

let input = prompt("Enter a number: ")

let number result = string_to_integer(input)

```

## Match

Using unlabeled templates:

```
option Shape = [
    Circle = [number]
    Square = [number]
    Rectangle = [number, number]
]

let get_area(Shape x) -> number {
    return match x {
        Circle [r] = π * r ^ 2
        Square [s] = s ^ 2
        Rectangle [w, h] = w * h
    }
}

let my_circle = Shape.Circle [5]
let area = get_area(my_circle)
```

Using labeled templates:

```
option Shape = [
    Circle = [number radius]
    Square = [number side]
    Rectangle = [number width, number height]
]

let get_area(Shape x) -> number = match x with Shape {
    Circle [radius = r] = π * r ^ 2
    Square [side = s] = s ^ 2
    Rectangle [width = w, height = h] = w * h
}

let my_circle = Shape.Circle [radius = 5]
let area = get_area(my_circle)
```

OR, you can use `type`:

```
let positive = {x | x > 0}
option Shape = [
    Circle = positive
    Square = positive
    Rectangle = [number width, number height]
]

let get_area(Shape x) -> number = match x with Shape {
    Circle [radius = r] = π * r ^ 2
    Square [side = s] = s ^ 2
    Rectangle [width = w, height = h] = w * h
}

let my_circle = Shape.Circle [radius = 5]
let area = get_area(my_circle)
```

## Type functions:

A type function is a function, but for types. It can be used to generate types.

```
type Pair(T) = [T, T]
```

## $

The `$` operator is used to insert a value where a variable definition is expected.

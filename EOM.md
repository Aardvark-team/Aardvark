```
type utf8_character = 0...127 U 49408...57343 \ 49280...49407 U 14712960...15794175 \ (14712960...14745599 U 15138816...15155200) U 4034953344...4103067391 \ 4034953344...4041910271

type ascii_character = 0...127
type extended_ascii_character = 0...255
# character is now its own data type

type utf8_string = [...utf8_character]
type ascii_string = [...ascii_character]
type extended_ascii_string = [...extended_ascii_character]

type string = utf8_string | ascii_string | extended_ascii_string
```

## Undecided Use
`&` ?? (No mathematical use)

## Mathematical Operators
`!` a! (Factorial)
`\` a \ b (Set subtraction, also character escape in strings)
`|` a | b (Such that)
`*` a * b (Multiplication)
`-` a - b (Subtraction)
`+` a + b (Addition)
`/` a / b (Division)
`<` a < b (Less than)
`<=` a <= b (Less than or equal to)
`.` Property or member access
`>` a > b (Greater than)
`>=` a >= b (Greater than or equal to)
`=` a = b (Equality)
`!=` ≠ = ¬(a = b) (Not equal)
`in` a ∈ b (Contains)
`!in` a ∉ b = ¬(a ∈ b) (Does not contain)
`has` a ∋ b (Has)
`!has` a ∌ b = ¬(a ∋ b) (Does not have)
`not` ¬a (complement/negation)
`or` a ∨ b (Logical or)
`nor` a ∨̸ b = ¬(a ∨ b) (Logical not or)
`and` a ∧ b (Logical and)
`nand` a ∧̸ b = ¬(a ∧ b) (Logical not and)
`xor` a ⊕ b (Logical exclusive or, symmetric Difference when a and b are sets)
`xnor` a ⊕̸ b = ¬(a ⊕ b) (Logical not exclusive or, the complement of the symmetric difference when a and b are sets)
`~not` Bitwise negation 
`~or` Bitwise or
`~nor` Bitwise not or
`~and` Bitwise and
`~nand` Bitwise not and
`~xor` Bitwise exclusive or
`~xnor` Bitwise not exclusive or
`~` Bitwise specifier
`mod` a mod b
`U` a ∪ b (Union)
`I` a ∩ b (Intersection)
`<=>` a <=> b (If and only if)
`>>` a >> b (Right shift)
`<<` a << b (Left shift)
`>>>` a >>> b (Rotate right)
`<<<` a <<< b (Rotate left)

## Special Operators
`@` @a (Reference)
`%` a% = a/100 (Percentage)
`^` a ^ b (Exponentiation)
`?` a? OR a?b (If a exists, returns a, otherwise returns b or null)

## Special Characters
`_` Underscore, used for number base and in variable names
`:` Type annotations (No mathematical use)
`;` ?? Optional end line??? (No mathematical use)
`'` String
`"` String
`\`` String
`,` Comma
`$` Special
`#` Comment


```
let x = 5
x = 7 # Error

mutable y = 5
y = 7 # Fine

if x = 5 {
    stdout.write("x is 5\n")
} else {
    stdout.write("x is not 5\n")
}

loop {
    stdout.write("x is 5\n")
    break
}
```

## Type annotations:
Type annotations are strictly enforced by the compiler.
```
let x: number = 5

let f(x: number) -> number = x + 1
```

## Unknown values
```
let 0 < x < 10

let y = x + 1

stdout.log(y) # interval (1, 11)

let possible_y = {y | 1 < y < 11} # Can also be written as `all y where 1 < y < 11`

if (possible y) = possible_y { # This is true!
    # The set of all possible values of y is strictly equal to the set {y | 1 < y < 11}
}
if y > 0 { # This is true!

}
```

## Comparison:
The only builtin conditional construct is `if`. There is no `while` or `for`, instead we have `loop`, which can be used in place of either of them.
`check` allows you to check if an expression is true or false. Assignment is not allowed in comparison contexts. We support operator chaining.
```
mutable x = 5 # Assignment
x = 7 # Reassignment

check x = 8 # Comparison: false

check 0 < x < 10 # Comparison: true

let y = check x = 7 # Assignment to a Comparison: true

if x = 7 { # Comparison: true
    
}
if 3 > x > -7 { # Comparison: false

}
```


## Specific Restraints:
The purpose of a type system is to be able to restrict values and how they are used.
```
mutable x: number in interval[0, 10) = 5

x = 3 # Fine
x = 11 # Error

restraint my_restraint = number in interval[0, 10)

mutable y: my_restraint = 5
y = 11 # Error
```
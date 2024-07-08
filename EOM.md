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
`!` Factorial
`@` Reference
`#` Comment
`$` Special
`%` Percentage
`^` Power
`&` ??
`*` Multiplication
`-` Subtraction
`_` Underscore, used for number base and in variable names
`+` Addition
`/` Division
`?` Exists
`\` Character escape in strings. Set subtraction
`|` ??
`:` ??
`;` ?? Optional end line???
`'` String
`"` String
`\`` String
`~` ??
`,` Comma
`<` Less than
`.` Property or member access
`>` Greater than
`in` ∈
`!in` ∉
`has` ∋
`!has` ∌
`not` ¬
`=` =
`!=` ≠ = ¬(a = b)
`or` ∨
`nor` ∨̸ = ¬(a ∨ b)
`and` ∧
`nand` ∧̸ = ¬(a ∧ b)
`xor` ⊕
`xnor` ⊕̸ = ¬(a ⊕ b)

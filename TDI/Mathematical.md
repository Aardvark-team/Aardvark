https://chatgpt.com/share/52046b7c-1247-43b6-b4ec-360a52ab1b54

Note: the following text was stuff I wrote in a conversation with ChatGPT. It helps to talk about what I'm thinking about even if I'm just talking to myself or to ChatGPT.

My programming language also allows easy definition of types.
`type percentage = {x | 0 <= x <= 100}`
My programming language is unique design-wise because it borrows from mathematics. For example, in many mathematical documents you may find language like the following:
Let $z = 5$ and $f(x) = 5x^2 - 3x + 2$.
If we convert that language to code we get:

```
let z = 5
let f(x) = 5x^2 - 3x + 2
```

Which is word for word exactly something you would see in math! We use the standard carrot symbol for exportation instead of `**` like some other languages. In addition, as you saw before, we support the formal mathematical notation for set comprehension, as well as all common mathematical operators for set manipulation.
My language is just an extension to math that makes it a programming language, thus making it natural to use because, well, everyone has to learn math, so why not double up with something everyone already knows?

All of those look like amazing ideas to me! However, we need to formalize this syntax a bit. In math, the use of variables is context-dependent. For example, in the below function:
`let f(x) = 5`
Without context, it is unclear whether $x$ is a value that was previously defined, or if it is a placeholder for any number. Or, it may have been defined as a number that is a member or a certain set, or in a certain range.
To continue with this design, we will need to formalize the often abstract and ambiguous mathematical notation.

To begin, let's consider the example I just gave:
`let f(x) = 5`

We will need to define each of the following:

1. When x is a variable with a specific value
2. When x is any value within a specific range
3. When x is in a specific set

To solve this, at least for functions (which is our current goal), perhaps we could add a `where` syntax.

1.

```
let x = 7
let f(x) = 5 where x = x
f(7) # 5
f(4) # Unknown, because f is only defined for x = 5
```

Hmm, this fixes the issue, but it doesn't look clear. The `where` keyword comes after the body of the function, with no clear delimitation. Perhaps we could use periods to end a complete thought?

2.

```
let f(x) = 5 where 0 < x < 1
f(1/2) # 5
f(2) # Unknown, because 2 is not in the domain of f
f(3/4) # 5
```

This issue is fixed as well! But we still have the same issue with a lack of delimitation.

3.

```
let f(x) = 5 where x ∈ {9, 17, 192}
f(4) # Unknown, because 4 is not in the domain of f.
f(17) # 5
f(192) # 5
```

Again, it provides clarity, but lacks clear delimitation.

We will need a solution to the lack of clear delimitation. Perhaps we could require a newline? But then it looks like a separate block of code. Or maybe a period? But that would be confusing. This is a problem that we will need to consider. In addition, we need to set a default behavior for when `where` is not used. Perhaps the default behavior is that $x$ can be any number? I think that would work well and make sense.

Of course, there are many other issues to solve, but this sets a standard for how we can solve them.

## Example:

```
let a = 8 # Variable definition

let f(x) = 2x where x ∈ {9, 17, 192}

f(9) # 18
f(7) # Domain Error: 7 is not in the domain of f
```

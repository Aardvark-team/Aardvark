## Author's Note

The last few months have been some of the busiest in my life. And I expect the next few to be even busier. Nevertheless, I have somehow made time for this. As I worked, I paid attention to everything.

# Back to the base: Theory and Design

## Theory

Everything is, at its base, a number; everything around us can be expressed in terms of them. Every color, every shape, every object is a number. But these numbers can mean many different things depending their purpose. Their interpretation, usage, and behavior all depend on this purpose.

The purpose of a number can be described as its type. Some "types" of numbers (i.e. numbers designated for a certain purpose) can only take on specific values or ranges of values. For example, a boolean value only has two possible values: true (1) or false (0).

Since the type is the purpose and context of the value, a value of one type should be inherently incompatible with a value of another type. A value that is meant to be used in one context should not be used in another, otherwise issues may arise regarding the interpretation of the values. However, a type may be compatible with another type if it is a subset of the later. However, this does not necessarily mean that the later type is compatible with the former. For example, all integers are numbers, but not all numbers are integers.

Variables are used to store values for later use. In mathematics, variables cannot be mutated in any way. However, in programming, it can be useful or even necessary to change the value of a variable. To this end, a syntax should be provided that allows the creation of mutable values. Changing the value of a variable should not be accomplished using an `=`, instead, it should have its own syntax to avoid confusion.

Standard mathematical operations should be supported in order to allow the full range of manipulation of values. Certain operations may only be valid for certain types of values. For example, it wouldn't make much sense to divide characters. If the language supports user-defined types, then it may also be beneficial to support the definition of new operators.

It can often be very useful to organize values into structures. For example, a "string" is a structure/array of "characters". Structures may be labeled or unlabeled. Labeled structures utilize named elements for improved readability. In unlabeled structures, elements are numbered and can be retrieved by index. Some structures should be immutable, while for others it may be useful to have the ability to add, delete, and modify elements. Allowing structures to be used as values provides the benefit of nested structures and the ability to pass them into functions.

Expanding upon the idea of structures, it can also be useful to support templates. Templates can be used to create a standard pattern for structures. Then, you would be able to create structures based upon these templates. They can also be used to ensure that structures conform to certain rules or patterns. In this way, they are very similar to types, the difference being that templates are for structures and types are for values.

In the same way that values may be organized into structures, types may also be organized into structures. Structures of types, like those of values, may be labeled or unlabeled. In unlabeled structures, elements are numbered and can be retrieved by index. This idea is comparable to the concept of an Enum in Rust. A structure of types includes various types.

Type A is compatible with type B if A ⊆ B and A supports all operations that B supports. Template A is compatible with template B if all elements in template A are also in template B and can be accessed by the same index or name. Template A must also support all operations that template B supports. The language should provide clear syntax for defining types or templates as being compatible with each other, or should automatically recognize compatibility.

Conversions between types can be categorized as either raw or explicit. In raw conversions, the numerical value of one type is read in the context of another type. Raw conversions can cause significant issues when the acceptable range of values for one type does not align with that of the other. Raw conversions are safe when the original type is compatible with the target type. Unsafe raw conversions should be highly discouraged and/or not allowed. Explicit conversions on the other hand, are safer and involve constructing a new value of the desired type based on the original value. For example, extracting numbers from strings would be explicit conversion, while getting the numerical code of a character would be a raw conversion.

Functions are a core concept in mathematics that allows us to create reusable operations on values. This idea can be extended to the field of computer science, introducing a way to reuse operations or blocks of code. In mathematics, functions may have different implementations depending on the arguments given. In computer science, this idea is called function overloading. While not a crucial feature, it can be very helpful to maintain safety and expressivity in code.

It can also be very practical to allow functions to function as values. This allows functions to be used within structures, passed as arguments to other functions, and created as closures.

Function may have specific parameter types and return types. These can be called function signatures. For example, one signature may take a string and return a string, while another may take a number and return a number.

Loops are a core concept in computer science that allow us to repeat certain operations. Because some variables can be mutable, the state may change over time. It is also necessary to provide a way to break out of loops. Because loops may be nested inside of each other, it becomes important to have a method of naming or labeling loops. Then, it would be possible to break out of outer loops from inner ones.

Conditional branching is a familiar concept in both mathematics and computer science. It allows you to do certain operations based on a condition. An otherwise or else branch specifies what happens if the condition is not met. Multiple branches are possible. Conditions should use the familiar `=`, `<`, `>`, `<=`, `>=`, and `!=` operators in some form, as well as logical operators including and, or, not, and xor. Comparisons should also be permitted outside of conditional branching (i.e. if and else) in order to get boolean results of conditional checks. Though a programmer can do without the ability to perform in-place conditional checks, it can nevertheless be a very useful feature.

The items defined above can be categorized into two sections: value-like, and type-like.
Value-like items include: values, functions, and structures (of value-like items).
Type-like items include: types, templates, structures (of type-like items), and function signatures.

## Design

### Principals of Design:

- To be as readable and easy to understand as possible.
- To be easy to use for any and every task.
- To, when it conforms to the above principles, use formal mathematical notation and otherwise use a design that complements a general mathematical understanding.

<!-- I have come across an issue.
There are many different designs that conform to my theory.
I think the theory works great.
But then what design do we want?
I have separated the possible designs into categories:

- **Mathematical:** I just started exploring this, but it looks absolutely amazing! It is essentially math but extended to computer science. It's so powerful and safe at the same time! I'll have to show a few examples of what I was exploring, but I'm not near done.
- **Traditional:** Looks kinda like Rust but a little more consistent, readable and following this theory. I didn't really like this one. Maybe its because I'm not that traditional of a person? You can go many ways with this.
- **Power:** This is a very minimal design built mostly with constructs. It seems too powerful imo.
- **Balanced:** This is what I was working on before. I partly went mathematical with a little syntax, but then I reigned myself into traditional stuff for the actual functionality and added a lot of construct systems. But it just doesn't seem to all fit together.

Which of those general design categories sound best to you?
Of course, there are infinitely many possible designs, but I put them into categories based on what our team had already expressed as our goals.
Also, would you like to see the mathematical design I was exploring? It was just for a little bit but nevertheless it is super cool. -->

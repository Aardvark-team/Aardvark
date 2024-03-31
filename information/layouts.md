# Types & Layouts (WIP)
Should we rename `class` to `type`??
In Aardvark, there are five essential types: Array, Object, Type, Function, and Bits. Object has no default properties or methods and is simply a high-level structure that you can build upon. Array is a basic primitive structure that is extended in the standard library to include many useful properties and methods. Type is the type of all other types. Like Object, Type has no default properties or methods and is simply a high-level abstraction provided for your convenience. Function is simply a function. It also has no default properties or methods (though, as always, you can extend it to add some). Both functions and classes/types are first-class in Aardvark. Bits are simply bits with no context or meaning baked in.

All other non-essential types provided in the Aardvark standard library are defined in Aardvark (often using ALL embeds) itself and are based upon the essential types.

When you define a variable and give it a value for the first time, that variable is initialized by the class' `$initialize` special method. See the example below:
```adk
class My_Type as this {
    let any value
    let method_called

    $initialize(value) {
        this.value = value
        this.method_called = "initializer"
    }
    $constructor(value) {
        this.value = value
        this.method_called = "constructor"
    }
}
let My_Type x = 5
stdout.write(type_of(x.value), x.value, x.method_called, '\n') # Number 5 initializer

let My_Type y = [1, 2, 3]
stdout.write(type_of(y.value), y.value, x.method_called, '\n') # Array [1, 2, 3] initializers
```
Let's consider what just happened. When we assigned `My_Type x` a value, it's `$initializer` was called and given the value it was assigned to. What is the difference between the initializer and the constructor? The initializer handles initialization of the variable to a value. The constructor handles construction of that value. So, what would happen if we constructed an instance of `My_Type` then initialized a variable to it? Which one would be called?
```adk
let My_Type z = My_Type(5)
stdout.write(type_of(z.value), z.value, z.method_called, '\n') # Number 5 constructor
```
Interesting! Only the constructor was called. Why? We didn't need to handle the initialization because we already had an instance of `My_Type`.
Let's now take a look at a part of the internal `Number` class from the standard library. 
```adk
# WORK IN PROGRESS
# Only integer as an example
static class Number as this {
    let Bits data
    $layout({ precision }) { # Runs at compile time.
        if precision
            data.to_length(precision)
    }
    $initialize(value) {
        this.data = value
    }
    $constructor(value) {
        this.data = value
    }
}
let layout(Number) {
    precision: 32
} x = 5
```
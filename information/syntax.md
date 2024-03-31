# Syntax Guide (unfinished)
## Comments

Comments serve no function purpose besides explaining code and documentation. Single line comments begin with a `# `and end at the end of the line, similar to Python. Multiline comments (Doc comments) begin with `#*` and end with `*#`

## Ifs

Ifs in Aardvark are very simple. Here is the general if syntax:
```
if condition {
  # Do Something.
} else if condition {
  # Do Something.
} else {
  # Do Something.
}
```
Ifs can also be one liners just like all blocks:
```
if condition statement
else if condition statement
else statement
```
And you can make it even more compact (the same can be done with other blocks):
```
if condition statement else statment
```
And inline ifs (unique to ifs):
```
statement if condition else statement
```
And examples:
```
main = true
stdout.write("Hello World") if main else if 5 < 6 stdout.write("5 < 6") else stdout.write("5 > 6")
```

Variables

Defining a variable is easy, its kinda similar to JavaScript. Declare a variable with `let`. The modifiers and type go after that. So, for example:
```adk
let x = 5
let Number my_number = 5
let static String my_string = "hello"
```
There is also the more advanced concept of layouts, which you can find in `layouts.md`.


Functions

Defining a function is similar to as you would do it in JavaScript.
```
function x() {
    # Do something.
}
```
The biggest difference, is Aardvark functions don't have a this by default. You can, however, define a this:
```
function x as this {}
```
This allows you to customize the name of this. Function in Aardvark are not built to be like classes as they are in JavaScript, use a class for that. The this is used mainly for dynamic functions, functions that you create programitally. If you want your function to have a specific return type, use the -> operator: `function x() -> Type {}`. Function parameters can also require a certain type: `function x(type param) {}`. You can also require one of many types for a parameter: `function x([Type1, Type2] param) {}`.You can also set a default value for parameters: `function x(param=x) {}`. This is a lot at once, so let me give you an example using this all at once:
```
function powPow([String, Number] x = 1) as this -> Number {
  if type_of(x) == String 
    x = Number(x)
  return this.lastResult = x^x
}
```
The ability to refer to the function itself within the function allows you to save data from previous function calls.

Objects

Objects in Aardvark are noticeably different than those of other languages. Every value that can be assigned to a variable is an Object, including Strings, Numbers, Classes, Functions, etc. The Object class is the base class of all data types. The Object class itself has no attributes or methods, not even length. We will refer to Objects as any member of the Object class or a class that inherits from it. Objects in Aardvark have both items and properties. By default, items and properties are equivalent, but this can be override. Properties are referenced by . as in other languages. Items use `[]`, also common in other languages, so I probably don't have to explain how this works, but I will give an example:
```
property_value = object.property_name
item_value = object[item_name]
```
If a class has set the `$getitem` and `$setitem`, then properties and items are no longer linked by default, and `$getitem` is used to find the value of an item, and `$setitem` is used to set the value of an item. Arrays have their getitem and setitem set so that `array[n]` is the nth element of the array (starting from 0).

Classes

Classes are an important part of high-level programming. We have designed classes in Aardvark with the highest level of extensibility and ease of use. Here is the standard:
```
class className as objectName {
    #* 
    NOTE: when attributes and methods are used as a class property (i.e. className.attribute), objectName will refer to the class itself, otherwise it refers to an instance of that class 
    *#
    attribute = value # This is an attribute that the class has and that all instances of this class will start with.
    $constructor(...args) {
        #* 
        Called like className(...args) 
        *#
    }
    $call(...args) {
        #* 
        When an instance of this class is called. 
        retvalue = objectName(...args) 
        *#
        return retvalue
    }
    $setitem(key, value) {
        #* 
        Called when an iten of an instance of this class is set. 
        objectName[key] = value 
        *#
            
    }
    $getitem(key) {
        #* 
        Called to get an item of an instance of this class. This function should return the value of that item. 
        value = objectName[key] 
        *#
        return value
    }
    $deleteitem(key) {
        #* 
        Called just before an item of an instance of this class is deleted. 
        delete objectName[key] 
        *#
    }
    $delete() {
        #* 
        Called when an instance of this class is deleted. 
        delete objectName 
        *#
    }
    function method() {
        # This is a method of both the class and instances of the class.
    }
}
```
The above code is the standard syntax for classes.

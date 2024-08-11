# Quzy

Quzy is a high-level, dynamically typed programming language built for extensibility, readability, and power. Here's a hello-world program in Quzy.

```javascript
{
	@do: console.write("Hello World!");
}
```

### Objects

Quzy is built around objects. Create an object with `{ ... }`. Inside an object, you can define _fields_. To index a field, use the `obj[index]`notation. Strings are inferred, and use the `.` notation.

```javascript
{
    x: 0;
    "y": "y";
}["y"]; // "y"

{
    x: 0;
    "y": "y";
}.x; // "x"
```

### Variables

Make a variable with `var $name: value`, and assign it with `$name: value`. Variables aren't fields, and they don't exist after the object is evaluated.

```javascript
var $obj: {
    var $x: 0;
    $x: 1;
};

var $x: @($obj.$x) // Error; field "x" doesn't exist
```

### Imperatives

Sometimes, during evaluation of a Quzy object, you want to create side effects. Use a `@do` block for this, to evaluate an expression and throw away its value.

```javascript
{
    @do: console.write("Hello World!");
}
```

### Functions

Define a function with the `@function` attribute. They list arguments and create an object. The `return` field of that object is returned when the function is called. Call the function with parenthesis.

```javascript
@do {
    id: @function ($x) {
        return: $x;
    }
}.id(1).return; // "1"
```

### Expressions

Define an expression with the `@( ... )` syntax. You can call functions, access data, and use operators in an expression.

```javascript
{
    two: 2;
    four: @(this.two + this.two);
}
```

### Imperatives

The `@for` directive creates a numerically-indexed object by iterating over every field of the object and evaluating the object over it.

```javascript
{
    squares: @for $item in @(1..100) {
        @($item * $item)
    }
}
```

The `@while`directive evaluates the object until the condition evaluates to a truthy value.

```javascript
{
    var $i : 0;
    squares: @while @($i < 100) {
        $i: @($i + 1);
        @($i * $i);
    };
};
```

### Comments

Use `//` to create a single-line comment, and `/* ... */` to create a block comment. Block comments can be nested.

```javascript
// This is a comment
{
    var $i: 0;
    /* comment /* comment */ comment */
}
```

### Classes

Use `@class` to make a special object that will be indexed first by objects. That is, if `$obj` is of type `$type`, and there exists `$obj.x` and `$type.x`; the syntax `$obj.x` will return `$type.x`. However, in a class, `this` refers to the current object.

```javascript
$vec2: @class {
    get_x: @function() {
        return: $this.x;
    };

    get_y: @function() {
        return $this.y;
    };
};


```

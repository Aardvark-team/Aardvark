# Luna Language Reference

### Variables

Declare variables with `let` (immutable) or `var` (mutable).

```csharp
let x = 0
var y = 0

x := y // ERROR; "x" is immutable
y := x // ok
```

### Procedures

Declare a procedure with `function name(args) { ... }`.

```csharp
function multiply(x int, y int) int
{
	x * y
}
```

### Classes

Make a product type with `class`, an object with `Type { field: value; field: value; }`, and index with `obj.field`.

```csharp
class vec2
{
	float x
	float y
}

let origin = vec2 { x: 0.0; y: 0.0; }
let x = origin.x
```

### Unions

Make a sum type with `union`, a literal with `Type { state: value; }`, and index it with `if let`.

```csharp
union Number
{
	float real
    int integer
}

let integer = Number { integer: 0; }

// When used as an expression, if statements must be exhaustive
let number = if let whole = integer.integer
{
	integer
}
else if let part = integer.real
{
	real
}
```

### Namespaces

Use `namespace` to write a grouping of procedures and datatypes in a namespace. Each class and union is a namespace, and `::thing` is global.

```csharp
namespace foo
{
	let bar = 0
}

let bar = foo::bar

class vec2
{
	float val

    let bar = ::bar

    function get_bar()
    {
    	return bar
    }
}

let vec2bar = vec2::get_bar()
```

### Pipes

Use `.` as a pipe operator. You don't need to specify a namespace for a variable of a given type. Pass by mutable reference is implicit when piping.

```csharp
class zeroable
{
	float val

    function nullify(this &var zeroable) zeroable
    {
    	this.val = 0
    }
}

var one = zeroable { val: 1.0; }
one.nullify() // one == zeroable { val: 0.0; }

// EQUIVALENT
zeroable::nullify(&var one)
```

### Pointers

Use `&` on a type for a pointer, and `&var` for a mutable pointer. These are also operators for explicit lvalue semantics.

```csharp
function setint(dest &var int, &int source)
{
	dest := source
}

var dest = 0
let source = 1

setint(&var dest, &source)
```

### Subroutines

Declare a subroutine (procedure without arguments) with `void` instead of arguments.

```csharp
import std/io

function sayHi()
{
	std::stdout.write("Hello, World!")
}
```

### Modules

Use `import` to include things, and `export` to make them available externally. The current module is declared with `module`.

```csharp
module maths

// Modules are also namespaces implicitly
import multiply

function private_square(int x) int
{
	multiply::multiply(x, x)
}

export function public_square(int x) int
{
	private_square(x)
}
```

### Types

The language comes with `int`, `uint`, `float`, `byte`, & `void` types--as well as `&`, `[]` (slice), `[n]` (array), and `?` (optional) modifiers.

```csharp
let whole int = 0
let positive uint = 0u
let fraction float = 3.14
let character byte = '0' + 0x01
let nothing void = null

let pointer &int = &whole
let array []int = [0, 1, 2] // Empty arrays aren't allowed
let pair [2]int = { 1, 2 } // Use {} for static-lengt arrays
var nullable ?int = null
nullable := 0
```

### Dynamic Dispatch\*h

Use `dynamic arg.func()` to dispatch `func` over all states of the union of which `arg` is an object.

```csharp
function unwrap(int x) int
{
	return x
}

function unwrap(void x) int
{
	return 0
}

let nullable ?int = null
let whole int = dynamic nullable.unwrap()
```

### Templates

Use `<T>` to create a template. To template a procedure argument, you can also just not specify its type.

```csharp
class Option<T>
{
	?T data
}

let optionalfloat = Option<float> { data: float }.data

function id<T>(T t) T
{
	t
}

let zero = id<int>(0)

function addtoint(x int, y) // return types are also inferrable :)
{
	x + y
}

addtoint(0, 0)
addtoint(0, 0.0)
```

### Operator Overloads

Overload `operator@` to define the behaviour of `@x` or `x@y`.

```csharp
class vec2
{
	float x
    float y
}

function operator+(x vec2, y vec2) vec2
{
	vec2 { x: x.x + y.x; y: x.y + y.y; }
}
```

### Imperatives

The language provides `if` expressions, which can also be used at execution level as statements. It also provides `while`, `break`, `continue`, and `return`.

```csharp
function btoi(bool b) int
{
	if b { 1 } else { 0 }
}

if 2 + 2 = 4
{
	std::stdout.write("Math works!")
}
else
{
	std::stdout.write("Math is broken????")
}

var i = 0
while i < 100
{
	i := i + 1

    if i % 2 = 0
    {
    	break
    }

    continue

    std::stdout.write("This never executes!")
}
```

### Monads

The language provides `>>=`, the "bind" operator. For the common case of passing a lambda for the second argument, the `for a in b { c }`/`for a, b in c { d }` expressions are provided.

```csharp
let optional ?int = null

let nil1 = optional >>= (x) { x + 1 }
let nil2 = for x in optional { x + 1 } // Equivalent

let numbers = [1, 2, 3]
let odds = for index, item in list { index + item }
```

### Procedure Types

Procedures are of type `(args)ret`. Lambdas can make closures, and are of type `[captures] (args)ret`. Both of these can become `&dynamic (args)ret`.

```csharp
let const = (x) { (y) { x } }
let zero [int] (int)int = const(0)

let zero2 (int)int = function(x) { 0 }

var zero3 &dynamic (int)int = zero
zero3 := zero2
```

### Manual Memory Management

Sometimes, reference counting is undesirable. At these times, compile with `-manualfree`. Use `new` to allocate on the heap and `delete` to deallocate heap. Implement `operator new` and `operator delete` to get a working runtime environment. `new` and `delete` are also available in `unsafe` blocks.

```cpp
function operator new(size uint) &void
{
	// ...
}

function operator delete(&void ptr) void
{
	// ...
}

let allocated = new int(0)
delete allocated
```

### Inline Assembly

Inline assembly is avilable only in unsafe blocks, and uses `asm`. Only primitive types can be used as registers, and bitwidths must match.

```csharp
let x = 0

asm unsafe {

; This "@" embeds an external expression to treat like a register
mov eax @(*x)

; This also applies to lvalues (which are treated like pointers)
load @(&var x), eax

}
```

If you start a file with `asm unsafe`, you create an _assembly header_, that's guaranteed to start your assembly file. This is useful for directives. You can also create assembly headers before functions, to add specifications for the assembly. The language does not do identifier mangling.

### Unsafe Cast

Any types of the same bitwidth can be cast to one another with `(dest_type)source`. There's no strict aliasing rule, but endianness is implementation defined.

```csharp
let x = 0.0 // float

unsafe
{
	let y = (int)x
}
```

### Unsafe Union

Unsafe unions can only be indexed in unsafe blocks, and aren't tagged.

```csharp
unsafe union UnsafeNumber
{
	float x
    int y
}

let number = UnsafeNumber { x: 0.0; }

let number2 = unsafe { number.y }
```

### Unsafe Class

Use `unsafe class` to create a packed class.

```csharp
unsafe class Packed
{
	&var byte pointer
    uint amount
    ?[]byte list
}
```

### Unsafe Procedure

Declare a procedure `unsafe`to restrict it to being called in `unsafe` blocks.

```csharp
unsafe function get_bytes(thing) &var byte
{
	return unsafe { (&var byte)&thing }
}

let &var bytes = unsafe
{
	get_bytes("Heya!")
}
```

# Mamba

### Language Reference

Use `let` to declare a value.

```rust
let std = import("std");
```

Use `fn` to make a function. If the value of `let` is runtime-known, it'll make a runtime constant. Use `var` for a traditional variable.

```rust
let square = fn(x) {
	let arg = x;
    var ret = arg;
    arg := arg * x;
    // This is the return value
    ret
};
```

Variables must be initialized, but can use `undefined(type)`to initialize to an indeterminate state (for optimization).

```rust
var null = undefined(f64);
null := 17;
```

Types are inferred or generic by default, but you can specify them as needed.

```rust
let sum f64(f64, f64) = fn(x f64) f64 {
	let arg: f64 = x;
    // Use "return" as an imperative, early-return
    return x + arg;
}
```

You can capture by value into a runtime-known procedure with `[]`.

```csharp
let curry = fn(x f64) [f64](i32)f64 {
	fn [x] (y i32) { x + y }
}
```

You can also capture by reference, but this can lead to dangling pointers.

```rust
let bad = fn(x) {
	// ERROR; "x" will be a dangling pointer
	fn [&x] (y) { x + y }
}
```

Use `struct`to create a `.` indexed product type.

```rust
let Point = struct {
	x f64;
    y f64;
};

let origin = Point { x: 0; y: 0; }
let zero = origin.x;
```

Use `union` to create a sum type. Index it with `.field(callback)` to execute the callback only if the field is defined. If you handle all fields, you can use the resultant return value.

```rust
let Pet = union {
	dog u8[];
    cat null;
};

let cat = Pet { cat: null; };

let name = cat.cat(fn(cat){
	"Heya!"
}).dog(fn(dog)){
	dog
};
```

To make this nicer, you can use the `use args <- body` syntax after a procedure call to insert a callback.

```rust
let name = cat.cat();
use cat <- { "Heya!" };
use dog <- { dog };
```

If you don't put a `<-`, the rest of the code in that `{...}` will be consumed by the `use`.

```rust
let set_username = fn(id, name) {
	let fallible = users[id].try();
    use error <- {
    	// Use "unreachable" to tell the compiler
        // that this code will never execute
    	unreachable
    };

    use user;

    user.name := name;
};
```

Types can be manipulated procedurally at compile-time.

```rust
let Pair = fn(T type, F type) type {
	struct {
    	x T;
        y F;
    }
};

let Point = Pair(f64, f64);
```

You can use `packed` to make a `union` untagged, or remove padding from a `struct`.

```rust
let FourBits = packed struct {
	x u2;
    y u2;
};

let Untagged = packed union {
	x u32;
    y @Vector(u8, 4);
}

let get_x = fn(untagged) {
	// There's no tag, so you can just raw index the union
	return untagged.x;
}
```

You can also use the `.packed` operator to convert a union into a packed union for raw indexing (e.g. `pet.packed.x`).

The builtin types are `uBB`, `iBB`, & `fBB` where `BB` is any bitwidth the hardware understands, and `u`/`i`/`f` are unsigned, integer, and floating point values. The type modifiers are `?` (option), `*` (pointer), `[]` (slice), and `[n]` (array). There's also the builtin function `@Vector(type, length)` that generates a SIMD-type, and `@Vector(val, val, val)` that generates a SIMD-value. Slices can never be empty, and pointers can never be null; for this, use `[]?` and `*?`respectively. Functions also are typed, and capture functions include their capture in the type (i.e. `[caps] ret(args)`). Use `virtual*` for a pointer to a function regardless of captures.

```rust
var integer: i32 = 0

let array: i32? = null;
let ptr: i32* = integer.&;
let var_ptr: i32 var* = integer.&var;
let slice: i32[] = [1, 2, 3, 4];
let array: i32[4] = { 1, 2, 3, 4 };
let empty: i32[]? = null;
let nullptr: i32*? = null;
let simd: @Vector(i32, 2) = @Vector(integer, integer);

let func: [i32] i32() = fn[integer] (x i32) i32 {
	integer + x
};

let func2: i32() = fn (x i32) i32 {
	x * 2
};

var ptr: i32() virtual* = func2;
ptr := func; // ok
```

Handle optionals with the `.try(none_callback, some_callback)` method. Pointers can implicitly reference/dereference one layer, but can never implicitly refernece mutably except in a method call. To dereference explicitly, use `ptr.*`. To reference explicitly, use `ptr.&` or `ptr.&var` (as needed). Use `[...]` to write a slice, `{ ... }` to write an array, `arr...` to splat an array/flatten a slice into another slice, and `arr[index]` to do a bounds checked index returning an optional.

Arrays and slices both have `.length()` methods. Runtime slices `.length()` is not compile-time known, but runtime arrays `.length()` is compile-time known. They also have `.for(callback)` methods to run a function on each of their items, and `.map(callback)` methods to construct a new array/slice respectively this way. The `.flatten()` method works for arrays or slices of arrays or slices, and flattens them out. It's a special case of the `.fold(callback)` method, which takes a binary operator and uses it to crush the array down to one value. The callback there is the `.append(arr)` method which creates a copy that concatenates the arguments. The `.concat(arr)` method does this in-place, mutating the first array.

To declare your own methods, write functions inside a datatype.

```rust
let Point = struct {
	x f64;
    y f64;

    let get_x = fn (this Point var*) {
    	this.x.&var
    };
};

let pt = Point { x: 0.0; y: 0.0; }
let zero = pt.get_x(); // Reference is implicit for method calls
// Equivalently
let zero2 = Point::get_x(pt.&var);
```

Use `const` to create a block that executes at compile-time. Arbitrary code is allowed inside a const block. A `const` function with always be computed at build-time.

```rust
let one = const {
	var x = 0u;
    x := x + 1;
    x
};

let comptime_call = const fn(callback) {
	callback();
};
```

Compile-time declarations are order-independent, whereas runtime declarations are order-dependent (top to bottom).

Use `import("name")` to import a module, `export` to export a declaration, and `module("name")` to declare the current module. Use `::` to index a module.

```rust
module("four");

let lib = import("lib");
let four = lib::square(2);

export let get_four = fn() {
	four
};
```

Use `asm { ... }` to write inline ASM, and use `@()` to embed expressions of primitive types or pointers as registers.

```rust
let set_eax = fn(arg i32) {
	asm {
		mov eax @(arg)
	};
};
```

Use the builtin `if` to takes a condition and a callback, and execute that block only if the condition is true. If two callbacks are provided, it will be treated as an if-else.

```rust
let std = import("std");

if(2 + 2 = 4)
use <- {
	std::console.write("Hello World!");
}
use <- {
	std::console.write("Something's broken....")
}
```

String literals are `u8[]`s, and character literals are `u8`. All other literals don't have a type, and are coerced to a type when used in code. To specify the type, use `NiBB`, `NuBB`, or `NfBB` (where `BB` defaults to word-size when unspecified). The `f` is inferred for literals with `.` in them. If none of this is provided, a word-sized signed integer will be assumed.

The language also has a large set of operators, but those aren't covered in this document. The standard library and tooling is outside the scope of this document.

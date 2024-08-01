## Structures

Working with data, we often have a need to handle separate properties of objects or **structures**. So, to solve this, let's define **structure** as structure composed of various named properties and corresponding values.
```
let Spencer = structure {
  let name = "Spencer Rosas-Gunn" # Immutable
  mutable age = 14 # Mutable
}
```

We will likely find that we often have lots of structures that have very similar properties, but different values, so let's create `structure template`s. A `structure template` is a template from which structures may be created. This allows us to reuse code.
```
let Person = structure template {
  let String name
  mutable Number age
}
let Spencer = Person:{name="Spencer Rosas-Gunn"; age=14} # I also considered using `with` instead of `:` here.
```

Structures and Arrays together give us a powerful way to represent data.

```
let Person = structure template {
  let String name
  mutable Number age
}
let Hudson = Person:{name="Hudson"; age=16}


let object_like_in_js = structure {
  let x = 5
  let y = 10
}



let SuperString = structure template {
  let String content
  let replace(x, y) {
    # Code to replace x with y
  }
}
let String(x) = SuperString:{content=x}
```
Written by Spencer Rosas-Gunn. This paper creates a programming language from formal mathematics.

### Formal Specification

Let's firstly define the abstraction calculus. Here's our expression grammar.

```csharp
expression ::= variable | application | abstraction
application ::= expression expression
abstraction ::= "lambda" expression "." expression
```

Next, we'll define a rule of computation. This rule is called $\beta$-reduction. This rule states that $(\lambda x.M) y$⇔$M[x/y]$.

### Integers & Booleans

We will use $=$ for "is defined as." With this, let's create two definitions.

$0 = \lambda x.\lambda f.x$

$S = \lambda n.\lambda f.\lambda x.f(n f x)$

These two seemingly arbitrary terms actually provide us something quite powerful. We represent a number $n$ as the function $\lambda f.\lambda x.f^n(x)$. To do this, we define the first number (zero) as $\lambda x.\lambda f.x$. Then, we define the function $S$ such that $S(x) := x + 1$. Using this, we can define the natural numbers by the following rule.

$x = 0 \lor x = S(y): y \in \textrm{Nat} \iff x \in \textrm{Nat}$

This is a _type rule_ that defines the natural numbers. We can also define booleans as follows.

$\top = \lambda x.\lambda y.x$
$\bot = \lambda x.\lambda y.y$

The power in this is that it lets us define a ternary if operator as follows.

$? = \lambda b.\lambda x.\lambda y.b x y$

Now, we can define a type rule for the booleans.

$x = \top \lor x = \bot \iff x \in \textrm{Bool}$

### Functions

We can define the type $A \rightarrow B$ with the rule that $\forall a \in A, x(a) \in B$. This defines a _function_ from type $A$ to type $B$.

Now that we can analyze them, let's define some boolean logic primitives. We can begin with not.

$\neg = \lambda b.b\bot\top$

We will introduce a syntactic shorthand, such that terms beginning with abstractions allow us to place the identifier in the definition. That is, we will be able to rewrite the definition $... = \lambda x.M$ to $... x = M$. This can be done recursively.

$\neg b = b\bot\top$

Now, before we go any further, consider the result of applying $\neg$ to $1$. We get the term $(\lambda x.\lambda f.f x)\bot\top$, which beta reduces to $\bot\top$ or $(\lambda x.\lambda y.x)(\lambda x.\lambda y.y)$, which itself beta reduces to $\lambda z.\lambda x.\lambda y.y$. This term has no real meaning, as it was the result of a meaningless operation. To prevent situations like this, we'll define a _type rule_. This is an arbitrary annotation that a value can be used only according to one of it's types (as a a value like $\lambda x.x$ is of type $A \rightarrow A$ for all $A$). That type will be specified with a $::$, followed by the type to be used as.

$\neg :: \textrm{Bool} \rightarrow \textrm{Bool}$
$\neg b = b\bot\top$

$\land :: \textrm{Bool} \rightarrow \textrm{Bool} \rightarrow \textrm{Bool}$
$\land xy = x y \bot$

$\lor :: \textrm{Bool} \rightarrow \textrm{Bool} \rightarrow \textrm{Bool}$
$\lor xy = x\top y$

$\oplus :: \textrm{Bool} \rightarrow \textrm{Bool} \rightarrow \textrm{Bool}$
$\oplus xy = \neg(\land (\neg x) (\neg y))$

Now, let's revisit the naturals. We can define functions to add, subtract, multiply, and exponentiate them.

$+ :: \textrm{Nat} \rightarrow \textrm{Nat} \rightarrow \textrm{Nat}$
$+ x y = \lambda z.\lambda s.n (m z s) s$

$- :: \textrm{Nat} \rightarrow \textrm{Nat} \rightarrow \textrm{Nat}$
$-xy=(y(\lambda n.\lambda f.\lambda x.n(\lambda g.\lambda h.h(g f))(\lambda u.x)(\lambda u.u))) x$

$* :: \textrm{Nat} \rightarrow \textrm{Nat} \rightarrow \textrm{Nat}$
$*xy=\lambda a.x(ya)$

$\uparrow :: \textrm{Nat} \rightarrow \textrm{Nat} \rightarrow \textrm{Nat}$
$\uparrow xy=yx$

We can also define a function to compare them.

$> :: \textrm{Nat} \rightarrow \textrm{Nat} \rightarrow \textrm{Bool}$
$>xy = \neg (\lambda n.n(\lambda x.\bot)\top)(- x y)$

From this, it's possible to derive many others.

$\neq :: \textrm{Nat} \rightarrow \textrm{Nat} \rightarrow \textrm{Bool}$
$\neq xy=\neg(\equiv x y)$
$\geq :: \textrm{Nat} \rightarrow \textrm{Nat} \rightarrow \textrm{Bool}$
$\geq xy=\neg(<xy)$
$\leq :: \textrm{Nat} \rightarrow \textrm{Nat} \rightarrow \textrm{Bool}$
$\leq xy = \neg(>xy)$
$< :: \textrm{Nat} \rightarrow \textrm{Nat} \rightarrow \textrm{Bool}$
$< xy=\neg((>xy)(\equiv xy))$
$\equiv :: \textrm{Nat} \rightarrow \textrm{Nat} \rightarrow \textrm{Bool}$
$\equiv xy=\land(\leq x y)(\geq x y)$

### Typechecking & Beta-Equivalence

Earlier, we defined type annotations. To ensure they're used properly, we say that the expression $f x$ where $f :: X \rightarrow Y$ only passes typechecking when $x :: X$, and that the definition $f = \lambda x.M$ where $f :: X \rightarrow Y$ only passes typechecking if $\forall x :: X$, $f x::Y$. We say $x \iff y$ if there exists $z$ such that $z \rightarrow _\beta x$ and $z \rightarrow _\beta y$.

### Arithmetic

From all this, we can now test basic arithmetic expressions. For example, the ubiquitous expression $2 + 2 = 4$ is encoded as $\equiv (4) (+ (2) (2))$. By substituting in the definitions of each term, we can perform beta reduction to find that this evaluates to $\top$.

### Dependent Typing

Consider the term $t = \lambda b.b0\bot$. If we say $T :: \textrm{Bool} \rightarrow X$, can we derive $X$? We know that $0 :: \textrm{Nat}$ and $\bot :: \textrm{Bool}$, so these are of different types. As such, the type of $t x$ depends not only on the _type_ of $x$, but on the _value_ of $x$. As such, we can consider $T$, the metafunction (function of types) $\lambda b.b(\textrm{Nat})(\textrm{Bool})$. We can then say that $tx :: T x$, or that $t :: (\textrm{Bool}: b) \rightarrow T(b)$. We'll hereforth define metafunctions with $\Lambda x.M$.

### Parametric Polymorphism

Consider the definition $\textrm{ID}=\lambda x.x$. We can say $\textrm{ID} :: A \rightarrow A$ for any type $A$, meaning that we'd need to redefine this function for all types $A$. Instead, we can say that $\textrm{ID} :: \Lambda A.A \rightarrow A$. Then, for an expression of the form $\textrm{ID}(x)$ where $x :: X$, we can say that the return type is $X$ since we're passing $X$ as argument to the $\Lambda A.A\rightarrow A$ metafunction, which beta-reduces to $B \rightarrow B$.

In general, a type defined by a metafunction that parameterizes a type is parametrically polymorphic. For example, the type definition $\textrm{True} = \Lambda X.\Lambda Y.X$ is parametrically polymorphic in $X$ and $Y$.

### Static Dispatch

Let there exist a term $x :: X$, and another $y :: Y$. We can define $f :: X \rightarrow X \rightarrow X$ such that $f xy=x$. We can then define $f :: Y \rightarrow Y \rightarrow Y$ such that $fxy=y$. We can then see that the expression $f$ is equal to $\bot$ over $x$ and $\top$ over $y$. We are _dispatching_ $f$ based on the types of $x$ and $y$.

### Dependent Typing

Consider the term $t = \lambda b.b0\bot$. If we say $T :: \textrm{Bool} \rightarrow X$, can we derive $X$? We know that $0 :: \textrm{Nat}$ and $\bot :: \textrm{Bool}$, so these are of different types. As such, the type of $t x$ depends not only on the _type_ of $x$, but on the _value_ of $x$. As such, we can consider $T$, the metafunction (function of types) $\lambda b.b(\textrm{Nat})(\textrm{Bool})$. We can then say that $tx :: T x$, or that $t :: (\textrm{Bool}: b) \rightarrow T(b)$. We'll hereforth define metafunctions with $\Lambda x.M$.

### Parametric Polymorphism

Consider the definition $\textrm{ID}=\lambda x.x$. We can say $\textrm{ID} :: A \rightarrow A$ for any type $A$, meaning that we'd need to redefine this function for all types $A$. Instead, we can say that $\textrm{ID} :: \Lambda A.A \rightarrow A$. Then, for an expression of the form $\textrm{ID}(x)$ where $x :: X$, we can say that the return type is $X$ since we're passing $X$ as argument to the $\Lambda A.A\rightarrow A$ metafunction, which beta-reduces to $B \rightarrow B$.

In general, a type defined by a metafunction that parameterizes a type is parametrically polymorphic. For example, the type definition $\textrm{True} = \Lambda X.\Lambda Y.X$ is parametrically polymorphic in $X$ and $Y$.

### Static Dispatch

Let there exist a term $x :: X$, and another $y :: Y$. We can define $f :: X \rightarrow X \rightarrow X$ such that $f xy=x$. We can then define $f :: Y \rightarrow Y \rightarrow Y$ such that $fxy=y$. We can then see that the expression $f$ is equal to $\bot$ over $x$ and $\top$ over $y$. We are _dispatching_ $f$ based on the types of $x$ and $y$.

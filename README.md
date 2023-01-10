# Pyrefact

This extension adds [Pyrefact](https://pypi.org/project/pyrefact/) as a formatter in VSCode.

Pyrefact automatically finds and solves a great deal of anti-patterns in python code code, and applies those automatically when formatting your code. It also removes commented and dead code, and trailing whitespace.

After completing, pyrefact also formats your code with black and isort.

## Examples

Below follows a number of examples to illustrate the sort of things pyrefact can do.

### Converting loops into constant expressions

```python
q = 3
w = list()
for a in range(-1, 10):
    for k in range(-1, 1):
        w.append(a ** 2 + q + k ** 2)
y = sum(w)
print(y)
```

```python
q = 3
y = 22 * q + 583
print(y)
```

### Replacing a loop filling up a set with a set comprehension

```python
x = set()
for i in range(100):
    if i > 3:
        if i % 8 == 0:
            x.add(i ** 2)
```

```python
x = {i**2 for i in range(100) if i > 3 and i % 8 == 0}
```

### Replacing a dict with a defaultdict where appropriate

```python
d = {}
for x in range(10):
    if x in d:
        d[x].append(f(x))
    else:
        d[x] = [f(x)]
```

```python
d = collections.defaultdict(list)
for x in range(10):
    d[x].append(f(x))
```

### Converting math loops into np.matmul()

```python
import numpy as np

i, j, k = 10, 11, 12

a = np.random.random((i, j))
b = np.random.random((j, k))

u = np.array(
    [
        [
            np.sum(
                a__ * b__
                for a__, b__ in zip(a_, b_)
            )
            for a_ in a
        ]
        for b_ in b.T
    ]
).T

print(u)
```

```python
import numpy as np

i, j, k = 10, 11, 12

a = np.random.random((i, j))
b = np.random.random((j, k))

u = np.matmul(a, b)

print(u)
```

### De-indenting nested code

```python
def f(x) -> int:
    if x == 1:
        x = 2
    else:
        if x == 3:
            x = 7
        else:
            if x != 8:
                x = 99
            else:
                if x >= 912:
                    x = -2
                elif x ** x > x ** 3:
                    x = -1
                else:
                    x = 14

    return x

```

```python
def _f(x) -> int:
    if x == 1:
        return 2
    if x == 3:
        return 7
    if x == 8:
        return 99
    if x >= 912:
        return -2
    if x**x > x**3:
        return -1

    return 14
```

### Removing dead code

```python
import random
import sys

def f(x: int) -> int:
    import heapq
    y = e = 112

    if x >= 2:
        d = 12

    if []:
        x *= 99

    if x == 3:
        y = x ** 13
        return 8
    else:
        return 19
while False:
    sys.exit(0)
```

```python
def f(x: int) -> int:
    if x == 3:
        return 8

    return 19
```

A complete-ish list of the things pyrefact can do can be found on the [pyrefact github page](https://github.com/OlleLindgren/pyrefact).

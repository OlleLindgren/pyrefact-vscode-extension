
## invalid_escape_sequence

### Before

```python

import re
print(re.findall("\d+", "1234x23"))
            
```

### After

```python

import re
print(re.findall(r"\d+", "1234x23"))
            
```

## simplify_math_iterators

### Before

```python

y = sum([x * a ** 3 - a * z ** 2 for a in range(10, 19, 2) for z in (3, 4, 5, 6) for x in range(1, 9, 5)])
h = sum(x * a ** 3 - a * z ** 2 for a in range(10, 19, 2) for z in [3, 4, 5, 6] for x in range(1, 9, 5))
w = sum([x * a ** 3 - a * z ** 2 for a in range(10, 19, 2) for z in {3, 4, 5, 6, 6, 5, 4} for x in range(1, 9, 5)])
            
```

### After

```python

y = 419160
h = 419160
w = 419160
            
```

## inline_math_comprehensions

### Before

```python

for i in range(10):
    w = [a ** 2 for a in range(10)]
    y = sum(w)
            
```

### After

```python

for i in range(10):
    w = [a ** 2 for a in range(10)]
    y = sum([a ** 2 for a in range(10)])
            
```

## implicit_matmul

### Before

```python

import numpy as np

i, j, k = 10, 11, 12

a = np.random.random((i, j))
b = np.random.random((j, k))
c = np.random.random((k, j))
d = np.random.random((j, i))

u = np.array([[np.dot(b[:, i], a[j, :]) for i in range(b.shape[1])] for j in range(a.shape[0])])
v = np.array([[np.dot(c[i, :], a[j, :]) for i in range(c.shape[0])] for j in range(a.shape[0])])
w = np.array([[np.dot(b[:, i], d[:, j]) for i in range(b.shape[1])] for j in range(d.shape[1])])
z = np.array([[np.dot(a[i, :], b[:, j]) for i in range(a.shape[0])] for j in range(b.shape[1])])

print(np.sum((u - np.matmul(a, b)).ravel()))
print(np.sum((v - np.matmul(a, c.T)).ravel()))
print(np.sum((w - np.matmul(b.T, d).T).ravel()))
print(np.sum((z - np.matmul(b.T, a.T)).ravel()))
            
```

### After

```python

import numpy as np

i, j, k = 10, 11, 12

a = np.random.random((i, j))
b = np.random.random((j, k))
c = np.random.random((k, j))
d = np.random.random((j, i))

u = np.matmul(b.T, a.T).T
v = np.matmul(c, a.T).T
w = np.matmul(b.T, d).T
z = np.matmul(a, b).T

print(np.sum((u - np.matmul(a, b)).ravel()))
print(np.sum((v - np.matmul(a, c.T)).ravel()))
print(np.sum((w - np.matmul(b.T, d).T).ravel()))
print(np.sum((z - np.matmul(b.T, a.T)).ravel()))
            
```

## early_continue

### Before

```python

for i in range(100):
    if i % 3 == 2:
        print(i ** i)
        print(i ** (i - 1))
        for i in range(10000):
            if i >= 1337 and i is not 99:
                print(i - i)
        if i % 6 == 1:
            print(i ** 3)
            print(i ** 4)
            
```

### After

```python

for i in range(100):
    if i % 3 != 2:
        continue
    else:
        print(i ** i)
        print(i ** (i - 1))
        for i in range(10000):
            if i >= 1337 and i is not 99:
                print(i - i)
        if i % 6 == 1:
            print(i ** 3)
            print(i ** 4)
            
```

## replace_for_loops_with_dict_comp

### Before

```python

u = {i: 10 - 1 for i in range(33)}
v = {i: 10 ** i - 1 for i in range(77, 22)}
w = {11: 342, 'key': "value"}
x = {**u, **v, **w}
for i in range(2, 4):
    x[i] = 10 ** i - 1
            
```

### After

```python

u = {i: 10 - 1 for i in range(33)}
v = {i: 10 ** i - 1 for i in range(77, 22)}
w = {11: 342, 'key': "value"}
x = {**u, **v, **w, **{i: 10 ** i - 1 for i in range(2, 4)}}
            
```

## simplify_matrix_operations

### Before

```python

np.matmul(a.T, b.T).T
np.matmul(a, b.T).T
np.matmul(a.T, b).T
np.matmul(a.T, b.T)
            
```

### After

```python

np.matmul(b, a)
np.matmul(a, b.T).T
np.matmul(a.T, b).T
np.matmul(a.T, b.T)
            
```

## replace_map_lambda_with_comp

### Before

```python

x = map(lambda y: y > 0, (1, 2, 3))
            
```

### After

```python

x = (y > 0 for y in (1, 2, 3))
            
```

## remove_redundant_chained_calls

### Before

```python

sorted(reversed(v))
sorted(sorted(v))
sorted(iter(v))
sorted(tuple(v))
sorted(list(v))
list(iter(v))
list(tuple(v))
list(list(v))
set(set(v))
set(reversed(v))
set(sorted(v))
set(iter(v))
set(tuple(v))
set(list(v))
iter(iter(v))
iter(tuple(v))
iter(list(v))
reversed(tuple(v))
reversed(list(v))
tuple(iter(v))
tuple(tuple(v))
tuple(list(v))
sum(reversed(v))
sum(sorted(v))
sum(iter(v))
sum(tuple(v))
sum(list(v))
sorted(foo(list(foo(iter((foo(v)))))))
            
```

### After

```python

sorted(v)
sorted(v)
sorted(v)
sorted(v)
sorted(v)
list(v)
list(v)
list(v)
set(v)
set(v)
set(v)
set(v)
set(v)
set(v)
iter(v)
iter(v)
iter(v)
reversed(v)
reversed(v)
tuple(v)
tuple(v)
tuple(v)
sum(v)
sum(v)
sum(v)
sum(v)
sum(v)
sorted(foo(list(foo(iter((foo(v)))))))
            
```

## deinterpolate_logging_args

### Before

```python

logging.log(logging.INFO, "interesting information: {}, {}, {}".format(13, 14, 15))
            
```

### After

```python

logging.log(logging.INFO, 'interesting information: {}, {}, {}', 13, 14, 15)
            
```

## singleton_comparison

### Before

```python

print(q == True is x)
print(k != True != q != None is not False)
            
```

### After

```python

print(q is True is x)
print(k is not True != q is not None is not False)
            
```

## simplify_transposes

### Before

```python

arr = np.array([[1, 2, 3], [4, 5, 6]])
assert list(zip(*arr.T)) == [[1, 2, 3], [4, 5, 6]]
assert list(zip(*arr.T.T)) == [[1, 4], [2, 5], [3, 6]]
assert list(zip(*zip(*arr))) == [[1, 2, 3], [4, 5, 6]]
assert list(zip(*zip(*arr.T))) == [[1, 4], [2, 5], [3, 6]]
assert list(zip(*zip(*arr.T.T))) == [[1, 2, 3], [4, 5, 6]]
            
```

### After

```python

arr = np.array([[1, 2, 3], [4, 5, 6]])
assert list(arr) == [[1, 2, 3], [4, 5, 6]]
assert list(arr.T) == [[1, 4], [2, 5], [3, 6]]
assert list(arr) == [[1, 2, 3], [4, 5, 6]]
assert list(arr.T) == [[1, 4], [2, 5], [3, 6]]
assert list(arr) == [[1, 2, 3], [4, 5, 6]]
            
```

## sorted_heapq

### Before

```python

x = sorted(y)
z = sorted(p)[0]
k = sorted(p)[-1]
r = sorted([q, x], key=foo)[-1]
w = sorted(p)[:5]
w = sorted(p)[:k]
w = sorted(p)[:-5]
f = sorted(p)[-8:]
f = sorted(p)[-q():]
f = sorted(p)[13:]
sorted(x)[3:8]
print(sorted(z, key=lambda x: -x)[:94])
print(sorted(z, key=lambda x: -x)[-4:])
            
```

### After

```python

x = sorted(y)
z = min(p)
k = max(p)
r = max([q, x], key=foo)
w = heapq.nsmallest(5, p)
w = heapq.nsmallest(k, p)
w = sorted(p)[:-5]
f = list(reversed(heapq.nlargest(8, p)))
f = list(reversed(heapq.nlargest(q(), p)))
f = sorted(p)[13:]
sorted(x)[3:8]
print(heapq.nsmallest(94, z, key=lambda x: -x))
print(list(reversed(heapq.nlargest(4, z, key=lambda x: -x))))
            
```

## abstractions

### Before

```python

for var in range(11):
    print(22)
    params = {"password": 11, "username": 22}

    if var == 2:
        params["x"] = True
    elif var == 11 and s == 3:
        params["y"] = var, s
    else:
        params["xxx"] = 3

    if foo:
        params["is_foo"] = True

    response = requests.get(url, params)
    assert response.status_code == 200, "got a non-200 response"
        
```

### After

```python

def _pyrefact_abstraction_1(foo, s, var):
    params = {'password': 11, 'username': 22}

    if var == 2:
        params['x'] = True
    elif var == 11 and s == 3:
        params['y'] = (var, s)
    else:
        params['xxx'] = 3

    if foo:
        params['is_foo'] = True

    return params


for var in range(11):
    print(22)

    params = _pyrefact_abstraction_1(foo, s, var)
    response = requests.get(url, params)
    assert response.status_code == 200, "got a non-200 response"
        
```

## simplify_redundant_lambda

### Before

```python

lambda: complicated_function()
lambda: pd.DataFrame()
lambda: []
lambda: {}
lambda: set()
lambda: ()
lambda value: [*value]
lambda value: {*value,}
lambda value: (*value,)
lambda value, /: [*value]
lambda value, /, value2: (*value, *value2)
lambda value, /, value2: (*value,)
lambda: complicated_function(some_argument)
lambda: complicated_function(some_argument=2)
lambda x: []
lambda x: list()
lambda q: h(q)
lambda z, w: f(z, w)
lambda *args: w(*args)
lambda **kwargs: r(**kwargs)
lambda *args, **kwargs: hh(*args, **kwargs)
lambda z, k, /, w, h, *args: rrr(z, k, w, h, *args)
lambda z, k, /, w, h, *args, **kwargs: rfr(z, k, w, h, *args, **kwargs)
lambda z, k, /, w, h, *args: rrr(z, k, w, w, *args)
lambda z, k, /, w, h: rrr(z, k, w, w, *args)
            
```

### After

```python

complicated_function
pd.DataFrame
list
dict
set
tuple
list
set
tuple
list
lambda value, /, value2: (*value, *value2)
lambda value, /, value2: (*value,)
lambda: complicated_function(some_argument)
lambda: complicated_function(some_argument=2)
lambda x: []
lambda x: list()
h
f
w
r
hh
rrr
rfr
lambda z, k, /, w, h, *args: rrr(z, k, w, w, *args)
lambda z, k, /, w, h: rrr(z, k, w, w, *args)
            
```

## remove_dead_ifs

### Before

```python

x = 13
a = x if x > 3 else 0
b = x if True else 0
c = x if False else 2
d = 13 if () else {2: 3}
e = 14 if list((1, 2, 3)) else 13
print(3 if 2 > 0 else 2)
print(14 if False else 2)
            
```

### After

```python

x = 13
a = x if x > 3 else 0
b = x
c = 2
d = {2: 3}
e = 14 if list((1, 2, 3)) else 13
print(3 if 2 > 0 else 2)
print(2)
            
```

## replace_with_filter

### Before

```python

for x in range(10):
    if not x:
        continue
    else:
        print(3)
            
```

### After

```python

for x in filter(None, range(10)):
    print(3)
            
```

## remove_redundant_iter

### Before

```python

values = range(50)
w = [x for x in list(values)]
print(w)
            
```

### After

```python

values = range(50)
w = [x for x in values]
print(w)
            
```

## remove_redundant_comprehensions

### Before

```python

a = {x: y for x, y in zip(range(4), range(1, 5))}
b = [w for w in (1, 2, 3, 99)]
c = {v for v in [1, 2, 3]}
d = (u for u in (1, 2, 3, 5))
aa = (1 for u in (1, 2, 3, 5))
ww = {x: y for x, y in zip((1, 2, 3), range(3)) if x > y > 1}
ww = {x: y for y, x in zip((1, 2, 3), range(3))}
            
```

### After

```python

a = dict(zip(range(4), range(1, 5)))
b = list((1, 2, 3, 99))
c = set([1, 2, 3])
d = iter((1, 2, 3, 5))
aa = (1 for u in (1, 2, 3, 5))
ww = {x: y for x, y in zip((1, 2, 3), range(3)) if x > y > 1}
ww = {x: y for y, x in zip((1, 2, 3), range(3))}
            
```

## breakout_common_code_in_ifs

### Before

```python

import random
import heapq
if random.random() < 2:
    print(33)
    print(100)
elif random.random() >= 2:
    if random is heapq:
        print(100)
    else:
        print(100)
        print(300)
else:
    print(21)
    print(100)
            
```

### After

```python

import random
import heapq
if random.random() < 2:
    print(33)
    print(100)
elif random.random() >= 2:
    print(100)
    if random is heapq:
        pass
    else:
        print(300)
else:
    print(21)
    print(100)
            
```

## overused_constant

### Before

```python

def foo():
    d = {"spam": 3, "eggs": 2, "snake": 1336}
    print(d.get("spam"))

def boo():
    r = {"spam": 3, "eggs": 2, "snake": 1336}
    print(r.get("spam"))

def moo():
    def zoo():
        s = {"spam": 3, "eggs": 2, "snake": 1336}
        print(s.get("spam"))

    def qoo():
        d = {"spam": 3, "eggs": 2, "snake": 1336}
        print(d.get("spam"))

    zoo() is zoo()

def koo():
    print({"spam": 3, "eggs": 2, "snake": 1336}.get("spam"))
            
```

### After

```python

PYREFACT_OVERUSED_CONSTANT_0 = {'spam': 3, 'eggs': 2, 'snake': 1336}
def foo():
    d = PYREFACT_OVERUSED_CONSTANT_0
    print(d.get("spam"))

def boo():
    r = PYREFACT_OVERUSED_CONSTANT_0
    print(r.get("spam"))

def moo():
    def zoo():
        s = PYREFACT_OVERUSED_CONSTANT_0
        print(s.get("spam"))

    def qoo():
        d = PYREFACT_OVERUSED_CONSTANT_0
        print(d.get("spam"))

    zoo() is zoo()

def koo():
    print(PYREFACT_OVERUSED_CONSTANT_0.get("spam"))
            
```

## replace_subscript_looping

### Before

```python

import numpy as np
[
    [
        np.dot(b[:, i], a[j, :])
        for i in range(b.shape[1])
    ]
    for j in range(a.shape[0])
]
        
```

### After

```python

import numpy as np
[
    [
        np.dot(b_, a_)
        for b_ in b.T
    ]
    for a_ in a
]
        
```

## replace_functions_with_literals

### Before

```python

u = list()
v = tuple()
w = dict()
a = dict(zip(range(4), range(1, 5)))
b = list((1, 2, 3, 99))
c = set([1, 2, 3])
d = iter((1, 2, 3, 5))
aa = (1 for u in (1, 2, 3, 5))
            
```

### After

```python

u = []
v = ()
w = {}
a = dict(zip(range(4), range(1, 5)))
b = [1, 2, 3, 99]
c = {1, 2, 3}
d = iter((1, 2, 3, 5))
aa = (1 for u in (1, 2, 3, 5))
            
```

## remove_duplicate_set_elts

### Before

```python

{1, 99, "s", 1, sum(range(11)), sum(range(11))}
            
```

### After

```python

{1, 99, 's', sum(range(11)), sum(range(11))}
            
```

## replace_dictcomp_assign_with_dict_literal

### Before

```python

x = {z: 21 for z in range(3)}
x[10] = 100
x[101] = 220
x[103] = 223
            
```

### After

```python

x = {**{z: 21 for z in range(3)}, 10: 100, 101: 220, 103: 223}
            
```

## implicit_defaultdict

### Before

```python

def f(x: int) -> int:
    return x+1
def h(x: int) -> int:
    return x**2
d = {}
for x in range(10):
    y = f(x)
    if x in d:
        d[x].extend([y, 2, 4])
    else:
        d[x] = [y, 2, 4]
    z = h(x)
    w = x+19
    if w in d:
        d[w].extend([z, 9, 12])
    else:
        d[w] = [z, 9, 12]
            
```

### After

```python

def f(x: int) -> int:
    return x+1
def h(x: int) -> int:
    return x**2
d = collections.defaultdict(list)
for x in range(10):
    y = f(x)
    d[x].extend([y, 2, 4])
    z = h(x)
    w = x+19
    d[w].extend([z, 9, 12])
            
```

## remove_redundant_chain_casts

### Before

```python

iter(itertools.chain(range(10), range(11)))
            
```

### After

```python

itertools.chain(range(10), range(11))
            
```

## redundant_elses

### Before

```python

def f(x: int) -> int:
    if x < 0:
        if x > -100:
            return 10
        else:
            return 101
    elif x >= 12:
        if x ** 2 >= 99:
            return x**x - 3
        elif x ** 3 >= 99:
            return x**2
        else:
            return 0
    else:
        return 11 - x
            
```

### After

```python

def f(x: int) -> int:
    if x < 0:
        if x > -100:
            return 10

        return 101
    if x >= 12:
        if x ** 2 >= 99:
            return x**x - 3
        if x ** 3 >= 99:
            return x**2

        return 0

    return 11 - x
            
```

## early_return

### Before

```python

def f(x) -> int:
    if x > 10:
        x += 1
        x *= 12
        print(x > 30)
        y = 100 - sum(x, 2, 3)
    else:
        y = 13
    return y
            
```

### After

```python

def f(x) -> int:
    if x > 10:
        x += 1
        x *= 12
        print(x > 30)
        return 100 - sum(x, 2, 3)
    else:
        return 13
            
```

## simplify_dict_unpacks

### Before

```python

x = {1: 2, 3: 4, **{99: 109, None: None}, 4: 5, **{"asdf": 12 - 13}}
            
```

### After

```python

x = {1: 2, 3: 4, 99: 109, None: None, 4: 5, 'asdf': 12 - 13}
            
```

## swap_if_else

### Before

```python

def f(x) -> int:
    if x > 10:
        if x < 100:
            return 4
        elif x >= 12:
            return 2
        return 99
    else:
        return 14
            
```

### After

```python

def f(x) -> int:
    if x <= 10:
        return 14
    else:
        if x < 100:
            return 4
        elif x >= 12:
            return 2
        return 99
            
```

## replace_dict_update_with_dict_literal

### Before

```python

x = {5: 13, **{102: 101, 103: 909}, 19: 14}
x.update({10: 100, 101: 220, 103: 223})
            
```

### After

```python

x = {5: 13, **{102: 101, 103: 909}, 19: 14, **{10: 100, 101: 220, 103: 223}}
            
```

## replace_collection_add_update_with_collection_literal

### Before

```python

x = {1, 2, 3}
x.update((7, 22))
x.update((191, 191))
            
```

### After

```python

x = {1, 2, 3, *(7, 22), *(191, 191)}
            
```

## add_missing_imports

### Before

```python

x = np.array()
z = pd.DataFrame()
            
```

### After

```python

import numpy as np
import pandas as pd


x = np.array()
z = pd.DataFrame()
            
```

## delete_unreachable_code

### Before

```python

def foo():
    import random
    return random.random() > 0.5
    print(3)
for i in range(10):
    print(2)
    if foo():
        break
    else:
        continue
    import os
    print(os.getcwd())
            
```

### After

```python

def foo():
    import random
    return random.random() > 0.5
for i in range(10):
    print(2)
    if foo():
        break
    else:
        continue
            
```

## remove_redundant_comprehension_casts

### Before

```python

list([x for y in range(10) for x in range(12 + y)])
            
```

### After

```python

[x for y in range(10) for x in range(12 + y)]
            
```

## move_imports_to_toplevel

### Before

```python

#!/usr/bin/env python3
'''docstring'''
import time
import os
import sys

sys.path.append(os.getcwd())
from somewhere import something

def function_call():
    from somewhere import something_else
    return something_else()

def call2():
    from somewhere_else import qwerty
    return qwerty()

def call3():
    import math
    print(math.sum([3]))
            
```

### After

```python

#!/usr/bin/env python3
'''docstring'''
import time
import os
import sys
import math

sys.path.append(os.getcwd())
from somewhere import something
from somewhere import something_else

def function_call():
    return something_else()

def call2():
    from somewhere_else import qwerty
    return qwerty()

def call3():
    print(math.sum([3]))
            
```

## implicit_dot

### Before

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

### After

```python

import numpy as np

i, j, k = 10, 11, 12

a = np.random.random((i, j))
b = np.random.random((j, k))

u = np.array(
    [
        [
            np.dot(a_, b_)
            for a_ in a
        ]
        for b_ in b.T
    ]
).T

print(u)
        
```

## merge_chained_comps

### Before

```python

x = (y ** z for y, z in ((y, z) for y, z in zip((3, 4, 5), [3, 4, 5])))
            
```

### After

```python

x = (y ** z for y, z in zip((3, 4, 5), [3, 4, 5]))
            
```

## replace_dictcomp_update_with_dict_literal

### Before

```python

x = {z: 21 for z in range(3)}
x.update({10: 100})
x.update({101: 220})
x.update({103: 223})
            
```

### After

```python

x = {**{z: 21 for z in range(3)}, **{10: 100}, **{101: 220}, **{103: 223}}
            
```

## delete_commented_code

### Before

```python

print('''
# x = 3
# y = z
'''
)

# true comment
# x = 3 > y  # this should be removed

z = 2
print(f'''
# x = {3}
# y = {z}
'''
)

print('''
# x = {x}
# y = {z}
'''.format(x=z, z=z)
)
            
```

### After

```python

print('''
# x = 3
# y = z
'''
)

# true comment

z = 2
print(f'''
# x = {3}
# y = {z}
'''
)

print('''
# x = {x}
# y = {z}
'''.format(x=z, z=z)
)
            
```

## replace_filter_lambda_with_comp

### Before

```python

x = itertools.filterfalse(lambda y: y > 0, (1, 2, 3))
            
```

### After

```python

x = (y for y in (1, 2, 3) if y <= 0)
            
```

## unravel_classes

### Before

```python

class Foo:
    def __init__(self):
        self.bar = 3

    def do_stuff(self):
        print(self.bar)

    @staticmethod
    def do_stuff_static(var, arg):
        print(var + arg)

    @classmethod
    def do_stuff_classmethod(cls, arg):
        cls.do_stuff_static(1, arg)

    def do_stuff_classmethod_2(self, arg):
        self.do_stuff_static(1, arg)

    @classmethod
    def do_stuff_classmethod_unused(cls, arg):
        print(arg)

    def do_stuff_no_self(self):
        print(3)

    @classmethod
    @functools.lru_cache(maxsize=None)
    @custom_decorator
    def i_have_many_decorators(cls):
        return 10
            
```

### After

```python

class Foo:
    def __init__(self):
        self.bar = 3

    def do_stuff(self):
        print(self.bar)

    @staticmethod
    def do_stuff_static(var, arg):
        print(var + arg)

    @classmethod
    def do_stuff_classmethod(cls, arg):
        cls.do_stuff_static(1, arg)

    @classmethod
    def do_stuff_classmethod_2(cls, arg):
        cls.do_stuff_static(1, arg)

    @staticmethod
    def do_stuff_classmethod_unused(arg):
        print(arg)

    @staticmethod
    def do_stuff_no_self():
        print(3)

    @staticmethod
    @functools.lru_cache(maxsize=None)
    @custom_decorator
    def i_have_many_decorators():
        return 10
            
```

## replace_for_loops_with_set_list_comp

### Before

```python

values = []
for i in range(10):
    if i % 3:
        if not i % 5:
            for j in range(11):
                if i % 7 and i % 9:
                    for k in range(5555):
                        values.append(i * j + k)
            
```

### After

```python

values = [i * j + k for i in range(10) if i % 3 and (not i % 5) for j in range(11) if i % 7 and i % 9 for k in range(5555)]
            
```

## optimize_contains_types

### Before

```python

1 in (1, 2, 3)
x in {1, 2, ()}
x in [1, 2, []]
w in [1, 2, {}]
w in {foo, bar, "asdf", coo}
w in (foo, bar, "asdf", coo)
w in {x for x in range(10)}
w in [x for x in range(10)]
w in (x for x in range(10))
w in {x for x in [1, 3, "", 909, ()]}
w in [x for x in [1, 3, "", 909, ()]]
w in (x for x in [1, 3, "", 909, ()])
x in sorted([1, 2, 3])
            
```

### After

```python

1 in {1, 2, 3}
x in {1, 2, ()}
x in (1, 2, [])
w in (1, 2, {})
w in {foo, bar, "asdf", coo}
w in (foo, bar, "asdf", coo)
w in {x for x in range(10)}
w in (x for x in range(10))
w in (x for x in range(10))
w in {x for x in [1, 3, "", 909, ()]}
w in (x for x in [1, 3, '', 909, ()])
w in (x for x in [1, 3, "", 909, ()])
x in [1, 2, 3]
            
```

## simplify_collection_unpacks

### Before

```python

x = (*(), 2, 3, *{99, 44}, (199, 991, 2), *[], [], *tuple([1, 2, 3]), 9)
            
```

### After

```python

x = (2, 3, *{99, 44}, 199, 991, 2, [], *tuple([1, 2, 3]), 9)
            
```

## replace_dict_assign_with_dict_literal

### Before

```python

x = {5: 13, **{102: 101, 103: 909}, 19: 14}
x[10] = 100
x[101] = 220
x[103] = 223
            
```

### After

```python

x = {5: 13, **{102: 101, 103: 909}, 19: 14, 10: 100, 101: 220, 103: 223}
            
```

## remove_duplicate_dict_keys

### Before

```python

{1: 2, 99: 101, "s": 4, 1: 22, sum(range(11)): 9999, sum(range(11)): 9999}
            
```

### After

```python

{99: 101, 's': 4, 1: 22, sum(range(11)): 9999, sum(range(11)): 9999}
            
```

## remove_duplicate_functions

### Before

```python

def f(a, b, c):
    w = a ** (b - c)
    return 1 + w // 2
def g(c, b, k):
    w = c ** (b - k)
    return 1 + w // 2
y = f(1, 2, 3)
h = g(1, 2, 3)
            
```

### After

```python

def f(a, b, c):
    w = a ** (b - c)
    return 1 + w // 2
y = f(1, 2, 3)
h = f(1, 2, 3)
            
```

## breakout_starred_args

### Before

```python

x = foo(a, b, *(c, d), e, *{f}, *[k, v, h])
            
```

### After

```python

x = foo(a, b, c, d, e, f, k, v, h)
            
```

## align_variable-names_with_convention

### Before

```python

some_variable = collections.namedtuple("some_variable", ["field", "foo", "bar"])
variable = TypeVar("variable")
T = Mapping[Tuple[int, int], Collection[str]]
something_else = 1


def foo() -> Tuple[some_variable, T]:
    _ax = 4
    print(_ax)
    R = 3
    print(R)
    s = 2
    print(s)
    return some_variable(1, 2, 3)

moose = namedtuple("moose", ["field", "foo", "bar"])

ax = 22
print(ax)


def main() -> None:
    bar: some_variable = foo()
    print(bar)
    return 0
        
```

### After

```python

SomeVariable = collections.namedtuple("some_variable", ["field", "foo", "bar"])
Variable = TypeVar("variable")
T = Mapping[Tuple[int, int], Collection[str]]
SOMETHING_ELSE = 1


def _foo() -> Tuple[SomeVariable, T]:
    ax = 4
    print(ax)
    r = 3
    print(r)
    s = 2
    print(s)
    return SomeVariable(1, 2, 3)

Moose = namedtuple("moose", ["field", "foo", "bar"])

AX = 22
print(AX)


def _main() -> None:
    bar: SomeVariable = _foo()
    print(bar)
    return 0
        
```

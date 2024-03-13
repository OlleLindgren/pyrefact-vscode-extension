import pathlib.Path as Path

import os, re

def asdf():
    x = None or os.getcwd()
    if 2 in {1, 2, 3}:
        print(3)
    print(Path.cwd())

class Foo:
    @staticmethod
    def asdf():
        x = None
        if 2 in {1, 2, 3}:
            y = x is not None
            z = y or not y
            print(3)

Foo.y = 3

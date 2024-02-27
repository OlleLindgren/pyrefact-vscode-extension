import os, re, sys as sys

# Start of range

from pathlib import Path

def asdf():
    print(3)
    print(Path.cwd())

# End of range

class Foo:
    @staticmethod
    def asdf():
        x = None
        if 2 in {1, 2, 3}:
            y = x is not None
            z = y or not y
            print(3)
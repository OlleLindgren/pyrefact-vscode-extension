import os
from pathlib import Path


def asdf():
    os.getcwd()
    print(3)
    print(Path.cwd())

class Foo:
    @staticmethod
    def asdf():
        print(3)

    y = 3

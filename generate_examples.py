"""Generate examples from pyrefact tests."""
import argparse
import ast
import sys
from pathlib import Path
from typing import Sequence

from pyrefact import parsing

TEMPLATE = """
## {fix_function_name}

### Before

```python
{before}
```

### After

```python
{after}
```
"""

EXAMPLES_MD = Path(__file__).parent / "EXAMPLES.md"


def _parse_args(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("pyrefact_repo_root", type=Path)
    return parser.parse_args(args)


def main(args: Sequence[str]) -> int:
    pyrefact_root = _parse_args(args).pyrefact_repo_root
    template = ast.Tuple(elts={ast.Tuple(elts=[ast.Constant(value=str)] * 2)})

    test_cases = []
    for test_filename in (pyrefact_root / "tests" / "unit").glob("test_*.py"):
        print(f"Found test file {test_filename}")
        with open(test_filename, "r", encoding="utf-8") as stream:
            source = stream.read()

        if "check_fixes_equal" not in source:
            continue

        root = parsing.parse(source)
        _, fix_function_name = test_filename.stem.split("_", 1)  # Remove test_
        try:
            matches = list(parsing.walk(root, template))
            if not matches:
                continue

            examples = [
                (test_case.elts[0].value, test_case.elts[1].value)
                for test_case in matches[0].elts
                if test_case.elts[0].value != test_case.elts[1].value
            ]

            before, after = max(
                examples,
                key=lambda testcase: (
                    testcase[0] != testcase[1]
                    and len(testcase[0].splitlines()) < 50
                    and len(testcase[1].splitlines()) < 50
                )
                * (len(testcase[1]) + len(testcase[0])),)

            test_cases.append(
                TEMPLATE.format(fix_function_name=fix_function_name, before=before, after=after))

        except StopIteration:
            continue

    with EXAMPLES_MD.open("w", encoding="utf-8") as stream:
        stream.write("".join(test_cases))

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

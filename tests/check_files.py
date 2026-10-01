#!/usr/bin/env python3
"""Check the shape of every *.lambda.txt file and print its length.

Each file must be exactly one line that starts with "=", has no trailing
whitespace, ends with a single newline, has balanced parentheses outside
string literals, and is at most 2084 chars (Name Manager's "Refers to" cap).
Exits non-zero on any failure.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAP = 2084


def problems(text):
    out = []
    if not text.endswith("\n") or text.endswith("\n\n"):
        out.append("must end with exactly one newline")
    lines = text.split("\n")[:-1] if text.endswith("\n") else text.split("\n")
    if len(lines) != 1:
        out.append(f"has {len(lines)} lines, expected 1")
    formula = lines[0] if lines else ""
    if not formula.startswith("="):
        out.append('does not start with "="')
    if formula != formula.rstrip():
        out.append("has trailing whitespace")
    depth, in_str = 0, False
    for c in formula:
        if c == '"':
            in_str = not in_str
        elif not in_str:
            depth += (c == "(") - (c == ")")
            if depth < 0:
                break
    if in_str:
        out.append("has an unterminated string literal")
    if depth != 0:
        out.append("has unbalanced parentheses")
    if len(formula) > CAP:
        out.append(f"is {len(formula)} chars, over the {CAP}-char cap")
    return out, len(formula)


def main():
    files = sorted(ROOT.glob("*/*.lambda.txt")) + sorted(ROOT.glob("*.lambda.txt"))
    if not files:
        print("no *.lambda.txt files found")
        return 1
    failures = 0
    for f in files:
        issues, length = problems(f.read_text(encoding="utf-8"))
        rel = f.relative_to(ROOT)
        if issues:
            failures += 1
            print(f"FAIL {rel}: {length} chars; " + "; ".join(issues))
        else:
            print(f"ok   {rel}: {length} chars ({CAP - length} under the {CAP} cap)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

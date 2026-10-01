#!/usr/bin/env python3
"""Check that each *.lambda.formatted.txt is exactly its *.lambda.txt plus whitespace.

All whitespace outside string literals is removed from the formatted file and
the result (plus the single final newline) must equal the single-line file
byte for byte. Exits non-zero on any mismatch or missing formatted file.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def strip_ws(text):
    """Remove whitespace outside "..." string literals ("" escapes toggle twice, so they work)."""
    out, in_str = [], False
    for c in text:
        if c == '"':
            in_str = not in_str
        if in_str or not c.isspace():
            out.append(c)
    if in_str:
        raise ValueError("unterminated string literal")
    return "".join(out)


def main():
    failures = 0
    sources = sorted(ROOT.glob("*/*.lambda.txt"))
    if not sources:
        print("no *.lambda.txt files found")
        return 1
    for src in sources:
        fmt = src.with_name(src.name.replace(".lambda.txt", ".lambda.formatted.txt"))
        rel = fmt.relative_to(ROOT)
        if not fmt.exists():
            print(f"FAIL {rel}: missing (run tools/pretty.py)")
            failures += 1
            continue
        want = src.read_bytes()
        got = (strip_ws(fmt.read_text(encoding="utf-8")) + "\n").encode("utf-8")
        if got == want:
            print(f"ok   {rel} == {src.relative_to(ROOT)} ({len(want) - 1} chars)")
        else:
            at = next((k for k, (a, b) in enumerate(zip(got, want)) if a != b), min(len(got), len(want)))
            print(f"FAIL {rel}: differs from {src.relative_to(ROOT)} at byte {at}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

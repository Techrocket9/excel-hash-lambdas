#!/usr/bin/env python3
"""Generate *.lambda.formatted.txt from each single-line *.lambda.txt.

Only newlines and two-space indentation are inserted, and only at top-level
commas inside LET(...) / LAMBDA(...) calls and around their parentheses.
String literals and {...} array constants are copied verbatim, and every
other function call stays on one line. Stripping all whitespace outside
string literals from the output gives back the input exactly (see
tools/check_formatted.py).

Usage:
  python tools/pretty.py            regenerate every formatted file
  python tools/pretty.py FILE...    print the formatted text of FILE(s)
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOCKS = ("LET", "LAMBDA")
IDENT = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.")


def skip_atom(s, i):
    """If s[i] opens a string literal or array constant, return the index just past it."""
    if s[i] == '"':
        j = i + 1
        while True:
            j = s.index('"', j) + 1
            if j < len(s) and s[j] == '"':  # "" is an escaped quote
                j += 1
                continue
            return j
    if s[i] == "{":
        return s.index("}", i) + 1
    return None


def close_paren(s, i):
    """s[i] == '('; return the index of its matching ')'."""
    depth = 0
    while i < len(s):
        end = skip_atom(s, i)
        if end is not None:
            i = end
            continue
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced parentheses")


def split_args(s):
    """Split an argument list at its top-level commas."""
    args, depth, start, i = [], 0, 0, 0
    while i < len(s):
        end = skip_atom(s, i)
        if end is not None:
            i = end
            continue
        c = s[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == "," and depth == 0:
            args.append(s[start:i])
            start = i + 1
        i += 1
    args.append(s[start:])
    return args


def block_at(s, i):
    """Return 'LET' or 'LAMBDA' if a call to it starts at s[i]."""
    if i > 0 and s[i - 1] in IDENT:
        return None
    for name in BLOCKS:
        if s.startswith(name + "(", i):
            return name
    return None


def fmt(s, level):
    """Format expression s, whose first character sits on a line indented `level` steps."""
    out, i = [], 0
    pad = "  " * level
    inner = "\n" + "  " * (level + 1)
    while i < len(s):
        end = skip_atom(s, i)
        if end is not None:
            out.append(s[i:end])
            i = end
            continue
        name = block_at(s, i)
        if name is None:
            out.append(s[i])
            i += 1
            continue
        lp = i + len(name)
        rp = close_paren(s, lp)
        args = split_args(s[lp + 1:rp])
        if name == "LAMBDA":
            # Parameters stay on the opening line; the body gets its own lines.
            out.append("LAMBDA(" + ",".join(args[:-1]) + "," + inner)
            out.append(fmt(args[-1], level + 1))
        else:
            # One "name,value," pair per line, then the final calculation.
            out.append("LET(")
            for k in range(0, len(args) - 1, 2):
                out.append(inner + args[k] + "," + fmt(args[k + 1], level + 1) + ",")
            out.append(inner + fmt(args[-1], level + 1))
        out.append("\n" + pad + ")")
        i = rp + 1
    return "".join(out)


def pretty(formula):
    formula = formula.strip()
    if not formula.startswith("="):
        raise ValueError("formula must start with '='")
    return "=" + fmt(formula[1:], 0) + "\n"


def lambda_files():
    return sorted(p for p in ROOT.glob("*/*.lambda.txt"))


def formatted_path(p):
    return p.with_name(p.name.replace(".lambda.txt", ".lambda.formatted.txt"))


def main(argv):
    if argv:
        for name in argv:
            sys.stdout.write(pretty(pathlib.Path(name).read_text()))
        return 0
    for src in lambda_files():
        dst = formatted_path(src)
        dst.write_text(pretty(src.read_text()))
        print(f"wrote {dst.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

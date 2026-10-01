#!/usr/bin/env python3
"""Check every row of the three test-vectors.md tables against Python hashlib.

Each table must have "Input", "Expected output" and "Excel-verified" columns.
Accepted Input forms:

  (empty string)
  `literal text`
  `x` × N                          the character x repeated N times
  `=REPT("s",N)`                   an Excel formula built from string
  `=REPT("s",N)&"t"`               literals, &, REPT, LEFT, CHAR and
  `=CHAR(n)`                       UNICHAR (backticks optional)

Expected output is either a lowercase hex digest, which must equal hashlib
over the UTF-8 bytes of the input, or the literal error string, in which case
the input must contain a code point above 127. Exits non-zero on any mismatch.
"""
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = {
    "md5/test-vectors.md": "md5",
    "sha256/test-vectors.md": "sha256",
    "sha3_256/test-vectors.md": "sha3_256",
}
ERROR = "Error: non-ASCII input detected"
EXCEL_MAX_CHARS = 32767  # Excel's cell / string length limit


# ---- a tiny evaluator for the Excel expressions used in the Input column ----

TOKEN = re.compile(r'\s*(?:(?P<str>"(?:[^"]|"")*")|(?P<num>\d+)|(?P<name>[A-Z]+)|(?P<op>[(),&]))')


def tokenize(src):
    pos, out = 0, []
    src = src.rstrip()
    while pos < len(src):
        m = TOKEN.match(src, pos)
        if not m:
            raise ValueError(f"cannot parse formula at {src[pos:]!r}")
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
        pos = m.end()
    return out


def char(n):
    # CHAR above 127 is code-page dependent in Excel (Mac Roman vs Windows-1252);
    # any such character is non-ASCII, which is all the error rows need.
    if not 1 <= n <= 255:
        raise ValueError(f"CHAR({n}) out of range")
    return chr(n)


FUNCS = {
    "REPT": lambda s, n: s * n,
    "LEFT": lambda s, n: s[:n],
    "CHAR": char,
    "UNICHAR": chr,
}


class Parser:
    def __init__(self, src):
        self.toks = tokenize(src)
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self, kind, value=None):
        k, v = self.peek()
        if k != kind or (value is not None and v != value):
            raise ValueError(f"expected {value or kind}, got {v!r}")
        self.i += 1
        return v

    def expr(self):
        val = self.term()
        while self.peek() == ("op", "&"):
            self.i += 1
            val = str(val) + str(self.term())
        return val

    def term(self):
        kind, v = self.peek()
        if kind == "str":
            self.i += 1
            return v[1:-1].replace('""', '"')
        if kind == "num":
            self.i += 1
            return int(v)
        if kind == "name" and v in FUNCS:
            self.i += 1
            self.take("op", "(")
            args = [self.expr()]
            while self.peek() == ("op", ","):
                self.i += 1
                args.append(self.expr())
            self.take("op", ")")
            return FUNCS[v](*args)
        raise ValueError(f"unsupported token {v!r}")

    def parse(self):
        val = self.expr()
        if self.i != len(self.toks):
            raise ValueError("trailing input")
        return str(val)


def parse_input(cell):
    cell = cell.strip()
    if cell == "(empty string)":
        return ""
    m = re.fullmatch(r"`(.)` × (\d+)", cell)
    if m:
        return m.group(1) * int(m.group(2))
    m = re.fullmatch(r"`(=.*)`|(=.*)", cell)
    if m:
        return Parser((m.group(1) or m.group(2))[1:]).parse()
    m = re.fullmatch(r"`(.*)`", cell)
    if m:
        return m.group(1)
    raise ValueError(f"unrecognised input form {cell!r}")


def selftest():
    assert parse_input("(empty string)") == ""
    assert parse_input("`abc`") == "abc"
    assert parse_input("`a` × 3") == "aaa"
    assert parse_input('`=REPT("ab",3)`') == "ababab"
    assert parse_input('=REPT("ab",2)&"c"') == "ababc"
    assert parse_input("`=CHAR(127)`") == "\x7f"
    assert parse_input('`=CHAR(9)&"t"&CHAR(10)`') == "\tt\n"
    assert parse_input('`=LEFT(REPT("abc",5),4)`') == "abca"
    assert parse_input("`=UNICHAR(128512)`") == "\U0001F600"
    assert parse_input('`="say ""hi"""`') == 'say "hi"'


# ---- table parsing ----

def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def tables(text):
    """Yield (line_no, header, rows) for each markdown table; rows are (line_no, cells)."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and re.fullmatch(r"\|?[\s:|-]+\|?", lines[i + 1].strip()):
            header, start, rows = cells(lines[i]), i + 1, []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append((i + 1, cells(lines[i])))
                i += 1
            yield start, header, rows
        else:
            i += 1


def check_file(rel, alg):
    text = (ROOT / rel).read_text(encoding="utf-8")
    failures = rows_seen = verified = 0
    for line_no, header, rows in tables(text):
        try:
            ci, ce, cv = (header.index(h) for h in ("Input", "Expected output", "Excel-verified"))
        except ValueError:
            print(f"FAIL {rel}:{line_no}: table header {header} lacks Input / Expected output / Excel-verified")
            failures += 1
            continue
        for row_no, row in rows:
            where = f"{rel}:{row_no}"
            rows_seen += 1
            if len(row) != len(header):
                print(f"FAIL {where}: {len(row)} cells, header has {len(header)}")
                failures += 1
                continue
            try:
                s = parse_input(row[ci])
            except ValueError as e:
                print(f"FAIL {where}: {e}")
                failures += 1
                continue
            expected = row[ce].strip("`")
            flag = row[cv]
            if flag not in ("yes", "no"):
                print(f"FAIL {where}: Excel-verified must be 'yes' or 'no', got {flag!r}")
                failures += 1
            verified += flag == "yes"
            if len(s) > EXCEL_MAX_CHARS:
                print(f"FAIL {where}: input is {len(s)} chars, over Excel's {EXCEL_MAX_CHARS} limit")
                failures += 1
            if expected == ERROR:
                if max(map(ord, s), default=0) <= 127:
                    print(f"FAIL {where}: expects the non-ASCII error but input {row[ci]} is pure ASCII")
                    failures += 1
                continue
            if max(map(ord, s), default=0) > 127:
                print(f"FAIL {where}: input {row[ci]} is non-ASCII, so the formula returns the error string")
                failures += 1
                continue
            got = hashlib.new(alg, s.encode("utf-8")).hexdigest()
            if got != expected:
                print(f"FAIL {where}: {row[ci]} expected {expected}, hashlib gives {got}")
                failures += 1
    if rows_seen == 0:
        print(f"FAIL {rel}: no test-vector rows found")
        failures += 1
    else:
        status = "ok  " if failures == 0 else "FAIL"
        print(f"{status} {rel}: {rows_seen} rows checked against hashlib.{alg} ({verified} marked Excel-verified)")
    return failures


def main():
    selftest()
    failures = sum(check_file(rel, alg) for rel, alg in FILES.items())
    if failures:
        print(f"{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

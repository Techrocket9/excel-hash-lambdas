# Test vectors

These are the standard [RFC 1321](https://www.rfc-editor.org/rfc/rfc1321) test vectors plus the well-known pangram. All six must produce the expected output.

| Input | Expected output |
|---|---|
| (empty string) | `d41d8cd98f00b204e9800998ecf8427e` |
| `a` | `0cc175b9c0f1b6a831c399e269772661` |
| `abc` | `900150983cd24fb0d6963f7d28e17f72` |
| `message digest` | `f96b697d7cb7938d525a2f31aaf161d0` |
| `abcdefghijklmnopqrstuvwxyz` | `c3fcd3d76192e4007dfb496cca67e13b` |
| `The quick brown fox jumps over the lazy dog` | `9e107d9d372bb6826bd81d3542a419d6` |

## Reproducing in Excel

After installing the `MD5` named LAMBDA per the [README](../README.md#2-installation-the-only-step-that-matters), drop the inputs into column A and the formula `=MD5(A1)` into column B:

| A | B |
|---|---|
| `=""` | `=MD5(A1)` |
| `a` | `=MD5(A2)` |
| `abc` | `=MD5(A3)` |
| `message digest` | `=MD5(A4)` |
| `abcdefghijklmnopqrstuvwxyz` | `=MD5(A5)` |
| `The quick brown fox jumps over the lazy dog` | `=MD5(A6)` |

Column B should match the expected outputs above exactly.

## Notes on what is *not* covered

- **Multi-block inputs.** The longest test vector here (43 chars) still fits in a single 512-bit block. The padding logic is exercised, but the outer `REDUCE` over blocks only ever runs once. Hashing a 100+ character string is a useful additional check if you fork the formula.
- **Non-ASCII text.** `CODE(MID(...))` returns the codepoint in Excel's current text encoding, which on most systems is UTF-16. Inputs containing characters outside the ASCII range will hash to something, but it will not match the byte-level MD5 of the UTF-8 encoding of the same string. If you need UTF-8 semantics, encode upstream.
- **Numeric inputs.** Pass everything as text. `=MD5(123)` will coerce to `"123"` in most cases, but be explicit with `=MD5(TEXT(A1,"0"))` if it matters.

# excel-md5-lambda

MD5, implemented as a single Excel LAMBDA. No VBA, no add-ins, no macros.

```
=MD5("abc")  →  900150983cd24fb0d6963f7d28e17f72
```

<!-- TODO: add screenshot -->

## 1. What this is

A pure-formula MD5 hash function for Excel, implemented as a single LAMBDA. No VBA, no add-ins, no macros, no Office Scripts — works in any Excel that supports `LAMBDA` / `LET` / `REDUCE` (Excel 365, Excel for the web, Excel 2024+).

Useful for:

- Generating deterministic IDs from row content.
- Detecting changed records by hashing a concatenation of fields.
- A hands-on demonstration of just how far Excel's modern formula language can go.
- **Not** for security. MD5 is cryptographically broken. Use this for non-adversarial fingerprinting only.

## 2. Installation (the only step that matters)

The function ships as a single line of text. To make `=MD5(...)` available in your workbook:

1. Open your workbook in Excel.
2. Go to **Formulas → Name Manager → New** (Ctrl+F3 on Windows, Cmd+F3 on Mac).
3. Set **Name** to `MD5`.
4. Set **Scope** to `Workbook`.
5. Open [`md5.lambda.txt`](md5.lambda.txt) from this repo, copy the entire single line (it's long — make sure you grab all of it).
6. Paste into the **Refers to** box. The leading `=` must be there.
7. Click **OK**, then **Close**.

You can now use `=MD5("abc")` in any cell. It returns `900150983cd24fb0d6963f7d28e17f72`.

If you'd like to read the formula before installing it, [`md5.lambda.formatted.txt`](md5.lambda.formatted.txt) contains the same expression with line breaks and indentation.

## 3. Test vectors

The standard [RFC 1321](https://www.rfc-editor.org/rfc/rfc1321) vectors plus the pangram. All six must pass.

| Input | Expected output |
|---|---|
| (empty string) | `d41d8cd98f00b204e9800998ecf8427e` |
| `a` | `0cc175b9c0f1b6a831c399e269772661` |
| `abc` | `900150983cd24fb0d6963f7d28e17f72` |
| `message digest` | `f96b697d7cb7938d525a2f31aaf161d0` |
| `abcdefghijklmnopqrstuvwxyz` | `c3fcd3d76192e4007dfb496cca67e13b` |
| `The quick brown fox jumps over the lazy dog` | `9e107d9d372bb6826bd81d3542a419d6` |

A reproducible cell layout is in [`tests/test-vectors.md`](tests/test-vectors.md).

## 4. How it works

A walk through each `LET` binding. For the algorithm itself, see [RFC 1321](https://www.rfc-editor.org/rfc/rfc1321); this section describes how each piece is expressed in Excel.

- **`modBig` / `maskAll` / `addM` / `notM` / `rotL`** — 32-bit unsigned arithmetic primitives built on top of Excel's `BITAND` / `BITOR` / `BITXOR` / `BITLSHIFT` / `BITRSHIFT`. `addM` does mod-2³² addition, `notM` does bitwise NOT against a 32-bit mask, and `rotL` is left-rotate. `rotL` masks its input down to `(32 - n)` bits *before* shifting so the shifted result cannot overflow past 2³² (see Quirk 3 below).
- **`mlen` / `plen` / `nblk`** — message length (in characters / bytes), padded length (rounded up to a multiple of 64 with room for an 8-byte length suffix), and the number of 512-bit blocks.
- **`padByte(idx)`** — returns the byte at index `idx` of the padded message: the original byte if in range, then `0x80`, then zeros, then the original message length in bits as a little-endian 64-bit integer in the final 8 bytes.
- **`getWord(blkIdx, wordIdx)`** — assembles four bytes into a little-endian 32-bit word. MD5 operates on words in little-endian order; this is where that conversion happens.
- **`karr`** — the K constant table, computed as `floor(2^32 * abs(sin(i)))` for `i = 1..64`. Generated with `SEQUENCE(64)`, so the whole table is one cell expression rather than 64 hard-coded constants.
- **`shiftV(idx)`** — the per-round per-step rotation amount lookup. Four rounds × four positions = 16 distinct values, indexed by `(round, idx mod 4)`.
- **`hInit`** — the four IV words A, B, C, D, expressed as a 1×4 row array via `CHOOSE({1,2,3,4}, ...)`.
- **`finalH`** — the meat. An outer `REDUCE` walks each 512-bit block, accumulating a 1×4 state array. Inside it, a second `REDUCE` walks all 64 round operations, picking the right F/G/H/I function and message-word index per round, then permuting the state. Carrying the four-word hash state as a 1×4 array through `REDUCE` is the trick that makes the whole thing pure-formula (see Quirk 4).
- **`hexByte` / `wordHex`** — convert each 32-bit word to 8 hex characters in little-endian byte order, then concatenate all four words and lowercase the result.

## 5. Excel quirks I had to work around

This was supposed to be a 30-minute exercise. It took several hours because Excel's formula parser has undocumented restrictions that silently reject otherwise valid LAMBDA bodies. Documenting them here, because anyone else attempting a pure-LAMBDA crypto/hashing function will hit them.

### Quirk 1: LET variable names cannot match the cell-reference pattern

Excel rejects any `LET` (or `LAMBDA` parameter) name that matches the pattern `[A-Z]{1,3}\d+` where the letter portion is a valid column ≤ XFD (16384) and the digit portion is a valid row ≤ 1048576. The rejection is silent — you get a generic "formula is invalid" error with no hint about which name caused it.

Names that look fine but Excel refuses:

| Rejected | Why |
|---|---|
| `M32` | column M, row 32 — valid cell reference |
| `ADD32` | "ADD" is column 784, row 32 — valid cell reference |
| `NOT32` | "NOT" is column 9874, row 32 — valid cell reference |
| `MOD32` | "MOD" is column 9182, row 32 — valid cell reference |
| `b1`, `b2`, `b3` | columns B, rows 1–3 |
| `MAX32` | "MAX" is column 8838, row 32 |

Names that **are** safe:

- 4+ letters before the digits (column letters max out at 3): `MASK`, `MASK32`, `modBig`, `addM`.
- A letter portion that produces a column > XFD: rare, hard to remember, don't bother.
- No digits at all: `karr`, `hInit`, `padByte`, `shiftV`.
- Underscores break the pattern: `b_1`, `MOD_32`.

In this implementation every internal name was chosen specifically to avoid this trap. If you fork and rename anything, run all six test vectors before assuming it still works.

### Quirk 2: Office.js `names.add()` cannot register LAMBDAs containing `REDUCE`

Attempting to register this LAMBDA programmatically via the JavaScript API (`context.workbook.names.add("MD5", formulaText)`) appears to succeed, but every call to `=MD5(...)` returns `#REF!`. The same exact formula text works perfectly when:

- pasted directly into a cell as `=LAMBDA(...)("abc")`, or
- entered manually through Name Manager in the UI.

This is why the install instructions tell users to use Name Manager rather than shipping a script. If you're building tooling that auto-installs LAMBDAs into workbooks, be aware that anything containing `REDUCE` over an array accumulator may silently break when added via the API.

### Quirk 3: `BITLSHIFT` overflows past 2³², so masking must come first

Excel's `BITLSHIFT(x, n)` will happily produce values larger than 2³², which corrupts subsequent bitwise operations. Every left-rotate has to mask the input down to `(32 - n)` bits before shifting:

```
rotL(x, n) = ((x AND (2^(32-n) - 1)) << n) OR (x >> (32-n))   mod 2^32
```

Forget the mask and you get garbage hashes for any input long enough to set the high bits.

### Quirk 4: Carrying array state through `REDUCE`

Modern Excel does support array accumulators in `REDUCE` — you can pass a 1×4 row array as the seed and have the lambda return another 1×4 row array each iteration. The trick is that you can't construct that array with `{a,b,c,d}` literal syntax when the elements are formula expressions; you need `CHOOSE({1,2,3,4}, a, b, c, d)`. This is used in two places: building the initial hash state, and producing the new state at the end of each round.

### Quirk 5: `INDEX(arr, 1, n)` for column extraction from a 1×4 row

Reading individual hash words from the 1×4 state array uses `INDEX(state, 1, 1)`, `INDEX(state, 1, 2)`, etc. The single-argument form `INDEX(state, n)` does not reliably work on a 1×N row array.

## 6. Performance

Hashing a single short string takes well under a second. Hashing thousands of strings down a column is slow — Excel re-evaluates the entire LAMBDA per cell, including rebuilding the 64-element K table and walking the full block/round structure. For bulk hashing, prefer Power Query's `Binary.Buffer(Text.ToBinary(x))` + `Binary.ToList` approach, or just use Python.

## 7. License

[MIT](LICENSE).

## 8. Contributing

Welcome PRs that:

- Add SHA-1 / SHA-256 in the same pure-LAMBDA style.
- Reduce the formula's character count without breaking the test vectors.
- Document additional Excel parser quirks discovered along the way.

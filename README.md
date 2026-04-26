# excel-hash-lambdas

Pure-formula cryptographic hash functions for Excel, implemented as single LAMBDA expressions. No VBA, no add-ins, no macros, no Office Scripts. Currently ships MD5 and SHA-256, both installed the same way: open Name Manager, paste the formula, give it a name.

```
=MD5_("abc")     →  900150983cd24fb0d6963f7d28e17f72
=SHA256_("abc")  →  ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
```

Works in any Excel that supports `LAMBDA` / `LET` / `REDUCE` / `HSTACK` (Excel 365, Excel for the web, Excel 2024+).

## 1. At a glance

| Function | Output | Speed | Use for |
|---|---|---|---|
| `=MD5_(text)` | 32 hex chars | fastest | non-security fingerprints, legacy interop |
| `=SHA256_(text)` | 64 hex chars | slower (longer schedule) | content addressing, change detection, anywhere you'd reach for a hash |

Neither is appropriate for security-sensitive use. MD5 is broken; SHA-256 is fine cryptographically but a formula in a spreadsheet is the wrong place to put a security primitive. Use these for fingerprinting, deduplication, and change detection.

## 2. Algorithms

- **[md5/](md5/)** — single-line formula, formatted version, [test vectors](md5/test-vectors.md). See the [MD5 internals](#md5-internals) section below for the deep walkthrough and the original Excel quirks list.
- **[sha256/](sha256/)** — single-line formula, formatted version, [test vectors](sha256/test-vectors.md) including the FIPS 180-2 two-block vector.

## 3. Install

Same procedure for every function in this repo. Substitute the function name and source file as appropriate.

1. Open your workbook in Excel.
2. **Formulas → Name Manager → New** (Ctrl+F3 on Windows, Cmd+F3 on Mac).
3. Set **Name** to the function name (`MD5_` or `SHA256_` — note the trailing underscore, see below).
4. Set **Scope** to `Workbook`.
5. Open the corresponding `*.lambda.txt` file from this repo and copy the entire single line — it's long, make sure you grab all of it:
   - MD5 → [`md5/md5.lambda.txt`](md5/md5.lambda.txt)
   - SHA-256 → [`sha256/sha256.lambda.txt`](sha256/sha256.lambda.txt)
6. Paste into the **Refers to** box. The leading `=` must be there.
7. **OK**, then **Close**.

Each `*.lambda.formatted.txt` next to the single-line file contains the same formula with line breaks and indentation if you want to read before you paste.

**Why the trailing underscore?** Excel's Name Manager rejects any defined name that looks like a cell address. `MD5` is parsed as "column MD, row 5" and refused; `SHA256` is parsed as "column SHA, row 256" and refused. This is the same `[A-Z]{1,3}\d+` rule documented in the [quirks section below](#quirk-1-cell-reference-pattern-names-are-rejected--both-inside-let-and-in-name-manager) — it applies to workbook-level defined names, not just LET variables. Trailing-underscore is the conventional escape hatch (cell addresses can't contain underscores). Call sites become `=MD5_("abc")` and `=SHA256_("abc")`.

## 4. What works the same across all functions

- Same Excel version requirements (`LAMBDA` / `LET` / `REDUCE`; SHA-256 also needs `HSTACK`).
- Same Name Manager install procedure.
- Same input handling: characters are read via `CODE(MID(...))`, which gives Excel's per-character codepoint (typically UTF-16 code units). **UTF-8 multi-byte input is not correctly handled** — any character outside the ASCII range will produce a hash that does not match `md5sum` / `sha256sum` on the UTF-8 encoding of the same string. Known limitation of both formulas; encode upstream if you need byte-level interop.
- Same performance shape: fine on individual cells, slow when filled down thousands of rows because Excel re-evaluates the whole LAMBDA per cell.

## 5. What's different about SHA-256

Same trick scaled up, plus one new pattern. Notable differences from the MD5 implementation:

- **Big-endian byte order throughout.** Word assembly, length encoding in padding, and final hex output all run high-byte-first. MD5 is little-endian for the same operations.
- **8-word state instead of 4.** The array carried through `REDUCE` is 1×8 (`a` through `h`), built and updated with `CHOOSE({1,2,3,4,5,6,7,8}, ...)`.
- **64-word message schedule built with `REDUCE` + `HSTACK`.** Each iteration appends one new word to a growing 1×N array. This is the key trick that makes pure-LAMBDA SHA-256 viable — without grown arrays you can't index back into prior schedule words from inside the loop.
- **K and H constants are embedded literally.** They're derived from cube/square roots of small primes, not from a closed form like MD5's `floor(2^32 * abs(sin(i)))`, so the formula carries them as inline `{...}` array literals.
- **Slower than MD5.** Longer schedule (64 vs 16 words after derivation), more state words to carry, and 64 rounds operating on more data per round.

## 6. Excel quirk addendum

The original [MD5 quirks list](#md5-excel-quirks-the-original-five) (cell-reference-shaped names rejected in both `LET` and Name Manager, `BITLSHIFT` overflow, array state through `REDUCE`, `INDEX` row addressing) all still apply. SHA-256 added these:

- **The cell-reference name trap claims new victims with two-letter prefixes.** `tt1` and `tt2` look harmless — but `TT` is column 540, valid through row 1048576, so Excel rejects both. Anything that ends in digits is suspect, regardless of the letter prefix length. SHA-256 uses `tone` / `ttwo` instead of `t1` / `t2`.
- **`HSTACK` inside `REDUCE` works for growing arrays.** This wasn't needed for MD5 but is essential here. Each iteration `HSTACK`s one new word onto the accumulator, producing a final 1×64 array indexed by the round loop. The shape stays 1×N throughout, which keeps `INDEX(arr, 1, n)` access patterns consistent with the rest of the formula.
- **Big-endian length encoding matters.** MD5 packs the message length as little-endian in the trailing 8 bytes; SHA-256 packs it big-endian. The padding lambda differs by exactly one expression: `256^(idx-plen+8)` (MD5) vs `256^(plen-1-idx)` (SHA-256). Easy thing to copy wrong, and the failure mode is silent — short inputs hash correctly, longer ones diverge.

## 7. Roadmap

- **SHA-1** — straightforward; same shape as SHA-256 with a smaller schedule and different round functions.
- **SHA-512** — needs 64-bit arithmetic, which Excel's `BIT*` family does not natively support. Doable by simulating 64-bit ops as pairs of 32-bit halves, but painful and slow. Probably not worth it unless someone asks.

PRs that shorten an existing formula without breaking its test vectors, or document additional Excel parser quirks, are also welcome.

## 8. License

[MIT](LICENSE).

---

## MD5 internals

Walkthrough of the MD5 LAMBDA, kept here so the per-algorithm directory stays small. For the algorithm itself see [RFC 1321](https://www.rfc-editor.org/rfc/rfc1321).

- **`modBig` / `maskAll` / `addM` / `notM` / `rotL`** — 32-bit unsigned arithmetic primitives built on top of Excel's `BITAND` / `BITOR` / `BITXOR` / `BITLSHIFT` / `BITRSHIFT`. `addM` does mod-2³² addition, `notM` does bitwise NOT against a 32-bit mask, and `rotL` is left-rotate. `rotL` masks its input down to `(32 - n)` bits *before* shifting so the shifted result cannot overflow past 2³² (see Quirk 3 below).
- **`mlen` / `plen` / `nblk`** — message length, padded length (rounded up to a multiple of 64 with room for an 8-byte length suffix), and number of 512-bit blocks.
- **`padByte(idx)`** — returns the byte at index `idx` of the padded message: original byte if in range, then `0x80`, then zeros, then the original message length in bits as a little-endian 64-bit integer in the final 8 bytes.
- **`getWord(blkIdx, wordIdx)`** — assembles four bytes into a little-endian 32-bit word.
- **`karr`** — the K constant table, computed as `floor(2^32 * abs(sin(i)))` for `i = 1..64`. Generated with `SEQUENCE(64)`, so the whole table is one cell expression rather than 64 hard-coded constants.
- **`shiftV(idx)`** — the per-round per-step rotation amount lookup.
- **`hInit`** — the four IV words A, B, C, D, expressed as a 1×4 row array via `CHOOSE({1,2,3,4}, ...)`.
- **`finalH`** — the meat. An outer `REDUCE` walks each 512-bit block, accumulating a 1×4 state array. Inside it, a second `REDUCE` walks all 64 round operations, picking the right F/G/H/I function and message-word index per round, then permuting the state.
- **`hexByte` / `wordHex`** — convert each 32-bit word to 8 hex characters in little-endian byte order, concatenate all four words, lowercase.

### MD5 Excel quirks (the original five)

#### Quirk 1: Cell-reference-pattern names are rejected — both inside LET *and* in Name Manager

Excel rejects any name that matches `[A-Z]{1,3}\d+` where the letter portion is a valid column ≤ XFD (16384) and the digit portion is a valid row ≤ 1048576. **This rule applies to both `LET` / `LAMBDA` parameter names and to workbook-level defined names registered through Name Manager.** Inside a formula the rejection is silent (generic "formula is invalid" error); in Name Manager the dialog gives a slightly more specific complaint about syntax but does not name the rule.

| Rejected | Why |
|---|---|
| `M32` | column M, row 32 |
| `ADD32` | "ADD" is column 784, row 32 |
| `NOT32` | "NOT" is column 9874, row 32 |
| `MOD32` | "MOD" is column 9182, row 32 |
| `b1`, `b2`, `b3` | columns B, rows 1–3 |
| `MAX32` | "MAX" is column 8838, row 32 |
| `MD5` | "MD" is column 342, row 5 — bites you when registering the LAMBDA |
| `SHA256` | "SHA" is column 12029, row 256 — same |

Safe: 4+ letters before digits (`MASK32`, `modBig`), no digits at all (`karr`, `padByte`), or underscores to break the pattern (`b_1`, `MD5_`, `SHA256_`). Anyone publishing a hash, cipher, or codec LAMBDA — `SHA1`, `RC4`, `AES1`, `B64`, `CRC32` — will hit this when they try to install it. Pick the trailing-underscore convention up front.

#### Quirk 2: Office.js `names.add()` cannot register LAMBDAs containing `REDUCE`

Registering programmatically via `context.workbook.names.add("MD5", formulaText)` appears to succeed, but every call returns `#REF!`. The same formula works when pasted into a cell as `=LAMBDA(...)("abc")` or entered through Name Manager. If you build tooling that auto-installs LAMBDAs, anything containing `REDUCE` over an array accumulator may silently break via the API.

#### Quirk 3: `BITLSHIFT` overflows past 2³²

`BITLSHIFT(x, n)` will produce values larger than 2³², which corrupts subsequent bitwise ops. Mask before shifting:

```
rotL(x, n) = ((x AND (2^(32-n) - 1)) << n) OR (x >> (32-n))   mod 2^32
```

#### Quirk 4: Carrying array state through `REDUCE`

`REDUCE` supports array accumulators — pass a 1×4 row array as the seed and return a 1×4 row array each iteration. You can't construct it with `{a,b,c,d}` literal syntax when the elements are formula expressions; use `CHOOSE({1,2,3,4}, a, b, c, d)`.

#### Quirk 5: `INDEX(arr, 1, n)` for column extraction from a 1×N row

`INDEX(state, 1, 1)`, `INDEX(state, 1, 2)`, etc. The single-argument form `INDEX(state, n)` does not reliably work on a 1×N row array.

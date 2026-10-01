# Changelog

## v2 (2026-09-30)

Each algorithm is now a single self-contained LAMBDA. Digests for ASCII input are unchanged.

| Defined name | v1 | v2 |
|---|---|---|
| `MD5_` | 1 LAMBDA, 2067 chars | 1 LAMBDA, 1013 chars |
| `SHA256_` | 5 LAMBDAs, plus the shared `ASCII_` | 1 LAMBDA, 1089 chars |
| `SHA3_` | 7 LAMBDAs, plus the shared `ASCII_` | 1 LAMBDA, 953 chars |

The v2 formulas were tested in Excel for Mac 16.113 (Microsoft 365). Each `test-vectors.md` lists the inputs that were run. The names were also registered through Office.js `names.add`. Windows Excel has not been tested.

**Upgrading from v1.** First paste the new text over `MD5_`, `SHA256_` and `SHA3_`. Then delete these names from Name Manager, because nothing uses them any more:

- `ASCII_`
- `SHA256K_`, `SHA256I_`, `SHA256H_`, `SHA256A_`
- `SHA3K_`, `SHA3T_`, `SHA3RP_`, `SHA3CI_`, `SHA3F_`, `SHA3H_`

### Test vectors

The formulas were always correct. Only the published vectors were wrong:

- SHA3-256 of `a` was wrong after the first 44 hex characters. It is now `80084bf2fba02475726feb2cab2d8215eab14bc6bdd8bfb2c8151257032ecd8b`.
- SHA3-256 of `a`×55 was wrong. It is now `78c2a04624b9328ae0e40cb8cdd29980f6ff55abf2dca68e3412d09eed4b9d03`. The row was also labelled a "rate-block edge", but 55 is only an edge for MD5 and SHA-256.
- `CHAR(127)` was missing for MD5 and SHA3-256. It is now filled in.

All three files share one input list: block-boundary lengths, multi-block lengths and the 32767-char maximum. Every digest is computed with `hashlib`, and an **Excel-verified** column records which rows were run in Excel.

### Checks

- `tests/verify_vectors.py`, `tests/emulate.py`, `tests/check_files.py` and `tools/check_formatted.py` check the repo without Excel.
- `tools/pretty.py` generates the `*.lambda.formatted.txt` files.

### Documentation corrections

- Office.js `names.add` with a `REDUCE` LAMBDA returning `#REF!` did not reproduce on Excel for Mac 16.113. The README now describes it as historical.
- Single-argument `INDEX(arr, n)` works on 1×N rows. The old "Quirk 5" said it didn't.
- The "64-bit rotate by 32 is the trap / 5 of 25 lanes" paragraph was wrong. No Keccak ρ offset is 32, so that branch of the v1 rotate never ran.
- Column SHA is 13053, not 12029. Bare `SHA3` is a cell reference (column SHA, row 3), so the old SHA3 README's claim that it was an acceptable name was wrong.
- Non-ASCII input is rejected with an error string. One old paragraph still said it produced a wrong hash.
- The old README said MD5 was ~1850 chars in one place and 2067 in another. 2067 was right for v1.

## v1

This is the history up to commit `82b77d6`:

- `MD5_`: one LAMBDA with the ASCII check inlined.
- `SHA256_`: five LAMBDAs.
- `SHA3_`: seven LAMBDAs, with Keccak lanes as pairs of 32-bit halves.
- `ASCII_`: a shared helper used by the SHA formulas.

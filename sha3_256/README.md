# SHA3-256

Pure-LAMBDA implementation of SHA3-256 ([FIPS 202](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.202.pdf)) for Excel.

- Permutation: Keccak-f[1600] (5×5 grid of 64-bit lanes, 24 rounds)
- Rate: 1088 bits (136 bytes per absorption block)
- Capacity: 512 bits
- Domain-separation suffix: `0x06`
- Output: 256 bits / 64 lowercase hex characters

## Install

See the [top-level install section](../README.md#3c-install-sha3-256). Seven LAMBDAs, install order matters (helpers before main).

## Files

| File | Defined name | Role |
|---|---|---|
| [`sha3k.lambda.txt`](sha3k.lambda.txt)   | `SHA3K_`  | 24 round constants (48 32-bit values, lo/hi pairs) |
| [`sha3t.lambda.txt`](sha3t.lambda.txt)   | `SHA3T_`  | θ (theta) sub-permutation |
| [`sha3rp.lambda.txt`](sha3rp.lambda.txt) | `SHA3RP_` | Combined ρ + π (rho + pi) sub-permutation |
| [`sha3ci.lambda.txt`](sha3ci.lambda.txt) | `SHA3CI_` | Combined χ + ι (chi + iota) sub-permutation; calls `SHA3K_` |
| [`sha3f.lambda.txt`](sha3f.lambda.txt)   | `SHA3F_`  | Keccak-f[1600]: 24-round REDUCE applying T → RP → CI |
| [`sha3h.lambda.txt`](sha3h.lambda.txt)   | `SHA3H_`  | Squeeze first 4 lanes (256 bits) to lowercase hex |
| [`sha3.lambda.txt`](sha3.lambda.txt)     | `SHA3_`   | Public entry point: pad, absorb, squeeze |
| [`sha3.lambda.formatted.txt`](sha3.lambda.formatted.txt) | — | Pretty-printed `SHA3_` body for reading |
| [`test-vectors.md`](test-vectors.md)     | — | Eight test vectors, all verified |

## Why seven LAMBDAs

Excel caps each defined name's "Refers to" field at 2084 characters. Keccak-f's five sub-permutations plus a 64-bit rotation primitive (expressed over pairs of 32-bit halves, since Excel's `BIT*` family is 32-bit) plus the squeeze and padding logic don't fit in one defined name. The split follows FIPS 202's vocabulary so the structure stays auditable.

## State representation

A 1×50 row array holding 25 lanes as interleaved (lo, hi) 32-bit pairs:

```
[L0_lo, L0_hi, L1_lo, L1_hi, ..., L24_lo, L24_hi]
```

Lane (x, y) lives at flat index `k = x + 5y`, with (lo, hi) at Excel 1-based positions `2k+1`, `2k+2`. Every sub-permutation reads and returns this same shape, which lets `SHA3F_` chain them with a plain `REDUCE`.

## Defined-name notes

- Public entry is `SHA3_`. The bare `SHA3` name is fine (only 4 letters with no digits, doesn't match the cell-reference pattern), but the trailing underscore keeps it consistent with `MD5_` and `SHA256_` and reserves `SHA3_512_` etc. as the natural extension if more SHA-3 variants are added.
- Several internal LET names had to be renamed away from the cell-reference pattern: `hi2`/`lo2`/`k1`/`k2`/`b1`/`b2`/`b3` are all valid cell addresses (HI2, LO2, K1, K2, B1, B2, B3) and silently rejected. The published bodies use `hiP`/`loP`/`kAlpha`/`kBeta`/`bA`/`bB`/`bC`/`bD` instead. Don't "simplify" by reverting.

# SHA3-256

Pure-LAMBDA implementation of SHA3-256 ([FIPS 202](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.202.pdf)) for Excel, as one defined name, `SHA3_`.

- Permutation: Keccak-f[1600] (25 lanes of 64 bits, 24 rounds)
- Rate: 1088 bits (136 bytes per absorbed block)
- Capacity: 512 bits
- Domain-separation suffix: `0x06`
- Output: 256 bits, as 64 lowercase hex characters

## Install

Make one Name Manager entry. Set **Name** to `SHA3_` and paste the single line of [`sha3.lambda.txt`](sha3.lambda.txt) (953 chars) into **Refers to**. See the [top-level install section](../README.md#3-install).

The trailing underscore is required. `SHA3` is a cell reference (column SHA, row 3), so Excel rejects it as a name (see [Quirk 1](../README.md#quirk-1-names-that-look-like-cell-references-are-rejected)).

The directory contains:
- [`sha3.lambda.txt`](sha3.lambda.txt): the formula to paste.
- [`sha3.lambda.formatted.txt`](sha3.lambda.formatted.txt): the same formula with line breaks, for reading next to this page.
- [`test-vectors.md`](test-vectors.md): the test vectors, with a column showing which ones were run in Excel.

## How it works

### The state is a 25×64 matrix of bits

The Keccak state is 25 lanes of 64 bits. The formula holds it as a 25×64 array of 0s and 1s:
- row = lane index k = x + 5y (0 to 24)
- column = bit index z (0 to 63), least significant bit first

Bitwise operations become arithmetic on 0/1 values:

| Operation | Formula |
|---|---|
| a XOR b | `MOD(a+b,2)` |
| a AND b | `a*b` |
| NOT a | `1-a` |

Excel's `BIT*` functions only accept values below 2^48. The previous version therefore carried each 64-bit lane as a pair of 32-bit halves, with a branching 64-bit rotate built from both. Working on bits removes that workaround completely: rotating a lane is just reading its columns in a different order, and every step of the round works on the whole state at once.

### Index arrays

These are computed once, outside the rounds. Index arrays used with `INDEX` are 1-based, so several end in `+1`.

| Name | Formula | Shape | Meaning |
|---|---|---|---|
| `k` | `SEQUENCE(25,,0)` | 25×1 | lane index |
| `x` | `MOD(k,5)` | 25×1 | the lane's x coordinate |
| `z` | `SEQUENCE(1,64,0)` | 1×64 | bit index |
| `cm` | `--(MOD(TOROW(k),5)=SEQUENCE(5,,0))` | 5×25 | selector: row x is 1 for the 5 lanes with that x |
| `pz` | `MOD(x+3*INT(k/5),5)+5*x+1` | 25×1 | π: the source lane for each destination lane |
| `rt` | `MOD(z-{0;44;43;…;2},64)+1` | 25×64 | ρ: the source bit for each destination bit |
| `ca` | `k-x+MOD(x+1,5)+1` | 25×1 | χ: the lane (x+1, y) |
| `cb` | `k-x+MOD(x+2,5)+1` | 25×1 | χ: the lane (x+2, y) |

The 25 constants in `rt` are the ρ rotation offsets, listed in destination-lane order. The offset for destination lane k is the one for the lane that π moves into position k.

### One round: `F`

`F` is a `REDUCE` over the 24 round codes. Each step applies θ, ρ, π, χ and ι to the accumulator `A`.

- **θ.** `D = MMULT(cm, A)` sums each of the 5 columns of lanes bit by bit, giving a 5×64 array of column sums C[x][z]. Parity is only needed mod 2, and that reduction happens once, at the end of the step:

  ```
  E = MOD(A + INDEX(D, MOD(x+4,5)+1, z+1) + INDEX(D, MOD(x+1,5)+1, MOD(z-1,64)+1), 2)
  ```

  This adds C[x−1][z] + C[x+1][z−1] to every bit. The second term is column x+1 rotated by one bit.
- **ρ and π.** `B = INDEX(E, pz, rt)` is one 2-D gather. A 25×1 row-index array combined with a 25×64 column-index array returns a 25×64 result. Destination lane k reads source lane `MOD(x+3y,5)+5x`, at bit `MOD(z−r,64)`, which rotates that lane left by r.
- **χ.** `B + (1-INDEX(B,ca,z+1))*INDEX(B,cb,z+1)` is b ⊕ (¬b[x+1] ∧ b[x+2]) in arithmetic form. The final `MOD(…,2)` covers it together with ι.
- **ι.** The round constant is XORed into lane 0. Every Keccak round constant has set bits only at positions 2^j−1 (0, 1, 3, 7, 15, 31, 63). Each constant is therefore stored as a 7-bit code in which bit j is bit 2^j−1 of the constant. For example:
  - round 0's constant 0x1 has code 1;
  - round 1's constant 0x8082 has bits 1, 7 and 15 set (j = 1, 3, 4), so its code is 2+8+16 = 26.

  The term added to the state is:

  ```
  (k=0) * (BITAND(z,z+1)=0) * MOD(INT(qc/(z+1)),2)
  ```

  `BITAND(z,z+1)=0` holds exactly when z+1 is a power of two, that is, when z = 2^j−1. Then z+1 = 2^j, and `MOD(INT(qc/2^j),2)` is bit j of the code.

### Padding and absorbing

`p = 136*INT(n/136+1)` is the smallest multiple of 136 bytes that leaves at least one padding byte. The padded bytes are:

```
by = IF(i<n,u,0) + (i=n)*6 + (i=p-1)*128
```

This is the input, then the `0x06` domain suffix at position n, then the final `0x80` at the last byte of the block. When n = p−1 (n = 135, 271, …) both terms land on the same byte and add up to `0x86`. That is the collapsed pad10\*1 case, and it needs no special branch.

The state starts as `k*z*0` (all zeros). Each block `bk` is absorbed into the first 17 lanes (17 × 8 bytes = the 136-byte rate). Bit z of lane k is bit `MOD(z,8)` of byte `136*bk + 8*k + INT(z/8)`, because lanes are little-endian:

```
F(MOD(st + IF(k<17, MOD(INT(INDEX(by,136*bk+8*k+INT(z/8)+1)/2^MOD(z,8)),2), 0), 2))
```

The lanes from 17 up (the capacity) are left unchanged.

### Squeeze

SHA3-256 outputs the first 256 bits of the state, which is lanes 0 to 3. The output is built in four steps:

1. `TOCOL(TAKE(S,4))` lists those lanes' bits in order: lane 0 bits 0–63, then lane 1, and so on.
2. `WRAPROWS(…,8)` groups the bits eight to a row, one byte per row with the least significant bit first.
3. `MMULT(…,2^SEQUENCE(8,,0))` multiplies each row by {1;2;4;…;128}, which gives the byte value.
4. `DEC2HEX(…,2)`, `CONCAT` and `LOWER` produce the hex string.

### ASCII check

This works as in the other two formulas (see [Common building blocks](../README.md#common-building-blocks)). `u` holds the `UNICODE` code of each character, and 999 past the end of the input. If any input position has a code above 127, the result is `Error: non-ASCII input detected`.

## Test vectors

See [`test-vectors.md`](test-vectors.md). Rows near the 135/136-char rate edge cover the `0x86` collapsed padding and the first two-block input. Rows up to the 32767-char maximum (241 blocks) cover multi-block absorption.

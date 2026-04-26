# SHA3-256 test vectors

Standard short vectors plus three padding/multi-block edge cases and the FIPS 202 example. All eight must match.

| Input | Expected output |
|---|---|
| (empty string) | `a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a` |
| `a` | `80084bf2fba02475726feb2cab2d8215eab14bc6bdd8bef0207448096cceeae5` |
| `abc` | `3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532` |
| `The quick brown fox jumps over the lazy dog` | `69070dda01975c8c120c3aada1b282394e7f032fa9cf32f4cb2259a0897dfc04` |
| `a` × 55 (rate-block edge) | `e9596fb33eecf04ed3b8aff96d24bd9b1d2cdcd9f3afd8d859a5b1c1aab8e8e1` |
| `a` × 135 (forces collapsed `0x86` padding case) | `8094bb53c44cfb1e67b7c30447f9a1c33696d2463ecc1d9c92538913392843c9` |
| `a` × 136 (forces a second absorption block) | `3fc5559f14db8e453a0a3091edbd2bc25e11528d81c66fa570a4efdcc2695ee1` |
| `abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq` (FIPS 202) | `41c0dba2a9d6240849100376a8235e2c82e1b9998a999e21db32dd97496d3376` |

The last three vectors are the interesting ones for regression testing:

- `a`×135 puts the suffix byte (`0x06`) and the final-byte marker (`0x80`) on the same byte position, which must collapse to `0x86`. The padding lambda special-cases `idx = mlen = plen - 1`.
- `a`×136 wraps to a second block, exercising the outer `REDUCE` over absorption blocks.
- The FIPS 202 example is the canonical 56-byte cross-implementation check.

## Reproducing in Excel

After installing the seven SHA-3 LAMBDAs per the [top-level README](../README.md#3c-install-sha3-256) (`SHA3K_`, `SHA3T_`, `SHA3RP_`, `SHA3CI_`, `SHA3F_`, `SHA3H_`, `SHA3_`), drop the inputs into column A and `=SHA3_(A1)` into column B. Output column should match the table above exactly.

For the repeated-character vectors, generate the input with `=REPT("a", 135)` etc.

## Known limitations

Same as MD5 and SHA-256: ASCII-safe only. Inputs containing characters outside the ASCII range will hash via Excel's `CODE` codepoints rather than UTF-8 bytes, so results will not match a reference SHA3-256 over the UTF-8 encoding of the same string. Encode upstream if you need byte-level compatibility.

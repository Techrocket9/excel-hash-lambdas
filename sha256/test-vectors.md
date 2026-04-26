# SHA-256 test vectors

Standard short vectors plus the FIPS 180-2 two-block vector. All seven must match.

| Input | Expected output |
|---|---|
| (empty string) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `a` | `ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb` |
| `abc` | `ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad` |
| `message digest` | `f7846f55cf23e14eebeab5b4e1550cad5b509e3348fbc4efa3a1413d393cb650` |
| `abcdefghijklmnopqrstuvwxyz` | `71c480df93d6ae2f1efad1447c66c9525e316218cf51fc8d9ed832f2daf18b73` |
| `The quick brown fox jumps over the lazy dog` | `d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592` |
| `abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq` | `248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1` |

The last vector is the FIPS 180-2 two-block test — at 56 characters, the padding bumps the message into a second 512-bit block, so it exercises the cross-block state carry through the outer `REDUCE`. Useful as a regression check if you fork.

## Reproducing in Excel

After installing the five SHA-256 LAMBDAs per the [README](../README.md#3b-install-sha-256) (`SHA256K_`, `SHA256I_`, `SHA256H_`, `SHA256A_`, `SHA256_`) plus the shared `ASCII_` helper, drop the inputs into column A and `=SHA256_(A1)` into column B. Output column should match the table above exactly.

## Non-ASCII rejection

The seven ASCII vectors above are unchanged. In addition, any input containing a character with codepoint ≥ 128 is rejected via the shared `ASCII_` helper (see [top-level README](../README.md#input-handling)) and the formula returns the literal error string instead of a hash.

| Input | Expected output |
|---|---|
| `café` | `Error: non-ASCII input detected` |
| `日本` | `Error: non-ASCII input detected` |
| `hello 🦄` | `Error: non-ASCII input detected` |
| `=CHAR(128)` | `Error: non-ASCII input detected` |
| `=CHAR(127)` | `620bfdaa346b088fb49998d92f19a7eaf6bfc2fb0aee015753966da1028cb731` (DEL — valid ASCII, real digest) |

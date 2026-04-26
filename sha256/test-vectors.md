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

After installing the `SHA256` named LAMBDA per the [README](../README.md#3-install), drop the inputs into column A and `=SHA256(A1)` into column B. Output column should match the table above exactly.

## Known limitations

Same as MD5: ASCII-safe only. Inputs containing characters outside the ASCII range will hash via Excel's `CODE` codepoints rather than UTF-8 bytes, so results will not match `sha256sum` on the UTF-8 encoding of the same string. Encode upstream if you need byte-level compatibility.

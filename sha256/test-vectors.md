# SHA-256 test vectors

Every expected digest below was computed with Python `hashlib` over the UTF-8 bytes of the input; [`tests/verify_vectors.py`](../tests/verify_vectors.py) recomputes all of them. An input that starts with `=` is the Excel formula that builds the string: enter it in a cell as written and hash that cell.

The **Excel-verified** column records what has actually been run through `SHA256_`:

- **yes**: run in Excel for Mac 16.113 (Microsoft 365) and the result matched the digest shown.
- **no**: hashlib-computed, not run in Excel.

Windows Excel has not been tested.

SHA-256 pads exactly like MD5 (64-byte blocks, at least 9 bytes of padding), except that the length is big-endian, so an *n*-char input takes `INT(n/64 + 9/8)` blocks: 55 chars is the largest 1-block input and 56 the smallest 2-block one.

## ASCII inputs

The inputs are standard short strings, the FIPS 180 two-block message, control characters, block-boundary lengths, a run of multi-block lengths, and the 32767-char maximum.

| Input | Expected output | Excel-verified | Notes |
|---|---|---|---|
| (empty string) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | yes |  |
| `a` | `ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb` | yes |  |
| `abc` | `ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad` | yes |  |
| `message digest` | `f7846f55cf23e14eebeab5b4e1550cad5b509e3348fbc4efa3a1413d393cb650` | yes |  |
| `abcdefghijklmnopqrstuvwxyz` | `71c480df93d6ae2f1efad1447c66c9525e316218cf51fc8d9ed832f2daf18b73` | no |  |
| `The quick brown fox jumps over the lazy dog` | `d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592` | yes |  |
| `abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq` | `248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1` | yes | FIPS 180 two-block message (56 chars: 2 blocks) |
| `=CHAR(127)` | `620bfdaa346b088fb49998d92f19a7eaf6bfc2fb0aee015753966da1028cb731` | yes | DEL, the highest ASCII code point |
| `=CHAR(9)&"tab"&CHAR(10)&"lf"` | `50facdbf3ce1286a1e5b9d0fc24ff5adc86d3a06c965aba0e785ede1a8a0f2bd` | yes | tab and line-feed control characters |
| `=REPT("a",55)` | `9f4390f8d30c2dd92ec9f095b65e2b9ae9b0a925a5258e241c9f1e910f734318` | yes | largest 1-block input |
| `=REPT("a",56)` | `b35439a4ac6f0948b6d6f9e3c6af0f5f590ce20f1bde7090ef7970686ec6738a` | yes | smallest 2-block input |
| `=REPT("a",64)` | `ffe054fe7ae0cb6dc65c3af9b61d5209f439851db43d0ba5997337df154668eb` | yes | 2 blocks |
| `=REPT("a",119)` | `31eba51c313a5c08226adf18d4a359cfdfd8d2e816b13f4af952f7ea6584dcfb` | no | largest 2-block input |
| `=REPT("a",120)` | `2f3d335432c70b580af0e8e1b3674a7c020d683aa5f73aaaedfdc55af904c21c` | no | smallest 3-block input |
| `=REPT("a",135)` | `dfa58dfd72f3c7080d0249a7758fd3636872f63fa24b18473ed36f031e248347` | yes | 3 blocks; SHA3-256 rate edge (not significant here) |
| `=REPT("a",136)` | `6f0e44b9ce4ea61d52a3479c10f60ef916937f799f11964b7f1c7771063905c4` | yes | 3 blocks; SHA3-256 rate edge (not significant here) |
| `=REPT("a",137)` | `b6dc2da678c065ebdce374ebe1842728277203ee1a9a29832f058cf013d5ad85` | no | 3 blocks; SHA3-256 rate edge (not significant here) |
| `=REPT("a",300)` | `9835fa6bf4e20a9b9ea812506302e98982721a6cf8d2cae67af57129bf21ae90` | no | 5 blocks |
| `=REPT("x",300)` | `0d4e2ca9e9cbced7a7a5380eb29e1a3783b9b6d0db72de36a1051038e1c1fbc7` | yes | 5 blocks |
| `=LEFT(REPT("abcdefghij",1000),1000)` | `c49bba59ccc72847b869b364a909a52606e91412eccdc570032df23b181fdfa9` | yes | 16 blocks |
| `=LEFT(REPT("abcdefghij",1000),1100)` | `84c8a808102f307bfc557d05a99b2131b6a3132c8f56b4345255e6ec10089470` | yes | 18 blocks |
| `=LEFT(REPT("abcdefghij",1000),1500)` | `2ffe759219dc3bd1b86b9197a87df682ee7de26248b274fd660336e95ead4ea8` | yes | 24 blocks |
| `=LEFT(REPT("abcdefghij",1000),2000)` | `ee07216f641886936f16a9610a03eb47c66854714c597de9d9931b196a6e9b8b` | yes | 32 blocks |
| `=LEFT(REPT("abcdefghij",1000),2500)` | `702e0e881f522ccd1f18d1693d8d9806c62d3ea19e8905cdc6447c9c37795685` | yes | 40 blocks |
| `=LEFT(REPT("abcdefghij",1000),3000)` | `7c27f87fc7b880b3bca117ed2ac631c33752a3a7f5a2230aba17456909c60267` | yes | 48 blocks |
| `=LEFT(REPT("abcdefghij",1000),4000)` | `f83864b7c78d7cb7618d8b8476c189f7b18222928edbd730e4ce60ae09bd146d` | yes | 63 blocks |
| `=LEFT(REPT("abcdefghij",1000),5000)` | `122a7d97ab2b2e492a2b4a0b88aa161f0429ec370d93eb60fd082f9fa9649d5c` | yes | 79 blocks |
| `=REPT("abcdefghij",3276)&"abcdefg"` | `3962cfc380ddc2fa1324adb24b6fef994ba037d60d8d53fc77233f49e9a02327` | yes | 32767 chars, Excel's maximum string length; 513 blocks |

## Non-ASCII rejection

Any input containing a character above U+007F returns the literal string `Error: non-ASCII input detected` instead of a digest (see [Input handling](../README.md#4-input-handling)).

| Input | Expected output | Excel-verified | Notes |
|---|---|---|---|
| `café` | `Error: non-ASCII input detected` | yes | é is U+00E9 |
| `日本` | `Error: non-ASCII input detected` | no |  |
| `hello 🦄` | `Error: non-ASCII input detected` | yes | U+1F984, a surrogate pair in Excel's UTF-16 text |
| `=UNICHAR(128512)` | `Error: non-ASCII input detected` | yes | U+1F600 |
| `=CHAR(128)` | `Error: non-ASCII input detected` | no | CHAR above 127 is code-page dependent, but never ASCII |

## Reproducing in Excel

Install `SHA256_` (see [Install](../README.md#3-install)), put the inputs in `A2:A34` (enter `=""` for the empty string), and put `=SHA256_(A2)` in `B2` and fill down. To hash the whole column in one cell, use `=MAP(A2:A34, SHA256_)`; passing the range straight to `SHA256_` returns `#VALUE!`.

The 32767-char row took about 0.7 s in Excel for Mac; rows of 1000 chars or fewer are effectively instant.

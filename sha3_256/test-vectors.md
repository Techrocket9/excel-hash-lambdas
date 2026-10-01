# SHA3-256 test vectors

Every expected digest below was computed with Python `hashlib` over the UTF-8 bytes of the input; [`tests/verify_vectors.py`](../tests/verify_vectors.py) recomputes all of them. An input that starts with `=` is the Excel formula that builds the string: enter it in a cell as written and hash that cell.

The **Excel-verified** column records what has actually been run through `SHA3_`:

- **yes**: run in Excel for Mac 16.113 (Microsoft 365) and the result matched the digest shown.
- **no**: hashlib-computed, not run in Excel.

Windows Excel has not been tested.

SHA3-256 absorbs 136 bytes per block (the rate) and always adds at least one padding byte, so an *n*-char input takes `INT(n/136 + 1)` blocks: 135 chars is the largest 1-block input (the `0x06` suffix and the final `0x80` land on the same byte, `0x86`) and 136 the smallest 2-block one. The 55/56/119/120 rows are block edges for MD5 and SHA-256 only; they are kept so the three files share one input list.

## ASCII inputs

The inputs are standard short strings, the FIPS 180 two-block message, control characters, block-boundary lengths, a run of multi-block lengths, and the 32767-char maximum.

| Input | Expected output | Excel-verified | Notes |
|---|---|---|---|
| (empty string) | `a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a` | yes |  |
| `a` | `80084bf2fba02475726feb2cab2d8215eab14bc6bdd8bfb2c8151257032ecd8b` | yes |  |
| `abc` | `3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532` | yes |  |
| `message digest` | `edcdb2069366e75243860c18c3a11465eca34bce6143d30c8665cefcfd32bffd` | yes |  |
| `abcdefghijklmnopqrstuvwxyz` | `7cab2dc765e21b241dbc1c255ce620b29f527c6d5e7f5f843e56288f0d707521` | no |  |
| `The quick brown fox jumps over the lazy dog` | `69070dda01975c8c120c3aada1b282394e7f032fa9cf32f4cb2259a0897dfc04` | yes |  |
| `abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq` | `41c0dba2a9d6240849100376a8235e2c82e1b9998a999e21db32dd97496d3376` | yes | FIPS 180 two-block message; 1 block here |
| `=CHAR(127)` | `aac68691d102829ac973f5b44c26165aa4e29cd498aff642a08944645d6ca5bd` | yes | DEL, the highest ASCII code point |
| `=CHAR(9)&"tab"&CHAR(10)&"lf"` | `db5d107fa196de214e113f1d4687be6ff12822141020ecaa6bb29f8298c8fe88` | yes | tab and line-feed control characters |
| `=REPT("a",55)` | `78c2a04624b9328ae0e40cb8cdd29980f6ff55abf2dca68e3412d09eed4b9d03` | yes | MD5/SHA-256 block edge (not significant for SHA3) |
| `=REPT("a",56)` | `f6fe8de5c8f5014786f07e9f7b08130f920dd55e587d47021686b26cf2323deb` | yes | MD5/SHA-256 block edge (not significant for SHA3) |
| `=REPT("a",64)` | `043d104b5480439c7acff8831ee195183928d9b7f8fcb0c655a086a87923ffee` | yes | 1 block |
| `=REPT("a",119)` | `b3601ba4f5087e26845f13b42d676fd89fb19af6076523cfee74f2a49a295f66` | no | MD5/SHA-256 block edge (not significant for SHA3) |
| `=REPT("a",120)` | `1f81a6276d67f626c68b8c5bb94ce2b3c2145c7093517a8eb7135d0a67863992` | no | MD5/SHA-256 block edge (not significant for SHA3) |
| `=REPT("a",135)` | `8094bb53c44cfb1e67b7c30447f9a1c33696d2463ecc1d9c92538913392843c9` | yes | largest 1-block input: the 0x06 suffix and final 0x80 share one byte (0x86) |
| `=REPT("a",136)` | `3fc5559f14db8e453a0a3091edbd2bc25e11528d81c66fa570a4efdcc2695ee1` | yes | smallest 2-block input |
| `=REPT("a",137)` | `f8d6846cedd2ccfadf15c5879ef95af724d799eed7391fb1c91f95344e738614` | no | 2 blocks |
| `=REPT("a",300)` | `8a5720b2ca0cae7b89ad399c5daab22c29f5c72bcf30ab81e807d9bda95b4580` | no | 3 blocks |
| `=REPT("x",300)` | `34ed36d4d71d1a9a582cce5a006d6102d173fd867a27be7b2fe5d854587ddba2` | yes | 3 blocks |
| `=LEFT(REPT("abcdefghij",1000),1000)` | `abaa4ae19e2acfaa0f4cd8674a4ab98e914a455ee3273c88996f1eeb3e0f0098` | yes | 8 blocks |
| `=LEFT(REPT("abcdefghij",1000),1100)` | `3043a203ed3417ce65c07d803f40c3a879b1e35964cf557d6c3bcbf8f6eb81e2` | yes | 9 blocks |
| `=LEFT(REPT("abcdefghij",1000),1500)` | `0cc0411282aa6e9dfb8b7be4885a292a607b28b5b74e8cc934f24ea80659f370` | yes | 12 blocks |
| `=LEFT(REPT("abcdefghij",1000),2000)` | `81db2df54e2f30ed268a44d44963145579cfec9325e4a30e2e8db71da5017c89` | yes | 15 blocks |
| `=LEFT(REPT("abcdefghij",1000),2500)` | `0b167a7348f9c8daaa87cad7531e58eec3a3b5868a69355e193bf2a9763a4cbf` | yes | 19 blocks |
| `=LEFT(REPT("abcdefghij",1000),3000)` | `c363ebb96f259dcbda701ded15a16bcecd8d2aaccdec17baa54f1bfca510dec9` | yes | 23 blocks |
| `=LEFT(REPT("abcdefghij",1000),4000)` | `63c52519a6f99748f11a99aa1f9037a83d21c210eb94a3f8a3a85b5a7ff3976a` | yes | 30 blocks |
| `=LEFT(REPT("abcdefghij",1000),5000)` | `2f823e6318973728e69b22fbc22ed980f94f7f426e556a85056d90ddeb21183f` | yes | 37 blocks |
| `=REPT("abcdefghij",3276)&"abcdefg"` | `305187db8aa839fa705f71f5347dc5750791d5c6948d4b9e9238f2d8f2eba20a` | yes | 32767 chars, Excel's maximum string length; 241 blocks |

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

Install `SHA3_` (see [Install](../README.md#3-install)), put the inputs in `A2:A34` (enter `=""` for the empty string), and put `=SHA3_(A2)` in `B2` and fill down. To hash the whole column in one cell, use `=MAP(A2:A34, SHA3_)`; passing the range straight to `SHA3_` returns `#VALUE!`.

The 32767-char row took about 4.7 s in Excel for Mac; rows of 1000 chars or fewer are effectively instant.

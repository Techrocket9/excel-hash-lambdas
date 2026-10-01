# MD5 test vectors

Every expected digest below was computed with Python `hashlib` over the UTF-8 bytes of the input; [`tests/verify_vectors.py`](../tests/verify_vectors.py) recomputes all of them. An input that starts with `=` is the Excel formula that builds the string: enter it in a cell as written and hash that cell.

The **Excel-verified** column records what has actually been run through `MD5_`:

- **yes**: run in Excel for Mac 16.113 (Microsoft 365) and the result matched the digest shown.
- **no**: hashlib-computed, not run in Excel.

Windows Excel has not been tested.

MD5 pads to a multiple of 64 bytes and needs at least 9 bytes of padding (the `0x80` marker plus an 8-byte length), so an *n*-char input takes `INT(n/64 + 9/8)` blocks: 55 chars is the largest 1-block input and 56 the smallest 2-block one.

## ASCII inputs

The inputs are [RFC 1321](https://www.rfc-editor.org/rfc/rfc1321) test-suite strings, control characters, block-boundary lengths, a run of multi-block lengths, and the 32767-char maximum.

| Input | Expected output | Excel-verified | Notes |
|---|---|---|---|
| (empty string) | `d41d8cd98f00b204e9800998ecf8427e` | yes |  |
| `a` | `0cc175b9c0f1b6a831c399e269772661` | yes |  |
| `abc` | `900150983cd24fb0d6963f7d28e17f72` | yes |  |
| `message digest` | `f96b697d7cb7938d525a2f31aaf161d0` | yes |  |
| `abcdefghijklmnopqrstuvwxyz` | `c3fcd3d76192e4007dfb496cca67e13b` | no |  |
| `The quick brown fox jumps over the lazy dog` | `9e107d9d372bb6826bd81d3542a419d6` | yes |  |
| `abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq` | `8215ef0796a20bcaaae116d3876c664a` | yes | FIPS 180 two-block message (56 chars: 2 blocks) |
| `=CHAR(127)` | `83acb6e67e50e31db6ed341dd2de1595` | yes | DEL, the highest ASCII code point |
| `=CHAR(9)&"tab"&CHAR(10)&"lf"` | `39f6a0104fa4ffeb6134149bb76774a1` | yes | tab and line-feed control characters |
| `=REPT("a",55)` | `ef1772b6dff9a122358552954ad0df65` | yes | largest 1-block input |
| `=REPT("a",56)` | `3b0c8ac703f828b04c6c197006d17218` | yes | smallest 2-block input |
| `=REPT("a",64)` | `014842d480b571495a4a0363793f7367` | yes | 2 blocks |
| `=REPT("a",119)` | `8a7bd0732ed6a28ce75f6dabc90e1613` | no | largest 2-block input |
| `=REPT("a",120)` | `5f61c0ccad4cac44c75ff505e1f1e537` | no | smallest 3-block input |
| `=REPT("a",135)` | `247dc7ffc545e4dda64ae12def481c4e` | yes | 3 blocks; SHA3-256 rate edge (not significant here) |
| `=REPT("a",136)` | `2dfd4def392ee9563241b7db7eb7c346` | yes | 3 blocks; SHA3-256 rate edge (not significant here) |
| `=REPT("a",137)` | `d11a18a4743a1a0a699d1704efb74a0d` | no | 3 blocks; SHA3-256 rate edge (not significant here) |
| `=REPT("a",300)` | `4e5475d125a33c6190718e75adc1b704` | no | 5 blocks |
| `=REPT("x",300)` | `8a4876ea55d998a5d91ed59db796af28` | yes | 5 blocks |
| `=LEFT(REPT("abcdefghij",1000),1000)` | `33ef314bbf752a16bcc48256b4b89e8e` | yes | 16 blocks |
| `=LEFT(REPT("abcdefghij",1000),1100)` | `1aaaca5d0e5ea739eb6ac374b5ee76f2` | yes | 18 blocks |
| `=LEFT(REPT("abcdefghij",1000),1500)` | `f457c28bd66059c73d161575dd7af630` | yes | 24 blocks |
| `=LEFT(REPT("abcdefghij",1000),2000)` | `f5fb626d1767fc9ce5789ae48e001f7a` | yes | 32 blocks |
| `=LEFT(REPT("abcdefghij",1000),2500)` | `585309c32353887d99170bf260bf9a8b` | yes | 40 blocks |
| `=LEFT(REPT("abcdefghij",1000),3000)` | `90c2537d7b2c9ff9cc070a380d6977a5` | yes | 48 blocks |
| `=LEFT(REPT("abcdefghij",1000),4000)` | `5f0ab94ad076c40b7cd830e77e96e8cc` | yes | 63 blocks |
| `=LEFT(REPT("abcdefghij",1000),5000)` | `5623f56f63faf7a90c89379c0129d05d` | yes | 79 blocks |
| `=REPT("abcdefghij",3276)&"abcdefg"` | `32df7f9ae51e624a8c7e924c0719df51` | yes | 32767 chars, Excel's maximum string length; 513 blocks |

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

Install `MD5_` (see [Install](../README.md#3-install)), put the inputs in `A2:A34` (enter `=""` for the empty string), and put `=MD5_(A2)` in `B2` and fill down. To hash the whole column in one cell, use `=MAP(A2:A34, MD5_)`; passing the range straight to `MD5_` returns `#VALUE!`.

The 32767-char row took about 0.2 s in Excel for Mac; rows of 1000 chars or fewer are effectively instant.

#!/usr/bin/env python3
"""NumPy emulators that follow md5.lambda.txt, sha256.lambda.txt and sha3.lambda.txt.

Each emulator mirrors its formula's LET bindings one for one (same names, same
intermediate arrays, Excel's 1-based INDEX written as explicit -1 offsets), so
a mistake in the algorithm design shows up here even without Excel. The
script asserts that:

- every emulator matches hashlib on random printable ASCII strings of every
  length 0-300, plus 1000, 5000 and 32767 chars;
- non-ASCII input gives the error string;
- the MD5 K table INT(2^32*|SIN(i)|) equals the RFC 1321 table;
- the SHA-256 K and IV computed from primes equal FIPS 180-4, and every
  value sits far enough from an integer that double precision cannot round
  it the wrong way;
- the SHA3 rho offsets and 7-bit round codes reproduce FIPS 202.

Exits non-zero on the first failure.
"""
import hashlib
import math
import random
import sys
from fractions import Fraction

import numpy as np

ERROR = "Error: non-ASCII input detected"
M = 2**32
BIT_LIMIT = 2**48  # Excel's BITAND/BITOR/BITXOR accept 0 <= x < 2^48


def bit(v):
    """Assert a value is a legal argument for Excel's BIT* functions."""
    assert v == int(v) and 0 <= v < BIT_LIMIT, v
    return int(v)


def BITAND(a, b):
    return bit(a) & bit(b)


def BITOR(a, b):
    return bit(a) | bit(b)


def BITXOR(a, b):
    return bit(a) ^ bit(b)


def excel_text(tx):
    """LEN and UNICODE(MID(tx,i+1,1)) work on UTF-16 code units."""
    raw = tx.encode("utf-16-le")
    return [int.from_bytes(raw[j:j + 2], "little") for j in range(0, len(raw), 2)]


def common(tx, p_of_n):
    """n, p, i and u, shared by all three formulas."""
    units = excel_text(tx)
    n = len(units)
    p = p_of_n(n)
    i = np.arange(p)                                      # SEQUENCE(p,,0)
    u = np.array([units[j] if j < n else 999 for j in i])  # IFERROR(UNICODE(MID(tx,i+1,1)),999)
    non_ascii = bool(np.any((i < n) & (u > 127)))         # OR((i<n)*(u>127))
    return n, p, i, u, non_ascii


# ---------------------------------------------------------------- MD5_

MD5_IV = [1732584193, 4023233417, 2562383102, 271733878]
MD5_SHIFTS = [[7, 12, 17, 22], [5, 9, 14, 20], [4, 11, 16, 23], [6, 10, 15, 21]]


def md5_kc():
    return np.floor(M * np.abs(np.sin(np.arange(1, 65, dtype=float))))  # INT(M*ABS(SIN(SEQUENCE(64))))


def md5_formula(tx):
    n, p, i, u, non_ascii = common(tx, lambda n: 64 * math.floor(n / 64 + 9 / 8))
    kc = md5_kc().astype(np.int64)

    def ro(xv, kv):  # rotl: MOD(xv,2^(32-kv))*2^kv+INT(xv/2^(32-kv))
        return (xv % 2**(32 - kv)) * 2**kv + xv // 2**(32 - kv)

    # Nested IF so 256^(i-p+8) is only evaluated for the last 8 bytes (exponent 0..7).
    def pad(j):
        if j < n:
            return u[j]
        if j == n:
            return 128
        if j < p - 8:
            return 0
        return (8 * n // 256**(j - p + 8)) % 256
    byts = np.array([pad(int(j)) for j in i], dtype=np.int64)
    wd = byts.reshape(-1, 4) @ (256 ** np.arange(4, dtype=np.int64))  # MMULT(WRAPROWS(...,4),256^{0;1;2;3})

    def block(hs, bk):
        ws = wd[16 * bk:16 * bk + 16]                     # TAKE(DROP(wd,16*bk),16)

        def step(s, j):
            bb, cc, dd = s[1], s[2], s[3]
            qq = j // 16
            ff = [BITXOR(dd, BITAND(bb, BITXOR(cc, dd))),
                  BITXOR(cc, BITAND(dd, BITXOR(bb, cc))),
                  BITXOR(BITXOR(bb, cc), dd),
                  BITXOR(cc, BITOR(bb, M - 1 - dd))][qq]
            gg = [j, (5 * j + 1) % 16, (3 * j + 5) % 16, (7 * j) % 16][qq]
            rot = ro((s[0] + ff + int(kc[j]) + int(ws[gg])) % M, MD5_SHIFTS[qq][j % 4])
            chosen = [s[3], s[1], s[1], s[2]]             # CHOOSECOLS(s,4,2,2,3)
            return [(c + m * rot) % M for c, m in zip(chosen, [0, 1, 0, 0])]

        s = hs
        for j in range(64):
            s = step(s, j)
        return [(a + b) % M for a, b in zip(hs, s)]

    fh = MD5_IV
    for bk in range(p // 64):
        fh = block(fh, bk)
    if non_ascii:
        return ERROR
    # TOCOL(MOD(INT(fh/256^{0;1;2;3}),256),,TRUE): 4x4, read column by column = little-endian bytes.
    grid = [[(w // 256**r) % 256 for w in fh] for r in range(4)]
    return "".join(f"{grid[r][c]:02X}" for c in range(4) for r in range(4)).lower()


# ---------------------------------------------------------------- SHA256_

FIPS_K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]
FIPS_IV = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


def sha256_primes():
    q = np.arange(2, 312)                                 # SEQUENCE(310,,2)
    divides = (q[:, None] % q[None, :] == 0).astype(int)  # --(MOD(q,TOROW(q))=0)
    return q[divides @ np.ones(len(q), dtype=int) == 1]   # FILTER(q,MMULT(...,q^0)=1)


def sha256_constants():
    pr = sha256_primes().astype(float)
    kc = np.floor(np.mod(pr ** (1 / 3), 1) * M)           # INT(MOD(pr^(1/3),1)*M)
    iv = np.floor(np.mod(np.sqrt(pr[:8]), 1) * M)         # INT(MOD(SQRT(TAKE(pr,8)),1)*M)
    return kc.astype(np.int64), iv.astype(np.int64)


def sha256_formula(tx):
    n, p, i, u, non_ascii = common(tx, lambda n: 64 * math.floor(n / 64 + 9 / 8))
    kc, iv = sha256_constants()

    def ro(xv, kv):  # rotr: INT(xv/2^kv)+MOD(xv,2^kv)*2^(32-kv)
        return xv // 2**kv + (xv % 2**kv) * 2**(32 - kv)

    def sg(xv, av, bv, dv):
        return BITXOR(BITXOR(ro(xv, av), ro(xv, bv)), dv)

    # n <= 32767, so 8n < 2^24 and one MOD(INT(8n/256^(p-1-i)),256) gives the zero fill and the length.
    # For i >= n the exponent is at most 71, so 256^(p-1-i) fits in a double; the i < n positions,
    # where it can overflow, take the u branch.
    byts = np.array([u[j] if j < n else (j == n) * 128 + (8 * n // 256**(p - 1 - j)) % 256
                     for j in map(int, i)], dtype=np.int64)
    wd = byts.reshape(-1, 4) @ (256 ** np.arange(3, -1, -1, dtype=np.int64))  # 256^{3;2;1;0}

    def block(hs, bk):
        ws = [int(w) for w in wd[16 * bk:16 * bk + 16]]
        for j in range(17, 65):                           # REDUCE(..., SEQUENCE(48,,17), VSTACK)
            y, z = ws[j - 2 - 1], ws[j - 15 - 1]
            ws.append((sg(y, 17, 19, y // 1024) + ws[j - 7 - 1] + sg(z, 7, 18, z // 8) + ws[j - 16 - 1]) % M)
        s = hs
        for r_ in range(1, 65):
            a, b, e, f, g = s[0], s[1], s[4], s[5], s[6]
            tv = s[7] + sg(e, 6, 11, ro(e, 25)) + BITXOR(g, BITAND(e, BITXOR(f, g))) + int(kc[r_ - 1]) + ws[r_ - 1]
            stacked = [tv + sg(a, 2, 13, ro(a, 22)) + BITOR(BITAND(a, b), BITAND(s[2], BITOR(a, b)))] + s[:-1]
            s = [(v + tv * (col == 5)) % M for col, v in enumerate(stacked, start=1)]
        return [(a + b) % M for a, b in zip(hs, s)]

    fh = [int(v) for v in iv]
    for bk in range(p // 64):
        fh = block(fh, bk)
    if non_ascii:
        return ERROR
    return "".join(f"{w:08X}" for w in fh).lower()        # DEC2HEX(fh,8)


# ---------------------------------------------------------------- SHA3_

SHA3_RT = [0, 44, 43, 21, 14, 28, 20, 3, 45, 61, 1, 6, 25, 8, 18, 27, 36, 10, 15, 56, 62, 55, 39, 41, 2]
SHA3_CODES = [1, 26, 94, 112, 31, 33, 121, 85, 14, 12, 53, 38, 63, 79, 93, 83, 82, 72, 22, 102, 121, 88, 33, 116]


def sha3_formula(tx):
    n, p, i, u, non_ascii = common(tx, lambda n: 136 * math.floor(n / 136 + 1))
    by = np.where(i < n, u, 0) + (i == n) * 6 + (i == p - 1) * 128
    k = np.arange(25)[:, None]                            # SEQUENCE(25,,0)
    x = k % 5
    z = np.arange(64)[None, :]                            # SEQUENCE(1,64,0)
    cm = (k.T % 5 == np.arange(5)[:, None]).astype(int)   # --(MOD(TOROW(k),5)=SEQUENCE(5,,0)): 5x25
    pz = (x + 3 * (k // 5)) % 5 + 5 * x + 1
    rt = (z - np.array(SHA3_RT)[:, None]) % 64 + 1
    ca = k - x + (x + 1) % 5 + 1
    cb = k - x + (x + 2) % 5 + 1

    def F(st):
        A = st
        for qc in SHA3_CODES:
            D = cm @ A                                    # 5x64 column sums
            E = (A + D[(x + 4) % 5, z] + D[(x + 1) % 5, (z - 1) % 64]) % 2
            B = E[pz - 1, rt - 1]                         # INDEX(E,pz,rt): rho and pi in one gather
            iota = (k == 0) * ((z & (z + 1)) == 0) * ((qc // (z + 1)) % 2)
            A = (B + (1 - B[ca - 1, z]) * B[cb - 1, z] + iota) % 2
        return A

    S = k * z * 0
    for bk in range(p // 136):
        idx = np.minimum(136 * bk + 8 * k + z // 8, p - 1)  # clamp the k>=17 rows that IF discards
        lanes = np.where(k < 17, (by[idx] // 2 ** (z % 8)) % 2, 0)
        S = F((S + lanes) % 2)
    if non_ascii:
        return ERROR
    bits = S[:4].reshape(-1)                              # TOCOL(TAKE(S,4))
    out = bits.reshape(-1, 8) @ (2 ** np.arange(8))       # MMULT(WRAPROWS(...,8),2^SEQUENCE(8,,0))
    return "".join(f"{b:02X}" for b in out).lower()


# ---------------------------------------------------------------- constant checks

RFC1321_T = [
    0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee, 0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
    0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be, 0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
    0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa, 0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
    0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed, 0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
    0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c, 0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
    0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05, 0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
    0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039, 0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
    0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1, 0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391,
]
RFC1321_IV = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476]
KECCAK_RHO = [0, 1, 62, 28, 27, 36, 44, 6, 55, 20, 3, 10, 43, 25, 39, 41, 45, 15, 21, 8, 18, 2, 61, 56, 14]


def iroot_frac_margin(p, k):
    """Distance from frac(p^(1/k))*2^32 to the nearest integer, computed exactly."""
    extra = 128
    target = p << (k * (32 + extra))
    lo, hi = 0, 1
    while hi**k <= target:
        hi *= 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if mid**k <= target else (lo, mid)
    v = Fraction(lo, 1 << extra)
    f = v - int(v)
    return min(f, 1 - f)


def keccak_rc_lfsr(t):
    """FIPS 202 Algorithm 5."""
    if t % 255 == 0:
        return 1
    R = [1, 0, 0, 0, 0, 0, 0, 0]
    for _ in range(t % 255):
        R = [0] + R
        for b in (0, 4, 5, 6):
            R[b] ^= R[8]
        R = R[:8]
    return R[0]


def check_constants():
    kc = md5_kc().astype(np.int64)
    assert list(kc) == RFC1321_T, "MD5 K table differs from RFC 1321"
    assert MD5_IV == RFC1321_IV, "MD5 IV differs from RFC 1321"
    assert MD5_SHIFTS == [[7, 12, 17, 22], [5, 9, 14, 20], [4, 11, 16, 23], [6, 10, 15, 21]]
    print("ok   MD5 K = INT(2^32*|SIN(i)|) matches the RFC 1321 table; IV matches")

    pr = sha256_primes()
    assert len(pr) == 64 and pr[-1] == 311
    kc, iv = sha256_constants()
    assert list(kc) == FIPS_K, "SHA-256 K differs from FIPS 180-4"
    assert list(iv) == FIPS_IV, "SHA-256 IV differs from FIPS 180-4"
    margin = min([iroot_frac_margin(int(q), 3) for q in pr] + [iroot_frac_margin(int(q), 2) for q in pr[:8]])
    assert margin >= Fraction(55, 10000), float(margin)
    print(f"ok   SHA-256 K and IV from the first 64 primes match FIPS 180-4 "
          f"(closest value is {float(margin):.4f} from an integer)")

    rho, (X, Y) = [0] * 25, (1, 0)
    for t in range(24):
        rho[X + 5 * Y] = (t + 1) * (t + 2) // 2 % 64
        X, Y = Y, (2 * X + 3 * Y) % 5
    assert rho == KECCAK_RHO
    assert 32 not in KECCAK_RHO
    src = [(x + 3 * (kk // 5)) % 5 + 5 * x for kk in range(25) for x in [kk % 5]]  # pz - 1
    assert SHA3_RT == [rho[s] for s in src], "rt table is not rho gathered through pi"
    for rnd, qc in enumerate(SHA3_CODES):
        from_code = sum(((qc >> j) & 1) << (2**j - 1) for j in range(7))
        from_lfsr = sum(keccak_rc_lfsr(j + 7 * rnd) << (2**j - 1) for j in range(7))
        assert qc < 128 and from_code == from_lfsr, f"round {rnd}: code {qc}"
    print("ok   SHA3 rt table is the FIPS 202 rho offsets in pi order (none is 32); "
          "the 24 round codes expand to the FIPS 202 round constants")


# ---------------------------------------------------------------- digest checks

EMULATORS = [("MD5_", md5_formula, "md5"), ("SHA256_", sha256_formula, "sha256"), ("SHA3_", sha3_formula, "sha3_256")]


def main():
    check_constants()
    rng = random.Random(20260930)
    printable = [chr(c) for c in range(0x20, 0x7F)]
    inputs = [""] + ["".join(rng.choice(printable) for _ in range(n)) for n in list(range(1, 301)) + [1000, 5000, 32767]]
    inputs.append("".join(map(chr, range(1, 128))))  # every ASCII code point Excel's CHAR can produce
    for name, emu, alg in EMULATORS:
        for s in inputs:
            want = hashlib.new(alg, s.encode("ascii")).hexdigest()
            got = emu(s)
            assert got == want, f"{name} emulator: len {len(s)} gave {got}, hashlib {want}"
        for s in ["café", "hello \U0001F984", "日本", chr(128512), "abc" + chr(128)]:
            assert emu(s) == ERROR, f"{name} emulator accepted non-ASCII {s!r}"
        print(f"ok   {name} emulator matches hashlib.{alg} on {len(inputs)} ASCII inputs "
              f"(lengths 0-300, 1000, 5000, 32767) and rejects non-ASCII")
    return 0


if __name__ == "__main__":
    sys.exit(main())

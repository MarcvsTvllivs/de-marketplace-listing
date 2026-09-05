#!/usr/bin/env python3
"""Generate photo fixtures for the photo-staging evals (evals 8 & 9).

Creates in ./photos/ (gitignored — regenerate any time):
    item-front.jpg     normal photo, well under 8 MB
    item-back.jpg      normal photo, well under 8 MB
    item-detail.jpg    normal photo, well under 8 MB
    item-huge.jpg      oversized photo (> 8 MB) — staging must downscale it
    item-iphone.heic   HEIC photo — staging must convert it to JPEG
                       (HEIC→JPEG conversion shipped in v2.4.1)

Uses only the stdlib (zlib PNG writer) plus macOS `sips` for format
conversion. Random noise is used because it defeats JPEG compression,
which is what makes the oversized fixture actually oversized.
"""

import os
import random
import struct
import subprocess
import sys
import zlib

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos")
MB = 1024 * 1024


def write_noise_png(path, w, h, seed):
    rng = random.Random(seed)
    raw = b"".join(
        b"\x00" + bytes(rng.getrandbits(8) for _ in range(w * 3))
        for _ in range(h)
    )

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", zlib.compress(raw, 1)))
        f.write(chunk(b"IEND", b""))


def sips(*args):
    subprocess.run(["sips", *args], check=True, capture_output=True)


def make_jpeg(name, w, h, seed):
    png = os.path.join(OUT, "_tmp.png")
    jpg = os.path.join(OUT, name)
    write_noise_png(png, w, h, seed)
    sips("-s", "format", "jpeg", png, "--out", jpg)
    os.remove(png)
    return jpg


def main():
    os.makedirs(OUT, exist_ok=True)

    for name, seed in (("item-front.jpg", 1), ("item-back.jpg", 2),
                       ("item-detail.jpg", 3)):
        p = make_jpeg(name, 1200, 900, seed)
        print(f"{name}: {os.path.getsize(p) / MB:.1f} MB")

    # Noise JPEG ≈ 1.5–2.5 bytes/pixel; grow until the file crosses 8 MB.
    dim = 2200
    while True:
        p = make_jpeg("item-huge.jpg", dim, dim, 99)
        size = os.path.getsize(p)
        if size > 8 * MB:
            print(f"item-huge.jpg: {size / MB:.1f} MB ({dim}px)")
            break
        dim = int(dim * 1.4)
        if dim > 12000:
            sys.exit("could not produce an >8 MB JPEG")

    small = make_jpeg("_heic_src.jpg", 1200, 900, 4)
    heic = os.path.join(OUT, "item-iphone.heic")
    sips("-s", "format", "heic", small, "--out", heic)
    os.remove(small)
    print(f"item-iphone.heic: {os.path.getsize(heic) / MB:.1f} MB")


if __name__ == "__main__":
    main()

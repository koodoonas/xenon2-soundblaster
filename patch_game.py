#!/usr/bin/env python3
"""Create a version-checked Xenon II INT81 copy; never edit the input."""
import argparse
import hashlib
from pathlib import Path
SHA256 = 'c623def4ac6bcd009a3a7295a671141be254d0d7641c02f5f6d048b290d44415'
OFFSETS = [0xd30,0xd87,0x20f7,0x296c,0x450b,0x47a8,0x47ca,0x48a2,
           0x4911,0x498c,0x546e,0x5474,0x54f7,0x5d53,0x6069,0x611d,
           0x680e,0x683c,0x9383,0xdeba]
def patch(src, dest):
    data = src.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError('Unsupported executable: SHA-256 does not match inspected release')
    result = bytearray(data)
    for offset in OFFSETS:
        if result[offset:offset+2] != b'\xcd\x80':
            raise ValueError(f'Unexpected instruction at {offset:#x}')
        result[offset+1] = 0x81
    with dest.open('xb') as f:  # refuse to overwrite originals or an existing output
        f.write(result)
    print(f'Created {dest}: {len(OFFSETS)} interrupt operands changed')
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=Path)
    ap.add_argument('destination',type=Path)
    args = ap.parse_args()
    patch(args.source,args.destination)

#!/usr/bin/env python3
"""Build a playable copy using your own supported DOS game and Amiga Disk 1."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
from patch_game import patch, SHA256

ADF_SHA = '70662b706fd6b262341d0c785499fb9a0856e1144f969666ebd9912691924391'
PACKED_SHA = '7561fe0a2508bb2876cf99587a35dbe48ff67da128c0e8b83442f99ff0fa4bdc'
UNPACKED_SHA = 'fd28f362956d89a6fbf87bffd5242eef099ee63b82de681ba01f917ff0b62c6b'
ROOT = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def extract(adf_path):
    if zipfile.is_zipfile(adf_path):
        with zipfile.ZipFile(adf_path) as z:
            names = [n for n in z.namelist() if n.lower().endswith('.adf') and not n.startswith('__MACOSX/')]
            if len(names) != 1:
                raise ValueError('Expected exactly one ADF in the Disk 1 ZIP')
            if z.getinfo(names[0]).file_size != 901120:
                raise ValueError('Expected an 880 KiB ADF')
            data = z.read(names[0])
    else:
        data = adf_path.read_bytes()
    if digest(data) != ADF_SHA:
        raise ValueError('Unsupported Amiga Disk 1: SHA-256 mismatch; see README')
    header = data[0x6f200:0x6f400]
    block = int.from_bytes(header[16:20], 'big')
    size = int.from_bytes(header[324:328], 'big')
    result = bytearray()
    seen = set()
    while block:
        if block in seen or not 0 < block < len(data)//512:
            raise ValueError('Invalid OFS data chain')
        seen.add(block)
        chunk = data[block*512:(block+1)*512]
        length = int.from_bytes(chunk[12:16], 'big')
        if int.from_bytes(chunk[:4], 'big') != 8 or length > 488:
            raise ValueError('Invalid OFS data block')
        result.extend(chunk[24:24+length])
        block = int.from_bytes(chunk[16:20], 'big')
    if len(result) != size or digest(result) != PACKED_SHA:
        raise ValueError('Extracted executable verification failed')
    return bytes(result)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dos', type=Path, required=True, help='Your extracted DOS game directory')
    ap.add_argument('--amiga', type=Path, required=True, help='Supported Amiga Disk 1 ADF or ZIP')
    ap.add_argument('--output', type=Path, default=Path('game'), help='New directory; must not already exist')
    args = ap.parse_args()
    if args.output.exists():
        ap.error('Output already exists; choose a new folder to protect existing files')
    exe = next((p for p in args.dos.iterdir() if p.name.upper() == 'XENON2.EXE'), None)
    if exe is None or digest(exe.read_bytes()) != SHA256:
        ap.error('Unsupported DOS executable; see README for the expected SHA-256')
    if not shutil.which('ffmpeg'):
        ap.error('FFmpeg must be installed and available on PATH')
    packed = extract(args.amiga)
    with tempfile.TemporaryDirectory(prefix='xenon2-build-') as tmp:
        tmp = Path(tmp)
        (tmp/'packed').write_bytes(packed)
        subprocess.run([sys.executable, str(ROOT/'unpack_xenon.py'), str(tmp/'packed'), str(tmp/'unpacked')], check=True)
        data = (tmp/'unpacked').read_bytes()
        if digest(data) != UNPACKED_SHA:
            raise ValueError('Decompressed executable verification failed')
        (tmp/'music-data.bin').write_bytes(data[0x19b9e:0x2a7e0])
        print('Rendering one 191.6-second music loop. This may take a few minutes.', flush=True)
        subprocess.run([sys.executable, str(ROOT/'xenon_music.py'), str(tmp/'music.wav'), '--data', str(tmp/'music-data.bin'), '--seconds', '191.6'], check=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(tmp/'music.wav'), '-ac', '1', '-ar', '10989', '-f', 'u8', str(tmp/'X2MUSIC.PCM')], check=True)
        # mkdir without exist_ok also protects against a destination created during rendering.
        args.output.mkdir(parents=True)
        for p in args.dos.iterdir():
            if p.name.upper() in ('XENON2.EXE', 'X2SB.EXE', 'X2SB.COM', 'X2MUSIC.PCM', 'START.BAT'):
                continue
            if p.is_symlink():
                raise ValueError('Symlinks in the DOS directory are not supported')
            if p.is_dir():
                shutil.copytree(p, args.output/p.name)
            else:
                shutil.copyfile(p, args.output/p.name)
        patch(exe, args.output/'X2SB.EXE')
        for name in ['X2SB.COM', 'START.BAT', 'dosbox-settings.conf']:
            shutil.copyfile(ROOT/name, args.output/name)
        shutil.copyfile(tmp/'X2MUSIC.PCM', args.output/'X2MUSIC.PCM')
    print(f'Ready: {args.output.resolve()}. Run START.BAT in DOS and select MUSIC ON.')

if __name__ == '__main__':
    main()

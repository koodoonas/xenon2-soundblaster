"""Append the same 18 Amiga raw effects used by the GUS version to SB music PCM."""
from pathlib import Path
import argparse,hashlib,json,math
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('unpacked',type=Path)
ap.add_argument('music',type=Path,help='10989 Hz unsigned 8-bit mono music PCM')
ap.add_argument('output',type=Path,help='New directory')
a=ap.parse_args();b=a.unpacked.read_bytes();music=a.music.read_bytes()
if hashlib.sha256(b).hexdigest()!='fd28f362956d89a6fbf87bffd5242eef099ee63b82de681ba01f917ff0b62c6b':raise ValueError('Unsupported Amiga executable')
if len(music)!=2105493:raise ValueError('Expected 191.6-second music render (2105493 bytes)')
out=bytearray(music);records=[];p=0x2b69c
for i in range(18):
 n=int.from_bytes(b[p:p+4],'big');rate=int.from_bytes(b[p+4:p+6],'big');raw=b[p+6:p+6+n]
 # Match GUS version's PAL Paula period. Linear interpolation; signed 8-bit output.
 source_rate=3546895/(3579545//rate);length=math.ceil(n*10989/source_rate);start=len(out)
 for j in range(length):
  x=j*source_rate/10989;k=int(x);f=x-k
  v0=raw[min(k,n-1)];v0=v0 if v0<128 else v0-256
  v1=raw[min(k+1,n-1)];v1=v1 if v1<128 else v1-256
  out.append(round((v0*(1-f)+v1*f)*.65)&255)
 records.append(dict(index=i,source=p+6,source_bytes=n,stored_rate=rate,play_rate=source_rate,offset=start,length=length))
 p+=6+n
mapping=[0,2,0,1,6,4,3,5,6,7,8,9,10,11,12,13,14,15,16,17,2,4,5,7,9]
a.output.mkdir(parents=True)
(a.output/'X2AUDIO.PCM').write_bytes(out)
lines=[f'music_bytes equ {len(music)}',f'audio_bytes equ {len(out)}','fx_table:']
for r in records:lines.append(f" dd {r['offset']},{r['length']} ; Amiga sample {r['index']}")
lines+=['fx_map:',' db '+','.join(map(str,mapping))]
(a.output/'fx_assets.inc').write_text('\n'.join(lines)+'\n')
(a.output/'effect-map.json').write_text(json.dumps(dict(dos_to_amiga=mapping,samples=records),indent=2)+'\n')
print(f'Music {len(music)} bytes; effects {len(out)-len(music)} bytes; combined {len(out)} bytes')

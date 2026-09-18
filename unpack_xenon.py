from pathlib import Path
import sys, hashlib
if len(sys.argv)!=3: raise SystemExit('Usage: python3 unpack-xenon.py EXTRACTED_XENON-II OUTPUT.bin')
src=Path(sys.argv[1]).read_bytes()
assert hashlib.sha256(src).hexdigest()=='7561fe0a2508bb2876cf99587a35dbe48ff67da128c0e8b83442f99ff0fa4bdc', 'Different executable version'
p=0x15a+0x32260
def long():
 global p
 p-=4
 return int.from_bytes(src[p:p+4],'big')
size=long(); bits=long(); out=bytearray(size); pos=size
consumed=0
def bit():
 global bits,consumed
 c=bits&1;bits>>=1
 if bits==0:
  v=long();c=v&1;bits=(v>>1)|0x80000000
 consumed+=1
 return c
def read(n):
 v=0
 for _ in range(n):v=(v<<1)|bit()
 return v
while pos>0:
 n=read(3)
 if n==7:
  if not bit():n=read(4)+7
  else:
   n=read(10)
   if n==0:n=read(18)
 for _ in range(n):
  pos-=1;out[pos]=read(8)
 if pos<=0:break
 typ=read(2)
 if typ==0:n=2;nb=8
 elif typ==1:n=3;nb=8 if bit() else 14
 else:
  n=4
  if typ==3:
   k=read(2)
   n=read(8) if k==3 else read(2)+7 if k==2 else k+5
  nb=16 if not bit() else 8 if bit() else 12
 off=read(nb)
 for _ in range(n):
  value=out[pos+off-1];pos-=1;out[pos]=value
assert pos==0
Path(sys.argv[2]).write_bytes(out)
print('unpacked',size,hex(size),'packed cursor',hex(p),'bits',consumed)

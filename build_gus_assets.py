from pathlib import Path
import sys,struct,math,json,hashlib
import argparse
from xenon_music import Player
ap=argparse.ArgumentParser(description="Extract signed samples and generate GF1 music commands from the supported unpacked Amiga executable")
ap.add_argument('unpacked',type=Path)
ap.add_argument('output',type=Path,help='New output directory')
args=ap.parse_args()
b=args.unpacked.read_bytes()
if hashlib.sha256(b).hexdigest()!='fd28f362956d89a6fbf87bffd5242eef099ee63b82de681ba01f917ff0b62c6b':
 raise ValueError('Unsupported unpacked executable')
root=args.output
root.mkdir(parents=True)
run=root
def volume(gain):return max(0,min(4095,round(4095+256*math.log2(gain))))<<4 if gain>0 else 0
def freq(rate):return round(rate*512/44100)*2
bank=bytearray(32);samples=[]
for section,p,count in [('music',0x1b780,19),('effect',0x2b69c,18)]:
 for i in range(count):
  n=int.from_bytes(b[p:p+4],'big');rate=int.from_bytes(b[p+4:p+6],'big');start=len(bank);bank+=b[p+6:p+6+n];end=len(bank)-1;bank+=bytes((-len(bank))%16+16)
  samples.append(dict(kind=section,index=i,source=p+6,length=n,rate=rate,start=start,end=end,frequency=freq(3546895/(3579545//rate)),volume=volume(.45 if section=='music' else .7),ticks=math.ceil(n/(3546895/(3579545//rate))*50)+1))
  p+=6+n
player=Player(b);period=[65535]*4;vol=[0]*4;ptr=[0]*4;trigger=[255]*4;enabled=[False]*4
pointers={s['source']:s['index'] for s in samples if s['kind']=='music'}
seq=bytearray()
for tick in range(9580):
 trigger=[255]*4
 for a,size,v in player.run():
  if a==0xdff096:
   for ch in range(4):
    if v&(1<<ch):
     on=bool(v&0x8000)
     if on and not enabled[ch]:trigger[ch]=pointers.get(ptr[ch],254)
     elif not on:trigger[ch]=254
     enabled[ch]=on
  elif 0xdff0a0<=a<0xdff0e0:
   ch,off=divmod(a-0xdff0a0,16)
   if off==0 and size==4:ptr[ch]=v
   elif off==6:period[ch]=v or 65535
   elif off==8:vol[ch]=v
 for ch in range(4):seq+=struct.pack('<HHHH',trigger[ch],freq(3546895/period[ch]),volume(vol[ch]/64*.45),0)
(run/'X2GUS.BNK').write_bytes(bank);(run/'X2GUS.SEQ').write_bytes(seq)
lines=['; Generated metadata only; no sample or song payload.','bank_bytes equ '+str(len(bank)),'sequence_frames equ 9580','sample_table:']
for s in samples:lines.append(' dw '+','.join(map(str,[s['start']>>7,(s['start']&127)<<9,s['end']>>7,(s['end']&127)<<9,s['frequency'],s['volume'],s['ticks'],0]))+' ; '+s['kind']+str(s['index']))
# Experimental semantic map: DOS firing=2; explosion/debris=6. Remaining roles less certain.
fx=[0,2,0,1,6,4,3,5,6,7,8,9,10,11,12,13,14,15,16,17,2,4,5,7,9]
lines+=['fx_map:',' db '+','.join(str(19+i) for i in fx),'fx_map_end:']
(root/'assets.inc').write_text('\n'.join(lines)+'\n');(root/'sample-map.json').write_text(json.dumps(samples,indent=2))
print('bank',len(bank),'sequence',len(seq),'notes',len(player.events))

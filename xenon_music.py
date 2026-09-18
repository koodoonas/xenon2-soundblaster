"""Xenon II Amiga sequencer, ported from the supplied BS1 game image.

Pure Python; see README.md for provenance, validation, and rendering limits.
Offsets refer to the decompressed executable, not a disk image.
"""
from pathlib import Path
from dataclasses import dataclass
B=0x19b9e
@dataclass
class Channel:
 flags:int=0; vibrato:int=0; note:int=0; transpose:int=0; ptr:int=0
 order:int=0; order_next:int=2; arp_start:int=0x1a306; arp_pos:int=0x1a306
 slide:int=0; slide_wait:int=0; loop_set:bool=True; instrument:int=0
 duration:int=0; remaining:int=1; slide_acc:int=0
 env_start:int=0; env_pos:int=0; env_delay:int=0; env_count:int=0
 vib_step:int=0; vib_phase:int=0; vib_limit:int=0
class Player:
 def __init__(self,data):
  self.data=data;self.writes=[];self.events=[];self.loops=[];self.commands={};self.tick=-1
  self.tempo=data[0x1a428];self.skip=data[0x1a429];self.acc=0;self.master=64;self.fade=0;self.fade_count=0;self.playing=True;self.marker=0
  self.inst=[];p=0x1b780
  for i in range(20):
   length=self.u32(p);rate=self.u16(p+4);loop=self.u32(0x1a338+12*i+4)
   self.inst.append((p+6,length//2,3579545//rate-{5:8,6:8,7:2,11:2}.get(i,0),loop));p+=6+length
  self.silence=p
  self.channels=[]
  for i in range(4):
   order=self.u16(0x1a42a+2*i)
   self.channels.append(Channel(order=order,ptr=B+self.u16(B+order)))
 def u16(self,p):return int.from_bytes(self.data[p:p+2],'big')
 def u32(self,p):return int.from_bytes(self.data[p:p+4],'big')
 def byte(self,c):
  x=self.data[c.ptr];c.ptr+=1;return x
 def reg(self,ch,off,value,size=2):self.writes.append((0xdff0a0+16*ch+off,size,value))
 def dma(self,value):self.writes.append((0xdff096,2,value))
 def pointer(self,ch,p,n):self.reg(ch,0,p,4);self.reg(ch,4,n)
 def period(self,c,arp=0):
  note=(c.note+c.transpose+arp)&255
  return (self.u16(0x1a256+note*2)*self.inst[c.instrument][2]>>10)&65535
 def volume(self,x):
  if x&128:x-=256
  return ((x*self.master)&65535)>>6
 def run(self):
  self.tick+=1;self.writes=[]
  if not self.playing:return self.writes
  self.acc+=self.skip
  if self.acc>=256:self.acc-=256;return self.writes
  if self.fade:
   self.fade_count=(self.fade_count-1)&255
   if not self.fade_count:
    self.master=(self.master-1)&65535;self.fade_count=self.fade
    if not self.master:self.playing=False;self.dma(15);self.writes.append((0xdff09e,2,255));return self.writes
  for ch,c in enumerate(self.channels):
   p,n,scale,loop=self.inst[c.instrument]
   if not c.loop_set:
    c.loop_set=True
    if loop&0x80000000:self.pointer(ch,self.silence,32)
    else:self.pointer(ch,p+loop,(n-(loop>>1))&65535)
   c.remaining=(c.remaining-1)&65535
   if c.remaining==0:
    c.flags=0
    for guard in range(1000):
     source=c.ptr;cmd=self.byte(c)
     if cmd<0x80:
      c.note=cmd;c.env_pos=c.env_start+1;c.env_count=c.env_delay
      p,n,scale,loop=self.inst[c.instrument]
      self.pointer(ch,p,n);self.reg(ch,8,self.volume(self.data[c.env_start]));period=self.period(c);self.reg(ch,6,period)
      c.loop_set=False;c.remaining=c.duration;self.dma(0x8200|(1<<ch))
      self.events.append([self.tick,ch,cmd,c.instrument,period,c.duration,hex(source)])
      break
     self.commands[cmd]=self.commands.get(cmd,0)+1
     if cmd>=0xe0:c.duration=((cmd-0xdf)*self.tempo)&65535
     elif cmd>=0xb0:c.instrument=cmd-0xb0
     elif cmd>=0xa0:
      c.env_start=B+self.u16(0x1b65c+2*(cmd-0xa0));c.env_delay=self.data[c.env_start-1]
     elif cmd>=0x90:
      c.arp_start=c.arp_pos=B+self.u16(0x1a2e6+2*(cmd-0x90))
     elif cmd==0x80:
      addr=c.order+c.order_next;c.order_next+=2
      if self.u16(B+addr)==0:
       addr=c.order;c.order_next=2;self.loops.append([self.tick,ch])
      c.ptr=B+self.u16(B+addr)
     elif cmd==0x81:
      c.slide_acc=0;c.slide=self.byte(c);c.slide_wait=self.byte(c);c.flags|=2
     elif cmd==0x82:
      c.remaining=c.duration;self.pointer(ch,self.silence,32);break
     elif cmd==0x83:
      c.remaining=c.duration;self.dma(0x8200|(1<<ch));break
     elif cmd==0x84:
      self.playing=False;self.dma(15);self.writes.append((0xdff09e,2,255));return self.writes
     elif cmd==0x85:self.marker=self.byte(c)
     elif cmd==0x86:
      c.vibrato=255;c.vib_step=self.byte(c);c.vib_limit=self.byte(c);c.vib_phase=0
     elif cmd==0x87:c.vibrato=0
     elif cmd==0x88:c.transpose=self.byte(c)
     elif cmd==0x89:c.order=(self.byte(c)<<8)|self.byte(c);c.order_next=0
     elif cmd==0x8a:self.tempo=self.byte(c)
     elif cmd==0x8b:self.fade=self.fade_count=self.byte(c)
     else:raise ValueError(('unknown',hex(cmd),hex(source)))
    else:raise RuntimeError('command loop')
   elif c.remaining==1:
    if self.data[c.ptr]!=0x83:self.dma(1<<ch)
   else:
    arp=self.data[c.arp_pos];c.arp_pos+=1
    if arp&128:c.arp_pos=c.arp_start
    period=self.period(c,arp&127)
    if c.flags&2:
     if c.slide_wait:c.slide_wait-=1
     else:
      c.slide_acc=(c.slide_acc+(c.slide if c.slide<128 else c.slide-256))&65535
      period=(period-c.slide_acc)&65535
    if c.vibrato:
     if c.vibrato&128:
      c.vib_phase=(c.vib_phase+c.vib_step)&255
      if c.vib_phase==c.vib_limit:c.vibrato^=128
     else:
      c.vib_phase=(c.vib_phase-c.vib_step)&255
      if c.vib_phase==0:c.vibrato^=128
     if c.vib_phase==0:c.vibrato^=1
     phase=c.vib_phase if c.vib_phase<128 else c.vib_phase-256
     period=(period+(phase if c.vibrato&1 else -phase))&65535
    self.reg(ch,6,period)
    c.env_count-=1
    if c.env_count<0:
     c.env_count=c.env_delay;v=self.data[c.env_pos]
     if not v&128:c.env_pos+=1
     self.reg(ch,8,self.volume(v&127))
  return self.writes

@dataclass
class Voice:
 pointer:int=0; length:int=2; period:int=65536; volume:int=0
 enabled:bool=False; position:float=0.0; active_pointer:int=0; active_length:int=2

class Mixer:
 """Four-channel DMA model with pending reload registers and sample hold.

Register updates are applied at frame boundaries; this is not a complete
cycle-accurate Amiga chipset or analog-filter simulation.
 """
 def __init__(self,data,sample_rate=44100,clock=3546895):
  self.data=data;self.rate=sample_rate;self.clock=clock
  self.voices=[Voice() for _ in range(4)];self.dmacon=0
 def write(self,address,size,value):
  if address==0xdff096:
   old=self.dmacon
   self.dmacon=(old|value&0x7fff) if value&0x8000 else (old&~value)
   for ch,v in enumerate(self.voices):
    enabled=bool(self.dmacon&0x200 and self.dmacon&(1<<ch))
    if enabled and not v.enabled:
     v.active_pointer=v.pointer;v.active_length=v.length;v.position=0.0
    v.enabled=enabled
  elif 0xdff0a0<=address<0xdff0e0:
   ch,off=divmod(address-0xdff0a0,16);v=self.voices[ch]
   if off==0 and size==4:v.pointer=value&0x7fffe
   elif off==4:v.length=2*(value or 65536)
   elif off==6:v.period=value or 65536
   elif off==8:v.volume=64 if value&64 else value&63
 def render(self,n):
  from array import array
  left=[0]*n;right=[0]*n
  for ch,v in enumerate(self.voices):
   if not v.enabled:continue
   target=left if ch in (0,3) else right
   pos=v.position;p=v.active_pointer;length=v.active_length
   step=self.clock/(v.period*self.rate);gain=v.volume
   for k in range(n):
    while pos>=length:
     pos-=length;p=v.pointer;length=v.length
    x=self.data[p+int(pos)]
    if x>=128:x-=256
    target[k]+=x*gain
    pos+=step
   v.position=pos;v.active_pointer=p;v.active_length=length
  # Each side has two 8-bit channels at volume 0..64. Fixed gain leaves headroom.
  result=array('h')
  for l,r in zip(left,right):
   result.append(round(l*1.7));result.append(round(r*1.7))
  if __import__('sys').byteorder!='little':result.byteswap()
  return result.tobytes()

def load_data(path=None):
 import hashlib
 p=Path(path) if path else Path(__file__).with_name('music-data.bin')
 raw=p.read_bytes()
 # Keeping original relative offsets makes comparison against 68000 code direct.
 if len(raw)!=0x2a7e0-B or hashlib.sha256(raw).hexdigest()!='935dcde143e1b3106e3c54fb5bb5552583d29c3ad0915ca194b5f680d9d2ab00':
  raise ValueError('Unexpected or modified music-data.bin')
 return bytes(B)+raw

def render(path,data,seconds=199.6,sample_rate=44100,tick_rate=50.0,clock=3546895):
 import wave,math,json,csv
 player=Player(data);mixer=Mixer(data,sample_rate,clock);frames=math.ceil(seconds*tick_rate)
 with wave.open(str(path),'wb') as w:
  w.setnchannels(2);w.setsampwidth(2);w.setframerate(sample_rate)
  count=0
  for frame in range(frames):
   for address,size,value in player.run():mixer.write(address,size,value)
   end=min(round((frame+1)*sample_rate/tick_rate),round(seconds*sample_rate))
   if end>count:w.writeframesraw(mixer.render(end-count));count=end
 notes=Path(path).with_suffix('.notes.csv')
 with notes.open('w',newline='') as f:
  writer=csv.writer(f);writer.writerow(['tick','channel','note_index','sample_index','period','duration_effective_ticks','sequence_offset'])
  writer.writerows(player.events)
 report={'sample_rate_hz':sample_rate,'update_rate_hz':tick_rate,'audio_clock_hz':clock,'seconds':seconds,'note_events':len(player.events),'channel_order_wraps':player.loops,'first_song_wrap_seconds':player.loops[0][0]/tick_rate if player.loops else None,'used_sample_indices':sorted({e[3] for e in player.events})}
 Path(path).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
 return report

if __name__=='__main__':
 import argparse,json
 ap=argparse.ArgumentParser(description='Render the recovered Xenon II Amiga in-game music.')
 ap.add_argument('output',type=Path,help='Output stereo 16-bit WAV')
 ap.add_argument('--data',type=Path,help='Path to companion music-data.bin')
 ap.add_argument('--seconds',type=float,default=199.6,help='Default: one sequence loop plus eight seconds')
 ap.add_argument('--sample-rate',type=int,default=44100)
 ap.add_argument('--tick-rate',type=float,default=50.0,help='Nominal PAL VBlank rate')
 ap.add_argument('--audio-clock',type=int,default=3546895,help='PAL Paula clock')
 args=ap.parse_args()
 if args.seconds<=0 or args.sample_rate<8000 or args.tick_rate<=0:ap.error('Invalid duration or rate')
 print(json.dumps(render(args.output,load_data(args.data),args.seconds,args.sample_rate,args.tick_rate,args.audio_clock),indent=2))

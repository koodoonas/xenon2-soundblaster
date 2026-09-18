# Implementation and verification

## Version and patch scope

Input `XENON2.EXE`: 123,496 bytes; SHA-256:

`c623def4ac6bcd009a3a7295a671141be254d0d7641c02f5f6d048b290d44415`

The patch changes exactly 20 bytes: the operand of each listed `CD 80` instruction becomes `81`. Executable size, MZ header, relocation table, and all other bytes remain unchanged. Offsets below are absolute file offsets, not runtime segment offsets.

```
000D30 000D87 0020F7 00296C 00450B 0047A8 0047CA 0048A2
004911 00498C 00546E 005474 0054F7 005D53 006069 00611D
00680E 00683C 009383 00DEBA
```

Useful sites:

| File offset | Observed role |
|---|---|
| `0x6069` | AH=2, AL=0: credits music start |
| `0x611D` | AH=1: credits music stop |
| `0x450B` | AH=2, AL=0: level music start, conditional on music option |
| `0x20F7` | AH=1: stop observed at level/death transition |
| `0x683C` | AH=3: original speaker effect request |
| `0x680E` | AH=0: native audio tick from timer path |
| `0x546E`, `0x5474` | stop followed by AH=2, AL=1 game-over music |
| `0x0D87` | native sound stop on normal exit |
| `0x668A`–`0x66E8` | original timer installation/removal code |

The native sound driver's segment base corresponds to file offset `0x15390`. The original INT 80 handler remains installed by the game. The launcher uses INT 81 and forwards native calls to INT 80. For the main song, it calls the original initialization, then AH=20h/AL=0 to disable native music without disabling the effects path, and starts PCM playback. Stop requests halt PCM and are forwarded. Native timer frequency/chaining is not patched.

The runtime trace confirmed calls from `0x6069`, `0x611D`, `0x450B`, `0x20F7`, and `0x0D87` in a music-enabled session. Temporary trace instrumentation was removed from the delivered binary. The menu initially says MUSIC OFF; switching it on triggers the original level-music call, so no extra patch to the music preference or level transition was necessary.

## Audio provenance

Disk 1 of the supplied two-disk Amiga release contains packed `XENON-II`. Its decoded image is 287,946 bytes, SHA-256:

`fd28f362956d89a6fbf87bffd5242eef099ee63b82de681ba01f917ff0b62c6b`

Within that decoded image:

| Offset | Data |
|---|---|
| `0x019B9E` | custom four-channel music module base |
| `0x01A428` | song/sequence data |
| `0x01B780` | sample bank record start |

It is a custom sequencer, not a standard ProTracker MOD. The bank has 20 sample records totaling 61,352 PCM bytes; this song uses samples 0–18. The previous renderer validation matched 19,161 ticks, 5,570 note events, and 122,028 register writes against the original 68000 player over two loops. The cycle is 9,580 50-Hz ticks, or 191.6 seconds. These facts and the extraction work are documented in the earlier renderer and disk reports.

## Driver design

The entire unsigned 8-bit mono track is loaded into EMS before executing the game. It needs 129 16-KiB EMS pages. A separate 16-KiB conventional allocation supplies an 8-KiB DMA window that cannot cross a physical 64-KiB boundary. The launcher itself is 6,256 bytes on disk.

- DSP auto-initialize 8-bit playback (`1Ch`), block interrupt every 4,096 samples, 8,192-byte DMA ring.
- Time constant 165: nominal `1,000,000 / 91 = 10,989.011 Hz`; the source was resampled to integer 10,989 Hz.
- DSP IRQ fills the completed buffer half, with its own stack. No DOS file I/O occurs in the IRQ.
- EMS mapping is saved/restored around copies; copies handle EMS-page and track-end boundaries.
- Original IRQ vector, INT 81 vector, selected PIC mask bit, and SB Pro mono/stereo mixer bit are restored at exit. Allocations are released and DMA playback is stopped.
- File reads are checked for short reads. Initialization failures report an error. EMS refill errors stop playback and produce a nonzero launcher exit code.

This approach avoids real-time mixing load, but trades roughly 2.1 MB of EMS for that simplicity. DSP reset on exit stops playback; this is not a transparent wrapper around another concurrently active sound application.

## Tests performed

Development execution tests used a headless DOSBox Pure libretro core on macOS. The project owner subsequently reported successful playback on a real 386 with a PicoGUS in Sound Blaster mode. CPU speed, DOS/EMS versions, PicoGUS firmware and full-playthrough coverage have not been recorded. This confirms that reported configuration, not every original Sound Blaster card.

| Test | Result |
|---|---|
| SB16 A220/I7/D1, standalone eight-second playback | Sound captured; 21 DMA interrupts, 23 filled halves, zero EMS errors; returned to DOS |
| Final SB16 game build: credits, MUSIC ON, level 1, firing/effects, death/ready transition, F10 | 48 DMA interrupts, 52 half-buffer fills, 2 music starts, 12 native effect requests, zero EMS errors, zero EXEC errors; returned to DOS |
| Final SB2 A220/I5/D3, forced loop | DSP 2.01; 21 DMA interrupts, 23 half-buffer fills, 1 wrap, zero EMS errors |
| Before/after standalone resource audit | Byte-identical snapshots |
| Before/after final game resource audit | Byte-identical snapshots |
| EMS disabled | Explicit insufficient/unavailable EMS error, returned to DOS |
| Sound Blaster disabled | Explicit DSP detection error, returned to DOS |
| Binary patch comparison | Exactly the 20 documented operands differ; original executable hash unchanged |

The resource snapshot records INT 08h, 09h, 0Dh, 0Fh, and 81h vectors; master PIC mask; free EMS pages; and the largest available conventional memory block. The final game before/after snapshots both equal:

`a5fe00f087e900f0e01200f0f400700000000000f8a403669d`

The standalone captured audio was compared locally to the source PCM at several positions: best local correlations were approximately 0.94–0.99, with smoothly changing alignment rather than 4,096-byte jumps. This supports correct buffer progression; it is not a proof of zero glitches under all loads. The emulator capture showed small sample-clock/filter differences from the source.

Audio recordings and game graphics are not included in this public repository.

## Concrete next work

1. Play through later levels, the shop, game-over, and pause/resume transitions; exercise repeated starts/stops and lower CPU speeds.
2. Test actual SB2/Pro/SB16 hardware, EMS managers, alternate base addresses, and DMA 0. Tighten DSP timeout/restart handling if those tests reveal failures.
3. For lower memory requirements, port the validated custom sequencer and four-channel sample mixer to DOS. The sample bank is about 61 KB; this would replace the 2.1 MB prerendered EMS track, at additional CPU cost.
4. For AdLib, design OPL2 instruments and a channel-allocation/percussion arrangement, then implement an OPL sequencer backend. The Amiga PCM samples cannot be used directly as OPL2 instruments.

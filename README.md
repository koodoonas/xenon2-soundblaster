# Xenon II — selectable Sound Blaster / Gravis UltraSound audio

**Experimental unified release.** One game folder, one patched game executable, and one startup menu. Both audio modes use the recovered Amiga music and the same provisional sampled-effect assignments.

## Get the unified version

**[Download the complete playable ZIP](https://github.com/pgeo101/xenon2-soundblaster/raw/refs/heads/main/Xenon2-SB-GUS-Unified-experimental.zip)** (about 2 MB).

1. Extract the ZIP into a fresh folder, keeping the S1–S5 subfolders.
2. In DOS or DOSBox-X, enter the extracted `xenon2-unified-experimental` folder.
3. Configure your sound card as described below, then run **START.BAT** and choose SB or GUS.
4. Enable **MUSIC ON** in the game's menu.

**No build step, Python, FFmpeg, or separate audio download is needed to play.** The archive includes:

| File | Contents |
| --- | --- |
| `X2AUDIO.PCM` | Sound Blaster music and digital effects (2,194,402 bytes) |
| `X2GUS.SEQ` | Gravis UltraSound music sequence (306,560 bytes) |
| `X2GUS.BNK` | Gravis UltraSound music/effect samples (124,496 bytes) |
| `X2GAME.EXE` | Matching patched game executable |
| `START.BAT`, `XENON2.COM`, `X2SB.COM`, `X2GUS.COM` | Selector and audio drivers |
| Game data and `S1`–`S5` | All five levels |

Keep these files together. If you use **Code → Download ZIP**, extract the playable ZIP inside that repository download before launching; the repository's loose COM files alone are not a complete game. Checksums are in `SHA256SUMS.txt`.

**Upgrading:** extract into a fresh folder; do not mix older patched EXEs, drivers, or audio banks with this version. Building from original files remains an optional developer workflow below.

## Start

Run **START.BAT** (or `XENON2.COM`) and choose:

- **1 — Sound Blaster**
- **2 — Gravis UltraSound**
- **Esc / Q — Exit**

Select **MUSIC ON** in the game's menu. Press Enter for VGA, then Space past the credits. From the default menu, Down twice and Space enables music; Up twice and Space selects one player. Space starts from Get Ready and fires. Effects work with music off. **F10** quits normally and returns to DOS.

The selector loads the corresponding driver and then the shared `X2GAME.EXE`. Do not run that EXE directly: it requires the launcher's audio and keyboard handlers. Use a new folder for this release; older patched EXEs do not include its hotkey patch.

## Live volume controls

| Key | Action |
| --- | --- |
| **F5** | Music volume down |
| **F6** | Music volume up |
| **F7** | Sound-effects volume down |
| **F8** | Sound-effects volume up |

Both levels start at **80%**, change in **10% steps**, and stop at **0% (mute)** and **100%**. Holding a key can repeat according to keyboard typematic behavior. Levels reset when launching the driver again; they are not saved to disk. Controls work in the game, including its menus, but not in standalone `/TEST` modes. There is no on-screen volume overlay; the final levels and key counts are recorded in the driver log. On a Mac, use Fn with the function keys if needed to send F5–F8 to the emulator.

Music mute does not stop its sequencer/PCM position. Effects are independently attenuated, including effects already playing. SB changes take effect as its buffered audio is replaced (up to about 93 ms); GUS updates occur on the next music/effects timer tick (about 20 ms). Each mode's 100% is its configured mix gain, not the sound card's physical master volume.

## Hardware setup

A 386 or newer and an EMS manager are required.

| Mode | Requirements |
| --- | --- |
| Sound Blaster | DSP 2.0+, **3 MB free EMS**, matching `BLASTER`; base 210h–280h in 10h steps, IRQ 5/7, DMA 0/1/3 |
| Gravis UltraSound | Configured GUS, **256 KB card RAM**, **512 KB free EMS**, matching `ULTRASND`; base 210h–260h |

**PicoGUS must already be in the matching SB or GUS mode.** Choosing an option in this menu selects a game audio driver; it does not reconfigure PicoGUS firmware.

Example environment values, only when they match your hardware:

```dos
SET BLASTER=A220 I7 D1 T6
SET ULTRASND=240,3,3,5,5
START
```

The supplied `dosbox-settings.conf` enables both emulated cards with separate IRQ/DMA settings and disables PC-speaker audio. Merge it into your emulator configuration, mount this folder as C:, and set the environment values above. No GUS patch/instrument library is needed; samples come from the bank in this folder.

### Run directly in one mode

After preparing the game, you can bypass the selector:

```dos
X2SB.COM
```

or:

```dos
X2GUS.COM
```

Use the driver for the configured card/PicoGUS mode. Both retain the same F5–F8 controls and use the shared `X2GAME.EXE`.

### Environment variables, IRQ and DMA

Settings are **read from the environment, not autodetected**:

- **SB:** `BLASTER` supplies A (base address), I (IRQ), and D (8-bit DMA). Without it, defaults are A220/I7/D1. The driver checks the DSP at the configured address but does not scan for the card or discover IRQ/DMA. IRQ 5/7 and DMA 0/1/3 are supported.
- **GUS:** `ULTRASND` must be set. Only its first field, the base address, is used. The IRQ/DMA fields are ignored by this player, which uploads samples through programmed I/O and uses the game's timer. The driver checks RAM at the configured base.

### DOSBox / DOSBox-X setup

Use the included [dosbox-settings.conf](dosbox-settings.conf) for the emulated devices. It enables SB16 at 220h/IRQ7/DMA1 and GUS at 240h/IRQ5/DMA3, with 16 MB memory and EMS enabled. At the emulator prompt:

```dos
MOUNT C "/path/to/new-unified-game"
C:
SET BLASTER=A220 I7 D1 T6
SET ULTRASND=240,3,3,5,5
START.BAT
```

Choose **1** or **2**. Unlike a single PicoGUS operating mode, an emulator can expose both cards simultaneously. Music remains off until enabled in the game's menu. On physical hardware, replace the example environment values with your configured settings.

### Audio checks and troubleshooting

From the generated game directory, run `X2SB.COM /TEST` or `X2GUS.COM /TEST` for an eight-second music/effects check. Standalone tests do not use the game's F5–F8 handler. If audio is missing, check the selected hardware mode, environment base address, and EMS availability first. SB also needs the correct supported IRQ/DMA. Keep every generated audio bank and game subdirectory together.

## Audio and limitations

- **SB:** 10,989 Hz, mono, 8-bit software mix; four simultaneous effect voices. Continuous DMA playback also runs while music is off. Heavy effect overlap can clip, and saturation is counted in the log.
- **GUS:** native GF1 sample playback; four stereo-positioned music voices plus eight centered effect voices. Samples reside in card RAM; music commands reside in EMS. No GUS DMA/IRQ is used.
- Both use the same 18 raw Amiga sampled effects. Shooting/explosion events are intercepted, but the firing sample choice and most other mappings remain provisional. Synthesized Amiga effects receive sample substitutes. The game-over cue is also a substitute.
- The song repeats its fixed 191.6-second first loop. This is not an exact emulation of every Paula behavior or original sequencer state across repeats.
- This release passed DOSBox Pure tests. The earlier real 386/PicoGUS SB test applies to the older music-only build, not this unified release. Physical-hardware validation remains outstanding.

After exit, `X2SB.LOG` or `X2GUS.LOG` records diagnostics, final volume levels, and F5/F6/F7/F8 counts in hexadecimal. Volume value A means 10/10, or 100%.

## Hardware demonstration and test status

**Earlier SB prototype hardware report:** Tested successfully on a real **386 with a PicoGUS in Sound Blaster mode**.

[Watch the earlier Sound Blaster prototype demonstration](https://www.youtube.com/watch?v=VaM9JKJuMTs)

That video and hardware report concern the earlier music-only version. They do not validate the new digital-effects mixer, native GUS driver, or F5–F8 controls on physical hardware. The unified release has passed the emulator tests in [TEST-RESULTS.txt](TEST-RESULTS.txt); detailed logs, key schedules, and resource audits are in [test-evidence.zip](test-evidence.zip).

## Build from your own files

This optional workflow rebuilds the playable folder from your original files. The ready-to-run ZIP above already includes the generated audio and game data. Rebuilding requires Python **3.10+** and **FFmpeg on PATH**. Download/extract the repository first. Supply the complete original DOS installation, including the S1–S5 folders, and Disk 1 of the supported Amiga two-disk BS1 release (`Xenon II - Megablast (1989)(ImageWorks)[cr BS1][t +3 BS1](Disk 1 of 2)`) as an ADF or a ZIP containing it. Disk 2 is not needed for audio extraction.

From the repository directory:

```sh
python3 prepare.py --dos /path/to/original-dos-game --amiga /path/to/Disk1.zip --output new-unified-game
```

Reuse the earlier SB music render to skip rendering/FFmpeg:

```sh
python3 prepare.py --dos /path/to/original-dos-game --amiga /path/to/Disk1.zip --music /path/to/old-sb/X2MUSIC.PCM --output new-unified-game
```

On Windows, use `py` instead of `python3` if appropriate. Allow a few minutes and approximately 50 MB of temporary space for a fresh music render. The destination must be new. Original files are read only. The optional PCM is checked for expected byte length, not musical content. The generators' metadata must match the included launcher metadata.

Supported original DOS `XENON2.EXE` SHA-256:
`c623def4ac6bcd009a3a7295a671141be254d0d7641c02f5f6d048b290d44415`

Supported Amiga Disk 1 ADF SHA-256:
`70662b706fd6b262341d0c785499fb9a0856e1144f969666ebd9912691924391`

Recompile from the source directory with NASM:

```sh
nasm -f bin xenon2.asm -o XENON2.COM
nasm -f bin x2sb.asm -o X2SB.COM
nasm -f bin x2gus.asm -o X2GUS.COM
```

## Reporting results

Please open an issue with CPU/speed, DOS version, EMS manager, sound card/firmware and mode, `BLASTER` or `ULTRASND` settings, what you tested, and relevant `X2SB.LOG`/`X2GUS.LOG` counters. Include whether F5–F8 change music/effects independently. Do not attach original game files, disk images, or extracted audio assets.

## Credits

Created with assistance from OpenAI Codex for reverse engineering, implementation, and emulator testing; earlier real-machine testing by pgeo101. This is an unofficial fan experiment, unaffiliated with the original developers or publishers. Original credits include The Bitmap Brothers, The Assembly Line, Bomb the Bass, and David Whittaker.

## License

Added launchers, player code, tools, and documentation: MIT License, copyright 2026 pgeo101. Original game code, music, samples, and artwork remain their respective owners' material and are not covered by MIT. The playable archive includes original game and audio material; the MIT license applies only to the added code, tools, and documentation.

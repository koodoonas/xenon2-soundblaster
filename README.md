# Xenon II Sound Blaster music — experimental

**Experimental prototype.** Adds music reconstructed from the Amiga release to the DOS version of Xenon II: Megablast, using Sound Blaster digital playback and retaining the original PC-speaker effects.

**Hardware report:** pgeo101 tested it successfully on a real **386 with a PicoGUS in Sound Blaster mode**. Development testing also covered DOSBox with emulated SB16 and SB2 configurations. A full playthrough and original Creative ISA cards have not been verified.

Created with assistance from OpenAI Codex for reverse engineering, implementation, and emulator testing; real-machine testing by pgeo101. This is an unofficial fan experiment, unaffiliated with the original developers or publishers.

## What is included

The repository contains the DOS launcher (`X2SB.COM`), NASM source, a version-checked DOS patcher, an Amiga extraction/rendering toolchain, and technical findings. It contains **no original game executable, disk image, music data, samples, or rendered soundtrack**. Supply your own supported copies to generate those files locally.

## Prepare your installation

On a modern machine, install Python 3.10+ and FFmpeg. Download this repository using **Code → Download ZIP**, then extract it. You also need:

- Your DOS Xenon II installation, extracted into a folder, including `XENON2.EXE` and all data/subdirectories.
- Disk 1 of the supported Amiga two-disk BS1 release: `Xenon II - Megablast (1989)(ImageWorks)[cr BS1][t +3 BS1](Disk 1 of 2)`, as an ADF or a ZIP containing that ADF. Disk 2 is not needed for music extraction.

From the repository directory:

```sh
python3 prepare.py --dos "/path/to/dos-game" --amiga "/path/to/Disk 1.zip" --output game
```

On Windows, use `py` instead of `python3` if appropriate. FFmpeg must be available on PATH. Allow a few minutes and approximately 50 MB temporary disk space. The script verifies the input versions, extracts and renders one music loop, and creates a new playable folder. It refuses to overwrite an existing output folder. Original inputs are read only.

Only these exact inputs are currently supported:

| Input | SHA-256 |
|---|---|
| DOS `XENON2.EXE` (123,496 bytes) | `c623def4ac6bcd009a3a7295a671141be254d0d7641c02f5f6d048b290d44415` |
| Amiga Disk 1 ADF (901,120 bytes, hash of ADF inside ZIP) | `70662b706fd6b262341d0c785499fb9a0856e1144f969666ebd9912691924391` |

An unsupported version is rejected rather than patched using incorrect offsets.

## Play

Copy the entire generated `game` folder to your DOS machine, or mount it in DOSBox. Keep the `S1`–`S5` directories intact. Requirements:

- **386 or later**, DOS, EMS enabled; at least **3 MB free EMS** recommended.
- Sound Blaster **DSP 2.0+**, IRQ **5 or 7**, 8-bit DMA **0, 1 or 3**.
- A `BLASTER` environment variable matching your actual sound configuration.

For DOSBox, the supplied configuration suggests SB16 at A220/I7/D1, 16 MB RAM, EMS enabled, normal core, and 20,000 cycles. With that configuration:

```dos
SET BLASTER=A220 I7 D1 T6
START.BAT
```

Use the settings configured on your own card/PicoGUS when running on hardware.

Press Enter for VGA, then Space to leave the credits. The menu defaults to **MUSIC OFF**: use Down twice and Space to enable **MUSIC ON**, then Up twice and Space for one player. Space starts from “Get Ready” and fires. **F10** exits normally.

Launch `START.BAT` or `X2SB.COM`—the patched `X2SB.EXE` requires the launcher's interrupt handler. Diagnostics are written to `X2SB.LOG` after exit. `X2SB.COM /TEST` plays eight seconds; `/LOOPTEST` exercises the track boundary.

## How it works and limitations

The patch redirects 20 sound API calls in a copy of the DOS executable. A small launcher preloads a 191.6-second, unsigned 8-bit mono track into EMS and feeds Sound Blaster DMA at approximately 10,989 Hz. Original sound effects and the game-over jingle retain their speaker path. See [TECHNICAL.md](TECHNICAL.md) for offsets and verification details.

This version uses a prerendered track, so it needs about 2.1 MB of EMS for audio. The renderer reconstructs the custom Amiga sequencer; it does not reproduce analog Amiga filtering. AdLib/OPL playback is not implemented. Later levels, shops, all pause/resume cases, and broad hardware compatibility still need testing.

To rebuild the supplied launcher with NASM:

```sh
nasm -f bin x2sb.asm -o X2SB.COM
```

## Reporting results

Please open an issue with CPU/speed, DOS version, EMS manager, sound device/firmware, BLASTER settings, what you tested, and relevant `X2SB.LOG` counters. Do not attach game executables, disk images, or extracted music assets. The 386/PicoGUS result is a successful user report; detailed settings and full-playthrough coverage have not yet been recorded.

## Credits and distribution

Xenon II, its original code, artwork, music, and samples belong to their respective rights holders. Credits in the supplied game include The Bitmap Brothers, The Assembly Line, Bomb the Bass, and David Whittaker. No rights to the original game or music are granted by this project.

The new project code and documentation are licensed under the [MIT License](LICENSE), copyright (c) 2026 pgeo101. This license does not cover the original Xenon II game code, artwork, music, samples, or other third-party assets. Users must supply their own game files; the original game assets must remain outside this repository.

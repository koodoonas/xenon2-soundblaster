# Changelog

## Complete playable download — 2026-09-25

- Added the ready-to-run ZIP with X2AUDIO.PCM, X2GUS.SEQ, X2GUS.BNK, matching executable/drivers, and all game data.
- Added direct download and extraction instructions; building is optional.
- Runtime binaries and audio are unchanged from the tested unified build.

## Unified experimental update — 2026-09-19

- One startup menu: Sound Blaster or Gravis UltraSound.
- Shared patched game executable and separate SB/GUS drivers.
- Digital Amiga sampled effects replace PC-speaker effects in both modes.
- F5/F6 change music volume; F7/F8 change effect volume during gameplay.
- Separate 0–100% levels in 10% steps, initialized to 80%.
- Native GUS sample voices; SB software mixing with four effect voices.
- Updated asset builder, emulator configuration, technical notes, and test evidence.
- Experimental: new functionality is emulator-tested; physical validation remains outstanding.

## Original Sound Blaster prototype

- Sound Blaster PCM music with original PC-speaker effects.
- Reported working on a real 386 with PicoGUS in SB mode; demonstration remains linked in the README.
- Earlier versions remain available in Git history.

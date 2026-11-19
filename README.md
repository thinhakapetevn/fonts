# Oxalis Monobit v1.0.0 — Complete Package

Owner: **Oxalis**. © 2026 Oxalis. All rights reserved in original contributions.

Two companion true-bitmap **monospace** font families, each in Regular 400 and Bold 700:

| Family | Line/cell (px) | BBX in BDF | A cap-height (px) | Advance (px) |
| --- | --- | --- | ---: | ---: |
| Oxalis Monobit Single | 6×16 | `6 15 0 -3` | 10 | 6 |
| Oxalis Monobit Double | 12×16 | `12 15 0 -3` | 10 | 12 |

At 16 px, a Double character occupies exactly two columns of a Single bitmap grid (the app must allocate those two columns itself). Pixel glyphs are 1-bit; source truth is BDF and JSON. Double width extends contours derived from X11 Fixed 8×13 rather than horizontally doubling Single pixels.

Each face includes **370 glyphs**, including ASCII, accented Vietnamese precomposed letters, UI symbols, a selected private-use icon subset, and Powerline. **Not full Nerd Fonts Unicode coverage.** NFC is supported; unrestricted NFD combining mark shaping is not claimed.

## Key user-approved decisions

- Single from public-domain X11 Fixed `6x13/6x13B`; Double from `8x13/8x13B`.
- Capital A height 10 px; Regular and Bold use aligned baseline and cap height.
- Zero **0** contains a diagonal slash. In **Double Regular**, the final joining pixel is at `(x=3,y=9)` (moved left 1 px from the previous release at `(x=4,y=9)`), extending the down-left diagonal without a kink. In **Double Bold**, the slash is shifted **one additional row upward**, and both endpoints connect to the original zero outline. The outer outlines of both digits remain unchanged.
- Double Regular `1` was already optically moved right by 1 px and remains unchanged.
- Regular/Bold punctuation shares the same basic glyph; `. : ! ; ?` use compact 2×2 pixel dots where specified.
- Vietnamese circumflex/breve positions are consistent in simple/stacked combinations; dot below remains one pixel by deliberate choice.

## Directories

- `dist/`: TTF, WOFF2, BDF, PCF, per-glyph JSON, QA CSV/JSON.
- `atlas/`: native 1-bit PNG spritesheets plus exact Unicode rectangle maps.
- `previews/`: four-face specimen, complete 370-glyph inventory, zero before/after, interactive HTML.
- `examples/`: CSS and compact notes for bitmap usage.
- `metadata/`: Unicode repertoire inventory.
- `tests/`: independent automated checks and bitmap/TrueType-outline geometry parity.
- `legacy/`: prior Oxalis source assets needed for **rebuilding** the full 370-glyph collection.
- `sources/`: compact original public-domain X11 Fixed glyph references.

## Technical validation

All source glyphs fit the BBX; all faces have fixed advances and cap height. Independent BDF/JSON, TTF/WOFF2, Unicode, confusion-pair and 1-bit TrueType **geometry** checks pass, including all 1,380 glyph outlines.

**Important:** A passing programmatic suite is NOT a 100% human-readability certification. The exact pixel source is BDF, PCF, JSON, atlas. FreeType/OS/Web rendering of outline TTF at 16 px may shift portions of accents because of hinting/rasterizer settings. See `QA-REPORT.md` and `KNOWN-TRADEOFFS.md`. Test on the actual target display before external deployment.

## Build / rights

Run `python build_full.py`, then `python verify_release.py`, `python tests/independent_qa.py` and `python tests/outline_parity.py`. Python dependencies: `numpy`, `scipy`, `Pillow`, `fonttools`, `brotli`, `shapely`; PCF generation also needs `bdftopcf` (from xorg-x11-font-utils).

For rights and source status, read `LICENSE.txt` and `SOURCE-PROVENANCE.md`.

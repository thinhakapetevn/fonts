# Oxalis Monobit — Final engineering QA report v1.0.0

**Date:** 2026-11-19  |  **Owner:** Oxalis  |  **Engineering status:** Passed all specified automatic acceptance checks.

## Scope

- Four complete faces: Single Regular/Bold and Double Regular/Bold, **370 glyphs each** (1,480 glyphs total).
- Single BBX `6 15 0 -3`, Double BBX `12 15 0 -3`; cell height 16, cap A height 10; advance 6/12.
- Source 1-bit bitmap BDF and JSON, PCF binary; portable pixel outline TTF and WOFF2.

## Test results (independent checks)

| Test | Result | What it proves |
|---|---:|---|
| Primary engineering QA (`verify_release.py`) | **8,480 / 8,480** | Glyph dimensions, source-BDF parity, Unicode, distinctions, glyph-level and weight-level checks |
| Independent release QA (`tests/independent_qa.py`) | **3,476 / 3,476** | Independent bitmap and metrics/repertoire checks, paragraph adjacency within the tested character set |
| TTF outline raster-centre geometry (`tests/outline_parity.py`) | **1,380 / 1,380** | Every TTF polygon has the same black pixels at 16px grid cell centres as the source bitmap |
| TTF vs WOFF2 contour parity (`tests/final_regression.py`) | **1,380 / 1,380** | Every TTF glyph preserves the same geometry when stored as WOFF2 |
| Latest user correction regression | **PASS** | Compared with the immediately preceding V1.0 ZIP, ONLY Double Regular `0` changed: one pixel moved from (4,9) to (3,9) |

**Changes beyond glyph artwork:** The TrueType export pipeline now assigns correct side bearings for each glyph and unites pixel rectangles before outlining. These prevent the previous horizontally shifted punctuation and non-binary grayscale interpolation artifacts in the validated 16px rasterizer. Native bitmap formats remain authoritative.

## Explicit limits; no 100% human readability claim

A passed computer test suite does not establish a perfect font for every reader, device, antialiasing mode or operating system. Testing is complete for the *defined engineering checks*, not for a blinded human visual recognition study.

The outline TTF files have mathematically correct 16px pixel-centre geometry. Operating-system FreeType hinting may still shift a few extreme-height accent pixels on 16px font rasterization compared with the 1-bit BDF, so use BDF/PCF/atlas when pixel-exact appearance is required. Remaining intended tradeoffs are detailed in `KNOWN-TRADEOFFS.md`.

## Final V1.0 bitmap regression

Relative to the immediately preceding `Oxalis_Monobit_Single_Double_V1.0_FINAL.zip`, Double Regular `0` moves exactly one ink pixel left: old `(4,9)` is cleared and new `(3,9)` is set (0-based `(x,y)` coordinates). No other glyph artwork changes. The test snapshot in `tests/previous_v1_glyph_hashes.json` refers to an **earlier baseline** before the previous Double zero corrections, and thus shows both Double zero glyphs as changed relative to that older baseline.

- Single Regular: 0/370 changed glyphs.
- Single Bold: 0/370 changed glyphs.
- Double Regular: only U+0030 `0` changed, with exactly one pixel moved from `(x=4,y=9)` to `(x=3,y=9)`; total ink count unchanged.
- Double Bold: **0/370 changed** relative to the immediately preceding V1.0 ZIP; the previously approved slash position and joins are retained.
- All 4 bitonal sprite atlases independently regenerated and checked cell-by-cell against the canonical JSON glyph matrices (1,380 cells total).
- `tests/zero_diagonal_integrity.py` verifies these deltas, slash endpoints, stroke connectivity and unchanged full set of other glyphs using archived SHA256 snapshots.

## Reproduce

```bash
python build_full.py
python verify_release.py
python tests/independent_qa.py
python tests/outline_parity.py
python tests/final_regression.py
python tests/zero_diagonal_integrity.py
```

Review `previews/Oxalis_Monobit_v1.0_Zero_Before_After.png`, `previews/Oxalis_Monobit_4Faces_Review.png`, and `previews/Oxalis_Monobit_All370Glyphs.png`.

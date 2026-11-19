# Local revision — middot 2×2 (2026-11-19)

- **U+00B7 MIDDLE DOT** changed from a single 1×1 pixel to a 2×2 square in Single and Double, Regular and Bold.
- Atlas PNG cells updated; BDF/PCF/TTF/WOFF2 rebuilt; checksum manifest regenerated.
- No other glyph changed.

# V1.0 FINAL — final zero-slash continuity revision (2026-11-19)

- **Double Regular 0 (final optical correction):** move the single recently added pixel from (x=4, y=9) **left by 1 px** to (x=3, y=9). The slash now follows a consistent down-left pixel staircase and joins the lower-left oval without a kink. This is a relocation of one ink pixel (one pixel removed, one added), **not an increase in stroke weight**. No other glyph was modified relative to the most recent V1.0 archive.
- **Double Bold 0:** remains **unchanged** relative to the preceding V1.0 archive. Its earlier approved upward-slash and border-joining corrections are retained.
- **Single Regular / Single Bold:** no bitmap changes. All 1,379 non-target glyphs are byte-identical to the preceding V1.0 archive.
- Rebuilt BDF, PCF, TTF, WOFF2, JSON, all 1-bit atlas PNGs, preview sheets and checksum manifest from matching canonical bitmap sources.
- Regression checks verify every glyph against the archived earlier V1.0 baseline and assert the newly corrected Double Regular diagonal coordinates.
- Engineering and geometry QA re-run; human readability limits remain documented in KNOWN-TRADEOFFS.md.

# Changelog

## v1.0.0 — 2026-11-19
- Move ONLY the interior slash of `0` in Double Regular and Double Bold up one pixel, preserving Single and every other glyph.
- Correct TrueType left side bearings so glyphs render in their intended horizontal positions.
- Replace overlapping pixel-square contours with unioned, clean polygon boundaries; eliminate grayscale artifacting at 16ppem in the validated FreeType test.
- Independently verify 1,380 geometric outline shapes against 1-bit bitmap matrices, plus 8,480 release checks and 3,476 independent checks.
- Deliver complete bundle, genuine 1-bit atlases, examples, documentation, provenance and checksums.

## v0.10.x
- Normalize Vietnamese accent stacking, `i`/`ị`, regular/bold height and punctuation.
- Fixed 6×15 / 12×15 BBX with 16px line height and A height 10px.
- Correct Double Regular `1` optical centering and Single Regular `0` diagonal bridge.

# Local revision — icon sizing + UI hybrid (2026-11-19)

- Rebuilt the PUA icon set at the full 12×16 Double width; icons no longer render from Unifont/Noto Color Emoji fallbacks.
- Added 10 PUA icon glyphs (mic, mic-slash, volume-up/down/off, sun, moon, power, logout, reboot); 370 glyphs per canonical face.
- Added `ui/OxalisMonobitUI-*.ttf`: Single text advances plus Double icon advances for single-font menus such as fuzzel.
- Waybar now uses PUA Double icons for every icon; powermenu uses the UI hybrid (Single text, Double icons).

# Local revision — standard icon set (2026-11-19)

- Added 15 standard Unicode icons to all four faces: ⚡ U+26A1, ⏻ U+23FB, 🔋 U+1F50B, 🎤 U+1F3A4, 🔊 U+1F50A, 🔇 U+1F507, ⚠ U+26A0, ☀ U+2600, ☾ U+263E, ↪ U+21AA, ↻ U+21BB, ⌂ U+2302, 🔒 U+1F512, ▶ U+25B6, ▾ U+25BE.
- Each face now has 370 glyphs; atlas regenerated as 20×19 cells.
- BDF, PCF, TTF, WOFF2, per-glyph JSON, metadata and checksums rebuilt.
- Waybar uses the Double face for every icon; Single remains the text face.

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

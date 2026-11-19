# Quickstart — Oxalis Monobit v1.0

Install all four `.ttf` files from `dist/`. At 16px font-size, Single has 6px advance and Double has 12px. In web UI load `.woff2` instead:

```css
@font-face { font-family: "Oxalis Monobit Single"; src: url("../dist/OxalisMonobitSingle-Regular.woff2") format("woff2"); font-weight: 400; }
@font-face { font-family: "Oxalis Monobit Single"; src: url("../dist/OxalisMonobitSingle-Bold.woff2") format("woff2"); font-weight: 700; }
@font-face { font-family: "Oxalis Monobit Double"; src: url("../dist/OxalisMonobitDouble-Regular.woff2") format("woff2"); font-weight: 400; }
@font-face { font-family: "Oxalis Monobit Double"; src: url("../dist/OxalisMonobitDouble-Bold.woff2") format("woff2"); font-weight: 700; }
.bitmap { font-family: "Oxalis Monobit Single", monospace; font-size: 16px; line-height: 16px; letter-spacing: 0; font-synthesis: none; font-kerning: none; }
.double { font-family: "Oxalis Monobit Double", monospace; }
```

For absolute pixel fidelity, use `atlas/*-1bit.png` (nearest-neighbor, integer scale) or `dist/*.bdf` and `dist/*.pcf`; outline font rasterization varies across OS/engines. Double occupies two Single cells **only when app lays it out that way**; it does not magically display as double-width in every terminal.

Vietnamese text should be normalized to Unicode NFC. Test at exactly 1× on the real screen and disable fractional scaling/antialiasing in bitmap renderers.

Test final zero slash continuity and previous V1.0 glyph identity with `python tests/zero_diagonal_integrity.py`.

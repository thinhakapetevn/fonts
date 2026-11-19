# Source provenance

The four public-domain X11 Fixed bitmap references, mirrored by U8g2:

- https://github.com/olikraus/u8g2/blob/master/tools/font/bdf/6x13.bdf
- https://github.com/olikraus/u8g2/blob/master/tools/font/bdf/6x13B.bdf
- https://github.com/olikraus/u8g2/blob/master/tools/font/bdf/8x13.bdf
- https://github.com/olikraus/u8g2/blob/master/tools/font/bdf/8x13B.bdf

Source files contain `COPYRIGHT "Public domain font. Share and enjoy."`.
Source reference rows are embedded compactly in `sources/x11_compact.py`.

Oxalis-authored modifications include 6/12px fixed-grid families; cap-height,
spacing, diacritics, accents, slash-zero, Double re-proportioning, additional UI
symbols and glyph-testing/build infrastructure. Existing Oxalis PUA icon glyphs
in `legacy/` are retained as source material for the build.

Do not use the `Oxalis` ownership statement to misrepresent public-domain X11
bitmap pixels as newly exclusive property.

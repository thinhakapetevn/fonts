# Known trade-offs / scope

1. **Human readability** has not been measured with a blinded user study; 100% automated QA is not a 100% readability rating. Review 1× on actual tablet/desktop before declaring that goal reached.
2. **Single Bold 6px width** reserves a 1-pixel side bearing, reducing available black-pixel columns to five. This prevents adjacent text from merging but can soften Bold or make certain wide letters asymmetric. Avoid globally forcing more black pixels.
3. **Vietnamese stacked upper-case accents** at 15 usable rows require shortened capital bodies (8–9px) for some characters. This is a conscious exception to the normal A height of 10px. Dot-below intentionally stays one pixel.
4. **TrueType/WOFF2 renderer-dependent hinting:** geometric outline points are pixel-aligned and match all 1,380 source glyph bitmaps at pixel centres. A specific FreeType build can still move some top accents by ~1px at 16 ppem. BDF/PCF/JSON/1-bit atlases are the authoritative pixel sources.
5. **Double 12×16** is a redesigned/widened Fixed-8×13 style, not independently hand-drawn for every Unicode symbol. Some shapes retain old source pixel characteristics. Unicode PUA icon subset is not complete Nerd Fonts.
6. **Unicode NFC vs NFD:** composed Vietnamese characters are supported. Generic grapheme shaping with arbitrary combining marks is outside this bitmap subset.
7. **Raster display:** fractional zoom, grayscale antialiasing, CRT shaders or subpixel placement may decrease readability even with mathematically exact pixels.

Treat these as explicitly documented limitations rather than declaring perfect human readability.

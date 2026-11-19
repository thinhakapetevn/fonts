# Bitmap integration

A correct pixel-art renderer should draw from `dist/*-glyphs.json`, the BDF/PCF files or `atlas/*-1bit.png` directly. Never smooth when scaling; move by integer pixel coordinates; compose Vietnamese into NFC; allocate 1 grid cell for Single and 2 for Double.

The TTF/WOFF2 files are convenience exports for layout engines. They are true vectorized pixel outlines, not a guarantee about every font rasterizer's hinting. For deterministic app appearance use 1-bit atlas and the accompanying JSON index.

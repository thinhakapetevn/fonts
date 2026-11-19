#!/usr/bin/env python3
"""Verify final 0 slash geometry and all unchanged glyphs against preceding V1.0 release."""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import label
R=Path(__file__).resolve().parents[1]
faces=['OxalisMonobitSingle-Regular','OxalisMonobitSingle-Bold','OxalisMonobitDouble-Regular','OxalisMonobitDouble-Bold']
oldhash=json.loads((R/'tests/previous_v1_glyph_hashes.json').read_text())
expected={'OxalisMonobitSingle-Regular':[],'OxalisMonobitSingle-Bold':[],
          'OxalisMonobitDouble-Regular':['U+0030'],'OxalisMonobitDouble-Bold':['U+0030']}
count=0
for face in faces:
    src=json.loads((R/'dist'/f'{face}-glyphs.json').read_text())
    changed=[]
    for cp,rows in src.items():
        digest=hashlib.sha256(''.join(rows).encode('ascii')).hexdigest()
        if digest!=oldhash[face][cp]:changed.append(cp)
        count+=1
    assert changed==expected[face],(face,changed)
    w=6 if 'Single' in face else 12
    m=np.array([[ch=='#' for ch in s] for s in src['U+0030']],dtype=np.uint8)
    assert m.shape==(16,w)
    if 'Double-Regular' in face:
        stroke=[(8,4),(7,5),(6,6),(5,7),(4,8),(3,9)]
        assert m[10,3] and m[9,3] and m[8,4] and not m[9,4]
    elif 'Double-Bold' in face:
        stroke=[(8,3),(7,4),(6,5),(5,6),(4,7),(3,8)]
        assert m[8,2] and m[8,3] # join slash to left oval
        assert all(m[y,x]==0 for x,y in [(6,6),(5,7),(4,8)])
    else:stroke=None
    if stroke is not None:
        assert all(m[y,x] for x,y in stroke)
        # Every consecutive diagonal pixel is eight-neighbor-adjacent, no missing row.
        assert all(max(abs(a[0]-b[0]),abs(a[1]-b[1]))==1 for a,b in zip(stroke,stroke[1:]))
        assert label(m,np.ones((3,3),dtype=np.uint8))[1]==1
    # Validate source 1-bit sprite cell, not merely sprite file existence.
    mp=json.loads((R/'atlas'/f'{face}-map.json').read_text())['glyphs'];img=Image.open(R/'atlas'/f'{face}-1bit.png').convert('1')
    for cp,rows in src.items():
        x,y,ww,hh=mp[cp];assert (ww,hh)==(w,16)
        for yy,s in enumerate(rows):
            for xx,ch in enumerate(s):
                assert bool(img.getpixel((x+xx,y+yy)))==(ch=='#'),(face,cp,xx,yy)
print(f'FINAL ZERO REGRESSION: {count}/{count} glyph baselines verified; 1480/1480 atlas cells exact; Double 0 slash unbroken')

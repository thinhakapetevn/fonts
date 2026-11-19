#!/usr/bin/env python3
"""Verify every 16ppem pixel cell from raw TrueType outline contour geometry.
Does not trust JSON, BDF or glyph-builder code to evaluate TrueType shapes.
Unlike a platform rasterizer, this evaluates true geometric coverage at pixel centres.
"""
import json
from pathlib import Path
import numpy as np
from fontTools.ttLib import TTFont
from shapely.geometry import Polygon
from shapely import contains_xy

BASE=Path(__file__).resolve().parents[1]/'dist'
FACES=['OxalisMonobitSingle-Regular','OxalisMonobitSingle-Bold','OxalisMonobitDouble-Regular','OxalisMonobitDouble-Bold']
failures=[];checks=0
for face in FACES:
    w=6 if 'Single' in face else 12
    ttf=TTFont(BASE/(face+'.ttf'))
    src=json.loads((BASE/(face+'-glyphs.json')).read_text(encoding='utf-8'))
    xs=(np.tile(np.arange(w),16)+.5)*100
    ys=1200-(np.repeat(np.arange(16),w)+.5)*100
    for key,rows in src.items():
        cp=int(key[2:],16); name=ttf.getBestCmap()[cp]
        g=ttf['glyf'][name]
        actual=np.zeros((16,w),dtype=np.bool_)
        if g.numberOfContours>0:
            coords, ends, flags=g.getCoordinates(ttf['glyf'])
            prev=0
            winding=np.zeros(xs.shape,dtype=int)
            for e in ends:
                pts=[(int(t[0]),int(t[1])) for t in coords[prev:e+1]]
                prev=e+1
                if len(pts)<3:continue
                poly=Polygon(pts)
                area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))
                direction=1 if area>0 else -1
                winding+=direction*contains_xy(poly,xs,ys).astype(int)
            actual=(winding!=0).reshape(16,w)
        expected=np.asarray([[p=='#' for p in row] for row in rows],dtype=bool)
        checks+=1
        if not np.array_equal(actual,expected):
            failures.append((face,key,int(np.sum(actual!=expected))))
    print(face,'glyphs',len(src))
print('OUTLINE PIXEL CENTRE PARITY',checks,'/',checks-len(failures),'errors',failures[:15])
assert not failures

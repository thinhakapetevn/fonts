#!/usr/bin/env python3
"""Final self-contained release contract: four faces and special-case fixes."""
from pathlib import Path
from fontTools.ttLib import TTFont
import numpy as np,json,unicodedata
BASE=Path(__file__).resolve().parents[1]/'dist'
checks=0
for fam,w in [('Single',6),('Double',12)]:
 for wt in ['Regular','Bold']:
  stem=f'OxalisMonobit{fam}-{wt}'
  g={chr(int(k[2:],16)):np.array([[c=='#' for c in row] for row in rows],dtype=bool) for k,rows in json.loads((BASE/(stem+'-glyphs.json')).read_text()).items()}
  ttf=TTFont(BASE/(stem+'.ttf'))
  woff=TTFont(BASE/(stem+'.woff2'))
  assert set(ttf.getBestCmap())==set(woff.getBestCmap())==set(map(ord,g))
  assert len(g)==345
  assert ttf['hhea'].ascent==1200 and ttf['hhea'].descent==-400
  assert ttf['OS/2'].sCapHeight==1000
  assert all(advance==w*100 for advance,lsb in ttf['hmtx'].metrics.values())
  assert 'Version 1.0.0' in ''.join(x.toUnicode() for x in ttf['name'].names if x.nameID==5)
  assert np.array_equal(np.flatnonzero(g['A'].any(axis=1)),np.arange(2,12))
  assert g['0'].shape==(16,w) and not g['0'][15].any()
  assert np.sum(g['0']!=g['O'])>=3
  if fam=='Double':
   if wt=='Regular':
    assert all(g['0'][y,x] for x,y in [(8,4),(7,5),(6,6),(5,7),(4,8),(3,9)])
    assert g['0'][10,3] and not g['0'][9,4], 'slash must align down-left into bottom oval'
   else:
    assert all(g['0'][y,x] for x,y in [(8,3),(7,4),(6,5),(5,6),(4,7),(3,8)])
    assert g['0'][8,2], 'slash not anchored to left oval'
    assert all(not g['0'][y,x] for x,y in [(6,6),(5,7),(4,8)]), 'old slash fragments remained'
  else:
   assert all(g['0'][y,x] for x,y in [(3,6),(2,7)])
  for ch in g:
   nm=ttf.getBestCmap()[ord(ch)]
   a=ttf['glyf'][nm];b=woff['glyf'][woff.getBestCmap()[ord(ch)]]
   assert a.numberOfContours==b.numberOfContours
   if a.numberOfContours>0:
    c1,e1,_=a.getCoordinates(ttf['glyf']);c2,e2,_=b.getCoordinates(woff['glyf'])
    assert list(e1)==list(e2) and list(c1)==list(c2)
   checks+=1
print('FINAL RELEASE CONTRACT:',checks,'/',checks,'TrueType/WOFF2 glyph matches; 4 faces; slash continuity passed')

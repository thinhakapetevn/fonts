#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import json,unicodedata,math
import numpy as np
from scipy.ndimage import label
from fontTools.ttLib import TTFont
D=Path(__file__).resolve().parents[1]/'dist'
F={
'oxalis-single-regular':('OxalisMonobitSingle-Regular',6),
'oxalis-single-bold':('OxalisMonobitSingle-Bold',6),
'oxalis-double-regular':('OxalisMonobitDouble-Regular',12),
'oxalis-double-bold':('OxalisMonobitDouble-Bold',12)
}
corpus=['Son Truong 100%','Nguoi Nguon o rung','Chào mừng đến Tú Làn', 'Người Nguồn ở rừng','Tất cả ký tự phải dễ đọc','0123456789 ABCDEFGHIJKLM','0O 1Il 5S 8B 2Z dđ DĐ']
alldata={};errors=[];checks=0;results={}
def check(cond,what):
 global checks
 checks+=1
 if not cond: errors.append(what)
for face,(fn,w) in F.items():
 dataset=json.loads((D/(fn+'-glyphs.json')).read_text())
 g={chr(int(k[2:],16)):np.array([[c=='#' for c in row] for row in rows],dtype=np.uint8) for k,rows in dataset.items()}
 alldata[face]=g
 fn_ttf=D/(fn+'.ttf');tf=TTFont(fn_ttf);wv=TTFont(D/(fn+'.woff2'))
 check(len(g)==370,f'{face}: expected 370 glyphs')
 check(len(tf.getBestCmap())==370,f'{face}: TTF glyph coverage')
 check(len(wv.getBestCmap())==370,f'{face}: WOFF2 glyph coverage')
 check(set(map(ord,g))==set(tf.getBestCmap()),f'{face}: cmap mismatch')
 check(set(map(ord,g))==set(wv.getBestCmap()),f'{face}: woff2 cmap mismatch')
 check(all(a==w*100 for a,_ in tf['hmtx'].metrics.values()),f'{face}: monospace')
 check(all(a==w*100 for a,_ in wv['hmtx'].metrics.values()),f'{face}: woff2 monospace')
 check(tf['hhea'].ascent==1200 and tf['hhea'].descent==-400,f'{face}: 12/4 vertical metrics')
 check(tf['OS/2'].sCapHeight==1000,f'{face}: cap height metadata')
 check(tf['OS/2'].sxHeight==600,f'{face}: x-height metadata')
 check((D/(fn+'.bdf')).read_text().find(f'FONTBOUNDINGBOX {w} 15 0 -3')!=-1,f'{face}: BDF BBX')
 check(all(mat.shape==(16,w) for mat in g.values()),f'{face}: bitmap shape')
 check(all(not mat[15].any() for mat in g.values()),f'{face}: 15-row usable BBX')
 for cp,mat in g.items():
  check(not mat[15].any(),f'{face}: glyph U+{ord(cp):04X} spills row15')
  check(np.any(mat) or cp in (' ','\u00a0'),f'{face}: missing ink U+{ord(cp):04X}')
 check(set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789').issubset(g),f'{face}: ASCII letters and digits')
 for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
  check(np.flatnonzero(g[c].any(axis=1)).tolist()==list(range(2,12)),f'{face}: cap height 10 {c}')
 # Classical x-height letters at 6 px shared by R/B, Single/Double.
 for c in 'aemnosuxz':
  check(np.flatnonzero(g[c].any(axis=1)).tolist()==list(range(6,12)),f'{face}: x-height6 {c}')
 # No two Latin letters (including Vietnamese) render as the same bitmap.
 dups=defaultdict(list)
 for c,mat in g.items():
  if c.isalpha():dups[mat.tobytes()].append(c)
 baddups=[lst for lst in dups.values() if len(lst)>1]
 check(not baddups,f'{face}: unintended alphabetic duplicate {baddups[:4]}')
 # no collisions between 232 typographic ASCII and Vietnamese chars; box
 # drawing intentionally has a different contract.
 chars=[c for c in g if c.isalpha() or c.isdigit() or 33<=ord(c)<=126]
 edge_right=[c for c in chars if g[c][:,w-1].any()]
 edge_left=[c for c in chars if g[c][:,0].any()]
 coll=[a+b for a in edge_right for b in edge_left if np.any(g[a][:,-1]&g[b][:,0])]
 check(not coll,f'{face}: touching typographic pairs {coll[:10]}')
 # Letter/symbol known cases: distinguish even when little font real estate
 for c0,c1 in [('0','O'),('1','I'),('1','l'),('5','S'),('8','B'),('2','Z'),('d','đ'),('D','Đ'),('ơ','o'),('ư','u'),('y','ỵ'),('ẳ','ẵ'),('â','ấ'),('á','à'),('ả','ã'),('í','ì')]:
  check(not np.array_equal(g[c0],g[c1]),f'{face}: indistinguishable {c0}/{c1}')
 # Canonical hat and breve rows must match with or without a tone.
 for c0,c1 in [('â','ấ'),('ê','ế'),('ô','ố'),('ă','ắ'),('Â','Ấ'),('Ê','Ế'),('Ô','Ố'),('Ă','Ắ')]:
  if c0.islower():
   a=g[c0][3:5].copy();b=g[c1][3:5].copy()
   check(np.array_equal(a,b),f'{face}: inconsistent shape {c0}/{c1}')
 # i-accent should not alias i or each other
 for p,q in [('i','í'),('i','ì'),('i','ỉ'),('i','ĩ'),('í','ì'),('ì','ĩ')]:
  check(not np.array_equal(g[p],g[q]),f'{face}: i-dot replacement {p}/{q}')
 # dot remains an extra single pixel for y/ỵ, u/ụ
 for p,q in [('y','ỵ'),('u','ụ')]:
  check(int((g[p]!=g[q]).sum())==1,f'{face}: 1 pixel dot below {p}/{q}')
 # basic ASCII single-component strokes, excluding separated i/j dots, diacritics
 for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghklmnopqrstuvwxz':
  check(label(g[c],np.ones((3,3),dtype=int))[1]==1,f'{face}: broken glyph stroke {c}')
 results[face]={'glyphs':len(g),'alphabetic_aliases':len(baddups),'typographic_edge_touching_pairs':len(coll),'right_edge_typographic_glyphs':len(edge_right), 'codepoints_checked':len(g),'notes':[]}
# Cross-weight same occupied vertical rows for A-Z/0-9/lowercase plain glyphs.
for fam in ['single','double']:
 r=alldata[f'oxalis-{fam}-regular']
 b=alldata[f'oxalis-{fam}-bold']
 for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789':
  ra=np.flatnonzero(r[c].any(axis=1))
  ba=np.flatnonzero(b[c].any(axis=1))
  check(np.array_equal(ra,ba),f'{fam} R/B vertical inconsistency {c}: {ra.tolist()} vs {ba.tolist()}')

report={'checks':checks,'failed':len(errors),'errors':errors,'results':results}
(D.parent/'tests'/'independent_qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'checks':checks,'failed':len(errors),'errors':errors[:30],'results':results},ensure_ascii=False,indent=2))
if errors:raise SystemExit(1)

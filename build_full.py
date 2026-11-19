#!/usr/bin/env python3
"""Oxalis Monobit Single and Double — full Unicode v1.0 final engineering build.

Sources: X11 Fixed 6x13/6x13B and 8x13/8x13B (public domain),
prior Oxalis Monobit Unicode/PUA catalogue (previous project artifacts).
Review version, not human-validated. All output uses true 1-bit 6x15/12x15 BBX.
"""
from __future__ import annotations
import os, sys, json, copy, math, unicodedata, re
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import label
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'sources'))
from x11_compact import source_ascii, source_vietnamese
OLD=HERE/'legacy'
OUT=HERE/'dist';OUT.mkdir(parents=True,exist_ok=True)
FACES={'single_r':(6,'Regular','6r'), 'single_b':(6,'Bold','6b'),
       'double_r':(12,'Regular','8r'),'double_b':(12,'Bold','8b')}

old={}
for face,(w,weight,_) in FACES.items():
   typ='Monobit' if w==6 else 'Double'
   pref='OxalisMonobit' if w==6 else 'OxalisMonobitDouble'
   file=OLD/typ/f'{pref}-{weight}-glyphs.json'
   old[face]={chr(int(k[2:],16)):np.array([[v=='#' for v in row] for row in rows],dtype=np.uint8)
              for k,rows in json.load(open(file,encoding='utf8')).items()}
ORDER=list(old['single_r'])
assert len(ORDER)==370 and all(set(x)==set(ORDER) for x in old.values())
VI=''.join(ch for ch in ORDER if ord(ch)>126 and 'LATIN' in unicodedata.name(ch,''))

src={}
for face,(w,weight,key) in FACES.items():
    src[face]=source_ascii(key)
    if weight=='Regular':
        for ch,byt in source_vietnamese(key,VI).items():src[face][ch]=byt

metrics_by_character={}
source_by_character={}

def from_bdf_bytes(b,source_width):
    assert len(b)==13
    return np.array([[(v>>(7-x))&1 for x in range(source_width)] for v in b],dtype=np.uint8)

def trim_vertical(m):
    ys=np.flatnonzero(m.any(axis=1));
    return m[ys[0]:ys[-1]+1,:].copy() if len(ys) else m[:0,:].copy()

def stable_insert_index(a):
    """Insert inside a stable vertical stem, minimizing changes to joins/curves.
    Never discard a source row. Prefer repeated inner-stem rows."""
    n=len(a)
    choices=range(1,max(2,n-1))
    return min(choices,key=lambda i:(int(np.count_nonzero(a[i]!=a[i-1]))+int(np.count_nonzero(a[i]!=a[min(i+1,n-1)])),
                            abs(i-(n-1)*.58), -int(np.count_nonzero(a[i]))))

def extend_rows(a, target):
    a=a.copy()
    while len(a)<target:
        i=stable_insert_index(a)
        a=np.insert(a,i,a[i],axis=0)
    return a

def reduce_rows(a,target):
    # Controlled reduction of duplicate straight-stem rows only. This function
    # never drops a structurally distinct pixel row (important prior regression).
    a=a.copy()
    while len(a)>target:
        candidates=[i for i in range(1,len(a)-1) if np.array_equal(a[i],a[i-1]) or np.array_equal(a[i],a[i+1])]
        if not candidates:
            # Do not destroy glyph skeleton: retain original height, record a
            # deliberate exception for the test report.
            return a
        i=min(candidates,key=lambda q:abs(q-len(a)*.6))
        a=np.delete(a,i,axis=0)
    return a

def place_y(m, y_bottom=11, target_height=None):
    a=trim_vertical(m)
    if not len(a):return np.zeros((16,m.shape[1]),dtype=np.uint8)
    if target_height is not None:
        if len(a)<target_height:a=extend_rows(a,target_height)
        elif len(a)>target_height:a=reduce_rows(a,target_height)
    out=np.zeros((16,m.shape[1]),dtype=np.uint8)
    start=y_bottom-len(a)+1
    # Clip only as a last resort; exceptions listed in QA; source data usually fits
    assert 0<=start and y_bottom<=14,(start,y_bottom,len(a))
    out[start:y_bottom+1]=a
    return out

def widen8(m):
    """Move strokes horizontally, DO NOT thicken verticals. 8 -> 12 canvas.
    Distinct X11 8x13 reference is used for Regular/Bold, not Single x2.
    Source adjacent horizontal pixels remain connected; center counters stay open.
    """
    assert m.shape[1]==8
    dst=np.zeros((m.shape[0],12),dtype=np.uint8)
    xp=[1,2,4,5,6,7,9,10]
    for y in range(m.shape[0]):
        for x in range(8):
            if m[y,x]:dst[y,xp[x]]=1
        # Only fill existing horizontal source strokes, not blank interior counters
        active=np.flatnonzero(m[y])
        for x in active:
            if x<7 and m[y,x+1]:dst[y,xp[x]:xp[x+1]+1]=1
    # Diagonal gaps from skipped columns: add a minimal 1px bridge only when
    # old 8-connected component existed and new pair is >1 pixel apart.
    for y in range(m.shape[0]-1):
        for x in range(8):
            if not m[y,x]:continue
            for xx in (x-1,x+1):
                if not (0<=xx<8 and m[y+1,xx]):continue
                a,b=xp[x],xp[xx]
                if abs(a-b)==2:
                    z=(a+b)//2
                    # Add 1 pixel at the row with smaller local population;
                    # preserves diagonal silhouette rather than building a block.
                    ay=int(dst[y].sum());by=int(dst[y+1].sum())
                    dst[y if ay<by else y+1,z]=1
    return dst

# Source X11 width/height classification. For Double x-height 7 px matches
# 8x13B's native reading size; Single remains x-height 6 px, matching 6x13.
CAPH=10; XHEIGHT_SINGLE=6;XHEIGHT_DOUBLE=7
PUNCT_KEEP_THIN='!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
DEFAULT_ASCII={}

# A bit of hand-specified numeral simplification after X11-based transform.
# A simple central dot (not slash) is the single intentional interior marker.
def zero_center_dot(m,width):
    out=m.copy()
    yy=7
    x=2 if width==6 else 6
    if out[yy,x]:
        # prefer position to right of center with room
        for try_x in (x-1,x+1,x-2,x+2):
            if 0<try_x<width-1 and not out[yy,try_x]:x=try_x;break
    out[yy,x]=1
    return out

def punctuation(m,ch,w):
    out=np.zeros((16,w),dtype=np.uint8)
    center=(w-1)//2
    def dot(x,y):out[y,x]=1
    if ch=='.':dot(center,11)
    elif ch==',':dot(center,11);dot(center-1,12)
    elif ch==':':dot(center,7);dot(center,11)
    elif ch==';':dot(center,7);dot(center,11);dot(center-1,12)
    elif ch=='!':
        for y in range(3,10):dot(center,y)
        dot(center,11)
    elif ch=='|':
        for y in range(3,12):dot(center,y)
    elif ch=='-':
        for x in (range(1,5) if w==6 else range(3,9)):dot(x,8)
    elif ch=='_':
        for x in (range(1,5) if w==6 else range(2,10)):dot(x,13)
    elif ch=='%':
        # the Double proportion sign uses familiar X11 8px silhouette, but with
        # 1px diagonal, two little circles; keep same in both weights.
        if w==6:
            pts=[(0,3),(1,3),(0,4),(1,4),(4,4),(3,5),(2,6),(1,7),(0,8),(3,10),(4,10),(3,11),(4,11)]
        else:
            pts=[(2,3),(3,3),(2,4),(3,4),(9,3),(8,4),(7,5),(6,6),(5,7),(4,8),(3,9),(2,10),(8,10),(9,10),(8,11),(9,11)]
        for x,y in pts:dot(x,y)
    else:
        # Retain the proven X11 Regular punctuation shape in both weights.
        # Double punctuation is not globally stretched across 12px.
        a=trim_vertical(m)
        yy=11-len(a)+1
        assert yy>=0
        out[yy:yy+len(a)]=a
    return out

def transform_ascii(ch,face):
    w,weight,key=FACES[face]; sw=6 if w==6 else 8
    source=from_bdf_bytes(src[face][ch],sw)
    if w==12:
        source=source if ch in PUNCT_KEEP_THIN else widen8(source)
        if ch in PUNCT_KEEP_THIN:
            # map 8px punctuation centered to a 12px canvas, NOT 2x expansion.
            z=np.zeros((13,12),dtype=np.uint8);z[:,2:10]=source;source=z
    if ch in PUNCT_KEEP_THIN:
        return punctuation(source,ch,w)
    if ch.isupper() or ch.isdigit():
        o=place_y(source,11,10)
        if ch=='0':o=zero_center_dot(o,w)
    elif ch=='j':
        # Separate i/j dot and descender; normalize to shared baseline by source shift.
        o=np.zeros((16,w),dtype=np.uint8)
        o[:13]=source
        o=np.roll(o,1,axis=0)
        assert not o[15].any()
    elif ch in 'gpqy':
        o=place_y(source,13,8)
    elif ch in 'bdfhklt':
        o=place_y(source,11,10)
    elif ch in 'i':
        o=np.zeros((16,w),dtype=np.uint8)
        o[1:14]=source
    else:
        o=place_y(source,11,6)
    return o

G={}
for face,(width,weight,key) in FACES.items():
    g={}
    for ch in ORDER:
        if ch in src[face] and 32<=ord(ch)<=126:
            g[ch]=transform_ascii(ch,face)
        else:
            # X11 glyph selected below, or retained legacy icons/symbols.
            g[ch]=old[face][ch].copy()
    G[face]=g

# Explicit glyph overrides for a few fragile structures in 6px Bold.
# The objective is recognition, not maximal stroke mass.
for face in ('single_b',):
    gg=G[face]
    for ch in 'MWm':
        # X11 Fixed Bold is extremely black at 6 columns. Preserve source
        # identity without turning open counters into solid interior blobs.
        base=G['single_r'][ch].copy()
        if ch in 'MW':
            for y in range(2,5):
                for x in (1,4):
                    if base[y,x] and base[y,max(0,x-1)]:base[y,x]=1
        gg[ch]=base

# Latin Vietnamese diacritic compositor. Regular uses carefully drawn X11 base
# contours; Bold uses separate X11 Bold letter base, not fake-bold Regular.
TONE_NAME={'\u0301':'acute','\u0300':'grave','\u0309':'hook','\u0303':'tilde','\u0323':'dot'}
SHAPE_NAME={'\u0302':'circumflex','\u0306':'breve','\u031b':'horn','\u0327':'cedilla'}

# Accent marks are deliberately thin for both weights, and must be visually
# distinct. The below uses a canonical geometry shared by all vowels.
def overlay_mark(o,kind,w,isupper,stacked=False):
    out=o.copy()
    x=(2 if w==6 else 6)
    # y0..2 for uppercase; y1..4 for lowercase. Uppercase double tone has
    # one extra tier, so base starts row4.
    top=0 if isupper else 1
    pts=[]
    if kind=='acute':pts=[(x+1,top),(x,top+1)]
    elif kind=='grave':pts=[(x-1,top),(x,top+1)]
    elif kind=='hook':pts=[(x-1,top),(x,top),(x,top+1),(x-1,top+2)]
    elif kind=='tilde':pts=[(x-1,top),(x,top),(x,top+1),(x+1,top+1)]
    elif kind=='dot':
        ys=np.flatnonzero(out.any(axis=1));last=int(max(ys))
        yy=13 if last<=11 else 14
        xx=x
        if out[yy,xx]:
            for altx in (x-2,x+2,x-1,x+1):
                if 0<=altx<w and not out[yy,altx]:xx=altx;break
        pts=[(xx,yy)]
    elif kind=='circumflex':pts=[(x-1,top+1),(x,top),(x+1,top+1)]
    elif kind=='breve':pts=[(x-1,top),(x,top+1),(x+1,top)]
    elif kind=='cedilla':pts=[(x,13),(x-1,14)]
    elif kind=='horn':
        # Distinct upper-right hook, separated from existing bowl; never
        # touch adjacent glyph. Two extra pixels minimum even in Single Bold.
        r=w-2
        pts=[(r,1 if isupper else 4),(r-1,1 if isupper else 4),
             (r,2 if isupper else 5)]
    for a,b in pts:
        if 0<=a<w and 0<=b<15:out[b,a]=1
    return out

def reduce_body_for_marks(body,w,isupper,ntop):
    if not isupper or ntop==0:return body.copy()
    # For accented uppercase, make room for a small detached mark; remove only
    # repeated straight-stem rows, never arbitrary distinct stroke rows.
    active=trim_vertical(body)
    target=9 if ntop==1 else 8
    short=reduce_rows(active,target)
    if len(short)>target:
        # For Double capital E with a stacked accent, draw an 8-row E by
        # retaining top / cross / bottom bars and shortening only stems.
        # No unique junctions are silently discarded.
        if w==12 and len(short)==9:
            barcounts=[int(r.sum()) for r in short]
            keepbar=set(sorted(range(len(short)),key=lambda i:barcounts[i],reverse=True)[:3])
            removals=[i for i in range(1,len(short)-1) if i not in keepbar]
            if removals:
                i=min(removals,key=lambda q:(barcounts[q],abs(q-5)))
                short=np.delete(short,i,axis=0)
        if len(short)>target:raise RuntimeError('Cannot shorten accented body without losing shape')
    dest=np.zeros_like(body)
    dest[12-len(short):12]=short
    return dest

def compose_latin(ch,face):
    w,weight,key=FACES[face]
    if ch in ('đ','Đ'):
        base=G[face]['d' if ch=='đ' else 'D'].copy()
        # Cross the upper ascender well above d's bowl. 3–6 distinct
        # pixels compared with d/D; keep mark inside cell.
        y=4 if ch=='đ' else 6
        xs=(range(1,5) if w==6 and ch=='đ' else
            range(0,5) if w==6 else
            range(3,10) if ch=='đ' else range(1,8))
        for x in xs:base[y,x]=1
        return base
    decom=unicodedata.normalize('NFD',ch)
    if len(decom)<=1:return None
    root=decom[0]
    if root not in G[face]:return None
    isupper=root.isupper()
    shape=[SHAPE_NAME[k] for k in decom[1:] if k in SHAPE_NAME]
    tone=[TONE_NAME[k] for k in decom[1:] if k in TONE_NAME]
    if not shape and not tone:return None
    n_top=len([a for a in shape+tone if a not in ('dot','cedilla','horn')])
    body=reduce_body_for_marks(G[face][root],w,isupper,n_top)
    # Add markers with tier-safe positions; designed independently of Bold.
    o=body.copy()
    for kind in shape:
        if kind in ('horn','cedilla'):o=overlay_mark(o,kind,w,isupper)
        elif kind in ('circumflex','breve'):
            if tone and tone[0]!='dot':
                # stacked pair: shape at y2..3 (cap) or y3..4 (lowercase)
                top=2 if isupper else 3
                x=2 if w==6 else 6
                coords=([(x-1,top+1),(x,top),(x+1,top+1)] if kind=='circumflex'
                        else [(x-1,top),(x,top+1),(x+1,top)])
                for x0,y0 in coords:
                    if 0<=x0<w and 0<=y0<15:o[y0,x0]=1
            else:o=overlay_mark(o,kind,w,isupper)
    for kind in tone:
        o=overlay_mark(o,kind,w,isupper)
    return o

# Vietnamese: generate regular and bold forms using the same algorithm and
# base source contours (the ordinary precomposed X11 forms are retained as
# references for morphology checks and visual inspection).
for face in FACES:
    for ch in VI:
        new=compose_latin(ch,face)
        if new is not None:G[face][ch]=new
        elif ch in src[face]:
            sw=6 if face.startswith('single') else 8
            base=from_bdf_bytes(src[face][ch],sw)
            if face.startswith('double'):base=widen8(base)
            gg=np.zeros((16,FACES[face][0]),dtype=np.uint8)
            gg[1:14]=base
            G[face][ch]=gg

# Box drawing glyphs in the older 16-row atlas touched row 15; remap that
# last row into the final legal BBX row instead of clipping a terminal stroke.
for face in FACES:
    for ch,m in G[face].items():
        if np.any(m[15]):
            m[14] |= m[15]; m[15]=0

# Extra Unicode and Nerd-style PUA icons: inherited from previous Oxalis font
# because X11 Fixed does not contain the private-use icon mappings.
# Keep no more than the requested glyph repertoire, not every X11 character.

# In the 6px Bold face, the capital Đ must remain recognizable beside D.
# A one-pixel left leading corner makes the crossing stroke visible at 1x
# without cutting the D's right contour or thickening the whole glyph.
if int(np.sum(G['single_b']['D']!=G['single_b']['Đ']))<3:
    G['single_b']['Đ'][5,0]=1

# Later structural refinement: preserve dash semantics; compact glyphs do not
# benefit from visually identical hyphen and en dash. Zero extra decoration.
for face,(w,_,_) in FACES.items():
    for ch,lo,hi in [('–',0 if w==6 else 2,4 if w==6 else 9),
                     ('—',0,w-1)]:
        m=np.zeros((16,w),dtype=np.uint8)
        m[8,lo:hi+1]=1
        G[face][ch]=m

# Bridge accidental corner-only contacts in 12px Bold letter arches/hooks.
# The 8px Fixed skeleton remains unchanged for all other glyphs; no bulk thickening.
def optical_bridge(m):
    m=m.copy()
    cross=np.array([[0,1,0],[1,1,1],[0,1,0]],dtype=np.uint8)
    for _ in range(3):
        labels,n=label(m,cross)
        if n<=1:break
        proposals=[]
        for y in range(2,13):
            for x in range(1,m.shape[1]-1):
                if m[y,x]:continue
                comps=set()
                for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
                    yy=y+dy;xx=x+dx
                    if 0<=yy<16 and 0<=xx<m.shape[1] and labels[yy,xx]:comps.add(int(labels[yy,xx]))
                if len(comps)>=2:proposals.append((y,x))
        if not proposals:break
        # Prefer joins near ascender shoulder, not lower counter edges.
        y,x=min(proposals,key=lambda c:(abs(c[0]-6),abs(c[1]-(m.shape[1]-1)/2)))
        m[y,x]=1
    return m
for face in ('double_r','double_b'):
    for ch in ('n','ơ','ư'):
        G[face][ch]=optical_bridge(G[face][ch])

# R0.10.1: Preserve the original X11 6x13B morphology.
# In v0.10 an automated operation moved every right-edge pixel inward,
# destroying some bowls and changing recognizability. Do not repeat.
# This leaves a documented adjacent-character collision risk in Single Bold.

# Metric assurance and small visual invariants
for face,(w,weight,key) in FACES.items():
    for ch,m in G[face].items():
        assert m.shape==(16,w),(face,ch,m.shape)
        assert not np.any(m[15]),(face,ch,'row 15 nonempty')
    assert all(np.any(G[face]['A'][y]) for y in range(2,12))
    assert not any(np.any(G[face]['A'][y]) for y in (0,1,12,13,14,15))
    assert np.sum(G[face]['A'].any(axis=1))==10
    assert np.sum(G[face]['0'])>0

# Numeral & basic punctuation identity is consistent: numbers bold independently
# drawn while typographic marks are identical in both weights.
for family in ['single','double']:
    r=G[family+'_r'];b=G[family+'_b']
    for ch in PUNCT_KEEP_THIN:
        b[ch]=r[ch].copy()

# Explicitly ensure 1px dot in the zero's counter and distinct from uppercase O.
for face in FACES:
    o=G[face]['O'];z=G[face]['0']
    if np.array_equal(o,z):z[7,2 if face.startswith('single') else 6]=1

# Targeted updates approved across late 2026 review rounds.
# (a) The zero's main exterior contour stays X11 Fixed-derived; interior
#     distinguishes it from O with a forward slash instead of a centre dot.
# (b) In Single Regular, the exact NEW change is one bridging pixel at
#     (x=2,y=7) between diagonal endpoints (3,6) and (1,8).
# (c) Double Regular '1' moves by +1 px to the optical middle of its 12px cell.
# (d) Punctuation marks use 2x2 dots independent of Regular/Bold, as approved.
for face,(fw,_,_) in FACES.items():
    zero=G[face]['0'].copy()
    zero[7,2 if fw==6 else 6]=0  # remove old centre dot
    if face=='single_r':
        # Before the user's final instruction: endpoints only (3,6),(1,8).
        # One NEW connecting pixel closes their visual diagonal gap.
        slash=[(3,6),(2,7),(1,8)]
    elif fw==6:
        slash=[(3,6),(2,7)]
    elif face=='double_r':
        # V1.0 FINAL optical correction: continue the slash diagonal one step
        # down-left instead of putting its closing pixel directly underneath.
        # Move sole added pixel (4,9) -> (3,9) to align (4,8) -> (3,9).
        # Bottom-left oval at (3,10) completes a single continuous stroke.
        slash=[(8,4),(7,5),(6,6),(5,7),(4,8),(3,9)]
    else:
        # Double Bold: move the diagonal body one row UP from the previous
        # path, while anchoring BOTH endpoints to the existing oval contour.
        # Start: upper-right contour at (8,3); end: left contour via (3,8).
        # Rebuild on the original zero before applying the new path, rather
        # than retaining old interior diagonal fragments.
        for x,y in [(6,6),(5,7),(4,8)]:
            zero[y,x]=0
        slash=[(8,3),(7,4),(6,5),(5,6),(4,7),(3,8)]
    for x,y in slash:
        zero[y,x]=1
    G[face]['0']=zero

one=G['double_r']['1'].copy()
assert not one[:,11].any(),'Cannot shift Double Regular 1 right within 12px cell'
centroid_before=float((one * np.arange(12)[None,:]).sum() / one.sum())
G['double_r']['1'][:,1:]=one[:,:-1]
G['double_r']['1'][:,0]=0
assert abs(float((G['double_r']['1']*np.arange(12)[None,:]).sum()/G['double_r']['1'].sum())-centroid_before-1)<1e-6

# 2x2 punctuation dot is exactly the same in both weights.
for fam in ('single','double'):
    w=FACES[fam+'_r'][0]; xs=[(w//2)-1,w//2]
    for face in (fam+'_r',fam+'_b'):
        for ch in '.:;!?':
            m=G[face][ch].copy()
            # Replace the previous dot portion; retain question-mark upper body.
            if ch=='?':
                m[10:14,:]=0
            else:
                m[:,:]=0
            def square(y):
                for yy in (y,y+1):
                    for xx in xs:m[yy,xx]=1
            if ch in '.:;!?':square(10)
            if ch in ':;':square(5)
            if ch==';':m[12,xs[0]]=1
            if ch=='!':
                for yy in range(2,9):m[yy,w//2]=1
            G[face][ch]=m
    for ch in '.:;!?':
        G[fam+'_b'][ch]=G[fam+'_r'][ch].copy()

# Normalize the height of native X11 Bold dots and of the five 8x13B
# lowercase shapes that cannot be shortened by removing duplicate rows.
# i/j: keep the top dot as one horizontal pixel row at y4 (Regular's height),
# not a two-row block extending a pixel taller than Regular.
for _face in ('single_b','double_b'):
    for _ch in 'ij':
        G[_face][_ch][3,:]=0

# These are the ONLY body glyphs where the original 8x13B has 7/9 unique
# rows at x-height/descender and Regular is 6/8. Merge the most similar
# neighboring stem rows (union), preserving all original occupied columns.
def _squash_ink_rows(m,target,bottom):
    a=trim_vertical(m)
    while len(a)>target:
        choices=[]
        for i in range(1,len(a)-2):
            # avoid changing the cap and foot profile; minimize amount of
            # new ink through the union of two original neighboring rows.
            dist=int(np.count_nonzero(a[i]!=a[i+1]))
            choices.append((dist,abs((i+.5)-len(a)*.56),i))
        assert choices
        j=min(choices)[-1]
        a[j]=a[j]|a[j+1]
        a=np.delete(a,j+1,axis=0)
    z=np.zeros_like(m);z[bottom-len(a)+1:bottom+1]=a
    return z
for _ch in 'acgsz':
    _height=8 if _ch=='g' else 6
    _bottom=13 if _ch=='g' else 11
    G['double_b'][_ch]=_squash_ink_rows(G['double_b'][_ch],_height,_bottom)

# A shared Vietnamese bitmap diacritic system.  In particular, the cap / breve
# are at the SAME pixel rows for a base (â/ấ, ă/ắ, ê/ế, ô/ố).  A tone is
# *added*, not a reason to shift the original shape vertically.  This fixes
# the prior high-floating marks and shape-mismatch regression.
def _vn_layer(m,face,ch):
    dec=unicodedata.normalize('NFD',ch)
    if len(dec)<2:return None
    root=dec[0]
    if root not in G[face]:return None
    marks=dec[1:]
    tones={"\u0300":'grave',"\u0301":'acute',"\u0309":'hook',"\u0303":'tilde',"\u0323":'dot'}
    shapes={"\u0302":'circumflex',"\u0306":'breve',"\u031b":'horn'}
    tone=next((tones[x] for x in marks if x in tones),None)
    shape=next((shapes[x] for x in marks if x in shapes),None)
    if not tone and not shape:return None
    w=FACES[face][0]; upper=root.isupper();cx=2 if w==6 else 6
    # All lowercase Latin vowels rest on exactly the same baseline, and retain
    # the full unmodified unaccented letter contour. Capitals must yield a
    # couple of pixels to stacked accents but never lose unique contour rows.
    base=G[face][root].copy()
    if upper and shape in ('circumflex','breve'):
        base=reduce_body_for_marks(base,w,True,2)
    elif upper and tone and tone!='dot':
        base=reduce_body_for_marks(base,w,True,1)
    # Vietnamese i: any above-letter tone REPLACES the i-dot.  Keep the dot
    # for 'ị' only (dot-below is an additional mark, not a replacement).
    if root=='i' and tone not in (None,'dot'):
        base[:5,:]=0
    out=base.copy()
    def ink(points):
        for x,y in points:
            if 0<=x<w and 0<=y<15:out[y,x]=1
    if shape=='circumflex':
        sy=2 if upper else 3
        ink([(cx,sy),(cx-1,sy+1),(cx+1,sy+1)])
    elif shape=='breve':
        sy=2 if upper else 3
        ink([(cx-1,sy),(cx,sy+1),(cx+1,sy)])
    elif shape=='horn':
        hx=w-2;hy=1 if upper else 4
        ink([(hx-1,hy),(hx,hy),(hx,hy+1)])
    # Long two-level stack is reserved for the canonical hat/breve + tone.
    stacked=shape in ('circumflex','breve') and tone and tone!='dot'
    y=0 if upper or stacked else 3
    if tone=='acute':ink([(cx+1,y),(cx,y+1)])
    elif tone=='grave':ink([(cx-1,y),(cx,y+1)])
    elif tone=='hook':
        if y==0:ink([(cx,y),(cx+1,y),(cx+1,y+1)])
        else:ink([(cx,y-1),(cx+1,y-1),(cx+1,y),(cx,y+1)])
    elif tone=='tilde':ink([(cx-1,y),(cx,y),(cx,y+1),(cx+1,y+1)])
    elif tone=='dot':
        # Exactly one dot, even with descenders (prevents y/ỵ alias).
        py=13 if not (base[13].any()) else 14
        if py<15:
            opts=[cx,cx+1,cx-1,cx+2,cx-2,1]
            px=next((x for x in opts if 0<=x<w and not base[py,x]),cx)
            ink([(px,py)])
    return out

for face in FACES:
    for ch in VI:
        if ch in 'đĐ':continue
        mm=_vn_layer(G[face].get(ch),face,ch)
        if mm is not None:G[face][ch]=mm

# Readability gate: preserve X11 6x13B as a shape reference, but fit type ink
# inside 5 columns of a 6-pixel advance.  This is the unavoidable 1-pixel
# inter-glyph aperture in a 6px line.  We do NOT shift all other columns: only
# the last column is folded onto the penultimate column.  Avoid redoing
# punctuation/line-drawing, which has its own semantics.
for ch,mat in G['single_b'].items():
    if not (ch.isalpha() or ch.isdigit()):continue
    mat[:,4] |= mat[:,5]
    mat[:,5]=0

# release-specific targeted invariants
for face,(w,_,_) in FACES.items():
    m=G[face]['0']
    assert m.shape==(16,w) and not m[15].any()
    assert np.any(m[7,:]),face
    if face=='single_r':
        assert all(m[y,x] for x,y in [(3,6),(2,7),(1,8)])
        assert (G[face]['0']!=G[face]['O']).sum()>=3
for fam in ('single','double'):
    for ch in '.:;!?':
        assert np.array_equal(G[fam+'_r'][ch],G[fam+'_b'][ch])

# Font export - BDF native 1-bit bitmap, PCF for X11, TTF/WOFF2 pixel outline.
# All four faces have 370 Unicode glyphs and exactly 6 / 12 px advance.
from fontTools.ttLib import TTFont
import subprocess

def build_bdf(face,gg):
    w,wt,key=FACES[face]
    family='Oxalis Monobit Single' if w==6 else 'Oxalis Monobit Double'
    filename=f'OxalisMonobit{"Single" if w==6 else "Double"}-{wt}'
    dest=OUT/(filename+'.bdf')
    lines=['STARTFONT 2.1',f'FONT -Oxalis-Monobit-{"Single" if w==6 else "Double"}-{wt}-R-Normal--16-160-75-75-M-{w*10}-ISO10646-1',
           'SIZE 16 75 75',f'FONTBOUNDINGBOX {w} 15 0 -3','STARTPROPERTIES 8',
           f'FAMILY_NAME "{family}"',f'WEIGHT_NAME "{wt}"', 'SPACING "M"','FONT_ASCENT 12','FONT_DESCENT 4',
           'CAP_HEIGHT 10', 'COPYRIGHT "Copyright 2026 Oxalis. All rights reserved. Original X11 Fixed reference bitmap is public domain."',
           'NOTICE "X11 Fixed public-domain font designs credited in README."','ENDPROPERTIES',f'CHARS {len(gg)}']
    for ch in sorted(gg,key=ord):
        m=gg[ch];nbytes=(w+7)//8
        lines+=['STARTCHAR uni%04X'%ord(ch),f'ENCODING {ord(ch)}',f'SWIDTH {round(w*1000/16)} 0',
                f'DWIDTH {w} 0',f'BBX {w} 15 0 -3','BITMAP']
        for row in m[:15]:
            bits=sum(int(val)<<(nbytes*8-x-1) for x,val in enumerate(row))
            lines.append(f'{bits:0{nbytes*2}X}')
        lines.append('ENDCHAR')
    lines.append('ENDFONT');dest.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # Binary PCF only when supported system tool is installed
    if os.path.exists('/usr/bin/bdftopcf'):
        with open(OUT/(filename+'.pcf'),'wb') as out:
            subprocess.run(['/usr/bin/bdftopcf',str(dest)],stdout=out,check=True)
    return filename

def build_ttf(face,gg,filename):
    w,wt,key=FACES[face]
    family='Oxalis Monobit Single' if w==6 else 'Oxalis Monobit Double'
    cmap={ord(ch):f'uni{ord(ch):04X}' for ch in gg}
    order=['.notdef']+[cmap[cp] for cp in sorted(cmap)]
    def pixel_glyph(m):
        # Build a *union* of the pixel squares before outlining. Earlier
        # versions emitted an independent, overlapping contour per pixel;
        # FreeType sometimes filled these incorrectly (especially arrows,
        # blocks, accents) despite valid bitmap source files.
        from shapely.geometry import box, Polygon, MultiPolygon
        from shapely.ops import unary_union
        from shapely.geometry.polygon import orient
        pen=TTGlyphPen(None)
        ink=np.argwhere(m[:15]!=0)
        if not len(ink):return pen.glyph()
        shape=unary_union([box(int(x),int(y),int(x)+1,int(y)+1) for y,x in ink])
        pieces=[shape] if isinstance(shape,Polygon) else list(shape.geoms)
        def ring(points):
            pts=list(points.coords)
            if len(pts)<4:return
            def cv(t):return (int(round(t[0]*100)),int(round(1200-t[1]*100)))
            pen.moveTo(cv(pts[0]))
            for v in pts[1:-1]:pen.lineTo(cv(v))
            pen.closePath()
        for poly in pieces:
            poly=orient(poly,sign=1.0)
            ring(poly.exterior)
            for r in poly.interiors:ring(r)
        return pen.glyph()
    glyf={cmap[ord(c)]:pixel_glyph(mat) for c,mat in gg.items()}
    glyf['.notdef']=TTGlyphPen(None).glyph()
    fb=FontBuilder(1600,isTTF=True)
    fb.setupGlyphOrder(order);fb.setupCharacterMap(cmap);fb.setupGlyf(glyf)
    # The TTF left side bearing MUST equal the actual glyph xMin. Setting
    # every LSB to 0 (old exports) caused FreeType to translate glyphs whose
    # first ink pixel was not in column 0 (punctuation, I, Double letters).
    # This preserves the true 6/12-px bitmap alignment at exactly 16 ppem.
    hmtx={'.notdef':(w*100,0)}
    for c,mat in gg.items():
        ink_cols=np.flatnonzero(mat.any(axis=0))
        lsb=int(ink_cols[0])*100 if len(ink_cols) else 0
        hmtx[cmap[ord(c)]]=(w*100,lsb)
    fb.setupHorizontalMetrics(hmtx)
    fb.setupHorizontalHeader(ascent=1200,descent=-400,lineGap=0)
    fb.setupNameTable({'familyName':family,'styleName':wt,'fullName':family+' '+wt,
                       'psName':family.replace(' ','')+'-'+wt,
                       'version':'Version 1.0.0',
                       'copyright':'Copyright 2026 Oxalis. All rights reserved. Source reference X11 Fixed public domain.'})
    fb.setupOS2(sTypoAscender=1200,sTypoDescender=-400,sTypoLineGap=0,
                usWinAscent=1200,usWinDescent=400,usWeightClass=700 if wt=='Bold' else 400,
                sxHeight=600,sCapHeight=1000)
    fb.setupPost(isFixedPitch=1);fb.setupMaxp()
    fb.save(OUT/(filename+'.ttf'))
    f=TTFont(OUT/(filename+'.ttf'))
    assert len(f.getBestCmap())==len(gg)
    assert all(adv==w*100 for name,(adv,lsb) in f['hmtx'].metrics.items())
    fw=TTFont(OUT/(filename+'.ttf'));fw.flavor='woff2';fw.save(OUT/(filename+'.woff2'))
    # per-glyph JSON for future inspection
    (OUT/(filename+'-glyphs.json')).write_text(json.dumps({f'U+{ord(c):04X}':[''.join('#' if p else '.' for p in r) for r in m] for c,m in gg.items()},ensure_ascii=False,indent=1),encoding='utf8')

for face,gg in G.items():
    stem=build_bdf(face,gg)
    build_ttf(face,gg,stem)
print('BUILT',len(G),'faces',len(ORDER),'glyphs each to',OUT)

#!/usr/bin/env python3
"""Independent release verifier, from exported artifacts only."""
from pathlib import Path
import json, csv, re, unicodedata
from collections import defaultdict,Counter
import numpy as np
from PIL import ImageFont
from scipy.ndimage import label
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parent
DIST=ROOT/'dist'
STEMS=['OxalisMonobitSingle-Regular','OxalisMonobitSingle-Bold',
       'OxalisMonobitDouble-Regular','OxalisMonobitDouble-Bold']
VIGN='ÀÁÂÃÇÈÉÊÌÍÑÒÓÔÕÙÚÝàáâãçèéêìíñòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
ALLOWED_SEMANTIC_ALIASES=[{'-','‐'},{'–','−'},{'←','\uf060'},{'→','\uf061'},{'■','\uf04d'},{'▼','\uf0d7'},{'✗','\uf00d'}]
ALLOWED_BLANK={' ','\u00a0'}
critical=[('0','O'),('1','I'),('1','l'),('5','S'),('8','B'),('d','đ'),('D','Đ'),('ơ','o'),('ư','u')]
CSV=[];stat={}; glyphs_by_stem={};ttf_by_stem={}

def bdf_decode(path,width):
    txt=path.read_text()
    assert f'FONTBOUNDINGBOX {width} 15 0 -3' in txt
    assert txt.count(f'DWIDTH {width} 0')==360
    out={}
    for part in txt.split('STARTCHAR ')[1:]:
        cp=int(re.search(r'ENCODING (\d+)',part).group(1))
        bits=part.split('BITMAP\n',1)[1].split('\nENDCHAR',1)[0].split()
        assert len(bits)==15
        out[chr(cp)]=np.array([[bool((int(row,16)>>(len(row)*4-x-1))&1) for x in range(width)]
            for row in bits]+[[False]*width],dtype=bool)
    return out

for stem in STEMS:
    w=6 if 'Single' in stem else 12
    style='Bold' if '-Bold' in stem else 'Regular'
    data=json.loads((DIST/(stem+'-glyphs.json')).read_text())
    g={chr(int(k[2:],16)):np.array([[c=='#' for c in r] for r in rows],dtype=bool) for k,rows in data.items()}
    bdf=bdf_decode(DIST/(stem+'.bdf'),w)
    ttf=TTFont(DIST/(stem+'.ttf'))
    assert len(g)==360 and set(g)==set(bdf)==set(chr(c) for c in ttf.getBestCmap())
    assert all(adv==w*100 for n,(adv,lsb) in ttf['hmtx'].metrics.items())
    assert ttf['OS/2'].sCapHeight==1000
    assert ttf['hhea'].ascent==1200 and ttf['hhea'].descent==-400
    font=ImageFont.truetype(DIST/(stem+'.ttf'),16)
    assert font.getlength('A')==w and font.getlength('a')==w
    assert set(font.getmask('A'))<={0,255} # exact binary raster at 16ppem
    assert font.getbbox('A')[1:4:2]==(2,12),font.getbbox('A')

    semantic=[];duplicates=defaultdict(list)
    for ch,m in g.items():
        duplicates[m.tobytes()].append(ch)
        c4=label(m,np.array([[0,1,0],[1,1,1],[0,1,0]],dtype=bool))[1]
        c8=label(m,np.ones((3,3),dtype=bool))[1]
        tests={
            'cell_shape':m.shape==(16,w),
            'last_row_empty':not m[15].any(),
            'not_blank_except_space':bool(m.any() or ch in ALLOWED_BLANK),
            'bdf_matches_bitmap':np.array_equal(m,bdf[ch]),
            'unicode_in_ttf':ord(ch) in ttf.getBestCmap(),
            'ttf_advance':ttf['hmtx'][ttf.getBestCmap()[ord(ch)]][0]==w*100,
        }
        # A diacritic intentionally forms an independent component.
        # Check only base ASCII letters here; separate marks are not punished.
        if ch.isascii() and ch.isalpha() and ch not in 'ij':
            tests['body_8_connected']=(c8==1)
        # Readability at exact 1x cannot be proven by pixel metrics.
        results={'face':stem,'glyph':ch,'unicode':f'U+{ord(ch):04X}', 'pixel_count':int(m.sum()),
                 'components_4':int(c4),'components_8':int(c8),
                 'touches_left':int(m[:,0].any()),'touches_right':int(m[:,-1].any()),
                 **{k:int(v) for k,v in tests.items()},'passed':sum(tests.values()),'checked':len(tests)}
        CSV.append(results)
        if not all(tests.values()):semantic.append((ch,[k for k,v in tests.items() if not v]))
    dup_groups=[list(v) for v in duplicates.values() if len(v)>1]
    unexpected=[x for x in dup_groups if set(x) not in ALLOWED_SEMANTIC_ALIASES and not set(x)<=set(' \u00a0')]
    if unexpected:
        print('ALIAS WARNING',stem,unexpected[:10])
    assert all(np.sum(g[a]!=g[b])>=3 for a,b in critical),(stem,[(a,b,int(np.sum(g[a]!=g[b]))) for a,b in critical])
    assert all(g[c].any() for c in VIGN),stem
    assert len(set(g[c].tobytes() for c in VIGN))==len(VIGN),(stem,'duplicate Latin glyph')
    assert np.flatnonzero(g['A'].any(axis=1)).tolist()==list(range(2,12))
    assert np.sum(g['0']!=g['O'])>=3
    # Dot below is just ONE additional pixel, no second dot; intentionally a
    # single-pixel distinction even where the letter also has a descender.
    for base,dotted in [('a','ạ'),('e','ẹ'),('i','ị'),('o','ọ'),('u','ụ'),('y','ỵ')]:
        if base in g and dotted in g:
            gain=g[dotted]&~g[base]
            assert gain.sum()==1,(stem,dotted,gain.sum())
    # punctuation exactly equivalent regular/bold is checked across families below
    left=int(sum(g[ch][:,0].any() for ch in VIGN))
    right=int(sum(g[ch][:,-1].any() for ch in VIGN))
    stat[stem]={'glyph_count':len(g),'all_glyph_failures':semantic,'left_edge_viet':left,'right_edge_viet':right,
                'semantic_aliases':dup_groups,'unintended_alias_groups':unexpected,
                'critical_pair_distances':{f'{a}/{b}':int(np.sum(g[a]!=g[b])) for a,b in critical},
                'automated_check_pass':sum(x['passed'] for x in CSV if x['face']==stem),
                'automated_check_total':sum(x['checked'] for x in CSV if x['face']==stem)}
    glyphs_by_stem[stem]=g;ttf_by_stem[stem]=ttf
    print(stem,'glyphs',len(g),'per-glyph fails',len(semantic),'unintended dup',len(unexpected),'right-edge viet',right)

for family in ('Single','Double'):
    r=glyphs_by_stem[f'OxalisMonobit{family}-Regular']
    b=glyphs_by_stem[f'OxalisMonobit{family}-Bold']
    punct='!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    assert all(np.array_equal(r[ch],b[ch]) for ch in punct),'punctuation not identical by weight'
    assert all(np.sum(r[x].any(axis=1))==np.sum(b[x].any(axis=1)) for x in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123606789'),'cap height weight mismatch'
    for ch in 'aemnoru':
        assert np.sum(r[ch].any(axis=1))==np.sum(b[ch].any(axis=1)),(family,ch,'xheight mismatch')

count=sum(s['automated_check_pass'] for s in stat.values());total=sum(s['automated_check_total'] for s in stat.values())
stat['SUMMARY']={'total_glpyhs':len(STEMS)*360,'automated_checks_passed':count,'automated_checks_total':total,
                 'automated_rate_pct':round(count/total*100,2),
                 'caveat':'Automated engineering audit, NOT human readability validation.'}
print('AUTOMATED ENGINEERING QA',count,'/',total, f'{100*count/total:.2f}%')
(DIST/'QA-SUMMARY.json').write_text(json.dumps(stat,ensure_ascii=False,indent=2))
columns=list(dict.fromkeys(k for r in CSV for k in r));
with (DIST/'QA-GLYPHS.csv').open('w',encoding='utf8',newline='') as f:
 wr=csv.DictWriter(f,fieldnames=columns);wr.writeheader();wr.writerows(CSV)

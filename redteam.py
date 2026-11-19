import numpy as np,unicodedata,json,sys,math
from scipy.ndimage import label
from collections import defaultdict,Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_full import G,ORDER,FACES,VI
OUT=Path(__file__).resolve().parent
REPORT={}
VISET=set(VI)
INTENTIONAL_MULTI=set('!"%:;?ij.,=öñüï')
PAIR=[('0','O'),('1','I'),('1','l'),('5','S'),('8','B'),('2','Z'),('d','đ'),('D','Đ'),('ạ','a'),('ỵ','y'),('á','à'),('ả','ã'),('ở','ỡ'),('ắ','ấ'),('ư','u'),('ơ','o')]

for face,fonts in G.items():
    groups=defaultdict(list)
    for ch,arr in fonts.items():groups[arr.tobytes()].append(ch)
    dups=[s for s in groups.values() if len(s)>1 and not (set(s)<={' ','\u00a0'})]
    area=[]; splits=[]; contacts=[]; width=FACES[face][0]
    struct=np.ones((3,3),dtype=int)
    for ch,a in fonts.items():
        if ch==' ':continue
        components=label(a,struct)[1]
        if components>1 and ch not in INTENTIONAL_MULTI and ch.isalnum():splits.append([ch,components])
        if np.any(a[15]):area.append(ch)
        if (ch in VISET or (ch.isalpha() and ch in 'aoumnw')) and a[:,width-1].any():contacts.append(ch)
    pairdist=[(a,b,int(np.sum(fonts[a]!=fonts[b]))) for a,b in PAIR]
    q=[c for c in VISET if unicodedata.normalize('NFD',c)!=c and not np.any(fonts[c])]
    small=[(a,b,d) for a,b,d in pairdist if d<=2]
    REPORT[face]={'dups':dups[:80],'dups_count':len(dups), 'unexpected_split_alnum':splits[:90],
                  'splits_count':len(splits),'right_edge_vi':contacts,'right_edge_vi_count':len(contacts),
                  'pairdist':pairdist,'confusable_le2':small,'overflow':area,'blank_viet':q}
    print(face,'duplicate',len(dups),'split_alnum',len(splits),'right-edge',len(contacts),'confusable<=2',small)
    print(' duplicates sample:',dups[:25]);print(' splits sample',splits[:20]);print(' contacts',contacts[:20])
(OUT/'redteam_firstpass.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2))

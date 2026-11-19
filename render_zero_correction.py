#!/usr/bin/env python3
"""Reproduce the approved one-pixel Double Regular zero correction preview."""
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw
import json
R=Path(__file__).resolve().parent
D=R/'dist'
reg=json.loads((D/'OxalisMonobitDouble-Regular-glyphs.json').read_text())
bold=json.loads((D/'OxalisMonobitDouble-Bold-glyphs.json').read_text())
new=reg['U+0030']
old=new.copy()
old[9]=old[9][:3]+'.#'+old[9][5:] # old pixel (x4) instead of current (x3)
assert old[9][3]=='.' and old[9][4]=='#'
assert new[9][3]=='#' and new[9][4]=='.'
assert [i for i in range(16) if old[i]!=new[i]]==[9]

BG='#0A1422'; PANEL='#122538'; OLD='#FEBF9C'; GREEN='#56DFC2'; FG='#E8F0F5'; MUT='#A7BECB'; LINE='#334E66'
F='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
FB='/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
H1=ImageFont.truetype(FB,32); H2=ImageFont.truetype(FB,22); SM=ImageFont.truetype(F,17); XS=ImageFont.truetype(F,15)
W,H=1560,850
im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
d.text((36,25),'OXALIS MONOBIT DOUBLE / ZERO CORRECTION',font=H1,fill=FG)
d.text((36,77),'V1.0 FINAL  |  BBX 12x15  |  1-pixel diagonal alignment fix',font=SM,fill=MUT)

# each panel is for exact bitmap rows; panels leave extra space between glyphs
panels=[(38,'REGULAR  / BEFORE',old,OLD),(552,'REGULAR  / FINAL',new,GREEN),(1066,'BOLD  / UNCHANGED',bold['U+0030'],GREEN)]
for px,label,bitmap,color in panels:
    d.rounded_rectangle((px,133,px+454,582),radius=12,fill=PANEL,outline=LINE,width=2)
    d.text((px+24,155),label,font=H2,fill=color)
    cell=18; x0=px+105;y0=218
    # glyph 12x16, 18px per input pixel
    for y,row in enumerate(bitmap):
        for x,char in enumerate(row):
            if char=='#':
                d.rectangle((x0+x*cell,y0+y*cell,x0+(x+1)*cell-1,y0+(y+1)*cell-1),fill=color)
    d.rectangle((x0-1,y0-1,x0+12*cell,y0+16*cell),outline=LINE,width=1)
    for x in range(1,12):d.line((x0+x*cell,y0,x0+x*cell,y0+16*cell),fill=BG,width=1)
    for y in range(1,16):d.line((x0,y0+y*cell,x0+12*cell,y0+y*cell),fill=BG,width=1)
    d.text((px+24,534),'12x16 actual bitmap · shown 18x',font=XS,fill=MUT)
# arrows emphasize the relocated pixel only in final
# note coordinates old x4,y9 -> new x3,y9
d.text((40,606),'PIXEL CHANGE:  (4, 9)   →   (3, 9)  ·  only Double Regular U+0030 changed',font=H2,fill=FG)
d.text((40,651),'ACTUAL 1x — no smoothing',font=SM,fill=MUT)

def sample(data,text,x,y,ink,scale=1):
    for i,c in enumerate(text):
        key=f'U+{ord(c):04X}'
        if key not in data:continue
        for yy,row in enumerate(data[key]):
            for xx,pixel in enumerate(row):
                if pixel=='#':
                    d.rectangle((x+i*12*scale+xx*scale,y+yy*scale,x+i*12*scale+(xx+1)*scale-1,y+(yy+1)*scale-1),fill=ink)

# sample tiny but original size explicitly; this part uses the rebuilt full font
for j,(title,glyphs) in enumerate([('DOUBLE REGULAR',reg),('DOUBLE BOLD',bold)]):
    y=699+j*52
    d.text((40,y),title,font=SM,fill=MUT)
    sample(glyphs,'00 0O O0 80 08 0123456789',265,y+1,GREEN)
    d.text((700,y),'00 0O O0 80 08',font=SM,fill=MUT)

out=R/'previews'/'Oxalis_Monobit_v1.0_Zero_Before_After.png'
im.save(out)
print(out)

from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
R=Path(__file__).resolve().parent/'dist'
faces=[('Oxalis Monobit Single','Regular',6),('Oxalis Monobit Single','Bold',6),('Oxalis Monobit Double','Regular',12),('Oxalis Monobit Double','Bold',12)]
COL={'bg':'#091625','panel':'#102536','grid':'#30475D','text':'#E8F0F6','muted':'#A2B7C6','teal':'#71E4C1','amber':'#F8C5A2'}
F='/usr/share/fonts/TTF/DejaVuSansMono.ttf'
FB='/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf'
Title=ImageFont.truetype(FB,40);Heading=ImageFont.truetype(FB,23);Small=ImageFont.truetype(F,15);Med=ImageFont.truetype(F,18)
G={}
for fam,style,w in faces:
   name=('Single' if w==6 else 'Double')
   p=R/f'OxalisMonobit{name}-{style}-glyphs.json'
   d=json.load(open(p));G[(name,style)]={chr(int(k[2:],16)):rows for k,rows in d.items()}

def draw_glyph(draw,rows,x,y,scale,color):
    for yy,row in enumerate(rows[:15]):
        for xx,px in enumerate(row):
            if px=='#':draw.rectangle((x+xx*scale,y+yy*scale,x+(xx+1)*scale-1,y+(yy+1)*scale-1),fill=color)

def draw_text(draw,glyphs,text,x,y,scale,color,advance):
    px=x
    for c in text:
        if c=='\n':
            y+=16*scale;px=x
        else:
            if c in glyphs:draw_glyph(draw,glyphs[c],px,y,scale,color)
            px+=advance*scale

W,H=2580,2010
im=Image.new('RGB',(W,H),COL['bg']);d=ImageDraw.Draw(im)
d.text((35,24),'OXALIS MONOBIT — V1.0 / SINGLE + DOUBLE',font=Title,fill=COL['text'])
d.text((35,77),'Single BBX 6×15    Double BBX 12×15    A height 10    Line 16    360 glyphs / face',font=Med,fill=COL['muted'])
d.text((35,104),'Base: X11 Fixed 6x13 / 6x13B  ·  8x13 / 8x13B     |     1-bit pixel outlines',font=Med,fill=COL['muted'])
CX=[30,675,1320,1965];CW=613
for i,(fam,style,w) in enumerate(faces):
    x=CX[i]
    d.rounded_rectangle((x,144,x+CW,H-42),radius=12,fill=COL['panel'],outline=COL['grid'],width=2)
    d.text((x+16,163),fam.upper().replace('OXALIS MONOBIT ','')+' / '+style.upper(),font=Heading,fill=COL['teal'])
    d.text((x+16,200),f'{w}x15 BBX  /  16px line',font=Med,fill=COL['muted'])
    glyph=G[('Single' if w==6 else 'Double',style)]
    samples=[
     ('CAPITALS','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
     ('LOWERCASE','abcdefghijklmnopqrstuvwxyz'),
     ('DIGITS','0123606789 100% -12.50'),
     ('CODING','0O 1Il 5S 8B 2Z {()} []'),
     ('VIETNAMESE','Tân Hóa - Tú Làn'),
     ('VIETNAMESE','Người Nguồn Ở rừng'),
     ('VIETNAMESE','Tiếng Việt: sắc, huyền'),
     ('VIETNAMESE','Hỏi ngã nặng / đ Đ ơ ư'),
    ]
    y=245
    for label,text in samples:
        d.text((x+16,y),label,font=Small,fill=COL['muted']);y+=25
        scale=1 if w==12 else 2
        # 2x may overflow for Single lines with 26 chars; use 1x for all 1x strips
        draw_text(d,glyph,text,x+20,y,1,COL['text'],w)
        y+=48
    d.text((x+16,y+5),'ZOOM 4x — CRITICAL GLYPHS',font=Med,fill=COL['muted'])
    y+=44
    chs='0O1Il5S8B2ZMDWmwaegrđĐÁẮẤỂỚỵịơư%?.,:;|'
    ncol=5
    cellw=114;cellh=105
    for j,ch in enumerate(chs):
        cc=j%ncol;rr=j//ncol
        xx=x+15+cc*cellw;yy=y+rr*cellh
        d.text((xx+4,yy+3),ch,font=Small,fill=COL['muted'])
        if ch in glyph:
            s=4 if w==6 else 3
            draw_glyph(d,glyph[ch],xx+16,yy+26,s,COL['teal'])
    y+=math.ceil(len(chs)/ncol)*cellh if False else ((len(chs)+ncol-1)//ncol)*cellh
    y+=24
    d.text((x+16,y),'ACTUAL PIXELS (1x, no smoothing)',font=Med,fill=COL['muted'])
    y+=36
    for item in ['ABDOMW 0123606789','da đe gỡ ơ ư ấ ẳ','100% 01:23 / 50.75']:
        draw_text(d,glyph,item,x+22,y,1,COL['text'],w);y+=30
    d.text((x+16,H-86),'© 2026 Oxalis  |  v1.0 FINAL',font=Small,fill=COL['muted'])
im.save(str(Path(__file__).resolve().parent/'previews/Oxalis_Monobit_4Faces_Review.png'))
print(str(Path(__file__).resolve().parent/'previews/Oxalis_Monobit_4Faces_Review.png'))

# 360 glyphs / face contact sheet for detailed independent inspection, 4 columns
w2,h2=2800,5900
sheet=Image.new('RGB',(w2,h2),COL['bg']);dr=ImageDraw.Draw(sheet)
dr.text((30,25),'OXALIS MONOBIT — ALL 360 GLYPHS / 4 FACES',font=Title,fill=COL['text'])
dr.text((30,80),'Each cell: source Unicode, one actual glyph, enlarged nearest-neighbor bitmap.',font=Med,fill=COL['muted'])
cellw=140;cellh=115
for face_idx,(fam,style,w) in enumerate(faces):
    x0=30+face_idx*695
    dr.text((x0,129),fam.replace('Oxalis Monobit ','')+' '+style,font=Heading,fill=COL['teal'])
    gg=G[('Single' if w==6 else 'Double',style)]
    items=sorted(gg.items(),key=lambda v:ord(v[0]))
    for i,(ch,mat) in enumerate(items):
        c=i%5;r=i//5
        x=x0+c*132;y=176+r*79
        if y>5700:break
        dr.rectangle((x,y,x+127,y+74),outline=COL['grid'])
        dr.text((x+5,y+5),f'{ord(ch):04X}',font=Small,fill=COL['muted'])
        if ch not in '\u00a0\u0020':draw_glyph(dr,mat,x+40,y+26,3,COL['teal'])
    dr.text((x0,5740),f'{len(gg)} Unicode codepoints',font=Med,fill=COL['muted'])
sheet.save(str(Path(__file__).resolve().parent/'previews/Oxalis_Monobit_All360Glyphs.png'))

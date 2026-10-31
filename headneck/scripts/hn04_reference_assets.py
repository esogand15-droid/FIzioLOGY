"""Render only chosen illustrations. Explicit PDF pages; no arithmetic page mapping."""
import json
from pathlib import Path
import pymupdf as fitz
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[2]
NETTER = ROOT/'علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1/Netter Atlas of Human Anatomy Classic Regional Approach.pdf'
GRAY = ROOT/"علوم تشریح دستگاه اعصاب/user - Gray's Anatomy For Students, 3rd Edition-801-1000.pdf"
SPECS = [
 ('hn04_grays_f825',GRAY,93,865,'8.25',None,[48,377,560,550],'حفرهٔ قدامی و نقشهٔ کوچک موقعیت آن'),
 ('hn04_grays_f826',GRAY,95,867,'8.26',None,[48,455,560,740],'حفرهٔ میانی و نقشهٔ کوچک موقعیت آن'),
 ('hn04_netter_p30_superior',NETTER,82,None,None,30,[50,80,580,415],'نمای فوقانی کالواریا و استخوان درزی'),
 ('hn04_netter_p31_inferior',NETTER,83,None,None,31,[48,80,590,735],'نام ساختارهای قاعدهٔ خارجی'),
]
def build():
 indexpath=ROOT/'headneck/images/INDEX.json'; index=json.loads(indexpath.read_text())
 for aid,src,page,printed,fig,plate,bbox,note in SPECS:
  path=Path('headneck/images')/(aid+'.jpeg'); d=fitz.open(src)
  pix=d[page-1].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(bbox))
  image=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
  masks=[]
  if aid == 'hn04_netter_p30_superior':
   # The lower panel overlaps the upper panel's rectangular extent only in
   # the bottom-left whitespace. Remove that unrelated fragment, not anatomy.
   masks=[[50,390,315,415]]
   draw=ImageDraw.Draw(image)
   for x0,y0,x1,y1 in masks:
    draw.rectangle([(x0-bbox[0])*3,(y0-bbox[1])*3,(x1-bbox[0])*3,(y1-bbox[1])*3],fill='white')
  image.save(ROOT/path,format='JPEG',quality=94)
  row=dict(asset_id=aid,book='netter' if plate else 'grays',session='hn04',source_file=str(src.relative_to(ROOT)),page=page,printed_page=printed,figure=fig,plate=plate,bbox=bbox,w=pix.width,h=pix.height,bytes=(ROOT/path).stat().st_size,path=str(path),note=note,mask_rects=masks)
  index['assets']=[a for a in index['assets'] if a['asset_id']!=aid]+[row]
 indexpath.write_text(json.dumps(index,ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__': build()

"""Prepare compact figures without baking source-slide attribution into the panel."""
from pathlib import Path
import hashlib,json,subprocess,sys
from PIL import Image,ImageDraw
import pymupdf
ROOT=Path(__file__).resolve().parents[2]; INV=ROOT/'headneck/reports/hn13_evidence/source_inventory.json';CACHE=ROOT/'.cache/hn13';OUT=CACHE/'final_assets';OUT.mkdir(parents=True,exist_ok=True)
NETTER=ROOT/'علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1/Netter Atlas of Human Anatomy Classic Regional Approach.pdf'
PAGES=[(77,25),(91,39),(79,27),(90,38),(84,32),(83,31),(95,43),(96,44),(105,53),(106,54)]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 inv=json.loads(INV.read_text());items=[]
 for source in inv['sources']:
  doc=pymupdf.open(ROOT/source['source'])
  for page in source['pages']:
   if 'figure' not in page:continue
   r=pymupdf.Rect(page['figure_rect']); pg=doc[page['page']-1]
   # Keep connected/disconnected drawn leaders inside the figure's vertical band.
   for drawing in pg.get_drawings():
    b=drawing['rect']
    if b.y0>=r.y0 and b.y1<=r.y1 and not (b & r).is_empty:r |= b
   r=(r + (-2,-2,2,2)) & pg.rect
   scale=2;pix=doc[page['page']-1].get_pixmap(matrix=pymupdf.Matrix(scale,scale),clip=r,alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);draw=ImageDraw.Draw(im)
   # The slide signature is always independently cited in the booklet. Mask
   # only spans that explicitly contain the recurring signature, never labels.
   for sp in page['spans']:
    if 'Dr Mirzaei' in sp['text'] or 'Hormozgan medical science university' in sp['text']:
     b=pymupdf.Rect(sp['bbox']) & r
     if not b.is_empty:draw.rectangle(((b.x0-r.x0)*scale,(b.y0-r.y0)*scale,(b.x1-r.x0)*scale,(b.y1-r.y0)*scale),fill='white')
   dest=OUT/f"part{source['part']}_page{page['page']:02}.jpg";im.save(dest,quality=94,subsampling=0,optimize=True)
   items.append({'part':source['part'],'page':page['page'],'asset':str(dest.relative_to(ROOT)),'sha256':digest(dest),'clip':list(r)})
 net=pymupdf.open(NETTER);refs=[]
 for n,plate in PAGES:
  pg=net[n-1];r=pg.rect;clip=pymupdf.Rect(0,r.height*.075,r.width,r.height*.94);pix=pg.get_pixmap(matrix=pymupdf.Matrix(2,2),clip=clip,alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);dest=OUT/f'netter_{n}.jpg';im.save(dest,quality=94,subsampling=0,optimize=True);refs.append({'page':n,'plate':plate,'asset':str(dest.relative_to(ROOT)),'sha256':digest(dest),'clip':list(clip)})
 result={'figures':items,'references':refs,'netter_sha256':digest(NETTER)};(ROOT/'headneck/reports/hn13_evidence/asset_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('figures',len(items),'references',len(refs),'JPEG bytes',sum((ROOT/x['asset']).stat().st_size for x in items+refs))
if __name__=='__main__':main()

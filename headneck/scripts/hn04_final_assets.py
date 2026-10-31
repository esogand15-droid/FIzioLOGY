"""Reproducible, individually readable subfigures selected during final review."""
import json
from pathlib import Path
import pymupdf as fitz
from PIL import ImageDraw
ROOT=Path(__file__).resolve().parents[2]
LECTURE=sorted((ROOT/'علوم تشریح سر و گردن/جلسه 4 - قاعده جمجمه').glob('*.pdf'))[0]
NETTER=ROOT/'علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1/Netter Atlas of Human Anatomy Classic Regional Approach.pdf'
# Coordinates are actual PDF points, not printed-page coordinates.
SPECS=[
 ('hn04_ethmoid_A',LECTURE,3,[148.5,535.2,278,637],'A — anterior view',None),
 ('hn04_ethmoid_B',LECTURE,3,[284,535.2,405,640],'B — superior view',None),
 ('hn04_ethmoid_C',LECTURE,3,[411,535.2,540,640],'C — posterior view',None),
 ('hn04_ethmoid_D',LECTURE,3,[148.5,648,344,755.15],'D — left lateral view',None),
 ('hn04_ethmoid_E',LECTURE,3,[355,648,540,755.15],'E — inferior view',None),
 ('hn04_labyrinth_A',LECTURE,5,[72,72,267,157],'Upper left — inferior view',None),
 ('hn04_labyrinth_B',LECTURE,5,[72,156,367,334.6],'Lower left — opened air cells',None),
 ('hn04_labyrinth_C',LECTURE,5,[400,97,539.3,192],'Upper right — medial orbital wall',None),
 ('hn04_labyrinth_D',LECTURE,5,[374,193,539.3,334.6],'Lower right — opened orbit',None),
 ('hn04_aqueduct_A',LECTURE,15,[72,72,340,351.25],'Left — superior view of petrous bone',None),
 ('hn04_aqueduct_B',LECTURE,15,[328,78,539.45,207],'Upper right — endolymphatic sac schema',None),
 ('hn04_aqueduct_C',LECTURE,15,[378,213,539.45,306],'Lower right — osseous labyrinth',None),
 ('hn04_fossa_color_A',LECTURE,25,[28,120,235,238],'Left upper — anterior fossa color map',None),
 ('hn04_fossa_color_B',LECTURE,25,[28,265,236,397],'Left middle — middle fossa color map',None),
 ('hn04_fossa_color_C',LECTURE,25,[28,399,235,555.7],'Left lower — posterior fossa color map',None),
 ('hn04_netter61_drainage',NETTER,113,[49,474,579,721],'Lower illustration — drainage openings',61),
 ('hn04_netter63_septum',NETTER,115,[65,429,583,725],'Lower illustration — bony nasal septum',63),
 ('hn04_netter125_labyrinth',NETTER,177,[48,88,582,430],'Upper illustration — labyrinth schema',125),
]
def build():
 ip=ROOT/'headneck/images/INDEX.json';index=json.loads(ip.read_text())
 for aid,source,page,bbox,note,plate in SPECS:
  with fitz.open(source) as doc:
   pix=doc[page-1].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(bbox))
  path=Path('headneck/images')/(aid+'.jpeg')
  masks={
   'hn04_labyrinth_A':[[72,72,94,86]],
   'hn04_aqueduct_A':[[330,170,340,185]],
   'hn04_aqueduct_B':[[328,78,385,160]],
   'hn04_netter61_drainage':[[49,474,272,489]],
   'hn04_netter63_septum':[[400,429,583,441]],
  }.get(aid,[])
  image=pix.pil_image();draw=ImageDraw.Draw(image)
  for x0,y0,x1,y1 in masks:
   draw.rectangle([(x0-bbox[0])*3,(y0-bbox[1])*3,(x1-bbox[0])*3,(y1-bbox[1])*3],fill='white')
  image.save(ROOT/path,format='JPEG',quality=94)
  row=dict(asset_id=aid,book='netter' if plate else 'lecture',session='hn04',source_file=str(source.relative_to(ROOT)),page=page,part=None if plate else 1,printed_page=None,figure=None,plate=plate,bbox=bbox,w=pix.width,h=pix.height,bytes=(ROOT/path).stat().st_size,path=str(path),note=note,mask_rects=masks)
  index['assets']=[a for a in index['assets'] if a['asset_id']!=aid]+[row]
 ip.write_text(json.dumps(index,ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':build()

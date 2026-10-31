"""Only named session-5 update assets/INDEX entries; does not touch base content."""
from pathlib import Path
import json
import pymupdf as f
from PIL import ImageDraw
ROOT=Path(__file__).resolve().parents[2]
NETTER=next((ROOT/'علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1').glob('*Netter*.pdf'))
GRAY=next((ROOT/'علوم تشریح دستگاه اعصاب').glob('*Gray*1001-1189.pdf'))
# Each crop is a single anatomical panel (or explicitly named related pair).
SPECS=[
 ('hn05_u_atlas_axis_lower',NETTER,95,[45,300,585,492],43,'Atlas inferior and axis posterosuperior views'),
 ('hn05_u_assembled',NETTER,95,[90,495,520,730],43,'Assembled C1–C4'),
 ('hn05_u_c7',NETTER,96,[45,510,590,758],44,'C7 superior view and original variation footnote'),
 ('hn05_u_external_lateral',NETTER,98,[40,360,600,720],46,'External ligaments: lateral panel'),
 ('hn05_u_tectorial',NETTER,99,[55,100,560,350],47,'Tectorial membrane intact'),
 ('hn05_u_cruciform',NETTER,99,[140,255,580,473],47,'Tectorial membrane removed; cruciform ligament'),
 ('hn05_u_alar',NETTER,99,[80,465,580,704],47,'Lower pair: deeper ligaments and median joint'),
 ('hn05_u_transverse',NETTER,99,[300,530,580,703],47,'Median atlantoaxial joint: superior view'),
 ('hn05_u_cervical_plexus',NETTER,109,[45,90,585,398],57,'Cervical plexus schema, upper illustration'),
 ('hn05_u_cutaneous',NETTER,108,[45,80,585,398],56,'Cutaneous nerves: upper illustration'),
 ('hn05_u_fascia_cross',NETTER,103,[48,80,585,420],51,'Cross section: complete legend'),
 ('hn05_u_fascia_sagittal',NETTER,103,[48,420,585,724],51,'Midsagittal section: complete legend'),
 ('hn05_u_veins',GRAY,31,[50,270,570,715],None,'Figure 8.160 superficial veins'),
]
def build():
 p=ROOT/'headneck/images/INDEX.json';j=json.loads(p.read_text())
 for aid,source,page,bbox,plate,note in SPECS:
  with f.open(source) as d:pix=d[page-1].get_pixmap(matrix=f.Matrix(3,3),clip=f.Rect(bbox))
  # Only adjacent-panel fragments outside the target anatomy/legend are hidden.
  masks={
   'hn05_u_external_lateral':[[335,360,600,490],[40,360,300,367]],
   'hn05_u_tectorial':[[345,257,560,350],[330,320,345,350]],
   'hn05_u_cruciform':[[140,255,310,350],[140,465,320,473]],
   'hn05_u_alar':[[340,465,580,474]],
   'hn05_u_transverse':[[300,530,326,560]],
  }.get(aid,[])
  image=pix.pil_image();draw=ImageDraw.Draw(image)
  for x0,y0,x1,y1 in masks:draw.rectangle([(x0-bbox[0])*3,(y0-bbox[1])*3,(x1-bbox[0])*3,(y1-bbox[1])*3],fill='white')
  path=Path('headneck/images')/(aid+'.jpeg');image.save(ROOT/path,quality=94)
  a=dict(asset_id=aid,session='hn05',book='netter' if plate else 'grays',source_file=str(source.relative_to(ROOT)),page=page,plate=plate,figure=None if plate else '8.160',printed_page=None if plate else 1003,bbox=bbox,path=str(path),w=pix.width,h=pix.height,bytes=(ROOT/path).stat().st_size,note=note,mask_rects=masks)
  j['assets']=[x for x in j['assets'] if x['asset_id']!=aid]+[a]
 p.write_text(json.dumps(j,ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':build()

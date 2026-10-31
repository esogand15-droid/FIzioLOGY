"""Selected session-six reference panels; preserves all old assets/base files."""
from pathlib import Path
import json
import pymupdf as f
ROOT=Path(__file__).resolve().parents[2]
NETTER=next((ROOT/'علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1').glob('Netter*'))
GRAY=next((ROOT/'علوم تشریح دستگاه اعصاب').glob('*Gray*1001-1189.pdf'))
BACK=next((ROOT/'علوم تشریح دستگاه اعصاب').glob('*Gray*1-200.pdf'))
SPECS=[
 ('gray_triangle',BACK,126,[55,65,565,380],None,'2.46',98,'Complete suboccipital figure, table excluded'),
 ('hyoid',NETTER,105,[45,185,590,630],53,None,None,'Complete anterior infrahyoid/suprahyoid illustration'),
 ('lateral',NETTER,106,[45,90,595,725],54,None,None,'Complete lateral neck illustration'),
 ('prevertebral',NETTER,107,[45,85,595,720],55,None,None,'Complete anterior/lateral cervical illustration'),
 ('posterior_superficial',NETTER,281,[45,85,595,720],195,None,None,'Whole superficial back illustration; cervical attachments in context'),
 ('posterior_deep',NETTER,283,[45,85,595,720],197,None,None,'Whole deep back illustration; cervical attachments in context'),
 ('infrahyoid',GRAY,37,[50,282,562,740],None,'8.164',1009,'Complete infrahyoid illustration with caption'),
 ('suprahyoid',GRAY,36,[55,323,308,740],None,'8.163',1008,'Both panels A and B with caption; not the adjacent text column'),
 ('gray_prevertebral',GRAY,57,[50,60,562,505],None,'8.185',1029,'Complete illustration and caption; table is separate'),
 ('plexus',NETTER,109,[45,90,595,398],57,None,None,'Upper schema; roots and ansa separately labelled'),
 ('prevertebral_table',GRAY,57,[50,520,562,742],None,'Table 8.16',1029,'Complete prevertebral table; separate from figure'),
 ('suboccipital',NETTER,285,[45,110,595,711],199,None,None,'Complete posterior neck nerves illustration'),
]
def build():
 p=ROOT/'headneck/images/INDEX.json';j=json.loads(p.read_text())
 for slug,src,pg,box,plate,figure,printed,note in SPECS:
  aid='hn06_u_'+slug;path=Path('headneck/images')/(aid+'.jpeg')
  with f.open(src) as d:pix=d[pg-1].get_pixmap(matrix=f.Matrix(3,3),clip=f.Rect(box),alpha=False)
  pix.pil_save(ROOT/path,quality=94)
  a=dict(asset_id=aid,session='hn06',book='netter' if plate else 'grays',source_file=str(src.relative_to(ROOT)),page=pg,plate=plate,figure=figure,printed_page=printed,bbox=box,path=str(path),w=pix.width,h=pix.height,bytes=(ROOT/path).stat().st_size,note=note,mask_rects=[])
  j['assets']=[x for x in j['assets'] if x['asset_id']!=aid]+[a]
 p.write_text(json.dumps(j,ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':build()

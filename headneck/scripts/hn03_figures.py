"""Extract selected illustrations from the locally supplied session 3 lecture PDF.
Page numbers are 1-based PDF pages (the printed pagination is one less).
"""
from pathlib import Path
import json, io
import pymupdf
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
SOURCE=next((ROOT/'علوم تشریح سر و گردن').glob('جلسه 3*/*.pdf'))
D=pymupdf.open(SOURCE)
# ordinal indexes count only image blocks on that page, top-to-bottom in the PDF.
PICKS={2:[('location',0)],3:[('anterior',1)],5:[('posterior',0)],7:[('superior',0)],9:[('clivus',0)],10:[('pterion',0),('pterion_vessels',1)],11:[('surface',0),('infratemporal',1)],12:[('pal_medial',0),('pal_lateral',2)],13:[('canals',0),('orbital',1)],14:[('pal_posterior',0)],15:[('palate',0),('sphenopalatine',1)],16:[('sutures',1)],17:[('occ_external',0),('occ_inferior',1)],18:[('occ_internal',0)],19:[('occ_endocranial',0)],20:[('venous',0)]}
index=ROOT/'headneck/images/INDEX.json'; data=json.loads(index.read_text()); data['assets']=[x for x in data['assets'] if x.get('session')!='hn03']
for page, entries in PICKS.items():
 blocks=[b for b in D[page-1].get_text('dict')['blocks'] if b['type']==1]
 for name,i in entries:
  b=blocks[i]; im=Image.open(io.BytesIO(b['image'])).convert('RGB'); out=ROOT/f'headneck/images/hn03_lec_p{page:02}_{name}.jpeg'; im.save(out,quality=92,optimize=True)
  data['assets'].append(dict(asset_id=out.stem,book='lecture',session='hn03',source_file=str(SOURCE.relative_to(ROOT)),page=page,bbox=[round(x,2) for x in b['bbox']],w=im.width,h=im.height,bytes=out.stat().st_size,path=str(out.relative_to(ROOT))))
index.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')
# Crops from Netter plates: retain legible relevant labels, with provenance.
netter=next((ROOT/'علوم تشریح سر و گردن').glob('جلسه 1*/*Netter*.pdf'))
N=pymupdf.open(netter)
for plate,name,box in [(29,'nasal',(50,490,560,730)),(33,'foramina',(60,330,580,665))]:
 page=N[plate+51]; out=ROOT/f'headneck/images/hn03_netter_p{plate}_{name}.jpeg'
 pix=page.get_pixmap(matrix=pymupdf.Matrix(2.5,2.5),clip=pymupdf.Rect(box),alpha=False)
 Image.frombytes('RGB',(pix.width,pix.height),pix.samples).save(out,quality=92,optimize=True)
 data['assets'].append(dict(asset_id=out.stem,book='netter',session='hn03',source_file=str(netter.relative_to(ROOT)),page=plate+52,plate=plate,bbox=box,w=pix.width,h=pix.height,bytes=out.stat().st_size,path=str(out.relative_to(ROOT))))
index.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')
print('extracted',sum(map(len,PICKS.values()))+2)

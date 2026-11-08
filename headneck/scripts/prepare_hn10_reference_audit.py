"""Extract individually reviewed reference figures for the session-ten image audit."""
from pathlib import Path
import hashlib,json
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
N='علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1/Netter Atlas of Human Anatomy Classic Regional Approach.pdf'
G='علوم تشریح دستگاه اعصاب/user - Gray\'s Anatomy For Students, 3rd Edition-801-1000.pdf'
G2='علوم تشریح دستگاه اعصاب/user - Gray\'s Anatomy For Students, 3rd Edition-1001-1189.pdf'
# Rectangles use the dimensions of the explicitly reviewed renders, not printed page numbers.
ITEMS=[
 ('netter_100',N,100,(630,810),(30,65,600,745)),
 ('netter_124',N,124,(630,810),(30,65,600,745)),
 ('netter_179',N,179,(630,810),(30,65,600,745)),
 ('netter_181_upper',N,181,(630,810),(40,65,600,350)),
 ('gray_867',G,150,(827,1070),(75,500,412,970)),
 ('gray_868',G,150,(827,1070),(425,500,762,733)),
 ('gray_869',G,151,(827,1070),(240,455,585,966)),
 ('gray_870',G,152,(827,1070),(78,428,752,966)),
 ('gray_871',G,153,(827,1070),(75,415,752,966)),
 ('gray_872',G,154,(827,1070),(425,515,752,965)),
 ('gray_8138',G2,6,(674,872),(55,380,625,814)),
 ('gray_8139',G2,7,(765,990),(88,425,696,900)),
 ('gray_8140',G2,8,(765,990),(75,440,697,900)),
]
def main():
 target=ROOT/'headneck/images/hn10_refs';target.mkdir(parents=True,exist_ok=True);records=[];docs={}
 for name,source,page,size,coords in ITEMS:
  if source not in docs:docs[source]=pymupdf.open(ROOT/source)
  p=docs[source][page-1];w,h=size;x0,y0,x1,y1=coords
  clip=pymupdf.Rect(x0*p.rect.width/w,y0*p.rect.height/h,x1*p.rect.width/w,y1*p.rect.height/h)
  out=target/(name+'.png');p.get_pixmap(matrix=pymupdf.Matrix(2.5,2.5),clip=clip,alpha=False).save(out)
  records.append({'asset':str(out.relative_to(ROOT)),'source':source,'page':page,'reference_render_size':size,'rect':coords,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
 path=ROOT/'headneck/reports/hn10_evidence/reference_audit_candidates.json';path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 print(len(records),'reference figures extracted')
if __name__=='__main__':main()

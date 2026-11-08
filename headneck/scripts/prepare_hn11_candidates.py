"""Extract candidate figures from the original session-eleven face lecture."""
from pathlib import Path
import hashlib,json
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'علوم تشریح سر و گردن/جلسه 11 - صورت/face.pdf'
OUT=ROOT/'headneck/images/hn11_candidates'
# Rectangles use the 796×1030 source-page render. Captions remain typed separately.
FIGS=[
 ('01',1,(65,220,705,600)),('02',2,(60,210,705,515)),('03',5,(205,590,670,900)),
 ('04',6,(135,350,710,870)),('05',8,(95,155,720,880)),('06',9,(220,125,705,570)),
 ('07',11,(75,175,705,565)),('08',11,(115,615,705,905)),('09',12,(100,450,700,815)),
 ('10',13,(150,470,700,880)),('11',15,(135,580,690,905)),('12',17,(90,135,705,540)),
 ('13',18,(140,255,705,780)),('14',19,(115,135,705,620)),
]
def main():
 OUT.mkdir(parents=True,exist_ok=True);doc=pymupdf.open(SOURCE);records=[]
 for name,n,(x0,y0,x1,y1) in FIGS:
  page=doc[n-1];rect=pymupdf.Rect(x0*page.rect.width/796,y0*page.rect.height/1030,x1*page.rect.width/796,y1*page.rect.height/1030)
  out=OUT/f'lecture_figure_{name}_p{n:02}.png';page.get_pixmap(matrix=pymupdf.Matrix(2.5,2.5),clip=rect,alpha=False).save(out)
  records.append({'figure':name,'pdf_page':n,'rect_796x1030':[x0,y0,x1,y1],'asset':str(out.relative_to(ROOT)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
 manifest=ROOT/'headneck/reports/hn11_evidence/figure_candidates.json';manifest.parent.mkdir(parents=True,exist_ok=True)
 manifest.write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'source_pages':len(doc),'figures':records},ensure_ascii=False,indent=2)+'\n')
 print(len(records),'candidate figures')
if __name__=='__main__':main()

"""Extract figure candidates from the original session-ten lecture PDF."""
from pathlib import Path
import hashlib,json
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'علوم تشریح سر و گردن/جلسه 10 - اسکالپ و ناحیه تمپورال/Scalp &Temporal region.pdf'
OUT=ROOT/'headneck/images/hn10_candidates'
# Rectangles refer to a 918 × 1188 render. Page 3 and page 4 have distinct
# figures both numbered 4; pages 5 and 7 have distinct figures both numbered 5.
FIGS=[('01',1,(40,200,865,710),'1'),('02',2,(95,585,425,860),'2'),('03',3,(50,125,423,290),'3'),('04_temporal_upper',3,(85,430,400,800),'4'),('04_temporal_lower',3,(95,817,400,1045),'4'),('04_vessels_nerves',4,(50,205,810,560),'4'),('05_veins',5,(110,170,815,570),'5'),('05_clinical',7,(490,300,810,575),'5'),('06_clinical',7,(115,475,425,720),'6')]
def main():
 OUT.mkdir(parents=True,exist_ok=True);doc=pymupdf.open(SOURCE);rec=[]
 for name,n,rect,label in FIGS:
  page=doc[n-1];x0,y0,x1,y1=rect;clip=pymupdf.Rect(x0*page.rect.width/918,y0*page.rect.height/1188,x1*page.rect.width/918,y1*page.rect.height/1188)
  blob=page.get_pixmap(matrix=pymupdf.Matrix(2.5,2.5),clip=clip,alpha=False).tobytes('png');file=OUT/f'lecture_{name}_p{n:02}.png';file.write_bytes(blob)
  rec.append({'id':name,'source_label':label,'pdf_page':n,'asset':str(file.relative_to(ROOT)),'rect_overview_918x1188':rect,'sha256':hashlib.sha256(blob).hexdigest()})
 target=ROOT/'headneck/reports/hn10_evidence/figure_candidates.json';target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'source_pages':len(doc),'figures':rec},ensure_ascii=False,indent=2)+'\n')
 print(len(rec),'candidate images from',len(doc),'source pages')
if __name__=='__main__':main()

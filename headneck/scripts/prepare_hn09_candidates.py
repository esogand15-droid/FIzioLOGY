"""Extract session 9 figure candidates from lecture pages, without altering source.

Rectangles are measured against the 918 x 1188 overview renders. Figures 14 and
19 are on different pages from their printed captions; the extra page-11 image
has no visible figure number. Candidates require checking before publication.
"""
from pathlib import Path
import hashlib,json
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'علوم تشریح سر و گردن/جلسه 9 - اعصاب گردن و غده تیروید/neck nerve and thyroid gland.pdf'
OUT=ROOT/'headneck/images/hn09_candidates'
# number, physical PDF page (one-based), rectangle on overview render, caption page
FIGS=[
 ('01',1,(170,195,815,715),1),('02',2,(170,175,810,550),2),('03',2,(90,635,400,925),2),
 ('04',3,(465,190,800,530),3),('05',3,(50,245,405,565),3),
 ('06',4,(485,385,810,910),4),('07',4,(80,210,415,465),4),
 ('08',5,(475,560,820,900),5),('09',5,(80,185,450,355),5),
 ('10',6,(475,225,810,770),6),('11',8,(480,300,820,615),8),('12',8,(75,435,425,725),8),
 ('13',9,(45,145,425,415),9),('14',9,(80,685,460,1060),10),
 ('15',10,(500,670,810,1060),10),('extra11',11,(505,125,810,485),None),
 ('16',12,(55,200,450,590),12),('17',13,(80,380,450,760),13),
 ('18',14,(80,450,425,823),14),('19',15,(510,125,815,510),14)]

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 doc=pymupdf.open(SOURCE);records=[]
 for num,p,rect,caption_page in FIGS:
  page=doc[p-1];x0,y0,x1,y1=rect
  # Coordinates scale with the PDF page rather than with a cached screenshot.
  clip=pymupdf.Rect(x0*page.rect.width/918,y0*page.rect.height/1188,x1*page.rect.width/918,y1*page.rect.height/1188)
  png=page.get_pixmap(matrix=pymupdf.Matrix(2.5,2.5),clip=clip,alpha=False).tobytes('png')
  name=f'lecture_figure_{num}_p{p:02}.png';(OUT/name).write_bytes(png)
  records.append({'figure':num,'pdf_page':p,'caption_pdf_page':caption_page,'rect_overview_918x1188':rect,'asset':str((OUT/name).relative_to(ROOT)),'sha256':sha(png)})
 manifest={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':sha(SOURCE.read_bytes()),'source_pages':len(doc),'candidates':records}
 target=ROOT/'headneck/reports/hn09_evidence/figure_candidates.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(f'{len(doc)} source pages; {len(records)} figure candidates; {target.relative_to(ROOT)}')
if __name__=='__main__':main()

"""Index all four practical-anatomy files; extract labelled figure regions and text spans.

Extraction is mechanical and does not establish anatomical correctness or transcription accuracy.
"""
import hashlib,json
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'علوم تشریح سر و گردن/جلسه 13 - اناتومی سر و گردن عملی'
FILES={'1':'Practical anatomy 1.pdf','3':'Practical anatomy 3 .pdf','4':'Practical anatomy 4.pdf','5':'Practical anatomy اصلاحیه 5 .pdf'}
IMAGE_DIR=ROOT/'.cache/hn13/candidates'; REPORT=ROOT/'headneck/reports/hn13_evidence/source_inventory.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 IMAGE_DIR.mkdir(parents=True,exist_ok=True);REPORT.parent.mkdir(parents=True,exist_ok=True);out=[]
 for part,name in FILES.items():
  path=BASE/name;doc=pymupdf.open(path);pages=[]
  for i,page in enumerate(doc):
   spans=[]
   for block in page.get_text('dict')['blocks']:
    for line in block.get('lines',[]):
     for s in line['spans']:
      if not s['text'].strip():continue
      spans.append({'text':s['text'].strip(),'bbox':[round(v,2) for v in s['bbox']]})
   entry={'page':i+1,'width':page.rect.width,'height':page.rect.height,'spans':spans}
   if i>=2:
    regions=[]
    for im in page.get_images(full=True):regions.extend(page.get_image_rects(im[0]))
    # Keep text near the anatomy, but exclude the author's recurring attribution
    # when it is separate from the figure.  Do not infer the label of any arrow.
    for sp in spans:
     if 'Dr Mirzaei' not in sp['text'] and 'Hormozgan medical science university' not in sp['text']:
      regions.append(pymupdf.Rect(sp['bbox']))
    if regions:
     r=pymupdf.Rect(regions[0])
     for b in regions[1:]:r|=b
     r=(r+(-4,-4,4,4)) & page.rect
     image=IMAGE_DIR/f'part{part}_page{i+1:02}.png';page.get_pixmap(matrix=pymupdf.Matrix(2,2),clip=r,alpha=False).save(image)
     entry.update(figure=str(image.relative_to(ROOT)),figure_sha256=sha(image),figure_rect=[round(v,2) for v in r])
   pages.append(entry)
  out.append({'part':part,'source':str(path.relative_to(ROOT)),'sha256':sha(path),'page_count':len(doc),'pages':pages})
 REPORT.write_text(json.dumps({'sources':out},ensure_ascii=False,indent=2)+'\n')
 print('files',len(out),'pages',sum(x['page_count'] for x in out),'figures',sum('figure' in p for x in out for p in x['pages']))
if __name__=='__main__':main()

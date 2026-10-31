"""Measure a session-six PDF. Never marks manual review or scientific checks complete."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'render'))
from hn_updates import apply_update

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(pdf):
 doc=pymupdf.open(pdf); errors=[];outside=[];fonts={};embedded={}
 for n,page in enumerate(doc,1):
  for x in page.get_fonts(full=True):
   if x[0] not in fonts:
    _,_,_,data=doc.extract_font(x[0]);fonts[x[0]]=dict(xref=x[0],name=x[3],type=x[2],embedded_bytes=len(data))
    if x[3]!='Helvetica' and not data:errors.append(f'Unembedded font {x[3]}')
  for img in page.get_images(full=True):
   sha=hashlib.sha256(doc.extract_image(img[0])['image']).hexdigest();embedded.setdefault(sha,[]).append(n)
  for block in page.get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    for span in line['spans']:
     if not page.rect.contains(pymupdf.Rect(span['bbox'])):outside.append(dict(page=n,bbox=span['bbox'],text=span['text']))
 if outside:errors.append('Text outside PDF page')
 idx={r['path']:r for r in json.loads((ROOT/'headneck/images/INDEX.json').read_text())['assets']}
 topics=[t for f in ['hn06_a.json','hn06_b.json'] for t in json.loads((ROOT/'headneck/content'/f).read_text())];figures=[];occurrences={}
 updated=apply_update('hn06',{t['topic_id']:t['blocks'] for t in topics})
 for t in topics:
  for b in updated[t['topic_id']]:
   if b['type']!='plate':continue
   meta=idx[b['asset']];sha=digest(ROOT/b['asset']);pages=embedded.get(sha,[])
   if not pages:errors.append('Missing embedded asset '+b['asset'])
   occurrence=occurrences.get(b['asset'],0);occurrences[b['asset']]=occurrence+1
   output_page=pages[occurrence] if occurrence<len(pages) else None
   if output_page is None:errors.append('Unmapped image occurrence '+b['asset'])
   figures.append(dict(output_page=output_page,topic=t['topic_id'],asset=b['asset'],asset_sha256=sha,output_pages=pages,book=b['book'],source_file=meta['source_file'],source_pdf_page=meta['page'],bbox=meta['bbox'],citation=b['citation']))
 paths=[f'headneck/content/hn06_{x}.json' for x in ['a','b','transcription','update']]+['headneck/content/outline/hn06_topics.json']
 sources=sorted({r['source_file'] for r in figures})
 return dict(sha256=digest(pdf),pages=len(doc),bytes=pdf.stat().st_size,baseline_pdf_sha256=digest(ROOT/'pdf/HumsYar_HeadNeck_Jalase6.pdf'),errors=errors,outside_spans=outside,fonts=list(fonts.values()),figures=figures,content=[dict(file=p,sha256=digest(ROOT/p)) for p in paths],sources=[dict(file=p,sha256=digest(ROOT/p)) for p in sources],manual_review='NOT_INFERRED_BY_THIS_SCRIPT')
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pdf',type=Path,default=ROOT/'pdf/HumsYar_HeadNeck_Jalase6_FINAL.pdf');parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
 result=audit(args.pdf);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['sha256'],result['pages'],'pages; errors:',len(result['errors']));sys.exit(bool(result['errors']))

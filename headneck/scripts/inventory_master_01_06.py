"""Inventory all local study files and extract selected PDFs; NEVER certifies reading.

Large extracted text/image resources live in --work, outside Git. Existing source
files and published PDFs are read-only. Historical 1–3 baselines are reconstructed
from a pinned local Git object, never by executing old preparation scripts.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'headneck/master_01_06'
HISTORY='026cbcc1191751a491bcb37675adcb2cb8c827d0'
SKIP={'.git','.cache','.venv','node_modules','__pycache__','build','dist'}
EXTS={'.pdf','.pptx','.ppt','.docx','.doc','.txt','.md','.png','.jpg','.jpeg','.webp','.tif','.tiff','.svg','.json'}
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def session(path):
 m=re.search(r'(?:جلسه\s*|Jalase|hn0)(\d+)',str(path),re.I)
 return int(m[1]) if m and 1<=int(m[1])<=6 else None

def inventory(work):
 rows=[]
 for p in sorted(ROOT.rglob('*')):
  rel=p.relative_to(ROOT)
  if not p.is_file() or any(x in SKIP for x in rel.parts) or rel.parts[:2]==('headneck','master_01_06') or p.suffix.lower() not in EXTS:continue
  name=str(rel);n=session(rel);role='SUPPORT_FILE';include=False
  if p.suffix.lower()=='.pdf':
   if 'Gray' in p.name or 'Netter' in p.name or 'Snell' in p.name:role='REFERENCE_SCOPE_PENDING';include=True
   elif name.startswith('علوم تشریح سر و گردن/جلسه ') and n:role='PRIMARY_LECTURE';include=True
   elif name.startswith('pdf/') and n:role='EXISTING_MASTER';include=True
   elif any(s in name for s in ['علوم تشریح سر و گردن/جلسه 12','علوم تشریح سر و گردن/جلسه 13','علوم تشریح دستگاه اعصاب/جلسه 1 ','علوم تشریح دستگاه اعصاب/جلسه 2 ']):role='SUPPLEMENT_RELEVANCE_PENDING';include=True
   else:role='OUTSIDE_REQUESTED_SESSIONS'
  elif p.suffix.lower() in {'.ppt','.pptx','.doc','.docx'}:role='EDITABLE_SOURCE_RELEVANCE_PENDING';include=True
  elif name.startswith('headneck/content/') and n:role='EXISTING_TYPED_CONTENT';include=True
  elif name.startswith('headneck/images/') and n:role='EXISTING_FIGURE_ASSET'
  row=dict(file=name,type=p.suffix.lower()[1:],session=n,role=role,bytes=p.stat().st_size,sha256=digest(p),selected_for_extraction=include,content_review='NOT_IMPLIED_BY_INVENTORY')
  if p.suffix.lower()=='.pdf':
   try:
    with pymupdf.open(p) as doc:row.update(pages=len(doc),metadata=doc.metadata,encrypted=doc.needs_pass)
   except Exception as e:row['error']=str(e)
  rows.append(row)
 # Same-content files are duplicates, but not automatically omitted from scientific review.
 groups=defaultdict(list)
 for r in rows:groups[r['sha256']].append(r['file'])
 duplicates=[dict(sha256=h,files=ps) for h,ps in groups.items() if len(ps)>1]
 result=dict(status='INVENTORY_ONLY_NOT_CONTENT_OR_VISION_APPROVAL',files=rows,duplicate_files=duplicates,limitations=[dict(source='اطلس نثر',status='NO_SEPARATELY_IDENTIFIED_LOCAL_FILE',note='Netter is present; do not silently claim these are two books or that the separate named atlas was read.'),*[dict(source=x,status='NO_IDENTIFIED_LOCAL_COPY') for x in ["Junqueira's Basic Histology","Langman's Medical Embryology","Moore's Clinically Oriented Anatomy"]]],totals=dict(files=len(rows),selected=sum(r['selected_for_extraction'] for r in rows),types=dict(Counter(r['type'] for r in rows))))
 save(OUT/'source_inventory.json',result)
 return result

def history(work):
 rows=[]
 for n in range(1,4):
  names=[f'headneck/content/hn{n:02}_{s}.json' for s in ['a','b','update']]+[f'headneck/content/outline/hn{n:02}_topics.json',f'pdf/HumsYar_HeadNeck_Jalase{n}.pdf']
  if n==3:names+=['headneck/content/hn03_source_transcription_wip.json','headneck/reports/HN_S03_TRANSCRIPTION_TOPIC_MAP_WIP.json']
  else:names+=[f'headneck/reports/HN_S{n:02}_VERBATIM_MAP.json']
  for name in names:
   b=subprocess.check_output(['git','show',HISTORY+':'+name],cwd=ROOT);dest=work/'historical'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
   row=dict(file=name,commit=HISTORY,session=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),workspace_file=str(dest.relative_to(ROOT)),review='HISTORICAL_NOT_REAPPROVED')
   if name.endswith('.pdf'):
    with pymupdf.open(stream=b,filetype='pdf') as doc:row['pages']=len(doc)
   rows.append(row)
 save(OUT/'historical_sources.json',dict(commit=HISTORY,files=rows))
 return rows

def extract_pdf(path,label,work,next_id):
 """Record raster placements/resources, text blocks, and vector-presence warnings.

 A raster resource can contain multiple scientific panels. Panel segmentation is
 never invented from XObject counts; unassessed panels keep the review gate shut.
 """
 cache=work/'extracted'/label;cache.mkdir(parents=True,exist_ok=True)
 manifest_path=cache/'manifest.json'
 with pymupdf.open(path) as doc:
  if doc.needs_pass:raise ValueError(f'Encrypted PDF: {path}')
  placements=[];pages=[];xrefs={};image_dir=work/'images';image_dir.mkdir(parents=True,exist_ok=True)
  text_out=cache/'pages.jsonl'
  with text_out.open('w') as stream:
   for n,page in enumerate(doc,1):
    blocks=page.get_text('dict',flags=pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES)['blocks']
    text=page.get_text(sort=False);(cache/f'{n:04}.txt').write_text(text)
    spans=[s for b in blocks for line in b.get('lines',[]) for s in line.get('spans',[])]
    page_row=dict(pdf_page=n,printed_page=None,printed_page_status='NEEDS_VISUAL_CONFIRMATION',raw_text=text,blocks=blocks,character_count=len(text),heading_candidates=[dict(text=s['text'],size=s['size']) for s in spans if s['size']>=13 and s['text'].strip()],transcription_status='RAW_EXTRACTION_NOT_VERIFIED',vision_status='NOT_REVIEWED')
    stream.write(json.dumps(page_row,ensure_ascii=False)+'\n')
    infos=page.get_image_info(xrefs=True)
    for k,img in enumerate(infos):
     x=img['xref'];resource=None
     if x and x not in xrefs:
      try:
       original=doc.extract_image(x);data=original['image'];h=hashlib.sha256(data).hexdigest();dest=image_dir/(h+'.'+original['ext'])
       if not dest.exists():dest.write_bytes(data)
       xrefs[x]=dict(resource_sha256=h,resource_file=str(dest.relative_to(work)),width=original['width'],height=original['height'],source_xref=x)
      except Exception as e:xrefs[x]=dict(source_xref=x,extraction_error=str(e))
     resource=xrefs.get(x,{})
     row=dict(image_id=f'IMG-{next_id:06}',source_label=label,pdf_page=n,placement=k,bbox=list(img['bbox']),resource=resource,inline=not bool(x),vision_status='NOT_REVIEWED',scientific_panel_status='UNASSESSED',reviewed_subpanels=[],session_candidates=[],topic_candidates=[],decision='PENDING_VISION_AND_RELEVANCE',output_location=None)
     placements.append(row);next_id+=1
    pages.append(dict(pdf_page=n,text_characters=len(text),image_placements=len(infos),low_text_needs_ocr_triage=len(text.strip())<50,has_vector_drawings=bool(page.get_drawings()),visual_review='NOT_REVIEWED'))
  # Every page remains a review unit as well: diagrams can be vector/inline and
  # several panels may be merged into one raster, so image counts aren't coverage.
  result=dict(label=label,file=str(path.relative_to(ROOT)),sha256=digest(path),pages=pages,image_occurrences=placements,unique_resources=len(xrefs),extractor_versions=dict(pymupdf=pymupdf.VersionBind),status='EXTRACTED_NOT_REVIEWED')
 save(manifest_path,result)
 return result,next_id

def extract_selected(inv,hist,work):
 tasks=[(ROOT/r['file'],'SRC-'+str(i).zfill(3),r) for i,r in enumerate(inv['files'],1) if r['selected_for_extraction'] and r['type']=='pdf']
 tasks +=[(ROOT/r['workspace_file'],f'HIST-HN{r["session"]:02}',r) for r in hist if r['file'].endswith('.pdf')]
 summaries=[];next_id=1
 registry=work/'image_registry.jsonl';registry.parent.mkdir(parents=True,exist_ok=True)
 with registry.open('w') as stream:
  for path,label,meta in tasks:
   result,next_id=extract_pdf(path,label,work,next_id)
   for row in result['image_occurrences']:
    row.update(source_file=meta['file'],source_sha256=meta['sha256'],source_role=meta.get('role','HISTORICAL_MASTER'),session_candidates=[meta['session']] if meta.get('session') else [])
    stream.write(json.dumps(row,ensure_ascii=False)+'\n')
   summaries.append(dict(label=label,file=meta['file'],sha256=meta['sha256'],role=meta.get('role','HISTORICAL_MASTER'),session=meta.get('session'),pages=len(result['pages']),image_occurrences=len(result['image_occurrences']),unique_resources=result['unique_resources'],low_text_pages=[p['pdf_page'] for p in result['pages'] if p['low_text_needs_ocr_triage']],manifest=str((work/'extracted'/label/'manifest.json').relative_to(ROOT)),text_reviewed=0,vision_reviewed=0))
   print(label,len(result['pages']),len(result['image_occurrences']),meta['file'],flush=True)
 save(OUT/'extraction_inventory.json',dict(status='EXTRACTION_NOT_VISION_OR_TRANSCRIPTION_APPROVAL',files=summaries,image_registry_sha256=digest(registry),image_registry=str(registry.relative_to(ROOT)),image_occurrences=next_id-1,source_pages=sum(r['pages'] for r in summaries),note='The registry includes irrelevant/duplicate candidates; relevance and panel segmentation require actual review. No extracted item has been automatically approved.'))

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,default=ROOT/'.cache/master_01_06');parser.add_argument('--extract',action='store_true');parser.add_argument('--reuse-inventory',action='store_true',help='Replay the saved inventory without renumbering sources when unrelated files change.');args=parser.parse_args();args.work.mkdir(parents=True,exist_ok=True)
 if args.reuse_inventory:
  inv=json.loads((OUT/'source_inventory.json').read_text())
  for r in inv['files']:
   if r['selected_for_extraction'] and digest(ROOT/r['file'])!=r['sha256']:raise ValueError('Selected source changed: '+r['file'])
 else:inv=inventory(args.work)
 hist=history(args.work)
 if args.extract:extract_selected(inv,hist,args.work)
 print(inv['totals'],flush=True)
if __name__=='__main__':main()

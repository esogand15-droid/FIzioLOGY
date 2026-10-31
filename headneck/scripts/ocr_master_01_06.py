"""OCR source lectures and unreadable PDF text; OCR output is NOT verified text.

Requires the optional tesserocr wheel and eng/fas data in --tessdata. No PDF is
created. Resume is keyed to the source hash, page, engine, model hashes and scale.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import unicodedata
import pymupdf
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'headneck/master_01_06'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def quality(text):
 nonspace=[c for c in text if not c.isspace()]
 control=sum(unicodedata.category(c)=='Cc' or c=='\ufffd' for c in nonspace)
 return dict(characters=len(nonspace),control_or_replacement=control,ratio=control/max(1,len(nonspace)),needs_ocr=len(nonspace)<50 or control/max(1,len(nonspace))>.03)

def worker(args):
 path,page_number,dest,recipe=args;dest=Path(dest)
 if dest.exists():
  old=json.loads(dest.read_text())
  if old.get('recipe')==recipe:return dict(file=str(dest.relative_to(ROOT)),sha256=sha(dest),cached=True)
 os.environ['OMP_THREAD_LIMIT']='1'
 import tesserocr
 with pymupdf.open(path) as doc:
  pix=doc[page_number-1].get_pixmap(matrix=pymupdf.Matrix(recipe['scale'],recipe['scale']),alpha=False,colorspace=pymupdf.csRGB)
  image=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
 with tesserocr.PyTessBaseAPI(path=recipe['tessdata'],lang=recipe['language'],psm=tesserocr.PSM.AUTO) as api:
  api.SetImage(image);text=api.GetUTF8Text();confidence=api.MeanTextConf()
  result=dict(recipe=recipe,pdf_page=page_number,text=text,mean_text_confidence=confidence,status='OCR_ONLY_NOT_VISUALLY_RECONCILED')
 dest.parent.mkdir(parents=True,exist_ok=True);tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');tmp.replace(dest)
 return dict(file=str(dest.relative_to(ROOT)),sha256=sha(dest),cached=False)

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,default=ROOT/'.cache/master_01_06');parser.add_argument('--workers',type=int,default=4);parser.add_argument('--scale',type=float,default=2);args=parser.parse_args()
 import tesserocr
 tess=(args.work/'tessdata').resolve();models={l:sha(tess/f'{l}.traineddata') for l in ['eng','fas']}
 inv=json.loads((OUT/'extraction_inventory.json').read_text());tasks=[];triage=[];seen={}
 for source in inv['files']:
  if source['role'] not in ['PRIMARY_LECTURE','REFERENCE_SCOPE_PENDING','SUPPLEMENT_RELEVANCE_PENDING']:continue
  if source['sha256'] in seen:
   triage.append(dict(label=source['label'],file=source['file'],identical_to=seen[source['sha256']],reason='BYTE_IDENTICAL_DOCUMENT_REUSE_NOT_NEW_READING'));continue
  seen[source['sha256']]=source['label'];ocr_pages=[];scores=[]
  for n in range(1,source['pages']+1):
   text=(args.work/'extracted'/source['label']/f'{n:04}.txt').read_text();q=quality(text);scores.append(q)
   if source['role']=='PRIMARY_LECTURE' or q['needs_ocr']:
    lang='fas+eng' if source['role'] in ['PRIMARY_LECTURE','SUPPLEMENT_RELEVANCE_PENDING'] else 'eng'
    recipe=dict(source_sha256=source['sha256'],pdf_page=n,scale=args.scale,language=lang,tessdata=str(tess),models={l:models[l] for l in lang.split('+')},tesserocr='2.12.0',tesseract=tesserocr.tesseract_version(),status='NOT_PROOF_OF_READING')
    target=args.work/'ocr'/source['label']/f'{n:04}.json';tasks.append((str(ROOT/source['file']),n,str(target),recipe));ocr_pages.append(n)
  triage.append(dict(label=source['label'],file=source['file'],source_sha256=source['sha256'],pages=source['pages'],pages_needing_ocr=ocr_pages,text_quality_scores=scores))
 triage_path=OUT/'ocr_triage.json';triage_path.write_text(json.dumps(dict(status='TRIAGE_NOT_READING',models=models,sources=triage,ocr_pages_scheduled=len(tasks)),ensure_ascii=False,indent=2)+'\n')
 print('OCR pages scheduled:',len(tasks),flush=True)
 receipts=[]
 with ProcessPoolExecutor(max_workers=args.workers) as pool:
  for i,result in enumerate(pool.map(worker,tasks),1):
   receipts.append(result)
   if i%25==0 or i==len(tasks):print('OCR',i,'/',len(tasks),flush=True)
 receipt_file=args.work/'ocr_receipts.json';receipt_file.write_text(json.dumps(receipts,indent=2)+'\n')
 (OUT/'ocr_run.json').write_text(json.dumps(dict(status='OCR_COMPLETE_NOT_VERIFIED',completed=len(receipts),models=models,receipts=str(receipt_file.relative_to(ROOT)),receipts_sha256=sha(receipt_file),engine=tesserocr.tesseract_version(),options=dict(scale=args.scale,workers=args.workers)),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()

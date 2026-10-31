"""Verify byte identity and recorded coverage, NOT whether reading actually happened."""
import hashlib
import json
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'headneck/reports/hn05_final_evidence'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(name):return json.loads((E/name).read_text())
def verify():
 pdf=ROOT/'pdf/HumsYar_HeadNeck_Jalase5_FINAL.pdf'
 sha=digest(pdf);count=len(pymupdf.open(pdf))
 manual=load('manual_review.json')
 assert manual['pdf_sha256']==sha and not manual['not_yet_reviewed']
 assert [r['page'] for r in manual['reviewed_pages']]==list(range(1,count+1))
 for r in manual['reviewed_pages']:assert digest(E/r['render'])==r['render_sha256']
 source=load('source_editorial_review.json');refs=load('reference_editorial_inventory.json')
 for inventory,key in [(source,'source_pages'),(refs,'pages')]:
  assert inventory['final_pdf_sha256']==sha
  for r in inventory[key]:assert digest(E/r['source_render'])==r['source_render_sha256']
 assert digest(ROOT/source['file'])==source['source_sha256']
 assert [r['source_pdf_page'] for r in source['source_pages']]==list(range(1,46))
 assert {(r['book'],r['source_pdf_page']) for r in refs['pages']}=={*(('netter',n) for n in [*range(95,106),108,109]),*(('gray',n) for n in range(26,36))}
 for r in refs['sources']:assert digest(ROOT/r['file'])==r['sha256']
 for n,printed in [(33,1006),(34,1005)]:
  assert next(r for r in refs['pages'] if r['book']=='gray' and r['source_pdf_page']==n)['printed_page']==printed
 machine=load('machine_manifest.json')
 assert machine['sha256']==sha and not machine['errors']
 assert machine['bytes']==pdf.stat().st_size and machine['pages']==count
 assert machine['baseline_pdf_sha256']==digest(ROOT/'pdf/HumsYar_HeadNeck_Jalase5.pdf')=='9ec70b745fc91b0740065bef73c83661761ee0b5b2dc4a311ec121194286fe70'
 for r in machine['content']+machine['sources']:assert digest(ROOT/r['file'])==r['sha256']
 assert len(machine['figures'])==71
 for r in machine['figures']:
  assert digest(ROOT/r['asset'])==r['asset_sha256']
  assert (ROOT/r['source_file']).is_file()
 assert load('layout_trace.json')['sha256']==sha
 assert sha in (ROOT/'headneck/reports/HN_S05_FINAL_TECHNICAL_QA_REPORT.md').read_text()
 return dict(sha256=sha,pages=count,source_pages=45,reference_pages=23,figures=71,result='Byte identity and recorded coverage verified; not automatic proof of reading or scientific correctness.')
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))

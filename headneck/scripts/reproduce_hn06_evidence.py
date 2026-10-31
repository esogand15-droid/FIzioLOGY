"""Recreate exact reviewed page images outside Git, validating recorded JPEG hashes.

Images are not committed to avoid duplicated source/output raster datasets. This
only reconstructs byte evidence; it does not perform or certify visual reading.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'headneck/reports/hn06_final_evidence'
def records():
 manual=json.loads((E/'manual_review.json').read_text())
 for r in manual['reviewed_pages']:
  yield r['render'],r['render_sha256'],dict(source_file='pdf/HumsYar_HeadNeck_Jalase6_FINAL.pdf',pdf_page=r['page'],**manual['render_recipe'])
 for name,key in [('source_editorial_review.json','source_pages'),('reference_editorial_inventory.json','pages')]:
  for r in json.loads((E/name).read_text())[key]:yield r['source_render'],r['source_render_sha256'],r['render_recipe']
def reproduce(out):
 docs={};n=0
 try:
  for rel,sha,recipe in records():
   dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True)
   if not dest.is_file() or hashlib.sha256(dest.read_bytes()).hexdigest()!=sha:
    path=recipe['source_file']
    if path not in docs:docs[path]=pymupdf.open(ROOT/path)
    page=docs[path][recipe['pdf_page']-1]
    pix=page.get_pixmap(matrix=pymupdf.Matrix(recipe['scale'],recipe['scale']))
    data=pix.pil_tobytes(format='JPEG',quality=recipe['quality'])
    assert hashlib.sha256(data).hexdigest()==sha, f'Render mismatch: {rel}. Check pinned source and recorded PyMuPDF/Pillow versions.'
    dest.write_bytes(data)
   n+=1
 finally:
  for doc in docs.values():doc.close()
 return n
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=ROOT/'.cache/hn06-reproduced');args=parser.parse_args();print(reproduce(args.out),'verified renders in',args.out)

"""Reproduce only the recorded view files and check hashes, without claiming Vision.

Source PDFs and extracted resource images must be present. Use the pinned
inventory replay + inline-image extraction to restore the ignored cache first.
--out mirrors repository-relative paths below another ignored directory.
"""
from pathlib import Path
import argparse,hashlib,json
import pymupdf
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'headneck/master_01_06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reproduce(dest):
 extraction=json.loads((OUT/'extraction_inventory.json').read_text());sources={r['label']:r for r in extraction['files']};count=0
 for file in ['lecture_page_observations.json','reference_page_observations.json']:
  for r in json.loads((OUT/file).read_text()):
   src=ROOT/sources[r['source_label']]['file'];recipe=r['render_recipe']
   if sha(src)!=r['source_sha256']:raise ValueError('Source SHA changed: '+str(src))
   if pymupdf.VersionBind!=recipe['pymupdf']:raise ValueError('Renderer version differs')
   with pymupdf.open(src) as doc:pix=doc[r['pdf_page']-1].get_pixmap(matrix=pymupdf.Matrix(recipe['scale'],recipe['scale']),alpha=False)
   target=dest/r['render'];target.parent.mkdir(parents=True,exist_ok=True);pix.save(target,jpg_quality=recipe['jpeg_quality'])
   if sha(target)!=r['render_sha256']:raise ValueError('Render differs: '+str(target))
   count+=1
 registry_path=ROOT/'.cache/master_01_06/image_registry.jsonl';registry={r['image_id']:r for r in map(json.loads,registry_path.read_text().splitlines())}
 for r in map(json.loads,(OUT/'vision_reviews.jsonl').read_text().splitlines()):
  if sha(registry_path)!=r['image_registry_sha256']:raise ValueError('Registry version differs')
  meta=registry[r['image_id']];resource=ROOT/'.cache/master_01_06'/meta['resource']['resource_file']
  if sha(resource)!=r['resource_sha256']:raise ValueError('Observed resource changed')
  im=Image.open(resource).convert('RGB');canvas=Image.new('RGB',(max(600,im.width),im.height+60),'white');canvas.paste(im,((canvas.width-im.width)//2,60));d=ImageDraw.Draw(canvas)
  d.text((10,10),r['image_id']+' | '+r['source_label']+' | PDF page '+str(r['pdf_page']),fill='black',font=ImageFont.load_default(size=17))
  d.text((10,32),'Identity header only; original pixels below, not upscaled.',fill='black',font=ImageFont.load_default(size=13))
  target=dest/r['preview'];target.parent.mkdir(exist_ok=True,parents=True);canvas.save(target)
  if sha(target)!=r['preview_sha256']:raise ValueError('Preview differs: '+str(target))
  count+=1
 return count
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=ROOT/'.cache/master_01_06/reproduced_views');args=parser.parse_args();n=reproduce(args.out);print(f'{n} view files reproduced with identical hashes; reproduction is NOT evidence of new reading or scientific approval.')

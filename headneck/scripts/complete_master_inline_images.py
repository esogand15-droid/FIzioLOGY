"""Extract the inline raster placements absent from xref-only extraction.

IDs/page locations stay unchanged. Rebind only reviewed resources whose exact
pixel-resource hashes have been checked; a changed registry is not reapproval.
"""
from pathlib import Path
import hashlib,json
from collections import defaultdict
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'headneck/master_01_06';WORK=ROOT/'.cache/master_01_06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(box):return tuple(round(v,2) for v in box)
def main():
 registry=WORK/'image_registry.jsonl';rows=[json.loads(l) for l in registry.read_text().splitlines()]
 pending=defaultdict(list)
 for r in rows:
  if r['inline'] and not r['resource'].get('resource_file'):pending[r['source_label']].append(r)
 summaries=json.loads((OUT/'extraction_inventory.json').read_text());lookup={r['label']:r for r in summaries['files']};receipts=[]
 for label,rs in pending.items():
  entry=lookup[label];p=ROOT/entry['file']
  if not p.exists():p=WORK/'historical'/entry['file']
  with pymupdf.open(p) as doc:
   by_page=defaultdict(list)
   for r in rs:by_page[r['pdf_page']].append(r)
   for n,page_rows in by_page.items():
    page=doc[n-1];blocks=page.get_text('dict',flags=pymupdf.TEXTFLAGS_DICT)['blocks'];candidates=defaultdict(list)
    for b in blocks:
     if b['type']==1:candidates[key(b['bbox'])].append(b)
    for r in page_rows:
     matches=candidates.get(key(r['bbox']),[])
     # get_image_info rounds some inline placement boxes to enclosing PDF
     # points; get_text keeps the fractional transform (observed on covers).
     if not matches:matches=[b for b in blocks if b['type']==1 and max(abs(a-c) for a,c in zip(b['bbox'],r['bbox']))<=1.1]
     info=page.get_image_info(xrefs=True)[r['placement']]
     # Some scanned inline placements have a slightly padded transform.
     # Resolve those by the decoded-pixel digest, NOT a guessed crop.
     if len(matches)!=1:
      matches=[b for b in blocks if b['type']==1 and pymupdf.Pixmap(b['image']).digest==info['digest']]
     if not matches:raise ValueError(f'{r["image_id"]}: no inline resource with identical decoded pixels')
     # Multiple appearances with the same decoded digest are the same pixels;
     # keep the placement bbox from the registry, not the text-block bbox.
     b=matches[0]
     if pymupdf.Pixmap(b['image']).digest!=info['digest']:raise ValueError(r['image_id']+': decoded pixels differ')
     data=b['image'];h=hashlib.sha256(data).hexdigest();dest=WORK/'images'/(h+'.'+b['ext']);dest.write_bytes(data)
     r['resource']=dict(resource_sha256=h,resource_file=str(dest.relative_to(WORK)),width=b['width'],height=b['height'],source_xref=0,extracted_via='PDF_TEXT_DICTIONARY_IMAGE_BLOCK',not_reviewed_by_extraction=True)
     receipts.append(dict(image_id=r['image_id'],source_label=label,pdf_page=n,resource_sha256=h))
  manifest=ROOT/entry['manifest'];m=json.loads(manifest.read_text());resource_by_id={r['image_id']:r['resource'] for r in rs}
  for r in m['image_occurrences']:
   if r['image_id'] in resource_by_id:r['resource']=resource_by_id[r['image_id']]
  manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 tmp=registry.with_suffix('.tmp');tmp.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows));tmp.replace(registry)
 summaries['image_registry_sha256']=sha(registry);summaries['inline_extraction_completed']=all(r['resource'].get('resource_file') for r in rows);summaries['inline_image_occurrences']=sum(r['inline'] for r in rows)
 summaries['unique_resource_sha256_count']=len({r['resource']['resource_sha256'] for r in rows})
 summaries['count_warning']='Resource placements include text glyphs, headings, logos and duplicates. They are not scientific-figure or subpanel counts.'
 (OUT/'extraction_inventory.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2)+'\n')
 (WORK/'inline_extraction_receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
 print('Extracted',len(receipts),'inline placements; registry SHA',sha(registry))
if __name__=='__main__':main()

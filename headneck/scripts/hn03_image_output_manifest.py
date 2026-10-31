#!/usr/bin/env python3
"""Bind the 43 used session-3 image assets to actual PDF pages by exact JPEG bytes.

Machine evidence only: this does not establish crop accuracy, figure relevance,
label legibility, or completeness of the Netter/Gray independent-figure inventory.
"""
import hashlib, json, os, sys
from pathlib import Path
import pymupdf
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'render'))
from hn_updates import apply_update

pdf = Path(sys.argv[1]); session = 'hn03'
os.environ['HUMSYAR_HN03_WIP'] = '1'
content = {t['topic_id']:t['blocks'] for part in ('a','b')
           for t in json.loads((ROOT/f'headneck/content/hn03_{part}.json').read_text(encoding='utf-8'))}
content=apply_update(session,content)
assets=[]
for tid,blocks in content.items():
    for i,b in enumerate(blocks):
        if b['type']!='plate':continue
        data=(ROOT/b['asset']).read_bytes()
        assets.append({'id':f'{tid}-plate-{i:03}','topic':tid,'asset':b['asset'],
            'asset_sha256':hashlib.sha256(data).hexdigest(),'source':b['book'],
            'citation':b.get('citation',''),'title':b.get('title',''),
            'source_reference':b.get('src',''),'output_pages':[],
            'image_visual_verification':'NOT_STARTED',
            'caveat':'Exact byte match confirms embedding only; not source/crop relevance or legibility.'})
doc=pymupdf.open(pdf)
for n,page in enumerate(doc,1):
    for image in page.get_images(full=True):
        xref=image[0]
        try: data=doc.extract_image(xref)['image']
        except (KeyError,ValueError):continue
        h=hashlib.sha256(data).hexdigest()
        for record in assets:
            if record['asset_sha256']==h:
                boxes=page.get_image_rects(xref)
                record['output_pages'].append({'page':n,'bbox_pdf_points':[list(r) for r in boxes]})
missing=[r['asset'] for r in assets if not r['output_pages']]
report={'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'plates':len(assets),
        'matched_plates':len(assets)-len(missing),'missing':missing,'images':assets,
        'disclaimer':'Used-output image manifest only. It does not inventory every independent source figure.'}
out=ROOT/'headneck/reports/hn03_audit_evidence/output_images.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print(f"{report['matched_plates']} of {len(assets)} plate assets matched by exact bytes; missing={len(missing)}")
if missing:raise SystemExit(1)

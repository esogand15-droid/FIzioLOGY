"""Machine evidence only: byte-identical embedded figures, bounds, and source mapping.

Does not assign human/visual/scientific VERIFIED statuses. Those belong in the
separate manual_review.json, bound to an exact PDF SHA-256.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
import pymupdf as fitz
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'render'))
from hn_updates import apply_update

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(pdf,out):
    original={t['topic_id']:t['blocks'] for t in json.loads((ROOT/'headneck/content/hn04_a.json').read_text())}
    content=apply_update('hn04',original)
    idx={a['path']:a for a in json.loads((ROOT/'headneck/images/INDEX.json').read_text())['assets']}
    doc=fitz.open(pdf); embedded=defaultdict(set); xrefs={};pages=[];errors=[]
    for n,p in enumerate(doc,1):
        spans=[s for b in p.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']]
        outside=[s['bbox'] for s in spans if s['bbox'][0]<-1 or s['bbox'][1]<-1 or s['bbox'][2]>p.rect.width+1 or s['bbox'][3]>p.rect.height+1]
        images=p.get_images(full=True)
        for row in images:
            x=row[0]
            if x not in xrefs:xrefs[x]=hashlib.sha256(doc.extract_image(x)['image']).hexdigest()
            embedded[xrefs[x]].add(n)
        pages.append(dict(pdf_page=n,text_spans=len(spans),images=len(images),outside_page_bounds=outside))
        if outside:errors.append(f'page {n}: text outside page')
    figures=[]
    for tid,blocks in content.items():
        for i,b in enumerate(blocks):
            if b['type']!='plate':continue
            a=idx[b['asset']];h=sha(ROOT/b['asset']);loc=sorted(embedded.get(h,[]))
            if not loc:errors.append(f'image not embedded byte-for-byte: {b["asset"]}')
            figures.append(dict(topic_id=tid,block_index=i,title=b['title'],asset=b['asset'],asset_sha256=h,
              source_file=a['source_file'],source_part=a.get('part'),source_pdf_page=a['page'],printed_page=a.get('printed_page'),plate=a.get('plate'),figure=a.get('figure'),crop_bbox=a['bbox'],mask_rects=a.get('mask_rects',[]),
              output_pdf_pages=loc,embedded_bytes_verified=bool(loc),subfigure_inventory_status='NOT_STARTED'))
    source_dir=ROOT/'علوم تشریح سر و گردن/جلسه 4 - قاعده جمجمه'
    source_pages=[];sources=[]
    for part,p in enumerate(sorted(source_dir.glob('*.pdf')),1):
        source=fitz.open(p);sources.append(dict(part=part,file=str(p.relative_to(ROOT)),pages=len(source),sha256=sha(p)))
        for n in range(1,len(source)+1):
            block_ids=[]
            for tid,blocks in original.items():
                for i,b in enumerate(blocks):
                    m=re.search(r'بخش ([۱۲])، صفحهٔ PDF (\d+)',b.get('src',''))
                    if m and int(m[1])==part and int(m[2])==n:block_ids.append(f'{tid}#{i}')
            assets=[f['asset'] for f in figures if f['source_part']==part and f['source_pdf_page']==n]
            source_pages.append(dict(part=part,pdf_page=n,role='cover' if n==1 else 'content',base_block_ids=block_ids,figure_assets=assets,independent_word_by_word_status='NOT_STARTED'))
    report=dict(pdf=str(pdf.relative_to(ROOT)),sha256=sha(pdf),pdf_pages=len(doc),base_blocks=sum(map(len,original.values())),updated_blocks=sum(map(len,content.values())),block_types=dict(Counter(b['type'] for bs in content.values() for b in bs)),
                sources=sources,source_pages=source_pages,output_pages=pages,figures=figures,unique_embedded_images=len(xrefs),errors=errors,
                limitations=['This is machine evidence, not a completed visual or scientific review.','Source-page attribution does not prove complete or faithful transcription.','A figure asset may contain several independent subfigures.'])
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(doc)} pages; {len(figures)} figure placements; {len(xrefs)} unique byte-matched embedded images; errors={len(errors)}')
    return bool(errors)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--pdf',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    raise SystemExit(audit(a.pdf.resolve(),a.out.resolve()))

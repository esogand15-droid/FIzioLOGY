"""Check evidence identity/coverage; cannot establish whether a page was read."""
from pathlib import Path
import hashlib
import json
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'headneck/reports/hn04_final_evidence'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    pdf = ROOT / 'pdf/HumsYar_HeadNeck_Jalase4_FINAL.pdf'
    sha = digest(pdf)
    count = len(pymupdf.open(pdf))
    manual = json.loads((EVIDENCE / 'manual_review.json').read_text())
    assert manual['pdf_sha256'] == sha
    assert not manual['not_yet_reviewed']
    assert [p['page'] for p in manual['reviewed_pages']] == list(range(1, count + 1))
    for row in manual['reviewed_pages']:
        assert digest(EVIDENCE / row['render']) == row['render_sha256'], row['page']
    source = json.loads((EVIDENCE / 'source_editorial_review.json').read_text())
    refs = json.loads((EVIDENCE / 'reference_editorial_inventory.json').read_text())
    for inventory, key in [(source, 'source_pages'), (refs, 'pages')]:
        assert inventory['final_pdf_sha256'] == sha
        for row in inventory[key]:
            assert digest(EVIDENCE / row['source_render']) == row['source_render_sha256']
    assert {(p['part'], p['source_pdf_page']) for p in source['source_pages']} == {
        *((1, n) for n in range(1, 26)), *((2, n) for n in range(1, 15))}
    assert sum(p['review_status'] == 'COVER_EXCLUDED' for p in source['source_pages']) == 2
    assert {(p['book'], p['source_pdf_page']) for p in refs['pages']} == {
        *(('netter', n) for n in [81, 82, 83, 84, 85, 86, 113, 114, 115, 177]),
        *(('gray', n) for n in range(88, 98))}
    for book in refs['sources']:
        assert digest(ROOT / book['file']) == book['sha256']
    machine = json.loads((EVIDENCE / 'machine_manifest.json').read_text())
    assert machine['sha256'] == sha and not machine['errors']
    for s in machine['sources']:
        assert digest(ROOT / s['file']) == s['sha256']
    for f in machine['figures']:
        assert (ROOT / f['source_file']).is_file(), f['source_file']
    assert json.loads((EVIDENCE / 'layout_trace.json').read_text())['sha256'] == sha
    return dict(sha256=sha, output_pages=count, source_pages=39, reference_pages=20,
                result='Evidence byte identity and recorded coverage verified; not automatic proof of reading.')


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))

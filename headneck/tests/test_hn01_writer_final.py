"""Checks for the writer edition; source/reference data stay untouched."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'headneck/scripts'))
import build_hn01_writer_final as b


def test_baseline_blocks_and_overlay_are_preserved():
    base, content, _, _ = b.original_blocks()
    assert sum(len(t['blocks']) for t in base) == 187
    assert sum(x['_origin'].startswith('old_overlay:') for rows in content.values() for x in rows) == 52
    for topic in base:
        rows = content[topic['topic_id']]
        for i, original in enumerate(topic['blocks']):
            result = next(x for x in rows if x['_origin'] == f'base:{i}')
            if original['type'] in ('p', 'ul', 'ol'):
                for key in ('text', 'items'):
                    if key in original:
                        assert result[key] == original[key]


def test_educational_content_and_figures_resolve():
    added = b.reader_additions()
    plans, _, _, stats = b.prepare_plan(added)
    assert len(added) == len(plans) == 17
    assert stats['base_blocks'] == 187
    assert stats['old_overlay_blocks'] == 52
    for item in stats['new_image_instruction_resolution']:
        assert item['figures'] or item['typed_review_card']
    assert all(added[tid]['diagram']['nodes'] for tid in plans)


def test_reader_cleanup_and_labels():
    assert not b.BAD.search(b.clean('hn01-T14، SRC-648، PDF page 45'))
    assert 'نتر' in b.reference({'source_label': 'SRC-648', 'pdf_page': 45, 'plate': 8})
    assert len(b.W.BOUNDARIES) == len(b.W.GUIDES) == 17

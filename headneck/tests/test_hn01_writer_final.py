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


def test_writer_layout_uses_one_historical_identity_card_per_topic():
    _, rows, _, outline = b.original_blocks()
    assert len(outline['topics']) == 17
    for topic in outline['topics']:
        blocks = rows[topic['topic_id']]
        assert blocks[0]['type'] == 'idcard'
        assert sum(block['type'] == 'idcard' for block in blocks) == 1
        assert len(blocks[0]['rows']) == 5
    assert b.compact_references([{'source_label': 'SRC-648', 'plate': 25, 'pdf_page': 77}]).startswith('نتر')


def test_layout_script_closes_with_checklist_not_figure_index():
    source = (ROOT / 'headneck/scripts/build_hn01_writer_final.py').read_text()
    assert "book.h1('جمع‌بندی، چک‌لیست و برگهٔ تحویل'" in source
    assert "book.h1('فهرست شکل‌ها')" not in source
    assert "book.h3('منابع این مبحث')" not in source

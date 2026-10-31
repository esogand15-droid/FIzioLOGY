"""Apply additive learning material without rewriting the source content files."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path

CONTENT = Path(__file__).resolve().parents[1] / 'headneck/content'


def _hn03_source_blocks(tid: str, mapping: dict) -> list:
    """Build traceable lecture-text blocks, leaving all base blocks untouched.

    The transcription is opt-in while the session-3 figure and layout audits
    remain unfinished. A page label is emitted once per contiguous source page.
    No lecture images are duplicated: they already exist as base plate blocks.
    """
    out, last_page = [], None
    for row in mapping[tid]:
        page, source = row['source_pdf_page'], row['block']
        if page != last_page:
            out.append({'type': 'h3', 'text': f'متن جزوهٔ درس — صفحهٔ PDF {page}'})
            last_page = page
        kind = source['type']
        src = f'جزوهٔ درس، صفحهٔ PDF {page} · متن منبع'
        if kind == 'heading':
            out.append({'type': 'h3', 'text': source['text']})
        elif kind == 'paragraph':
            out.append({'type': 'p', 'text': source['text'], 'src': src})
        elif kind == 'list':
            out.append({'type': 'ol', 'items': deepcopy(source['items']), 'src': src})
        else:
            raise ValueError(f'{tid}: unexpected lecture block {kind}')
    return out


def apply_update(session: str, content: dict[str, list]) -> dict[str, list]:
    draft_hn03 = session == 'hn03' and os.environ.get('HUMSYAR_HN03_WIP') == '1'
    if session not in ('hn01', 'hn02', 'hn04', 'hn05', 'hn06') and not draft_hn03:
        return content
    mapping = None
    if draft_hn03:
        report = CONTENT.parent / 'reports/HN_S03_TRANSCRIPTION_TOPIC_MAP_WIP.json'
        mapping = json.loads(report.read_text(encoding='utf-8'))['topics']
        if set(mapping) != set(content):
            raise ValueError('hn03: transcription and base topic IDs differ')
    overlay = json.loads((CONTENT / f'{session}_update.json').read_text(encoding='utf-8'))['topics']
    if set(overlay) != set(content):
        raise ValueError(f'{session}: overlay and base topic IDs differ')
    result = {}
    for tid, original in content.items():
        spec = overlay[tid]
        if not original or original[0]['type'] != 'idcard' or original[-1]['type'] != 'handoff':
            raise ValueError(f'{tid}: unexpected base block structure')
        positions = {int(k) for k in spec['after']}
        if not positions.issubset(set(range(len(original)-1))):
            raise ValueError(f'{tid}: insertion index outside base content')
        blocks = []
        for i, block in enumerate(original):
            b = deepcopy(block)
            if i == 0:
                b['rows'].extend(deepcopy(spec['card_rows']))
            # Presentation metadata only: preserve the underlying text/items.
            # Original enumerated items are displayed as numbered lists.
            if b.get('type') == 'ul' and session != 'hn04':
                b['type'] = 'ol'
            # The temporal-bone list already contains source numbers 2–4;
            # use those as the displayed numbering instead of adding 1–3 on
            # top of them.  The base strings themselves remain untouched.
            if session == 'hn02' and tid == 'hn02-T16' and i == 12:
                b['display_start'] = 2
                b['display_items'] = [item.split('. ', 1)[1] for item in b['items']]
            if 'src' in b:
                b['src'] = b['src'].replace(' — رونویسی در حال مقابله', '')
            if session in ('hn04', 'hn05', 'hn06') and str(i) in spec.get('plate_overrides', {}):
                override = spec['plate_overrides'][str(i)]
                allowed = {'asset', 'citation', 'src', 'fa_text', 'max_h', 'min_img_h', 'fresh', 'title', 'en_caption', 'view', 'labels'}
                if b['type'] != 'plate' or not set(override).issubset(allowed):
                    raise ValueError(f'{tid}: invalid figure presentation override at {i}')
                b.update(deepcopy(override))
            if session == 'hn04' and str(i) in spec.get('source_reconciliation', {}):
                patch = spec['source_reconciliation'][str(i)]
                if b.get('type') != 'h3' or b.get('text') != patch['expected_text']:
                    raise ValueError(f'{tid}: source reconciliation mismatch at {i}')
                b['text'] = patch['text']
                b['src'] = (f"مقابلهٔ تیتر با اصل منبع؛ بخش ۲، صفحهٔ واقعی PDF {patch['source_pdf_page']}")
            blocks.append(b)
            if draft_hn03 and i == 0:
                blocks.extend(_hn03_source_blocks(tid, mapping))
            blocks.extend(deepcopy(spec['after'].get(str(i), [])))
        result[tid] = blocks
    return result

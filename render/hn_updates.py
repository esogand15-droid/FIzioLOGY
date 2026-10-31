"""Apply additive learning material without rewriting the source content files."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

CONTENT = Path(__file__).resolve().parents[1] / 'headneck/content'


def apply_update(session: str, content: dict[str, list]) -> dict[str, list]:
    if session not in ('hn01', 'hn02'):
        return content
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
            if b.get('type') == 'ul':
                b['type'] = 'ol'
            # The temporal-bone list already contains source numbers 2–4;
            # use those as the displayed numbering instead of adding 1–3 on
            # top of them.  The base strings themselves remain untouched.
            if session == 'hn02' and tid == 'hn02-T16' and i == 12:
                b['display_start'] = 2
                b['display_items'] = [item.split('. ', 1)[1] for item in b['items']]
            if 'src' in b:
                b['src'] = b['src'].replace(' — رونویسی در حال مقابله', '')
            blocks.append(b)
            blocks.extend(deepcopy(spec['after'].get(str(i), [])))
        result[tid] = blocks
    return result

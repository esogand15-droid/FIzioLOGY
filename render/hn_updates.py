"""Apply additive learning material without rewriting the source content files."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

CONTENT = Path(__file__).resolve().parents[1] / 'headneck/content'


def apply_update(session: str, content: dict[str, list]) -> dict[str, list]:
    if session != 'hn01':
        return content
    overlay = json.loads((CONTENT / 'hn01_update.json').read_text(encoding='utf-8'))['topics']
    if set(overlay) != set(content):
        raise ValueError('session 1 overlay and base topic IDs differ')
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
            if 'src' in b:
                b['src'] = b['src'].replace(' — رونویسی در حال مقابله', '')
            blocks.append(b)
            blocks.extend(deepcopy(spec['after'].get(str(i), [])))
        result[tid] = blocks
    return result

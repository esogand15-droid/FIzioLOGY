"""Writer-specific handoff sheets shared by sessions 1 and 2."""
from __future__ import annotations


def checklist(session: int, idx: int, card: dict, copy_module) -> list[str]:
    """Use topic-specific writer guidance or learning objectives, never generic checks."""
    if session == 1:
        rows = list(copy_module.GUIDES[idx])
    elif session == 2:
        objectives = next((r.get('items', []) for r in card['rows']
                           if r.get('label') == 'اهداف یادگیری'), [])
        rows = list(objectives[:3]) + [copy_module.GUIDES[idx][0]]
    else:
        raise ValueError('Unsupported session')
    if len(rows) < 2 or len(set(rows)) != len(rows):
        raise ValueError(f'Invalid checklist for session {session}, topic {idx}')
    return rows


def review_point(session: int, idx: int, handoff: dict, copy_module) -> str:
    """Restore historical open points; replace a generic instruction with topic-specific context."""
    if session == 2 and idx == 1:
        return ('در برگهٔ تحویل پیشین نام پس‌سری در فهرست آمده بود؛ متن صفحهٔ ۳ نام‌های '
                'پیشانی، گونه‌ای، آهیانه‌ای و گیجگاهی را آورده است. تطبیق فهرست بررسی شود.')
    old = str(handoff.get('open', '')).strip()
    if old and 'پیش از انتشار' not in old:
        return old
    if session == 1:
        return 'موضوع برای بررسی: ' + copy_module.BOUNDARIES[idx]
    if session == 2:
        return 'نکتهٔ مفهومی برای بازبین: ' + copy_module.GUIDES[idx][2]
    raise ValueError('Unsupported session')


def emit(book, session: int, idx: int, card: dict, handoff: dict, copy_module, clean):
    title = clean(handoff.get('title', 'برگهٔ تحویل مبحث'))
    sources = handoff.get('sources', '')
    if isinstance(sources, (list, tuple)):
        sources = ' · '.join(map(str, sources))
    question = str(handoff.get('question', '')).strip().removeprefix('پرسش باز:').strip()
    book.handoff_sheet(
        title, clean(sources), checklist(session, idx, card, copy_module),
        clean(review_point(session, idx, handoff, copy_module)),
        kicker='برای تکمیل جزوه‌نویس', note='پرسش باز: ' + clean(question) if question else '',
        writer_name=True,
    )

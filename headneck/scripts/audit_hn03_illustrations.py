"""Audit each embedded illustration in lecture PDF pages 2–20 against hn03 content.

This is a reproducible coverage check of PDF image blocks, not a claim that the
source itself contains every possible relevant anatomical figure. It skips the
cover artwork on page 1, and does not classify text or vector drawings as images.
Run after hn03_figures.py and hn03_build_content.py.
"""
import json
from pathlib import Path
import pymupdf

R = Path(__file__).resolve().parents[2]
source = next((R/'علوم تشریح سر و گردن').glob('جلسه 3*/*.pdf'))
doc = pymupdf.open(source)
assets = json.loads((R/'headneck/images/INDEX.json').read_text(encoding='utf-8'))['assets']
lecture_assets = [a for a in assets if a.get('session') == 'hn03' and a.get('book') == 'lecture']
contents = [t for suffix in ('a', 'b') for t in json.loads((R/f'headneck/content/hn03_{suffix}.json').read_text(encoding='utf-8'))]
used = {b['asset']: (t['topic_id'], b['title']) for t in contents for b in t['blocks'] if b.get('type') == 'plate'}
rows = []
missing = []
for page_no in range(2, len(doc) + 1):
    blocks = [b for b in doc[page_no - 1].get_text('dict')['blocks'] if b['type'] == 1]
    for i, block in enumerate(blocks, 1):
        matches = [a for a in lecture_assets if a['page'] == page_no and
                   all(abs(a['bbox'][j] - block['bbox'][j]) < 0.1 for j in range(4))]
        if len(matches) != 1 or matches[0]['path'] not in used:
            missing.append((page_no, i))
            rows.append(f'| {page_no} | {i} | ثبت نشده | — | — |')
            continue
        asset = matches[0]
        topic, title = used[asset['path']]
        rows.append(f"| {page_no} | {i} | `{Path(asset['path']).name}` | {topic} | {title} |")
ref_rows = []
for topic in contents:
    for b in topic['blocks']:
        if b.get('type') == 'plate' and b.get('book') in ('netter', 'grays'):
            ref_rows.append(f"| {topic['topic_id']} | {b['citation']} | `{Path(b['asset']).name}` | {b['title']} |")
report = R/'headneck/reports/HN_S03_IMAGE_AUDIT.md'
report.write_text('\n'.join([
    '# ممیزی تصویری جلسهٔ ۳', '',
    'شماره‌ها شمارهٔ یک‌مبنای صفحات فایل PDF منبع هستند؛ صفحهٔ ۱ جلد و شامل طرح تزئینی و لوگو است و در این شمارش آموزشی نیست.',
    f'جزوهٔ اصلی در صفحات ۲ تا ۲۰ **{len(rows)} بلوک تصویر** دارد. در خروجی **{len(rows)-len(missing)} از {len(rows)}** به قاب‌های موضوعی نگاشت شدند. این شمارش شامل تصاویر تکراری و تصاویر فاقد برچسب هم هست.',
    'این کنترل، شمارش بلوک‌های تصویری فایل است، نه بررسی خودکار تمام نقاشی‌های برداری یا اثبات علمی برچسب‌ها. بررسی تصویری شکل‌ها و جایگاهشان جداگانه انجام شده است.', '',
    'شمارهٔ تصویر همان ترتیب بلوک‌های تصویری استخراج‌شده از صفحه است، نه الزاماً ترتیب دیداری از بالا به پایین. صفحات ۴، ۶ و ۸ بلوک تصویری ندارند.', '', '## تصویرهای جزوه', '', '| صفحهٔ PDF منبع | شمارهٔ تصویر در صفحه | دارایی | مبحث | عنوان قاب خروجی |', '|---|---|---|---|---|', *rows, '',
    '## قاب‌های منتخب کتاب‌ها', '',
    'این‌ها تمام تصاویر کتاب‌ها نیستند: شکل‌های مرتبط با موضوع این جلسه از صفحات بررسی‌شده انتخاب شده‌اند. پلیت‌های ۲۷ تا ۳۷ نتر و صفحات چاپی ۸۵۵ تا ۸۷۲ گری از نظر تصویر بررسی شدند؛ شکل‌های نامرتبط یا تکراری کتاب‌ها لزوماً وارد سند نشده‌اند.', '',
    '| مبحث | ارجاع | دارایی | عنوان قاب خروجی |', '|---|---|---|---|', *ref_rows, '',
    'برش‌های کتاب، فقط ناحیهٔ مرتبط شکل را شامل می‌شوند: برای مثال در پلیت ۳۴ نتر بخش مرکزی سوراخ‌های مرتبط نگه داشته شده و بقیهٔ پلیت در خروجی نیست. شکل ۸.۳۱ گری صفحهٔ ۸۷۰ به‌دلیل برچسب مشکوک V2 در ناحیهٔ mandibular انتخاب نشد؛ برچسب مستقل بازبینی نشده است.', '', 'تصویر بی‌برچسب صفحهٔ ۱۲ و یکی از نماهای خلفی صفحهٔ ۱۶ در جزوه فاقد برچسب کامل‌اند؛ قاب آن‌ها این محدودیت را تصریح می‌کند و نام‌های توضیحی را جایگزین برچسب چاپی معرفی نمی‌کند.',
    'کیفیت بعضی تصاویر همان کیفیت جزوهٔ اصلی است. تطابق نهایی همهٔ برچسب‌های چاپ‌شده و اظهارات علمی با نظر متخصص آناتومی تأیید نشده است.', ''
]), encoding='utf-8')
print(f'lecture image blocks={len(rows)}, mapped={len(rows)-len(missing)}, reference plates={len(ref_rows)}')
if missing:
    raise SystemExit(f'Unmapped lecture image blocks: {missing}')

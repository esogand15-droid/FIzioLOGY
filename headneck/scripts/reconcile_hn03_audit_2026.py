"""Apply the session 3 source/figure audit to the current topic-based content.

Run after hn03_build_content.py *and* the existing text reconciliation.  This
script does not regenerate the already-reconciled content: the historical
builder alone predates that reconciliation and overwrites it. Idempotent.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
paths = [ROOT / f'headneck/content/hn03_{s}.json' for s in 'ab']
docs = [json.loads(p.read_text(encoding='utf-8')) for p in paths]
topics = {t['topic_id']: t for doc in docs for t in doc}

def insert_before(topic, needle, block):
    blocks = topics[topic]['blocks']
    if any(b.get('text') == block.get('text') for b in blocks):
        return
    matches = [i for i, b in enumerate(blocks) if needle in b.get('text', '')]
    if len(matches) != 1:
        raise ValueError(f'{topic}: expected one anchor {needle!r}, found {len(matches)}')
    blocks.insert(matches[0], block)

def quote(text, page):
    return {'type': 'p', 'text': 'نقل از جزوه: «' + text + '»',
            'src': f'جزوهٔ درس، صفحهٔ PDF {page} · نقل از متن'}

def note(text, src):
    return {'type': 'callout', 'kind': 'info', 'title': 'توضیح تکمیلیِ جدا از متن جزوه',
            'text': text, 'src': src}

insert_before('hn03-T02', 'جسم اسفنوئید میان دو بال', quote(
    'قسمت بالا و خارج: دهانه سینوس اسفنوئید (Sphenoidal Sinus) قرار گرفته است که با سینوس‌های اتموئیدال (Ethmoidal Sinuses) مفصل می‌شوند.', 3))
insert_before('hn03-T03', 'شکاف چشمی فوقانی (Superior orbital fissure)', note(
    'در پلیت ۳۴ نتر، برای شکاف چشمی فوقانی اعصاب حرکتی چشم (III)، قرقره‌ای (IV)، چشمی (V1) و دورکننده (VI) و ورید چشمی فوقانی درج شده‌اند. این فهرست توضیحی از مرجع تصویری است، نه نقل از جزوه.',
    'نتر، ویراست ۸، پلیت ۳۴، ص ۸۶'))
insert_before('hn03-T06', 'در سطح فوقانی جسم، یوغ اسفنوئید', quote(
    'ناودان کیاسماتیک (Chiasmatic Groove / Sulcus): عقب‌تر از یوغ اسفنوئیدی، یه ناودان عرضی داریم که محل عبور و تقاطع عصب بینایی یا زوج 2 مغزی (II Cranial Nerve) است.', 7))
insert_before('hn03-T07', 'شیار کاروتید در دو سوی جسم', quote(
    'محتویات عبوری: یه ورید خروجی (Emissary vein) ازش رد میشه که سینوس کاورنوس (Cavernous sinus) رو به شبکه وریدی بیرون جمجمه وصل می‌کنه.', 9))
insert_before('hn03-T08', 'سطح خلفی جسم اسفنوئید', quote(
    'این مفصل از نوع غضروفی (Synchondrosis) است. تو افراد زیر 25 سال این جا غضروف رشد وجود داره، اما بالای 25 سال این غضروف استخوانی می شود (سین‌استوزیس) و درز بین این دو استخوان کاملاً از بین می رود و به هم جوش می‌خورن!', 6))
insert_before('hn03-T09', 'پتریون (Pterion) محل اتصال', quote(
    'در سمت خلف (عقب): با صدف استخوان گیجگاهی (Temporal) و زاویه قدامی-تحتانی استخوان آهیانه یا پری‌تال (Parietal) (که به این زاویه، زاویه اسفنوئیدال استخوان پری‌تال هم میگن).', 10))
insert_before('hn03-T11', 'سطح داخلی صفحهٔ عمودی رو به حفرهٔ بینی است', quote(
    'تیغه اتموئیدال (Ethmoidal Crest): تو قسمت بالا قرار داره و با استخوان اتموئید یا پرویزنی (ethmoid) مفصل میشه.', 12))
insert_before('hn03-T12', 'زائدهٔ اسفنوئیدیِ کوچک‌تر', quote(
    'یادآوری زائده اوربیتال پالاتین: تو تصاویر استاد مشخصه که این زائده تو قسمت خلفی جدار داخلی کاسه چشم (Orbit) شرکت می‌کنه.', 15))
insert_before('hn03-T12', 'زائدهٔ اسفنوئیدیِ کوچک‌تر', note(
    'جزوه در صفحهٔ ۱۳ از سهم این زائده در قسمت خلفی کف کاسهٔ چشم و در صفحهٔ ۱۵ از جدار داخلی سخن می‌گوید. هر دو عبارت به منبع نسبت داده شده‌اند؛ تصویر صفحهٔ ۱۳ برای تطبیق جهت نما کنار متن آمده است و رفع قطعی اختلاف جزو این بررسی نیست.',
    'جزوهٔ درس، صفحات PDF ۱۳ و ۱۵؛ شکل صفحهٔ PDF ۱۳'))
insert_before('hn03-T13', 'زائدهٔ هرمی به عقب، پایین و خارج می‌رود', quote(
    'اعصاب و عروقی به همین نام (Lesser palatine nerves/vessels) از اینجا عبور می‌کنن و میرن حس کام نرم و عضله زبان کوچک (Uvula) رو تامین می‌کنن.', 15))
insert_before('hn03-T17', 'همراه عصب زیرزبانی', quote(
    'خود این شریان حلقی صعودی، شاخه‌ای از شریان کاروتید خارجی (External Carotid Artery) هست.', 20))
insert_before('hn03-T17', 'همراه عصب زیرزبانی', note(
    'جزوه، شاخهٔ مننژیالِ شریان پس‌سری را همراه ورید ارتباطی برای کانال کندیلار نام می‌برد؛ پلیت ۳۴ نتر برای همان کانال، شاخهٔ مننژیال شریان حلقی صعودی را برچسب زده است. این دو نام را یکی فرض نمی‌کنیم؛ تفاوت منابع و تنوع احتمالی باید جداگانه بررسی شود.',
    'جزوهٔ درس، صفحهٔ PDF ۱۸؛ نتر، ویراست ۸، پلیت ۳۴، ص ۸۶'))
insert_before('hn03-T17', 'همراه عصب زیرزبانی', note(
    'در پلیت ۳۳ نتر، افزون بر بصل‌النخاع، شریان‌های مهره‌ای و ریشه‌های نخاعی عصب اکسسوری برای فورامن مگنوم نشان داده شده‌اند؛ این‌ها یادداشت مرجع تصویری‌اند.',
    'نتر، ویراست ۸، پلیت ۳۳، ص ۸۵'))
insert_before('hn03-T18', 'برجستگی پس‌سری داخلی در محل', quote(
    'یادآوری: سینوس‌های وریدی مغز از دو لایه شدن سخت‌شامه یا Dura mater تشکیل میشن.', 18))
insert_before('hn03-T19', 'این وریدها غالباً فاقد دریچه‌اند', quote(
    'چون این وریدها دریچه (Valve) ندارن، عفونت‌های پوست سر یا صورت می‌تونه از طریق این وریدها به داخل مغز (سینوس‌های سخت‌شامه‌ای) کشیده بشه و مننژیت یا ترومبوز ایجاد کنه!', 20))

# Place the quoted origin immediately after the paragraph naming that artery.
blocks = topics['hn03-T17']['blocks']
origin_index = next(i for i, b in enumerate(blocks) if b.get('text', '').startswith('نقل از جزوه: «خود این شریان حلقی صعودی'))
origin = blocks.pop(origin_index)
target_index = next(i for i, b in enumerate(blocks) if 'همراه عصب زیرزبانی، شبکهٔ وریدی' in b.get('text', ''))
blocks.insert(target_index + 1, origin)

# Clarifications that differ from the source must not masquerade as lecture text.
for topic_id, needle, src in [
    ('hn03-T02', 'جسم اسفنوئید میان دو بال', 'StatPearls، Anatomy, Head and Neck, Sinus Function and Development، بخش Structure and Function؛ نتر، پلیت ۲۹، ص ۸۱'),
    ('hn03-T06', 'در سطح فوقانی جسم، یوغ اسفنوئید', 'Surgical Anatomy of the Sellar Region، بخش Sphenoid bone؛ گری، شکل ۸.۲۶، ص ۸۶۷'),
]:
    block = next(b for b in topics[topic_id]['blocks'] if needle in b.get('text', ''))
    block.update(type='callout', kind='info', title='توضیح تکمیلیِ جدا از متن جزوه', src=src)

# More precise reference labels and no unsupported assertion about frequency.
for t in topics.values():
    for b in t['blocks']:
        if b.get('type') == 'table':
            for row in b.get('rows', []):
                if len(row) >= 3 and row[0] == 'Foramen ovale':
                    row[2] = 'عصب پتروزال کوچک و عروق نیز ممکن است همراه باشند'
        asset = b.get('asset', '')
        if asset.endswith('hn03_lec_p14_pal_posterior.jpeg'):
            b['labels'] = [["شیار کامی بزرگ", "Greater palatine groove"], ["بریدگی اسفنوپالاتین", "Sphenopalatine notch"], ["صفحهٔ افقی", "Horizontal plate"]]
        if asset.endswith('hn03_lec_p15_palate.jpeg'):
            b['labels'][0] = ['درز کامی‌فکی', 'Palatomaxillary suture']
            b['fa_text'] = 'درز کامی‌فکی (درز کامی عرضی)، صفحهٔ افقی کامی و سوراخ‌های کامی را دنبال کنید؛ نام انگلیسی درز مطابق برچسب خود شکل آمده است.'
        if asset.endswith('hn03_lec_p17_occ_external.jpeg'):
            b['fa_text'] = 'بخش صدفی، کندیلار و قاعده‌ای را با سوراخ بزرگ تطبیق دهید؛ نام فورامن مگنوم در راهنمای قاب برای جهت‌یابی افزوده شده است.'

for path, doc in zip(paths, docs):
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('session 3 audit applied')

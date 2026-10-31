#!/usr/bin/env python3
"""Record the session-3 lecture-asset visual review without certifying the PDF."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
# Each listed JPEG was opened individually in the viewer on this review pass.
# Limitations refer to the asset itself; readability in final PDF is untested.
notes={
'p02_location':'نمای رنگی طرفی؛ تنها بال بزرگ برچسب دارد، بقیهٔ نام‌ها در توضیح قاب‌اند.',
'p03_skull_sections':'نمای ترکیبی با فهرست عددی؛ واترمارک و لبهٔ تیره در خود تصویر منبع وجود دارد.',
'p03_anterior':'نمای قدامی اسفنوئید؛ متن پایین نزدیک لبه است و کیفیت اولیه محدود است.',
'p05_posterior':'نمای خلفی اسفنوئید با فهرست قلاب، کانال و صفحات؛ نوار و واترمارک منبع باقی است.',
'p07_superior':'نمای فوقانی با بال کوچک، زین و سوراخ‌ها؛ واترمارک و نوار پایین از منبع است.',
'p09_clivus':'نمای فوقانی‌ـ‌طرفی با کلیووس و سوراخ‌ها؛ واترمارک از منبع باقی است.',
'p10_pterion':'جمجمهٔ رنگی طرفی با محل پتریون؛ مشابه تصویر صفحهٔ ۲ اما با برچسب متفاوت.',
'p10_pterion_vessels':'دو نما، راهنمای انگشت و مسیر شریان؛ همهٔ برچسب‌ها با کیفیت منبع حفظ شده‌اند.',
'p11_surface':'نمای جمجمه و صورت با شماره‌ها؛ جمجمه شبیه صفحهٔ ۱۰ ولی تصویر سطحی اطلاعات تکمیلی دارد.',
'p11_infratemporal':'نمای حفرهٔ پتریگوپالاتین؛ برچسب‌های کوچک محدود به کیفیت اصلی هستند.',
'p12_context':'نمای استخوانی بدون برچسب؛ نام‌های قاب نباید به صورت برچسب خود شکل معرفی شوند.',
'p12_pal_medial':'نمای مدیال کامی با ستیغ‌ها، زوائد و صفحهٔ افقی.',
'p12_pal_lateral':'نمای لترال کامی؛ بخشی از برچسب سمت چپ به لبهٔ تصویر نزدیک و منبع نیز محدود است.',
'p13_orbital':'نمای کاسهٔ چشم و نمای رنگی کوچک؛ زائدهٔ کامی در تصویر مشخص است.',
'p13_canals':'گذرگاه‌ها با اصطلاحات لاتین؛ ارتباط با کانال‌های حفره باید کنار متن خوانده شود.',
'p14_pal_posterior':'نمای خلفی کامی با زوائد و شیار؛ اندازهٔ نسبتاً باریک نیازمند کنترل اندازه در PDF است.',
'p15_palate':'نمای تحتانی کام با درزها و سوراخ‌ها؛ برچسب‌های منبع حفظ شده‌اند.',
'p15_sphenopalatine':'نمای دیوارهٔ بینی با سوراخ اسفنوپالاتین مشخص‌شده و واترمارک منبع.',
'p16_posterior':'نمای خلفی کلی؛ شکل ساده با برچسب محدود است.',
'p16_sutures':'نمای خلفی با درزهای لامبدوئید، ساجیتال و دو نقطهٔ کرانیومتریک.',
'p16_occ_side':'نمای طرفی استخوان پس‌سری؛ خطی در لبهٔ پایین از برش تصویر منبع باقی است.',
'p17_occ_external':'نقشهٔ سطح خارجی رنگی؛ برخی برچسب‌های چپ در نزدیکی لبه‌اند.',
'p17_occ_inferior':'نمای تحتانی پس‌سری با کندیل، کانال، خطوط گردنی و سوراخ بزرگ.',
'p18_occ_internal':'نمای رنگی سطح داخلی با سینوس‌ها و اجزای استخوان.',
'p19_occ_endocranial':'دو نمای سطح داخلی، رنگی و استخوان خشک، شامل کانال‌ها و ناودان‌ها.',
'p20_venous':'سینوس‌های وریدی و وریدهای ارتباطی در نمای خلفی؛ برچسب‌ها در خود دارایی دیده می‌شوند.',
}
index=json.loads((ROOT/'headneck/images/INDEX.json').read_text(encoding='utf-8'))['assets']
assets={a['path']:a for a in index}
rows=[]
for part in ('a','b'):
    for topic in json.loads((ROOT/f'headneck/content/hn03_{part}.json').read_text(encoding='utf-8')):
        for block_index, b in enumerate(topic['blocks']):
            if b.get('book')!='lecture' or b.get('type')!='plate':continue
            path=b['asset']; key=Path(path).stem.removeprefix('hn03_lec_')
            assert key in notes and path in assets and (ROOT/path).exists(), path
            a=assets[path]
            rows.append({'asset':path,'source_pdf_page':a['page'],'source_bbox':a['bbox'],
                         'base_topic':topic['topic_id'],'base_block_index':block_index,
                         'title':b['title'],'asset_viewed_individually':True,
                         'asset_review_note':notes[key], 'final_pdf_reviewed':False})
assert len(rows)==len(notes)==26 and len({r['asset'] for r in rows})==26
out=ROOT/'headneck/reports/HN_S03_LECTURE_ASSET_VISUAL_REVIEW_WIP.json'
out.write_text(json.dumps({'disclaimer':'Each existing lecture asset was opened individually. '
    'This does not certify final PDF placement, printed label readability, or scientific accuracy.',
    'assets':rows},ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print(f'{len(rows)} existing lecture assets individually reviewed; PDF layout remains unchecked')

"""Finish session-2 editorial metadata and image captions after transcription.

Descriptions are separate from source transcription. They describe features
actually visible in each figure; the lecture text itself is not rewritten here.
"""
from __future__ import annotations
import json
from pathlib import Path

CONTENT = Path(__file__).resolve().parents[1] / 'content'
UPDATES = {
 'hn02_lec_p03_zygo': {'fa_text':'توضیح تکمیلی تصویر: در نمای قدامی، استخوان گونه در دو طرف و زیر کاسهٔ چشم رنگی نشان داده شده است.'},
 'hn02_lec_p04_lat': {'fa_text':'توضیح تکمیلی تصویر: تکمهٔ ویتنال، رباط پلکی طرفی، آپونوروز بالابرندهٔ پلک و لیگامان معلق در تصویر برچسب دارند.'},
 'hn02_lec_p04_whitnall': {'fa_text':'توضیح تکمیلی تصویر: پیکان جای تکمهٔ حاشیه‌ای را بر روی استخوان گونه نشان می‌دهد.'},
 'hn02_lec_p04_arch': {'fa_text':'توضیح تکمیلی تصویر: مسیر قوس گونه در تصویر سر و در نمای طرفی جمجمه مشخص شده است.'},
 'hn02_lec_p05_foramina': {'title':'سه سوراخ استخوان گونه و شاخه‌های عصبی', 'view':'دو نما؛ سوراخ‌های گونه‌ای‌چهره‌ای، گونه‌ای‌گیجگاهی و گونه‌ای‌کاسه‌ای', 'fa_text':'توضیح تکمیلی تصویر: دو نمای تصویر، سه سوراخ و شاخه‌های عصب گونه‌ای را با خطوط راهنما نشان می‌دهند.'},
 'hn02_lec_p06_blackeye': {'title':'شکستگی گونه و کبودی دور چشم', 'fa_text':'توضیح تکمیلی تصویر: در سمت جمجمه خط شکستگی و در سمت صورت کبودی دور چشم نشان داده شده است.'},
 'hn02_lec_p08_outer': {'fa_text':'توضیح تکمیلی تصویر: خط مایل، سوراخ چانه‌ای، زاویه و زائده‌های راموس با برچسب مشخص شده‌اند.'},
 'hn02_lec_p08_xray': {'fa_text':'توضیح تکمیلی تصویر: حفرهٔ پالپ، سپتوم بین‌دندانی، استخوان اسفنجی، کانال مندیبل و استخوان متراکم در تصویر برچسب دارند.'},
 'hn02_lec_p09_angle': {'fa_text':'توضیح تکمیلی تصویر: خطوط دندانه‌دار طرح‌واره مسیرهایی را در گردن کندیل، زاویه و جسم مندیبل نشان می‌دهند.'},
 'hn02_lec_p11_medial': {'fa_text':'توضیح تکمیلی تصویر: نمای داخلی مندیبل دارای برچسب خارهای چانه‌ای، خط مایلوهایوئید، حفره‌ها، سوراخ مندیبل و لینگولا است.'},
 'hn02_lec_p15_mental': {'title':'جای سوراخ چانه در مندیبل بی‌دندان و نوزاد', 'view':'A: مندیبل بی‌دندان؛ B: مندیبل نوزاد', 'fa_text':'توضیح تکمیلی تصویر: زیر شکل A عبارت مندیبل بی‌دندان و زیر شکل B عبارت مندیبل نوزاد آمده است؛ جای سوراخ چانه در هر دو نما نشان داده شده است.', 'labels':[['مندیبل بی‌دندان','Edentulous mandible'],['مندیبل نوزاد','Neonatal mandible'],['سوراخ چانه‌ای','Mental foramen']]},
 'hn02_lec_p14_prognathism': {'fa_text':'توضیح تکمیلی تصویر: دو طرح‌واره، فک دارای دندان و فک بی‌دندان را نشان می‌دهند؛ واژهٔ Prognathism کنار نمای پایینی نوشته شده است.'},
 'hn02_lec_p15_xray': {'title':'دو تصویر فک و سوراخ چانه', 'view':'رادیوگرافی نیم‌رخ و تصویر مندیبل', 'fa_text':'توضیح تکمیلی تصویر: در نمای نیم‌رخ، فک فوقانی و تحتانی با نام نشان داده شده‌اند؛ در تصویر مقابل، فلش‌ها سوراخ‌های چانه‌ای را مشخص می‌کنند.', 'labels':[['فک فوقانی','Maxilla'],['فک تحتانی','Mandible'],['سوراخ چانه‌ای','Mental foramen']]},
 'hn02_lec_p17_surface': {'fa_text':'توضیح تکمیلی تصویر: نقاط شماره‌دار صورت و راهنمای سوراخ‌های فوق‌کاسه‌ای، زیرکاسه‌ای و چانه‌ای در تصویر آمده‌اند.'},
 'hn02_lec_p18_norma': {'fa_text':'توضیح تکمیلی تصویر: در نمای طرفی جمجمه، استخوان‌ها با رنگ‌های مختلف از هم جدا شده‌اند.'},
 'hn02_grays_p857': {'fa_text':'توضیح تکمیلی تصویر: در نمای طرفی گری، استخوان‌ها، چند درز، پتریون و آستریون با خط راهنما نام‌گذاری شده‌اند.'},
 'hn02_lec_p19_tempbone': {'view':'جمجمه و دو نمای استخوان گیجگاهی', 'fa_text':'توضیح تکمیلی تصویر: در نمای جمجمه جای استخوان گیجگاهی و در دو نمای کناری بخش‌های صدفی، تیمپانیک، خاره‌ای و زائدهٔ استایلوئید برچسب دارند.'},
 'hn02_lec_p22_deep': {'fa_text':'توضیح تکمیلی تصویر: در این نما سوراخ‌های بیضی، خاری و پاره و نیز درزهای پتروسکواموس و پتروتیمپانیک برچسب دارند.'},
 'hn02_lec_p23_suprameatal': {'view':'نمای طرفی سر با نقاط شماره‌دار', 'fa_text':'توضیح تکمیلی تصویر: نقاط و خطوط آناتومی سطحی روی سر مشخص شده‌اند؛ خود تصویر برای تطبیق شماره‌ها به متن و منبع اصلی ارجاع می‌دهد.'},
 'hn02_lec_p26_parietal': {'fa_text':'توضیح تکمیلی تصویر: کنارها، زاویه‌ها، برجستگی آهیانه و خطوط گیجگاهی در سطح بیرونی استخوان با خطوط راهنما نشان داده شده‌اند.'},
 'hn02_netter_p38': {'title':'حفرهٔ زیرگیجگاهی و اطراف آن در نتر', 'fa_text':'توضیح تکمیلی تصویر: پلیت دو نمای خلفی و طرفی را نشان می‌دهد؛ در نمای طرفی حفرهٔ زیرگیجگاهی، سوراخ‌های بیضی و خاری و زائدهٔ پتریگوئید برچسب دارند.', 'labels':[['حفرهٔ زیرگیجگاهی','Infratemporal fossa'],['سوراخ بیضی','Foramen ovale'],['سوراخ خاری','Foramen spinosum'],['زائدهٔ پتریگوئید','Pterygoid process']]},
 'hn02_lec_p22_infratemp': {'fa_text':'توضیح تکمیلی تصویر: عکس ناحیهٔ زیرگیجگاهی همراه با کلید اختصارات در همان تصویر منبع آمده است؛ برای تطبیق هر حروف به کلید کنار عکس مراجعه کنید.', 'labels':[['برجستگی مفصلی','Articular tubercle'],['حفرهٔ فک تحتانی','Mandibular fossa'],['شکاف پتروسکواموس','Petrosquamous fissure'],['تگمن تیمپانی','Tegmen tympani'],['سوراخ استایلوماستوئید','Stylomastoid foramen']]},
 'hn02_lec_p27_inner': {'fa_text':'توضیح تکمیلی تصویر: شیار سینوس ساجیتال فوقانی، شیار سینوس سیگموئید و شیار عروق مننژی میانی روی سطح داخلی نام‌گذاری شده‌اند.', 'labels':[['ناودان سینوس ساجیتال فوقانی','Groove for superior sagittal sinus'],['شیار عروق مننژی میانی','Groove for middle meningeal vessels'],['سوراخ آهیانه‌ای','Parietal foramen'],['شیار سینوس سیگموئید','Groove for sigmoid sinus']]},
 'hn02_lec_p20_tmj': {'view':'نمای طرفی استخوان گیجگاهی؛ برجستگی و حفرهٔ مفصلی', 'fa_text':'توضیح تکمیلی تصویر: حفرهٔ فک تحتانی، برجستگی مفصلی و تکمهٔ پس‌گلنوئیدی در تصویر با خطوط راهنما مشخص شده‌اند.', 'labels':[['برجستگی مفصلی','Articular tubercle'],['حفرهٔ فک تحتانی','Mandibular fossa'],['تکمهٔ پس‌گلنوئیدی','Postglenoid tubercle'],['زائدهٔ استایلوئید','Styloid process']]},
 'hn02_lec_p24_petrous': {'fa_text':'توضیح تکمیلی تصویر: در دو نما قسمت‌های صدفی، تیمپانیک، پتروس، زائدهٔ استایلوئید و حفرهٔ مندیبولار برچسب دارند.', 'labels':[['بخش تیمپانیک','Tympanic part'],['بخش خاره‌ای','Petrous part'],['بخش صدفی','Squamous part'],['زائدهٔ استایلوئید','Styloid process']]},
 'hn02_grays_p860': {'fa_text':'توضیح تکمیلی تصویر: در نمای فوقانیِ خارجی، استخوان‌های پیشانی، آهیانه و پس‌سری، درزها، برگما، لامبدا و سوراخ آهیانه‌ای مشخص شده‌اند.'},
 'hn02_lec_p28_composite': {'view':'نمای سینوس ساجیتال، جوانهٔ عنکبوتیه و سطح داخلی کالواریا', 'fa_text':'توضیح تکمیلی تصویر: ترکیب سه تصویر در منبع، موقعیت جوانهٔ عنکبوتیه و اثر حفره‌های گرانولار در کنار شیار سینوس را نشان می‌دهد.'},
 'hn02_netter_p35': {'fa_text':'توضیح تکمیلی تصویر: در نمای طرفی ملاج‌های اسفنوئیدال و ماستوئیدی و در نمای فوقانی ملاج‌های قدامی و خلفی برچسب دارند.'},
 'hn02_grays_p864': {'fa_text':'توضیح تکمیلی تصویر: سطح داخلی سقف جمجمه، شیار سینوس ساجیتال، حفره‌های گرانولار و شیارهای شریان مننژی میانی نام‌گذاری شده‌اند.'},
 'hn02_lec_p29_pforamen': {'fa_text':'توضیح تکمیلی تصویر: سوراخ آهیانه‌ای در کنار درز ساجیتال و نزدیک لامبدا با دایره مشخص شده است.'},
}

# Exact headings/captions printed on the selected reference plates and figures.
REFERENCE_CAPTIONS = {
 'hn02_netter_p35':'Cranium of Newborn',
 'hn02_netter_p38':'Cranium: Posterior and Lateral Views',
 'hn02_netter_p39':'Mandible',
 'hn02_netter_p42':'Temporomandibular Joint',
 'hn01_grays_p855':'Anterior view of the skull.',
 'hn02_grays_p857':'Lateral view of the skull.',
 'hn02_grays_p860':'Superior view of the skull.',
 'hn02_grays_p864':'Roof of the cranial cavity.',
}


def main():
    paths=[CONTENT/f'hn02_{part}.json' for part in 'ab']
    docs=[json.loads(p.read_text(encoding='utf8')) for p in paths]
    topics=[t for doc in docs for t in doc]
    first=next(t for t in topics if t['topic_id']=='hn02-T01')
    first['blocks']=[b for b in first['blocks'] if b.get('title')!='شناسنامهٔ جزوهٔ اصلی']
    first['blocks'].insert(1, {'type':'callout','kind':'info','title':'شناسنامهٔ جزوهٔ اصلی',
        'text':'علوم تشریح سر و گردن؛ استاد خدیجه میرزایی؛ پزشکی مهر ۱۴۰۴، دانشگاه علوم پزشکی بندرعباس؛ گروه جزوه نویسی A. جلسه دوم: بررسی استخوان های جمجمه. نام‌های خوانای گروه A در صفحهٔ منبع: نرگس بنایی، پارسا پورشهابی، وحید رحمانیان، عبدالله دردری، طاها سالارحسینی، آریا امیری زاده، محمد نصیری. بخشی از فهرست در تصویر منبع پوشیده شده است.',
        'src':'جزوهٔ درس، ص ۱–۲ · شناسنامه'})
    count=0
    for topic in topics:
        for block in topic['blocks']:
            # Keep the source/page citation but remove the repeated editorial
            # status from the reader-facing text; do not alter lecture content.
            if 'src' in block:
                block['src'] = block['src'].replace(' — رونویسی در حال مقابله', '')
            if block['type']=='plate':
                ident=Path(block['asset']).stem
                if ident in UPDATES:
                    block.update(UPDATES[ident]); count+=1
                if ident in REFERENCE_CAPTIONS:
                    block['en_caption']=REFERENCE_CAPTIONS[ident]
            if block['type']=='handoff' and block.get('open')=='رونویسی این مبحث هنوز به مقابلهٔ مستقل واژه‌به‌واژه و بازبینی علمی نیاز دارد.':
                block['open']='پیش از انتشار، متن این مبحث را با صفحه‌های منبع مقابله کنید.'
    for path, doc in zip(paths, docs):
        path.write_text(json.dumps(doc,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    print(f'updated {count} captions and session-2 editorial metadata')

if __name__=='__main__': main()

"""Rebuild the session-4 topical transcription and figure provenance.

The two lecture PDFs retain separate PDF page numbering; review both sources
before making claims of verbatim identity. Run from any working directory.
"""
from pathlib import Path
import io, json
import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = next((ROOT/'علوم تشریح سر و گردن').glob('جلسه 4*/*پارت_اول*.pdf'))
DOC = pymupdf.open(SOURCE)
INDEX = ROOT/'headneck/images/INDEX.json'
index = json.loads(INDEX.read_text(encoding='utf-8'))
index['assets'] = [a for a in index['assets'] if not a.get('asset_id','').startswith('hn04_p1_open_')]

# Ordinals are image-block order, not reading order; the page 3 images are
# extracted in the opposite order to their appearance on the page.
assets = {}
for page, ordinal, name in [(2,0,'base'),(2,1,'ethmoid_location'),(3,1,'ethmoid_parts'),(3,0,'ethmoid_views'),(4,0,'ethmoid_superior'),(5,0,'labyrinth'),(6,0,'lateral_ethmoid'),(6,1,'inferior_ethmoid'),(7,0,'nasal_conchae'),(7,1,'uncinate'),(8,0,'ethmoid_section'),(8,1,'nasal_septum'),(9,0,'coronal'),(9,1,'temporal'),(10,0,'petrous_base'),(11,0,'petrous_anterior'),(12,0,'petrous_anterior_detail'),(13,0,'ear_section'),(13,1,'ear_tubes'),(14,0,'petrous_posterior'),(15,0,'labyrinth_aqueduct'),(16,0,'petrous_inferior'),(16,1,'petrous_inferior_detail'),(17,0,'canaliculi'),(18,0,'cranial_bones'),(18,1,'cranial_fossae'),(18,2,'cranial_sagittal'),(19,0,'cranial_overview'),(25,0,'fossae_bones'),(25,1,'fossa_anterior'),(25,2,'fossa_middle'),(25,3,'fossa_posterior')]:
    b = [b for b in DOC[page-1].get_text('dict')['blocks'] if b['type']==1][ordinal]
    im = Image.open(io.BytesIO(b['image'])).convert('RGB')
    out = ROOT/f'headneck/images/hn04_p1_open_{name}.jpeg'
    im.save(out,quality=94,optimize=True)
    rel = str(out.relative_to(ROOT)); assets[name] = rel
    index['assets'].append(dict(asset_id=out.stem, book='lecture', session='hn04',
        source_file=str(SOURCE.relative_to(ROOT)), part=1, page=page,
        bbox=[round(v,2) for v in b['bbox']],w=im.width,h=im.height,bytes=out.stat().st_size,path=rel))
INDEX.write_text(json.dumps(index,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')


def p(text, page): return {'type':'p','text':text,'src':f'جزوهٔ درس، بخش ۱، صفحهٔ PDF {page}'}
def heading(text): return {'type':'h3','text':text}
def plate(name,page,title,view,description,labels):
    return {'type':'plate','book':'lecture','asset':assets[name], 'title':title,
      'citation':f'جزوهٔ درس، بخش ۱، ص {page} از فایل PDF','view':view,
      'fa_text':description,'labels':labels,'src':f'جزوهٔ درس، بخش ۱، صفحهٔ PDF {page}',
      'max_h':115,'fresh':False}
def reference(book,asset,title,citation,caption,view,text,labels):
    return {'type':'plate','book':book,'asset':'headneck/images/'+asset,'title':title,
      'citation':citation,'en_caption':caption,'view':view,'fa_text':text,'labels':labels,
      'src':citation,'max_h':125,'fresh':False}

def topic(n,title,pages,gist,question,body):
    tid=f'hn04-T{n:02}'; footer='جزوهٔ درس، بخش ۱، صفحهٔ PDF '+ '، '.join(map(str,pages))
    meta={'topic_id':tid,'title':title,'pages':pages,'gist':gist,'prereq':'نماها و استخوان‌های جمجمه'}
    card={'type':'idcard','title':'شناسنامهٔ مبحث','kicker':'قبل از شروع این مبحث بخوانید',
      'rows':[{'label':'جای این مبحث','text':gist},{'label':'هدف یادگیری','text':question},
              {'label':'پیش‌نیاز','text':'نماها و استخوان‌های جمجمه'}],'footer':footer}
    hand={'type':'handoff','title':f'برگهٔ تحویل — مبحث {n}','kicker':'برای تکمیل جزوه',
      'sources':footer,'checklist':['متن با صفحات منبع مقابله شود.','شکل و برچسب‌ها با منبع کنترل شوند.',
      'توضیح تکمیلی از متن جزوه تفکیک شود.','صفحه‌بندی نهایی بررسی شود.',
      'موارد مبهم برای بازبینی ثبت شوند.'],
      'open':'برای تحویل، متن و برچسب‌های شکل با ارجاعات منبع کنترل شوند.', 'question':question}
    return meta, {'topic_id':tid,'blocks':[card,*body,hand]}

items=[]
items.append(topic(1,'دو نمای قاعدهٔ جمجمه',[1,2], 'معرفی نماهای درون‌سری و برون‌سری', 'قاعدهٔ جمجمه از چه دو نمایی بررسی می‌شود؟',[
 heading('بررسی قاعده جمجمه (Base of Skull)'),
 p('برای بررسی بیس (قاعده) جمجمه، ما کرانیال والت (سقف جمجمه) را به صورت عرضی برش می‌زنیم. بعد از این برش، بیس جمجمه را از دو نمای اصلی مورد بررسی قرار می‌دهیم:',2),
 p('۱. نمای درون‌سری (داخلی)',2),
 p('۲. نمای برون‌سری (خارجی)',2),
 plate('base',2,'دو نمای قاعدهٔ جمجمه','نمای درونی و نمای تحتانی','دو تصویر جزوه بدون برچسب‌اند؛ نام نماها در راهنمای قاب برای جهت‌یابی افزوده شده است.',[['نمای درونی','Internal view'],['نمای تحتانی','Inferior view']]),
 reference('grays','hn03_grays_p869_fig827.jpeg','حفرهٔ جمجمه‌ای خلفی','گری، ویراست ۳، شکل ۸.۲۷، ص ۸۶۹','Posterior cranial fossa','نمای داخلی','این قاب مرجع بخشی از نمای داخلی قاعده، یعنی حفرهٔ خلفی، را نشان می‌دهد.',[['سوراخ بزرگ','Foramen magnum'],['کلیووس','Clivus'],['شیار سینوس عرضی','Groove for transverse sinus']])]))
items.append(topic(2,'استخوان اتموئید؛ جایگاه و اجزا',[2,3], 'جای استخوان اتموئید و اجزای آن', 'اتموئید از کدام اجزا تشکیل شده است؟',[
 heading('استخوان اتموئید (Ethmoid Bone) - معرفی کلی'),
 p('استخوان اتموئید (پرویزنی) جزء استخوان‌های فردِ جمجمه محسوب می‌شود. موقعیت قرارگیری آن به این شکل است:',2),
 p('در قسمت عقب استخوان نازال (بینی).',2),
 p('در قسمت قدام (جلو) استخوان اسفنوئید.',2),
 p('این استخوان داخل حفره جمجمه‌ای قدامی قرار گرفته است و در تشکیل ساختارهای زیر مشارکت دارد:',2),
 p('جدار داخلی اربیت (کاسه چشم).',2),
 p('جدار خارجی حفره بینی.',2),
 p('سقف حفره بینی.',2),
 p('جدار داخلی حفره بینی.',2),
 p('تیغه بینی (Nasal Septum).',2),
 plate('ethmoid_location',2,'جای اتموئید در استخوان‌های جمجمه','نمای ترکیبی استخوان‌های صورت','اجزای اتموئید با فهرست شماره‌دار در تصویر جزوه مشخص شده‌اند.',[['صفحهٔ چشمی','Orbital plate'],['سلول هوایی اتموئید','Ethmoidal air cell'],['شاخک میانی','Middle concha']]),
 reference('netter','hn03_netter_p29_nasal.jpeg','دیوارهٔ طرفی بینی','نتر، ویراست ۸، پلیت ۲۹، ص ۸۱','Cranium: Median Section','نمای دیوارهٔ بینی پس از برداشتن تیغه','شاخک‌های میانی و فوقانی و مجاورت استخوان پرویزنی را در تصویر مرجع ببینید.',[['استخوان پرویزنی','Ethmoid bone'],['شاخک میانی بینی','Bony middle nasal concha'],['شاخک فوقانی بینی','Bony superior nasal concha']]),
 heading('اجزای تشکیل‌دهنده استخوان اتموئید'),
 p('این استخوان کلاً از چهار بخش اصلی تشکیل شده است:',3),
 p('۱. صفحه افقی یا Cribriform plate (صفحه غربالی).',3),
 p('۲. صفحه عمودی یا Perpendicular plate.',3),
 p('۳. دو عدد توده طرفی یا Labyrinth (توده‌های پیچ‌درپیچ).',3),
 plate('ethmoid_parts',3,'بخش‌های اتموئید در نمای جداشده','نمای داخلی بخش‌های جداشدهٔ قاعده','استخوان اتموئید در تصویر رنگی و فهرست خود تصویر مشخص شده است.',[['استخوان اتموئید','Ethmoidal bone'],['تیغهٔ چشمی','Orbital plate'],['تاج خروس','Crista galli']])]))
items.append(topic(3,'نماها و صفحهٔ غربالی اتموئید',[3,4], 'نماهای اتموئید، کریستا گالی و صفحهٔ غربالی', 'صفحهٔ غربالی چه رشته‌هایی را عبور می‌دهد؟',[
 heading('بررسی استخوان اتموئید از نماهای مختلف'),
 plate('ethmoid_views',3,'نماهای مختلف استخوان اتموئید','نماهای قدامی، فوقانی، خلفی، طرفی و تحتانی','در تصویر جزوه اجزای استخوان در نماهای مختلف برچسب‌گذاری شده‌اند.',[['صفحهٔ عمودی','Perpendicular plate'],['تیغهٔ غربالی','Cribriform plate'],['تاج خروس','Crista galli']]),
 p('نمای قدامی: استخوان از این نما قابل مشاهده است.',4),
 p('نمای فوقانی: شامل صفحه غربالی، توده‌های طرفی و بخشی از صفحه عمودی.',4),
 p('نمای خلفی: شامل صفحه عمودی، صفحه افقی و توده‌های طرفی (لابیرنت).',4),
 p('نمای لترال (کناری): شامل صفحه افقی، صفحه عمودی و توده‌های طرفی.',4),
 p('نمای تحتانی: در این نما استخوان در محل اتموئیدال ناچ (Ethmoidal notch) از استخوان فرونتال قرار می‌گیرد. در این نما هم توده‌های طرفی، صفحه افقی و صفحه عمودی قابل مشاهده هستند.',4),
 heading('جزئیات ساختاری (صفحه غربالی، کریستا گالی و اعصاب)'),
 p('داخل صفحه افقی (Cribriform plate)، سوراخ‌های ریزی وجود دارد که برای عبور رشته‌های اعصاب بویایی (Olfactory nerves) تعبیه شده‌اند. به همین دلیل است که به آن صفحه غربالی می‌گویند. بالای این سوراخ‌ها، پیاز بویایی یا Olfactory bulb قرار می‌گیرد.',4),
 p('کریستا گالی (Crista galli): بخشی از صفحه عمودی که بالای صفحه غربالی قرار می‌گیرد و در مرکز صفحه افقی واقع شده است. به معنی تاج خروسی هست.',4),
 p('اگر در طرفین کریستا گالی برجستگی وجود داشته باشد، حاوی سلول‌های هوایی است.',4),
 p('فرامن سکوم (Foramen cecum): کریستا گالی دو بال در جلو ایجاد می‌کند که با دو بال از تیغه فالکس (Falx cerebri) در تشکیل فرامن سکوم (Foramen caecum) شرکت می‌کند.',4),
 p('کانال‌های اتموئیدال: در سطوح فوقانی صفحه غربالی ناودان‌هایی وجود دارد؛ همچنین در حاشیه بریدگی استخوان اتموئیدال از استخوان فرونتال هم ناودان‌هایی است. از ترکیب این ناودان‌ها، کانال‌هایی در قسمت قدامی و خلفی ایجاد می‌شود که به آنها کانال‌های اتموئیدال قدامی و خلفی می‌گویند. این کانال‌ها باعث ارتباط اربیت با حفره جمجمه‌ای قدامی می‌شوند.',4),
 plate('ethmoid_superior',4,'نمای فوقانی اتموئید','نمای فوقانی','صفحهٔ غربالی و کریستا گالی و توده‌های طرفی در تصویر جزوه نام‌گذاری شده‌اند.',[['صفحهٔ غربالی','Cribriform plate'],['کریستا گالی','Crista galli'],['لابیرنت','Labyrinth']])]))

items.append(topic(4,'توده‌های طرفی و لامینا پاپیراسه',[5,6], 'سلول‌های هوایی اتموئید و مجاورت‌های سطح خارجی', 'لامینا پاپیراسه در کدام دیواره شرکت می‌کند؟',[
 heading('توده‌های طرفی (لابیرنت) و سلول‌های هوایی'),
 p('توده‌های طرفی (لابیرنت یا توده‌های پیچ‌درپیچ) در سطح فوقانی خودشون با اتموئیدال ناچ از استخوان فرونتال مفصل می‌شوند. این توده‌ها دارای سلول‌های هوایی هستند که به آنها اتموئیدال ایرسل (Ethmoidal air cells) می‌گویند. این سلول‌ها در سه بخش دسته‌بندی می‌شوند:',5),
 p('۱. سلول‌های هوایی قدامی: ۱۱ عدد.',5),
 p('۲. سلول‌های هوایی میانی: ۳ عدد در هر طرف.',5),
 p('۳. سلول‌های هوایی خلفی: ۶ عدد که در قسمت خلف قرار گرفته‌اند.',5),
 plate('labyrinth',5,'لابیرنت، سلول‌ها و صفحهٔ چشمی','تصویر ترکیبی جزوه','در این تصویر سلول‌های هوایی و صفحهٔ چشمی اتموئید نشان داده شده‌اند.',[['سلول‌های هوایی اتموئید','Ethmoid air cells'],['لابیرنت','Labyrinth'],['صفحهٔ چشمی','Orbital plate']]),
 heading('ادامه بررسی توده‌های طرفی و لامینا پاپیراسه'),
 p('توده‌های طرفی استخوان اتموئید در سطح خارجی خودشان با اوربیتال پلیت (Orbital plate) پوشیده شده‌اند. به دلیل نازک بودن این صفحه، به آن لامینا پاپیراسه (Lamina papyracea) می‌گویند؛ لامینا یعنی تیغه و پاپیراسه یعنی کاغذی.',5),
 p('نقش: لامینا پاپیراسه داخل تشکیل جدار داخلی کاسه چشم (Orbit) نقش دارد.',6),
 heading('مجاورت‌ها:'),
 p('در جدار داخلی اربیت، این صفحه سلول‌های هوایی خلفی و میانی اتموئید را می‌پوشاند.',6),
 p('در قسمت قدام دیواره داخلی اربیت، استخوان لاکریمال (اشکی) قرار دارد که جدار قدامی اربیت را می‌سازد و سلول‌های هوایی قدامی رو می‌پوشاند.',6),
 p('سلول‌های هوایی اتموئیدال قدامی با سلول‌های هوایی زائده فرونتال استخوان ماگزیلا و استخوان لاکریمال تکمیل می‌شوند.',6),
 p('توده‌های طرفی در قسمت خلف با استخوان اسفنوئید مفصل می‌شوند.',6),
 p('سطح تحتانی توده‌های طرفی با زائده اوربیتال استخوان کامی (Palatine bone) و صفحه اوربیتال استخوان ماگزیلا مفصل می‌شوند.',6),
 plate('lateral_ethmoid',6,'لامینا پاپیراسه در نمای طرفی','نمای طرفی استخوان اتموئید','صفحهٔ چشمی و سلول‌های اتموئیدی در تصویر جزوه برچسب دارند.',[['صفحهٔ چشمی','Orbital plate'],['سلول‌های اتموئیدی','Ethmoid air cells'],['زائدهٔ قلابی','Uncinate process']])]))
items.append(topic(5,'شاخک‌ها و مجاری بینی',[6,7], 'شاخک‌ها، مجاری و زائدهٔ قلابی اتموئید', 'شاخک‌ها چه ارتباطی با مجاری بینی دارند؟',[
 heading('شاخک‌های بینی (Conchae) و مجاری بینی (Meatuses)'),
 p('اگر اوربیتال پلیت رو برداریم، در عمقش شاخک فوقانی و شاخک میانی رو می‌بینیم. این شاخک‌ها صفحات استخوانی خمیده‌ای هستند که از صفحه عمودی به سمت خارج برگشته‌اند.',6),
 plate('inferior_ethmoid',6,'اتموئید از پایین','نمای تحتانی استخوان اتموئید','شاخک‌های فوقانی و میانی در تصویر جزوه مشخص‌اند.',[['شاخک فوقانی','Superior concha'],['شاخک میانی','Middle concha'],['زائدهٔ قلابی','Uncinate process']]),
 p('نکته مهم کنکوری: شاخک تحتانی (Inferior nasal concha) یک استخوان مستقل است و جزئی از استخوان اتموئید محسوب نمی‌شود!',7),
 p('ماتوس‌ها (مجاری بینی): زیر هر شاخک، یک فضا یا مجرا به نام ماتوس به وجود می‌آید:',7),
 p('سوپریور نیزال ماتوس (Superior meatus): محل تخلیه سلول‌های اتموئیدال خلفی.',7),
 p('میدل نیزال ماتوس (Middle meatus): محل تخلیه سینوس ماگزیلا، سینوس فرونتال، سلول‌های اتموئیدال قدامی و میانی و مجرای نازولاکریمال (مجرای اشکی).',7),
 {'type':'callout','kind':'info','title':'توضیح تکمیلی جدا از متن جزوه','text':'جزوه در جملهٔ بالا مجرای نازولاکریمال را در فهرست مجرای میانی آورده است. مرجع مستقل StatPearls دهانهٔ مجرای نازولاکریمال را در مجرای تحتانی بینی معرفی می‌کند؛ عبارت جزوه دست‌نخورده حفظ شده است.','src':'StatPearls، Anatomy, Head and Neck, Nasal Cavity، بخش Structure and Function'},
 plate('nasal_conchae',7,'شاخک‌های بینی','نمای دیوارهٔ طرفی بینی','تصویر جزوه شاخک‌های فوقانی و میانی را نام‌گذاری می‌کند.',[['شاخک فوقانی بینی','Superior nasal concha'],['شاخک میانی بینی','Middle nasal concha']]),
 heading('آنسینیت پروسس (Uncinate Process) و بولای اتموئیدال'),
 p('از توده‌های طرفی، زائده‌ای به سمت پایین و عقب می‌آید که به آن آنسینیت پروسس (Uncinate process) یا زائده قلابی می‌گویند.',7),
 p('عملکرد آنسینیت پروسس: ۱. دهانه سینوس ماگزیلاری رو محدود می‌کند.',7),
 p('۲. از توده‌های طرفی اتموئید به پایین و عقب کشیده می‌شود و به زائده اتموئیدال از شاخک تحتانی بینی متصل می‌شود.',7),
 p('بولای اتموئیدال (Bulla ethmoidalis): سلول‌های هوایی میانی یک برجستگی را در جدار خارجی حفره بینی ایجاد می‌کنند که به آن بولا (به معنی توپ یا برجستگی کوچک) می‌گویند.',7),
 p('هیاتوس سمی‌لوناریس (Hiatus semilunaris): بین بولا و آنسینیت پروسس، یک شکاف هلالی وجود دارد که به آن هیاتوس سمی‌لوناریس می‌گویند. دهانه سینوس ماگزیلاری در این شکاف باز می‌شود.',7),
 plate('uncinate',7,'زائدهٔ قلابی و مجاری بینی','نمای دیوارهٔ طرفی بینی','زائدهٔ قلابی و ناحیهٔ بولا در تصویر جزوه نشان داده شده‌اند.',[['زائدهٔ قلابی','Uncinate process'],['بولای اتموئیدی','Bulla ethmoidalis'],['شکاف نیم‌هلالی','Hiatus semilunaris']])]))
items.append(topic(6,'صفحهٔ عمودی استخوان اتموئید',[8], 'شکل، سطوح و کنارهای صفحهٔ عمودی', 'صفحهٔ عمودی در تشکیل کدام تیغه شرکت دارد؟',[
 heading('صفحه عمودی استخوان اتموئید (Perpendicular Plate)'),
 p('این صفحه بخش میانی استخوان اتموئید می‌باشد:',8),
 p('شکل: نازک، تخت و به صورت چهارگوش (Quadrilateral).',8),
 p('موقعیت: از زیر صفحه افقی به سمت پایین کشیده شده است و دقیقاً در خط وسط (مدین) قرار دارد.',8),
 p('این صفحه در تشکیل تیغه بینی (Nasal Septum) مشارکت می‌کند.',8),
 plate('ethmoid_section',8,'اتموئید در برش میانی جمجمه','برش میانی جمجمه','صفحهٔ غربالی، تاج خروس و استخوان ومر در تصویر مشخص‌اند.',[['صفحهٔ غربالی','Cribriform plate'],['تاج خروس','Crista galli'],['خیش','Vomer']]),
 heading('ادامه بررسی صفحه عمودی استخوان اتموئید (Perpendicular Plate)'),
 p('سطوح: صفحه عمودی دو سطح جانبی دارد که جدار داخلی حفره‌های بینی را در سمت راست و چپ تشکیل می‌دهد.',8),
 p('بافت: سطح استخوان به طور کلی صاف می‌باشد، ولی در نزدیکی صفحه افقی، شیارهایی وجود دارد که مربوط به عصب بویایی (Olfactory nerve) هستند. گاهی اوقات این شیارها عمیق‌تر می‌شوند و تشکیل کانال می‌دهند.',8),
 p('نقش: صفحه عمودی در تشکیل تیغه بینی (Nasal septum) نقش اساسی دارد.',8),
 p('کنارها (Borders): این صفحه چهار کنار دارد:',8),
 p('۱. کنار قدامی (Anterior border): با نازال کرست (Nasal crest) از استخوان بینی (Nasal bone) و خار بینی استخوان فرونتال (Nasal spine of frontal bone) مفصل می‌شود.',8),
 p('۲. کنار فوقانی (Superior border): زیر صفحه غربالی (Cribriform plate) واقع شده است و به آن وصل می‌شود.',8),
 plate('nasal_septum',8,'تیغهٔ بینی و صفحهٔ عمودی','نمای داخلی تیغهٔ بینی','صفحهٔ عمودی، غضروف و خیش در تصویر جزوه نشان داده شده‌اند.',[['صفحهٔ عمودی','Perpendicular plate'],['غضروف تیغه','Septal cartilage'],['خیش','Vomer']])]))

exec((ROOT/'headneck/scripts/prepare_hn04_petrous.py').read_text(encoding='utf-8'))
exec((ROOT/'headneck/scripts/prepare_hn04_fossae.py').read_text(encoding='utf-8'))
exec((ROOT/'headneck/scripts/prepare_hn04_part2.py').read_text(encoding='utf-8'))
exec((ROOT/'headneck/scripts/prepare_hn04_reference.py').read_text(encoding='utf-8'))

outline={'session':'hn04','title':'قاعدهٔ جمجمه','pages':[1,25],'topics':[m for m,_ in items]}
content=ROOT/'headneck/content'; (content/'outline/hn04_topics.json').write_text(json.dumps(outline,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
(content/'hn04_a.json').write_text(json.dumps([x for _,x in items],ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
(content/'hn04_b.json').write_text('[]\n',encoding='utf-8')
print('Prepared 20 topical sections from both parts; review the audit report for limitations.')

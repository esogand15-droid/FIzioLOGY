"""Shared four-page shell modelled on the original HumsYar writer edition."""
from __future__ import annotations
import copy
import build_headneck as H
K=H.K

NFIG={1:78,2:65,3:43,4:69}
FIG_TYPES={1:(45,29,4),2:(35,26,4),3:(26,12,5),4:(54,10,5)}
NEXT={1:'جلسهٔ ۲: استخوان گونه، فک تحتانی، گیجگاهی و آهیانه.',2:'جلسهٔ ۳: استخوان‌های اسفنوئید، کامی و پس‌سری.',3:'جلسهٔ ۴: قاعدهٔ جمجمه و سوراخ‌ها و مجاری آن.',4:'جلسهٔ ۵: مهره‌ها، مفاصل، فاسیاها و فضاهای گردن.'}

def cfg_for(n):
 cfg=copy.deepcopy(H.HN_SESSIONS[f'hn{n:02}'])
 # The title must be specific to the booklet, but the visual layout follows the sample.
 cfg['cover_title']=["آناتومی سر و گردن",{1:'جلسهٔ ۱ — جمجمه و فک فوقانی',2:'جلسهٔ ۲ — استخوان‌های صورت و طرفی',3:'جلسهٔ ۳ — استخوان‌های عمقی جمجمه',4:'جلسهٔ ۴ — قاعدهٔ جمجمه'}[n]]
 return cfg

def cover(book,cfg):
 c=book.c
 for text,font,size,color,y in [
  ('HumsYar · جزوهٔ مادر آناتومی','VazirM',11,K.TEAL_L,.86),
  (cfg['cover_title'][0],'VazirB',29,K.CARD,.615),
  (cfg['cover_title'][1],'VazirB',27,K.CARD,.552),
  (cfg['cover_topic'],'Vazir',12,K.TEAL_L,.475)]:
  K.draw_shaped(c,K.A4W/2,K.A4H*y,K.shape(text),font,size,color,align='center')
 c.setStrokeColor(K.HexColor('#0d9488'));c.setLineWidth(1.4);c.line(K.A4W*.30,K.A4H*.44,K.A4W*.70,K.A4H*.44)
 lines=[f"جلسهٔ {cfg['num']} از {cfg['of']} — {cfg['lecture']}",
        'متن: جزوهٔ درس · توضیح‌های تکمیلی با ارجاع جداگانه',
        'تصویر: جزوهٔ درس · نتر، اطلس آناتومی انسان، ویراست ۸ · گری، آناتومی برای دانشجویان، ویراست ۳',
        'نسخهٔ به‌روزشدهٔ جزوه‌نویسی']
 for i,text in enumerate(lines):
  K.draw_shaped(c,K.A4W/2,K.A4H*.375-i*18,K.shape(text),'Vazir',9.8,K.HexColor('#94a3b8'),align='center')
 K.draw_shaped(c,K.A4W/2,K.A4H*.12,K.shape('سند کاری درس آناتومی سر و گردن — نسخهٔ آموزشی'),'VazirL',8.4,K.HexColor('#64748b'),align='center')

def front(book,cfg):
 n=cfg['n'];book.h1('ساختار این جزوه و قاعدهٔ خواندن آن',anchor='front-colophon',kicker='قبل از شروع بخوانید')
 rows=[
  {'label':'قاعدهٔ ساخت','text':'متن درس و توضیح‌های تکمیلی با عنوان و ارجاع مشخص در مبحث‌ها آمده‌اند. هر مبحث شناسنامه، متن، شکل و برگهٔ تحویل دارد.'},
  {'label':'جای شکل‌ها','text':'قاب‌ها در مبحث مرتبط قرار گرفته‌اند؛ ممکن است قاب بزرگ به صفحهٔ بعد منتقل شود. شرح هر تصویر در کنار همان قاب آمده است.'},
  {'label':'منابع متن','text':cfg['lecture']+'؛ متن درس و توضیح‌های افزوده با ارجاع مجزا آمده‌اند. نتر و گری برای تصاویر و توضیح‌های مستند به همان منبع استفاده شده‌اند.'},
  {'label':'منابع تصویر','text':(' · '.join(K.fa_digits(str(v))+' قاب از '+name for v,name in zip(FIG_TYPES[n],('جزوهٔ درس','نتر','گری')))+'. منبع هر قاب در همان مبحث مشخص شده است.')},
  {'label':'واحد شمارش','text':'واحد این جزوه «مبحث» است: هر مبحث یک شماره، یک عنوان و یک سطر در فهرست دارد؛ ارجاع‌دهی و ویرایش بر همین شماره انجام می‌شود.'}]
 book.label_card('این جزوه چگونه ساخته شده است',rows,accent=K.TEAL,tint=K.TEAL_LL,kicker='شناسنامه',footer='جزوهٔ مادر برای کار جزوه‌نویسان')
 book.h2('قاعدهٔ ارجاع و علامت‌گذاری',anchor='front-cite')
 book.numbered([
  'شمارهٔ صفحهٔ جزوه، شمارهٔ صفحهٔ فایل منبع است؛ شمارهٔ صفحهٔ چاپی، شمارهٔ پلیت و شمارهٔ شکل کتاب با برچسب خودشان مشخص می‌شوند.',
  'هر قاب تصویر عنوان و ارجاع منبع دارد؛ شرح فارسی، تصویر را به متن مبحث مرتبط می‌کند و عنوان اصلی در صورت وجود آمده است.',
  'برچسب‌های دوزبانه نام ساختارها یا راهنمای جهت‌یابی‌اند؛ در تصویر بدون برچسب، راهنما را جای برچسب چاپ‌شده فرض نکنید.',
  'متن درس و توضیح‌های آموزشی یا مقایسهٔ منابع به‌صورت جداگانه و با ارجاع همان بخش خوانده می‌شوند.',
  'کادر یادداشت و برگهٔ تحویل پایان هر مبحث برای ثبت نکته، پرسش، منابع و مشخصات جزوه‌نویس در نظر گرفته شده‌اند.'
 ])

def opening(book,n,outline,toc):
 cfg=cfg_for(n)
 book.dark_page(lambda b:cover(b,cfg),reuse_blank_page=True)
 front(book,cfg)
 H.toc_page(book,cfg,outline,toc or {})
 H.divider(book,f"فصل {cfg['num']} · جلسهٔ {cfg['num']}",cfg['divider_title'],cfg['divider_sub'],
   [K.fa_digits(str(len(outline['topics'])))+' مبحث · '+K.fa_digits(str(NFIG[n]))+' قاب تصویر',
    'متن هر مبحث با ارجاع، و هر تصویر با مشخصات منبع',
    'متن درس · شکل · جدول · راهنمای جزوه‌نویس'])
 book.heading_pages[cfg['anchor']]=book.page-1
 return cfg

def next_section(book,n):
 book.ensure(165)
 book.h1('قدم بعدی: چه چیزی در جلسهٔ بعد می‌آید',anchor='hn-next',kicker='ادامهٔ کار')
 book.para('ادامهٔ این مجموعه در جلسهٔ بعد دنبال می‌شود:')
 book.bullets([NEXT[n]])

def back(book,n):
 # Paint on the last page without creating a superfluous blank page afterwards.
 cfg=cfg_for(n);book.new_page();book.dark_mode=True
 c=book.c;c.saveState();p=c.beginPath();p.rect(0,0,K.A4W,K.A4H);c.clipPath(p,stroke=0,fill=0)
 c.setFillColor(K.DARK_1);c.rect(0,0,K.A4W,K.A4H,stroke=0,fill=1)
 c.linearGradient(0,K.A4H,K.A4W,0,(K.DARK_1,K.DARK_2,K.DARK_3),(0,.55,1));c.restoreState()
 book._halo(K.A4W*.84,K.A4H*.88,250,K.Color(37/255,99/255,235/255),.30)
 book._halo(K.A4W*.16,K.A4H*.10,270,K.Color(20/255,184/255,166/255),.26)
 for text,font,size,color,y in [('HumsYar','VazirB',20,K.CARD,.62),('جزوهٔ مادر آناتومی سر و گردن','Vazir',11,K.TEAL_L,.56),
  (f"جلسهٔ {cfg['num']} از {cfg['of']} — {cfg['title']}",'Vazir',9.5,K.HexColor('#94a3b8'),.50),
  ('تصویرها از جزوه، نتر و گری · متن از جزوهٔ درس','VazirL',8.4,K.HexColor('#94a3b8'),.44)]:
  K.draw_shaped(c,K.A4W/2,K.A4H*y,K.shape(text),font,size,color,align='center')

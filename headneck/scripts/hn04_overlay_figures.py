"""Attach reference figures and readable citation overrides to the teaching layer."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def attach(overlay):
 base=json.loads((ROOT/'headneck/content/hn04_a.json').read_text())
 idx={a['path']:a for a in json.loads((ROOT/'headneck/images/INDEX.json').read_text())['assets']}
 for t in base:
  spec=overlay['topics'][t['topic_id']]
  overrides={}
  for i,b in enumerate(t['blocks']):
   if b['type']!='plate' or b['book']=='lecture':continue
   a=idx[b['asset']]
   cite=b['citation']
   if b['book']=='grays':
    printed=a.get('printed_page',860)
    cite=f"گری، شکل {a.get('figure','8.21')}، ص چاپی {printed}؛ ص {a['page']} PDF بخش ۸۰۱–۱۰۰۰".translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
   overrides[str(i)]={'citation':cite,'src':cite,'min_img_h':70}
  spec['plate_overrides']=overrides
 def add(n,aid,title,cite,caption,description,labels,max_h):
  b=dict(type='plate',book='netter' if 'netter' in aid else 'grays',asset='headneck/images/'+aid+'.jpeg',title=title,citation=cite,en_caption=caption,view='نمای فوقانی' if n in (13,14,19) else 'نمای تحتانی',fa_text=description,labels=labels,src=cite,max_h=max_h,min_img_h=100 if n == 14 else 80)
  # Directly beside its lecture counterpart, before the additive learning table.
  original=base[n-1]['blocks']; plateidx=max(i for i,b in enumerate(original) if b['type']=='plate')
  key=str(plateidx); after=overlay['topics'][f'hn04-T{n:02}']['after']
  after[key]=[b]+after.get(key,[])
 add(13,'hn04_grays_f825','نقشهٔ مرجع حفرهٔ قدامی',
     'گری، شکل ۸.۲۵، ص چاپی ۸۶۵؛ ص ۹۳ PDF بخش ۸۰۱–۱۰۰۰','Anterior cranial fossa',
     'در شکل اصلی، کریستا گالی را در خط وسط و صفحهٔ غربالی را در طرفین آن پیدا کنید؛ نمای کوچک کنار شکل، جای حفره را در کل قاعده نشان می‌دهد.',
     [['کریستا گالی','Crista galli'],['صفحهٔ غربالی','Cribriform plate'],['بال کوچک','Lesser wing']],110)
 add(14,'hn04_grays_f826','نقشهٔ مرجع حفرهٔ میانی',
     'گری، شکل ۸.۲۶، ص چاپی ۸۶۷؛ ص ۹۵ PDF بخش ۸۰۱–۱۰۰۰','Middle cranial fossa',
     'ابتدا زین ترکی را در مرکز و سپس روتاندوم، اوال و اسپاینوزوم را در طرفین پیدا کنید. دهانهٔ کانال کاروتید و سوراخ پاره دو برچسب جدا دارند.',
     [['روتاندوم','Foramen rotundum'],['اوال','Foramen ovale'],['اسپاینوزوم','Foramen spinosum']],125)
 add(19,'hn04_netter_p30_superior','استخوان درزی در نمای فوقانی کالواریا',
     'نتر، پلیت ۳۰، ص ۸۲ فایل PDF','Calvaria — Superior view',
     'برش انتخابی از نمای فوقانی است؛ قطعهٔ کوچک ورمین کنار درز لامبدوئید برچسب دارد. آن را با لامبدا، یعنی محل تلاقی درزها، اشتباه نگیرید.',
     [['استخوان ورمین','Sutural bone (Wormian)'],['لامبدا','Lambda'],['درز لامبدوئید','Lambdoid suture']],125)
 add(10,'hn04_netter_p31_inferior','جای پتروس در قاعدهٔ تحتانی',
     'نتر، پلیت ۳۱، ص ۸۳ فایل PDF','Cranial Base: Inferior View',
     'دهانهٔ کانال کاروتید را جلوتر از حفرهٔ ژوگولار پیدا کنید. این نمای جامع برای جهت‌یابی است؛ کانالیکول‌های کوچک در قاب‌های بزرگ‌نمایی مبحث ۱۱ و ۱۷ خوانده می‌شوند.',
     [['دهانهٔ خارجی کانال کاروتید','External opening of carotid canal'],['حفرهٔ ژوگولار','Jugular fossa'],['بخش پتروس','Petrous part']],170)
 return overlay

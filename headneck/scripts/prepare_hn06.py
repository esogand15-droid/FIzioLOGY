"""Generate session 6 topical content and individually sourced figure assets.

The page-indexed transcription is maintained separately. Figure placement keys
are explicit (page, block index), preserving cross-page continuations.
"""
from __future__ import annotations
import io, json
from pathlib import Path
import pymupdf
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'علوم تشریح سر و گردن/جلسه 6 - عضلات گردن/جلسه_ششم_علوم_تشریح_سر_و_گردن_مهر_1404.pdf'
NETTER=next((ROOT/'علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1').glob('Netter*'))
GRAY=ROOT/"علوم تشریح دستگاه اعصاب/user - Gray's Anatomy For Students, 3rd Edition-1001-1189.pdf"
C=ROOT/'headneck/content'; I=ROOT/'headneck/images/INDEX.json'
index=json.loads(I.read_text(encoding='utf-8'))
index['assets']=[a for a in index['assets'] if not a.get('asset_id','').startswith('hn06_')]
doc=pymupdf.open(SOURCE)
# Source figure order is top-to-bottom, not necessarily PDF object order.
spec={
 2:[('عضلات بالا و زیر لامی',[('استخوان لامی','Hyoid bone'),('عضله اوموهایوئید','Omohyoid')],(2,8))],
 3:[('عضلات لامی و اوموهایوئید',[('عضله اوموهایوئید','Omohyoid'),('استخوان لامی','Hyoid bone')],(3,9))],
 4:[('نمای عضلات بالا و زیر لامی',[('عضله مایلوهایوئید','Mylohyoid'),('عضله استرنوهایوئید','Sternohyoid')],(4,7))],
 7:[('عضله استایلوهایوئید و عضلات لامی',[('استایلوهایوئید','Stylohyoid'),('بطن خلفی دیگاستریک','Digastric posterior belly')],(7,5))],
 9:[('عضلات کف دهان و گردن',[('مایلوهایوئید','Mylohyoid'),('ژنیوهایوئید','Geniohyoid')],(8,13))],
 11:[('عضلات پیش‌مهره‌ای و اسکالن',[('لانگوس کولی','Longus colli'),('اسکالن میانی','Middle scalene')],(10,19))],
 14:[('ناحیه خلفی گردن',[('تراپزیوس','Trapezius'),('اسپلنیوس کپیتیس','Splenius capitis')],(14,8))],
 15:[('نمای عضلات شانه و فاسیای گردن',[],(15,1)),('عضله تراپزیوس',[('بخش میانی','Middle part'),('خار کتف','Spine of scapula')],(15,3)),('اتصالات تراپزیوس',[('خار کتف','Spine of scapula'),('ترقوه','Clavicle')],(15,5))],
 16:[('اسپلنیوس کپیتیس و سرویسس',[('اسپلنیوس کپیتیس','Splenius capitis'),('اسپلنیوس سرویسس','Splenius cervicis')],(16,0))],
 17:[('عضله لواتور اسکاپولا',[('لواتور اسکاپولا','Levator scapulae'),('زاویه فوقانی کتف','Superior angle of scapula')],(17,4))],
 18:[('عضلات عمقی خلف گردن',[('سمی‌اسپاینالیس کپیتیس','Semispinalis capitis'),('رکتوس کپیتیس خلفی بزرگ','Rectus capitis posterior major')],(17,11))],
 19:[('اتصالات سمی‌اسپاینالیس کپیتیس',[('سمی‌اسپاینالیس کپیتیس','Semispinalis capitis'),('رباط نوکال','Ligamentum nuchae')],(18,1)),('مثلث ساب‌اکسیپیتال',[('رکتوس کپیتیس خلفی بزرگ','Rectus capitis posterior major'),('اوبلیکوس کپیتیس تحتانی','Obliquus capitis inferior')],(19,10))],
 20:[('عضلات زیر پس‌سری',[('رکتوس کپیتیس خلفی کوچک','Rectus capitis posterior minor'),('اوبلیکوس کپیتیس فوقانی','Obliquus capitis superior')],(20,0))],
}
slots={}
def register(name,book,src,page,bbox,im):
 path=ROOT/f'headneck/images/{name}.jpeg'; im.save(path,quality=95,optimize=True); rel=str(path.relative_to(ROOT))
 index['assets'].append({'asset_id':name,'book':book,'session':'hn06','source_file':str(src.relative_to(ROOT)),'page':page,'bbox':[round(x,2) for x in bbox],'w':im.width,'h':im.height,'bytes':path.stat().st_size,'path':rel})
 return rel
for pg,figs in spec.items():
 blocks=sorted((b for b in doc[pg-1].get_text('dict')['blocks'] if b['type']==1 and b['bbox'][1]>50 and b['bbox'][3]<725),key=lambda b:b['bbox'][1])
 assert len(blocks)==len(figs),(pg,len(blocks),len(figs))
 for j,(b,(title,labs,where)) in enumerate(zip(blocks,figs),1):
  bbox=pymupdf.Rect(b['bbox']);im=Image.open(io.BytesIO(b['image'])).convert('RGB')
  h=max(1,round(im.width*bbox.height/bbox.width));im=im.resize((im.width,h),Image.Resampling.LANCZOS)
  rel=register(f'hn06_lecture_p{pg:02}_{j}','lecture',SOURCE,pg,bbox,im)
  item={'type':'plate','book':'lecture','asset':rel,'title':title,'citation':f'جزوهٔ جلسهٔ ۶، ص {pg} از فایل PDF','src':f'جزوهٔ جلسهٔ ۶، صفحهٔ PDF {pg}','view':'تصویر جزوه','fa_text':'تصویر جزوه برای همین بخش.', 'labels':labs,'max_h':120,'min_img_h':round(min(75,165*im.height/im.width))}
  slots.setdefault(where,[]).append(item)
# Figures of reference books; rectangles include figure and its own caption when applicable.
refs=[
 ('netter',NETTER,105,(52,170,578,600),'hyoid','عضلات بالا و زیر لامی','نتر، ویراست ۸، پلیت ۵۳، ص ۱۰۵ فایل PDF','Infrahyoid and Suprahyoid Muscles',[('استخوان لامی','Hyoid bone'),('مایلوهایوئید','Mylohyoid')],(2,8)),
 ('netter',NETTER,106,(52,95,576,716),'lateral','عضلات گردن از پهلو','نتر، ویراست ۸، پلیت ۵۴، ص ۱۰۶ فایل PDF','Muscles of Neck: Lateral View',[('استایلوهایوئید','Stylohyoid'),('بطن خلفی دیگاستریک','Posterior belly of digastric')],(7,9)),
 ('netter',NETTER,107,(52,95,576,716),'prevertebral','عضلات قدامی و طرفی گردن','نتر، ویراست ۸، پلیت ۵۵، ص ۱۰۷ فایل PDF','Anterior and Lateral Cervical Muscles',[('لانگوس کولی','Longus colli'),('اسکالن قدامی','Scalenus anterior')],(11,0)),
 ('netter',NETTER,281,(48,100,582,345),'posterior_superficial','لایهٔ سطحی عضلات پشت گردن','نتر، ویراست ۸، پلیت ۱۹۵، ص ۲۸۱ فایل PDF','Muscles of Back: Superficial Layer',[('تراپزیوس','Trapezius m.'),('اسپلنیوس کپیتیس','Splenius capitis m.')],(15,6)),
 ('netter',NETTER,283,(85,100,565,300),'posterior_deep','لایهٔ عمقی عضلات پشت گردن','نتر، ویراست ۸، پلیت ۱۹۷، ص ۲۸۳ فایل PDF','Muscles of Back: Deep Layer',[('سمی‌اسپاینالیس کپیتیس','Semispinalis capitis m.'),('اوبلیکوس کپیتیس تحتانی','Obliquus inferior capitis m.')],(18,5)),
 ('grays',GRAY,37,(50,280,555,740),'infrahyoid','عضلات زیر لامی','گری، ویراست ۳، شکل ۸.۱۶۴، ص چاپی ۱۰۰۹، ص ۳۷ فایل PDF','Fig. 8.164 Infrahyoid muscles.',[('استرنوهایوئید','Sternohyoid muscle'),('اوموهایوئید','Omohyoid muscle')],(4,5)),
 ('grays',GRAY,36,(55,325,310,740),'suprahyoid','عضلات بالای لامی','گری، ویراست ۳، شکل ۸.۱۶۳، ص چاپی ۱۰۰۸، ص ۳۶ فایل PDF','Fig. 8.163 Suprahyoid muscles. A. Lateral view. B. Inferior view.',[('استایلوهایوئید','Stylohyoid muscle'),('مایلوهایوئید','Mylohyoid muscle')],(8,11)),
 ('grays',GRAY,57,(55,65,555,505),'prevertebral','عضلات پیش‌مهره‌ای و طرفی','گری، ویراست ۳، شکل ۸.۱۸۵، ص چاپی ۱۰۲۹، ص ۵۷ فایل PDF','Fig. 8.185 Prevertebral and lateral vertebral muscles supplied by cervical plexus.',[('لانگوس کپیتیس','Longus capitis muscle'),('اسکالن‌ها','Scalene muscles')],(13,6)),
]
for book,src,pg,box,slug,title,cite,caption,labs,where in refs:
 with pymupdf.open(src) as ref:
  pix=ref[pg-1].get_pixmap(matrix=pymupdf.Matrix(2,2),clip=pymupdf.Rect(box),alpha=False)
 im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
 rel=register(f'hn06_{book}_{slug}',book,src,pg,box,im)
 slots.setdefault(where,[]).append({'type':'plate','book':book,'asset':rel,'title':title,'citation':cite,'src':cite,'en_caption':caption,'view':'تصویر مرجع','fa_text':'تصویر مرجع برای مطالعهٔ ساختارهای همین مبحث.','labels':labs,'max_h':130,'min_img_h':round(min(100,165*im.height/im.width))})
I.write_text(json.dumps(index,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
trans=json.loads((C/'hn06_transcription.json').read_text(encoding='utf-8'))
assert [p['pdf_page'] for p in trans['pages']]==list(range(2,21))
entries=[(p['pdf_page'],i,b['text']) for p in trans['pages'] for i,b in enumerate(p['blocks'])]
# Topic boundaries are anchored to an exact block, so shared pages never duplicate text.
sections=[
 ((2,0),'عضلات زیر لامی: دسته‌بندی','گروه‌های سطحی و عمقی عضلات زیر لامی'),
 ((2,9),'استرنوهایوئید و اوموهایوئید','اتصالات، مسیر و عملکرد عضلات سطحی'),
 ((4,6),'استرنوتیروئید و تیروهایوئید','عضلات عمقی زیر لامی'),
 ((5,16),'دیگاستریک و استایلوهایوئید','عضلات سطحی بالای استخوان لامی'),
 ((8,2),'مایلوهایوئید، ژنیوهایوئید و مرور','کف دهان و مرور عضلات لامی'),
 ((10,17),'عضلات پیش‌مهره‌ای قدامی','رکتوس‌ها، لانگوس کپیتیس و لانگوس کولی'),
 ((13,5),'عضلات اسکالن','اسکالن‌های قدامی، میانی و خلفی'),
 ((14,7),'ناحیهٔ خلفی گردن و تراپزیوس','حدود ناحیه و طبقهٔ اول عضلات'),
 ((16,0),'اسپلنیوس و لواتور اسکاپولا','طبقهٔ دوم عضلات خلفی گردن'),
 ((17,9),'سمی‌اسپاینالیس و عضلات زیرپس‌سری','لایه‌های عمقی و چهار عضلهٔ ساب‌اکسیپیتال'),
 ((19,8),'مثلث زیرپس‌سری','مرزهای عضلانی مثلث ساب‌اکسیپیتال'),
]
starts=[next(i for i,e in enumerate(entries) if e[:2]==key) for key,_,_ in sections]+[len(entries)]
headings={(2,0),(2,9),(3,7),(4,6),(4,8),(5,7),(5,16),(6,1),(6,11),(7,4),(8,2),(8,12),(9,7),(10,17),(11,1),(12,0),(12,6),(12,12),(13,5),(13,10),(13,18),(14,2),(14,7),(15,2),(16,0),(16,2),(16,3),(16,8),(17,4),(17,9),(17,11),(18,4),(19,3),(19,8)}
outline=[];content=[];used=[]
for n,((key,title,gist),lo,hi) in enumerate(zip(sections,starts,starts[1:]),1):
 chunk=entries[lo:hi];pages=sorted({pg for pg,_,_ in chunk});
 if n==1: pages.insert(0,1)
 tid=f'hn06-T{n:02}';footer=f'جزوهٔ جلسهٔ ۶، صفحات PDF {pages[0]} تا {pages[-1]}'
 outline.append({'topic_id':tid,'title':title,'pages':pages,'gist':gist,'prereq':'شناخت استخوان لامی و نماهای گردن'})
 body=[{'type':'idcard','title':'شناسنامهٔ مبحث','kicker':'قبل از شروع این مبحث بخوانید','rows':[{'label':'جای این مبحث','text':gist},{'label':'هدف یادگیری','text':f'ساختارها و تصویرهای مبحث «{title}» را مرور کنید.'},{'label':'پیش‌نیاز','text':'شناخت استخوان لامی و نماهای گردن'}],'footer':footer}]
 for pg,i,text in chunk:
  # The original four-column table straddles PDF pages 18 and 19. Keep
  # the cells and row order intact, while presenting it as a real table.
  if (pg,i)==(18,6):
   table_rows=[e[2].split(' | ') for e in chunk if e[:2] in {(18,7),(18,8),(19,0),(19,1)}]
   assert len(table_rows)==4 and all(len(r)==4 for r in table_rows)
   body.append({'type':'table','head':text.split(' | '),'rows':table_rows,'src':'جزوهٔ جلسهٔ ۶، صفحات PDF 18 و 19'})
  elif (pg,i) not in {(18,7),(18,8),(19,0),(19,1)}:
   body.append({'type':'h3' if (pg,i) in headings else 'p','text':text,'src':f'جزوهٔ جلسهٔ ۶، صفحهٔ PDF {pg}'})
  body.extend(slots.get((pg,i),[]));used.append((pg,i))
 body.append({'type':'handoff','title':f'برگهٔ تحویل — مبحث {n}','kicker':'برای تکمیل جزوه','sources':footer,'checklist':['مبدأ و انتهای عضلات مرور شوند.','عملکرد و عصب‌دهی ثبت شوند.','شکل‌ها با متن مرتبط خوانده شوند.','اصطلاحات انگلیسی مرور شوند.','نکات جزوه از توضیحات جدا بمانند.'],'open':'مبحث را با تصویر و ارجاع آن مرور کنید.','question':gist})
 content.append({'topic_id':tid,'blocks':body})
assert used==[(pg,i) for pg,i,_ in entries]
assert all(key in used for key in slots)
(C/'outline/hn06_topics.json').write_text(json.dumps({'session':'hn06','title':'عضلات گردن','pages':[1,20],'topics':outline},ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
(C/'hn06_a.json').write_text(json.dumps(content,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
(C/'hn06_b.json').write_text('[]\n',encoding='utf-8')
print(len(entries),'transcription blocks;',len(sections),'topics;',sum(map(len,slots.values())),'plates')

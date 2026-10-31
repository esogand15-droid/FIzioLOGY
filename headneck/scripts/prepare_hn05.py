"""Build topical session 5 content from its page-reconciled transcription.

The page transcription remains the source of truth for lecture wording. Figure
blocks retain the PDF page number and never substitute whole source pages.
"""
from __future__ import annotations
import io, json
from pathlib import Path
import pymupdf
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'علوم تشریح سر و گردن/جلسه 5 - گردن/جلسه_پنجم_علوم_تشریح_سر_و_گردن_مهر_1404.pdf'
NETTER=next((ROOT/'علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1').glob('Netter*'))
GRAY=ROOT/"علوم تشریح دستگاه اعصاب/user - Gray's Anatomy For Students, 3rd Edition-1001-1189.pdf"
DOC=pymupdf.open(SOURCE); INDEX=ROOT/'headneck/images/INDEX.json'
index=json.loads(INDEX.read_text(encoding='utf-8'))
index['assets']=[x for x in index['assets'] if not x.get('asset_id','').startswith('hn05_')]
# Each pair describes labels actually present in the corresponding source figure.
vertebra=[['جسم مهره','Vertebral body'],['زائده عرضی','Transverse process']]
atlas=[['قوس قدامی','Anterior arch'],['قوس خلفی','Posterior arch']]
axis=[['دنس','Dens'],['زائده خاری','Spinous process']]
fascia=[['فاسیای سطحی','Superficial fascia'],['فاسیای پیش‌مهره‌ای','Prevertebral fascia']]
neck=[['فک تحتانی','Mandible'],['ترقوه','Clavicle']]
labels={2:[[['مهره گردنی','Cervical vertebrae'],['مهره سینه‌ای','Thoracic vertebrae']],vertebra],4:[atlas],6:[axis],8:[axis],9:[vertebra,vertebra],10:[[ ['دنده گردنی','Cervical rib'],['شبکه بازویی','Brachial plexus'] ]],11:[[ ['اطلس','Atlas'],['استخوان پس‌سری','Occipital bone'] ],[['پرده قدامی','Anterior atlantooccipital membrane'],['پرده خلفی','Posterior atlantooccipital membrane']]],12:[[ ['مفصل میانی','Median atlantoaxial joint'],['دنس','Dens'] ]],13:[[ ['رباط عرضی اطلس','Transverse ligament of atlas'],['دنس','Dens'] ],[['رباط صلیبی','Cruciate ligament'],['رباط آلار','Alar ligament']]],14:[[ ['تکتوریال ممبرین','Tectorial membrane'],['رباط طولی خلفی','Posterior longitudinal ligament'] ]],15:[[ ['لیگامان فلاوا','Ligamenta flava'],['اطلس','Atlas'] ],[['رباط نوکال','Nuchal ligament'],['دیسک بین‌مهره‌ای','Intervertebral disk']]],16:[[ ['دیسک فتق‌یافته','Herniated disk'],['ریشه عصب','Nerve root'] ]],17:[[ ['اعصاب نخاعی','Spinal nerves'],['درماتوم','Dermatome'] ],[['دلتوئید','Deltoid'],['دوسر بازویی','Biceps brachii']]],18:[[ ['کلونوس مچ پا','Ankle clonus'],['علامت بابینسکی','Babinski sign'] ]],19:[neck],20:[[ ['زائده ماستوئید','Mastoid process'],['زائده خاری','Spinous process'] ]],21:[[ ['خطوط کرایسل','Kraissl’s lines'],['گردن','Neck'] ],[['ناحیه قدامی گردن','Anterior cervical region'],['ناحیه خلفی گردن','Posterior cervical region']]],22:[fascia],23:[[ ['پلاتیسما','Platysma'],['ترقوه','Clavicle'] ]],24:[[ ['پلاتیسما','Platysma'],['گردن','Neck'] ],[['عصب پس‌سری کوچک','Lesser occipital nerve'],['عصب عرضی گردن','Transverse cervical nerve']]],25:[[ ['عصب گوشی بزرگ','Great auricular nerve'],['عصب عرضی گردنی','Transverse cervical nerve'] ]],26:[[ ['عصب گوشی بزرگ','Great auricular nerve'],['ورید ژوگولار خارجی','External jugular vein'] ]],27:[[ ['ورید ژوگولار خارجی','External jugular vein'],['ورید ژوگولار داخلی','Internal jugular vein'] ]],28:[[ ['ورید ژوگولار قدامی','Anterior jugular vein'],['ورید زیرچانه‌ای','Submental vein'] ]],29:[[ ['ورید ژوگولار قدامی','Anterior jugular vein'],['قوس وریدی ژوگولار','Jugular venous arch'] ]],30:[fascia],31:[[ ['لایه احاطه‌کننده','Investing layer'],['غلاف کاروتید','Carotid sheath'] ]],32:[[ ['غده پاروتید','Parotid gland'],['عضله ماستر','Masseter muscle'] ]],33:[fascia],34:[[ ['فضای فوق‌جناغی','Suprasternal space'],['فاسیای پیش‌نایی','Pretracheal fascia'] ]],35:[fascia],36:[[ ['غلاف کاروتید','Carotid sheath'],['لایه پیش‌مهره‌ای','Prevertebral layer'] ],[['غلاف کاروتید','Carotid sheath'],['غده پاروتید','Parotid gland']]],37:[fascia,[['لایه احاطه‌کننده','Investing layer'],['لایه پیش‌نایی','Pretracheal layer']]],38:[fascia,[['فاسیای بوکوفارنژیال','Buccopharyngeal fascia'],['عضله بوکسیناتور','Buccinator muscle']]],39:[[ ['فاسیای بوکوفارنژیال','Buccopharyngeal fascia'],['فاسیای پیش‌مهره‌ای','Prevertebral fascia'] ],[['غلاف کاروتید','Carotid sheath'],['لایه پیش‌مهره‌ای','Prevertebral layer']]],40:[[ ['غلاف آگزیلاری','Axillary sheath'],['شبکه بازویی','Brachial plexus'] ],[['فضای رتروفارنژیال','Retropharyngeal space'],['فضای خطر','Danger space']]],42:[[ ['فضای رتروفارنژیال','Retropharyngeal space'],['فاسیای پیش‌مهره‌ای','Prevertebral fascia'] ],[['فضای پیش‌مهره‌ای','Prevertebral space'],['فضای خطر','Danger space']]],43:[[ ['استخوان لامی','Hyoid bone'],['عضله اوموهایوئید','Omohyoid'] ]],44:[[ ['شاخ بزرگ','Greater horn'],['جسم','Body'] ]],45:[[ ['فاسیای پیش‌نایی','Pretracheal fascia'],['فضای فوق‌جناغی','Suprasternal space'] ]]}
titles={2:['ستون مهره‌ای در سه نما','مهرهٔ چهارم گردنی'],4:['اطلس در دو نما'],6:['اکسیس در دو نما'],8:['اکسیس از پهلو'],9:['مهرهٔ ششم گردنی','مهرهٔ هفتم گردنی'],10:['دندهٔ گردنی'],11:['مفاصل جمجمه و مهره','پرده‌های اطلس و پس‌سری'],12:['مفاصل اطلس و اکسیس'],13:['رباط عرضی اطلس','رباط‌های عمقی اطلس و اکسیس'],14:['غشای تکتوریال'],15:['لیگامان فلاوا','رباط‌های ستون مهرهٔ گردنی'],16:['فتق دیسک گردنی'],17:['اعصاب نخاعی و درماتوم‌ها','یافته‌های ریشه‌های گردنی'],18:['یافته‌های میلوپاتی گردنی'],19:['نمای قدامی سر و گردن'],20:['نمای خلفی گردن'],21:['خطوط کشش پوست','ناحیه‌های گردنی'],22:['لایه‌های فاسیای گردن'],23:['عضلهٔ پلاتیسما'],24:['نمای سطحی گردن','اعصاب سطحی گردن'],25:['شاخه‌های سطحی شبکهٔ گردنی'],26:['اعصاب و ورید سطحی گردن'],27:['ورید ژوگولار خارجی'],28:['ورید ژوگولار قدامی'],29:['قوس وریدی ژوگولار'],30:['برش عرضی فاسیاهای گردن'],31:['لایه‌های عمقی فاسیا'],32:['فاسیای سطحی عمقی در نمای طرفی'],33:['لایه‌های فاسیا در برش عرضی'],34:['فضای فوق‌جناغی'],35:['فاسیای عضلات تحت‌لامی'],36:['غلاف کاروتید','غلاف کاروتید در نمای طرفی'],37:['فاسیای احشایی در برش عرضی','لایهٔ پیش‌نایی'],38:['فاسیای پیش‌مهره‌ای','فاسیای بوکوفارنژیال'],39:['فاسیای پیش‌مهره‌ای در نمای طرفی','امتداد فاسیای پیش‌مهره‌ای'],40:['انتشار عفونت به غلاف آگزیلاری','فضاهای گردنی در برش عرضی'],42:['فضای رتروفارنژیال','فضای پیش‌مهره‌ای'],43:['عضلات گردن و لامی'],44:['استخوان لامی'],45:['برش میانی فاسیاهای گردن']}
figures={}
for pg in sorted(titles):
 blocks=[b for b in DOC[pg-1].get_text('dict')['blocks'] if b['type']==1]
 count=2 if pg==2 else len(blocks)
 assert count==len(titles[pg])==len(labels[pg]),pg
 for i in range(count):
  b=blocks[i]; bbox=pymupdf.Rect(b['bbox'])
  name=f'hn05_lecture_p{pg:02}_{i+1}'; path=ROOT/f'headneck/images/{name}.jpeg'
  if pg==2:
   bbox=pymupdf.Rect((34,36,365,339) if i==0 else (34,375,339,631))
   pix=DOC[pg-1].get_pixmap(matrix=pymupdf.Matrix(2,2),clip=bbox,alpha=False)
   im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
  else:
   im=Image.open(io.BytesIO(b['image'])).convert('RGB')
   # Images can be non-uniformly scaled on the source page. Preserve their
   # displayed proportions, not the intrinsic pixel aspect ratio.
   displayed_height=max(1,round(im.width*bbox.height/bbox.width))
   if displayed_height != im.height:
    im=im.resize((im.width,displayed_height),Image.Resampling.LANCZOS)
  im.save(path,quality=95,optimize=True)
  rel=str(path.relative_to(ROOT));index['assets'].append({'asset_id':name,'book':'lecture','session':'hn05','source_file':str(SOURCE.relative_to(ROOT)),'page':pg,'bbox':[round(v,2) for v in bbox],'w':im.width,'h':im.height,'bytes':path.stat().st_size,'path':rel})
  figures.setdefault(pg,[]).append({'type':'plate','book':'lecture','asset':rel,'title':titles[pg][i], 'citation':f'جزوهٔ جلسهٔ ۵، ص {pg} از فایل PDF', 'src':f'جزوهٔ جلسهٔ ۵، صفحهٔ PDF {pg}', 'view':'تصویر جزوه','fa_text':'تصویر آموزشی جزوه در ارتباط با متن این مبحث.', 'labels':labels[pg][i], 'max_h':120, 'min_img_h':round(min(75,165*im.height/im.width)), 'fresh':False})
# Image-block order on page 38 is opposite its visual order.
figures[38].reverse()
# Independent references were visually reviewed. Clip only the figure regions.
refspec=[
 ('netter',NETTER,96,(40,65,580,365),'vertebrae','مهره‌های گردنی تیپیک','نتر، ویراست ۸، پلیت ۴۴، ص ۹۶ فایل PDF',vertebra,1),
 ('netter',NETTER,95,(45,60,580,292),'atlas_axis','اطلس و اکسیس','نتر، ویراست ۸، پلیت ۴۳، ص ۹۵ فایل PDF',atlas,2),
 ('netter',NETTER,99,(35,65,590,445),'ligaments','رباط‌های عمقی اتصال جمجمه و گردن','نتر، ویراست ۸، پلیت ۴۷، ص ۹۹ فایل PDF',[['رباط صلیبی','Cruciate ligament'],['رباط آلار','Alar ligament']],6),
 ('grays',GRAY,29,(75,455,545,650),'fascia','فاسیاهای گردن در برش عرضی','گری، ویراست ۳، شکل ۸.۱۵۸، ص چاپی ۱۰۰۱، ص ۲۹ فایل PDF',[['غلاف کاروتید','Carotid sheath'],['لایه پیش‌مهره‌ای','Prevertebral layer']],11),
 ('grays',GRAY,30,(90,510,550,720),'spaces','فاسیا و فضاهای گردن در برش میانی','گری، ویراست ۳، شکل ۸.۱۵۹، ص چاپی ۱۰۰۲، ص ۳۰ فایل PDF',[['فضای رتروفارنژیال','Retropharyngeal space'],['فضای پیش‌نایی','Pretracheal space']],13),
]
refs={}
captions={'vertebrae':'Cervical Vertebrae','atlas_axis':'Cervical Vertebrae: Atlas and Axis','ligaments':'Internal Craniocervical Ligaments','fascia':'Fascia of neck, transverse view','spaces':'Fascia of the neck, sagittal view'}
for book,src,page,box,slug,title,citation,labs,tid in refspec:
 doc=pymupdf.open(src);rect=pymupdf.Rect(box);pix=doc[page-1].get_pixmap(matrix=pymupdf.Matrix(2,2),clip=rect,alpha=False)
 im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);name=f'hn05_{book}_{slug}';path=ROOT/f'headneck/images/{name}.jpeg';im.save(path,quality=95,optimize=True);rel=str(path.relative_to(ROOT))
 index['assets'].append({'asset_id':name,'book':book,'session':'hn05','source_file':str(src.relative_to(ROOT)),'page':page,'bbox':list(box),'w':im.width,'h':im.height,'bytes':path.stat().st_size,'path':rel})
 refs.setdefault(tid,[]).append({'type':'plate','book':book,'asset':rel,'title':title,'citation':citation,'src':citation,'en_caption':captions[slug], 'view':'تصویر مرجع','fa_text':'تصویر مرجع برای مطالعهٔ ساختارهای همین مبحث.', 'labels':labs,'max_h':130,'min_img_h':round(min(75,165*im.height/im.width)),'fresh':False})
INDEX.write_text(json.dumps(index,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
trans=json.loads((ROOT/'headneck/content/hn05_transcription.json').read_text(encoding='utf-8'))
assert [x['pdf_page'] for x in trans['pages']]==list(range(2,46))
by_page={x['pdf_page']:x['blocks'] for x in trans['pages']}
sections=[
 (1,'مهره‌های تیپیک گردنی',1,4,'اجزای مهرهٔ گردنی نمونه'),
 (2,'اطلس و ویژگی‌های آن',4,5,'اطلس و تفاوت‌های مهرهٔ اول'),
 (3,'شکستگی اطلس و مهرهٔ اکسیس',6,8,'شکستگی جفرسون، دنس و هنگمن'),
 (4,'مهره‌های ششم و هفتم و دندهٔ گردنی',9,10,'مهره‌های C6 و C7 و دندهٔ گردنی'),
 (5,'مفاصل اطلس با جمجمه و اکسیس',11,12,'اتصالات و حرکت مفاصل فوقانی'),
 (6,'رباط‌ها و غشاهای گردنی',13,15,'رباط عرضی، آلار، تکتوریال و نوکال'),
 (7,'دیسک گردنی و تنگی کانال',16,18,'فتق دیسک، علائم ریشه‌ای و میلوپاتی'),
 (8,'حدود و نواحی گردن',18,22,'محدوده‌های گردن، پوست و تقسیمات'),
 (9,'فاسیای سطحی و اعصاب گردنی',23,26,'پلاتیسما و اعصاب سطحی گردن'),
 (10,'وریدهای سطحی گردن',27,29,'وریدهای ژوگولار خارجی و قدامی'),
 (11,'فاسیای عمقی و لایهٔ اینوستینگ',30,35,'لایه‌های فاسیا و اتصالات آن‌ها'),
 (12,'غلاف کاروتید و فاسیاهای عمقی',36,40,'فاسیاهای احشایی و پیش‌مهره‌ای'),
 (13,'فضاهای گردن و انتشار عفونت',41,43,'فضاهای کاروتید، رتروفارنژیال و خطر'),
 (14,'استخوان لامی و عضلات گردن',43,45,'استخوان هایوئید و اتصالات آن'),
]
outline=[];contents=[]
for n,title,first,last,gist in sections:
 tid=f'hn05-T{n:02}';pages=list(range(first,last+1));footer=f'جزوهٔ جلسهٔ ۵، صفحات PDF {first} تا {last}'
 outline.append({'topic_id':tid,'title':title,'pages':pages,'gist':gist,'prereq':'شناخت نماهای سر و گردن'})
 card={'type':'idcard','title':'شناسنامهٔ مبحث','kicker':'قبل از شروع این مبحث بخوانید','rows':[{'label':'جای این مبحث','text':gist},{'label':'هدف یادگیری','text':f'ساختارها و تصویرهای مبحث «{title}» را مرور کنید.'},{'label':'پیش‌نیاز','text':'شناخت نماهای سر و گردن'}],'footer':footer}
 body=[card]
 for pg in pages:
  if pg==1:continue
  entries=by_page[pg];plates=figures.get(pg,[])
  # Separate source pages that cross a genuine topic boundary.
  if pg==4:
   cut=next(i for i,b in enumerate(entries) if b['type']=='h3' and 'آتیپیک' in b['text'])
   entries,plates=(entries[:cut],[]) if n==1 else (entries[cut:],plates)
  if pg==18:
   cut=next(i for i,b in enumerate(entries) if b['type']=='h3' and b['text'].startswith('گردن:'))
   entries,plates=(entries[:cut],plates) if n==7 else (entries[cut:],[])
  if pg==43:
   cut=next(i for i,b in enumerate(entries) if b['type']=='h3' and b['text'].startswith('عضلات گردن'))
   entries,plates=(entries[:cut],[]) if n==13 else (entries[cut:],plates)
  # Keep each original educational image close to its page's subject text.
  positions=[max(1,round((j+1)*len(entries)/(len(plates)+1))) for j in range(len(plates))]
  if pg==4 and plates: positions=[len(entries)]  # atlas appears at the end of this page
  if pg==43 and plates: positions=[next(i for i,b in enumerate(entries,1) if b['type']=='h3' and 'عضلات گردن' in b['text'])]
  slots={position: [] for position in positions}
  for position,plate in zip(positions,plates): slots[position].append(plate)
  for i,b in enumerate(entries,1):
   b=dict(b)
   if b['type']=='p':b['src']=f'جزوهٔ جلسهٔ ۵، صفحهٔ PDF {pg}'
   body.append(b)
   if pg==9 and b['type']=='p' and 'تا 31 گردنی' in b['text']:
    body.append({'type':'callout','kind':'info','title':'یادداشت تحریری جدا از متن جزوه','text':'در عبارت بالا عدد 31 همان‌طور که در جزوه چاپ شده حفظ شده است؛ مقصود از آن نیاز به مقابله دارد.','src':'جزوهٔ جلسهٔ ۵، صفحهٔ PDF 9'})
   body.extend(slots.get(i,[]))
 body.extend(refs.get(n,[]))
 body.append({'type':'handoff','title':f'برگهٔ تحویل — مبحث {n}','kicker':'برای تکمیل جزوه','sources':footer,'checklist':['متن با صفحه‌های منبع مقابله شود.','شکل و برچسب‌ها با منبع کنترل شوند.','توضیح تکمیلی از متن جزوه تفکیک شود.','صفحه‌بندی نهایی بررسی شود.','موارد مبهم برای بازبینی ثبت شوند.'],'open':'برای تحویل، متن و شکل‌ها با ارجاعات منبع کنترل شوند.','question':gist})
 contents.append({'topic_id':tid,'blocks':body})
content=ROOT/'headneck/content';(content/'outline/hn05_topics.json').write_text(json.dumps({'session':'hn05','title':'گردن','pages':[1,45],'topics':outline},ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
(content/'hn05_a.json').write_text(json.dumps(contents,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
(content/'hn05_b.json').write_text('[]\n',encoding='utf-8')
print('Prepared',len(sections),'topics,',sum(len(v) for v in figures.values()),'lecture plates and',len(refspec),'reference plates')

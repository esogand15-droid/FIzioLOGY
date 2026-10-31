"""Update the 100-page edition's complete topic/overlay structure for writers.

Scientific review was explicitly waived by the user. 'Final' here is an
editorial deliverable, not scientific clearance. Provenance and build QA belong
in the companion manifest, never in the reader-facing book. Baselines immutable.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'render'),str(Path(__file__).parent)]
import pymupdf
import build_hn01_updated_review as R
import hn01_writer_copy as W
import writer_handoff as WH
import writer_shell as SHELL
K,H=R.K,R.H
OUT=ROOT/'.cache/hn01_writer_original_layout'
BAD=re.compile(r'IMG[-ـ]?\d+|SRC[-ـ]?\d+|hn\d\d[-–]T\d+|C-\d{3}|JSON|jason|BLOCKED|DOCUMENTED|NOT_YET|AUTHORED|INTEGRATED|PENDING|Arena|غیرنهایی|پیش‌نویس|رونویسی در حال مقابله|دروازهٔ نهایی',re.I)
DIGITS=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')
TITLE='جزوهٔ مادر آناتومی سر و گردن — جلسهٔ ۱'
def dump(path,obj):path.parent.mkdir(exist_ok=True,parents=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def clean(s):
 s=str(s)
 def link(m):
  ident=m.group();n=int(ident[2:4]);tid=ident
  return ('مبحث «'+TITLES[tid]+'»' if tid in TITLES and n==1 else 'جلسهٔ '+K.fa_digits(str(n))+('، مبحث «'+TITLES[tid]+'»' if tid in TITLES else ''))
 s=re.sub(r'hn\d\d-T\d+',link,s)
 s=s.replace('hn06','جلسهٔ۶').replace(' تا T10',' تا مبحث استخوان بینی').replace(' تا T15',' تا مبحث سینوس فک فوقانی')
 for key,value in {'SRC-649':'جزوهٔ درس، جلسهٔ۱','SRC-648':'نتر، ویراست۸','SRC-632':'گری، ویراست۳، بخش سر و گردن','SRC-628':'گری، ویراست۳، بخش سر و گردن'}.items():s=s.replace(key,value)
 s=re.sub(r'\s*[—·]\s*رونویسی در حال مقابله','',s)
 s=s.replace('PDF page','صفحهٔ فایل').replace('PDF','صفحهٔ فایل').replace('printed','چاپی').replace('Plate','پلیت')
 return s
TITLES={t['topic_id']:t['title'] for t in R.load('topic_matrix.json')['topics']}
LABELS={**R.LABELS,'boundary_of_topic':'تمایز مفهومی','observable_anchor':'راهنمای شکل','numerical_caveat':'نسبت اجزای کام','assessment_importance':'کاربرد در پرسش','link_forward':'پیوند با مباحث دیگر'}

def reference(r):
 label=r.get('source_label');parts=[{'SRC-649':'جزوهٔ درس، جلسهٔ۱','SRC-648':'نتر، اطلس آناتومی انسان، ویراست۸','SRC-632':'گری، آناتومی برای دانشجویان، ویراست۳، سر و گردن','SRC-628':'گری، آناتومی برای دانشجویان، ویراست۳، سر و گردن'}.get(label,'جزوهٔ درس، جلسهٔ۱')]
 for key,lab in [('plate','پلیت'),('printed_page','صفحهٔ چاپی'),('pdf_page','صفحهٔ فایل'),('figure','شکل'),('table','جدول')]:
  if r.get(key) is not None:parts.append(lab+' '+K.fa_digits(str(r[key])))
 if r.get('pdf_pages'):parts.append('صفحه‌های فایل '+ '،'.join(K.fa_digits(str(n)) for n in r['pdf_pages']))
 if label in ['SRC-632','SRC-628']:parts.append('فایل بخش '+('۸۰۱–۱۰۰۰' if label=='SRC-632' else '۱۰۰۱–۱۱۸۹'))
 return '؛ '.join(parts)

def compact_references(refs):
 groups={}
 for r in refs:
  label=r.get('source_label')
  if label=='SRC-649':
   pages=r.get('pdf_pages') or ([r['pdf_page']] if r.get('pdf_page') else [])
   groups.setdefault('جزوهٔ درس، جلسهٔ ۱',[]).extend('فایل '+K.fa_digits(str(n)) for n in pages)
  elif label=='SRC-648':
   groups.setdefault('نتر، ویراست ۸',[]).append(('پلیت '+K.fa_digits(str(r['plate']))+'، ' if r.get('plate') else '')+'فایل '+K.fa_digits(str(r.get('pdf_page',''))))
  elif label in ('SRC-632','SRC-628'):
   groups.setdefault('گری، ویراست ۳، سر و گردن',[]).append(('چاپی '+K.fa_digits(str(r['printed_page']))+'، ' if r.get('printed_page') else '')+'فایل '+K.fa_digits(str(r.get('pdf_page','')))+' (بخش '+('۸۰۱–۱۰۰۰' if label=='SRC-632' else '۱۰۰۱–۱۱۸۹')+')')
 return ' ؛ '.join(name+': '+ '، '.join(dict.fromkeys(entries)) for name,entries in groups.items())

def reader_additions():
 a=copy.deepcopy(R.load('educational_additions.json')['topics'])
 for i,(tid,b) in enumerate(a.items(),1):
  card=b['scientific_card'];card['boundary_of_topic']=W.BOUNDARIES[i]
  card.pop('assessment_importance',None)
  # These fields contained editorial audit instructions, not anatomy.
  if i==17:
   card['title']='مرور جلسه؛ از نام ساختار تا رابطهٔ فضایی'
   card['precise_definition']='مرور پایانی شامل شمار استخوان‌ها، لامی، پیشانی، بینی، مکسلا، کام و سینوس است. در هر بخش تعریف، محل، تمایز و تصویر را به هم پیوند دهید.'
   card['function']='بازیابی فعال نام‌ها و روابط و استفاده از متن و تصویر برای پاسخ‌دادن به پرسش‌ها.'
   b['key_points'][1]='هر مقایسه را با دو ساختار مشخص و یک رابطهٔ فضایی بنویسید.'
   b['common_errors']=[dict(error='خواندن خلاصه بدون بازیابی نام ساختارها',correction='ابتدا بدون نگاه‌کردن پاسخ دهید و سپس نام و محل را روی شکل پیدا کنید.'),dict(error='به‌کاربردن یک نام برای دو مفهوم نزدیک',correction='قرارداد شمار استخوان‌ها، تشکیل و رویش دندان و مقصد دو دهانه را جدا بیان کنید.')]
   b['comparison']['rows'][4][2]='تمایز تشکیل، دندان نهفته و رویش تاج'
   b['summary']='مرور را با متن کامل درس، بازیابی فعال و دو نمای قدامی و برش پیشانی انجام دهید؛ نام ساختار، محل و تفاوت آن با ساختار مشابه باید در پاسخ روشن باشد.'
  if i==14:
   card['numerical_caveat']='در متن درس سهم مکسلا دو سوم قدامی است. گری، ویراست۳، در صفحهٔ چاپی۱۰۸۸ دو سوم و در صفحهٔ چاپی۱۱۰۵ سه چهارم می‌گوید؛ در هر دو شرح، مکسلا قدامی و استخوان کامی خلفی است.'
   b['common_errors'][0]['correction']='در همین ویراست گری، عبارت دو سوم در شرح مکسلا و سه چهارم در شرح کام سخت آمده است؛ عدد را همراه بخش و صفحهٔ مرجع بنویسید.'
  if i==2:
   b['common_errors'][1]['correction']='کالواریا را از قاعدهٔ جمجمه جدا در نظر بگیرید؛ ضخامت و ساختمان آن‌ها یکسان فرض نمی‌شود.'
   b['comparison']['columns'][2]='نمای مناسب'
  if i==5:b['common_errors'][1]['correction']=W.BOUNDARIES[5]
  if i==10:
   card['learning_objective']='چهار کنار استخوان بینی و همسایه‌های آن را نام ببرید و ناسیون را از درزهای مجاور تشخیص دهید.'
   b['key_points'][1]='برای دیدن سطح داخلی از نمای داخلی استخوان بینی استفاده کنید.'
   b['comparison']['columns'][2]='نمای مناسب'
  if i==11:b['key_points'][2]='توبروزیته برجستگی بخش خلفی مکسلا در نزدیکی سطح اینفراتمپورال است.'
  if i==12:
   b['plain_explanation']='زائده‌های پیشانی، گونه‌ای و آلوئولار به ترتیب به بالا، خارج و پایین می‌روند. زائدهٔ کامی به داخل امتداد دارد و در ساخت کام مشارکت می‌کند؛ نمای داخلی یا تحتانی آن را بهتر نشان می‌دهد. ستیغ اشکی قدامی نشانه‌ای روی زائدهٔ پیشانی است، نه زائدهٔ پنجم.'
  if i==14:b['comparison']['rows'][1][2]='عبارت دو سوم در شرح مکسلا'
  if i==15:b['common_errors'][1]['correction']='موقعیت بالای دهانه تنها یکی از ویژگی‌های سینوس است و به تنهایی همهٔ عوامل تخلیه و بیماری را توضیح نمی‌دهد.'
  if i==16:
   b['common_errors'][1]['correction']='در رادیوگرافی، استخوان‌ها و دندان‌ها را با توجه به همپوشانی ساختارها بخوانید.'
   for n in b['diagram']['nodes']:
    if 'نیازمند شاهد' in n['text']:n['text']='نیاز به نمای درون استخوان'
  if i==17:
   b['plain_explanation']='ابتدا پاسخ کوتاه بدهید و سپس ساختار را روی تصویر نشان دهید. برای نمونه، شاخک تحتانی مستقل را در نمای قدامی کنار شاخک میانی اتموئید پیدا کنید و مقصد دو مسیر سینوسی و اشکی را جدا بنویسید.'
   b['comparison']['columns'][2]='تمایز و تصویر'
   b['diagram']['edge_labels']['ans:view']='مطابقت با تصویر'
  if i==6:b['key_points'][2]='راست و چپ در نمای روبه‌رو نسبت به خود جمجمه تعیین می‌شوند، نه نسبت به دست راست و چپ بیننده.'
  if i==7:
   card['distinct_landmarks'][1]='در جمجمهٔ نوزاد، درز پیشانی یا متوپیک در خط وسطِ پیشانی دیده می‌شود.'
   b['common_errors'][0]['correction']='درز طبیعی یا باقی‌ماندهٔ آن را از شکستگی تفکیک کنید؛ صرف وجود یک خط، نام آن را تعیین نمی‌کند.'
   b['common_errors'][1]['correction']='محل میانیِ گلابلا را از خود قوس‌های ابرویی جدا کنید؛ توصیف متن درس و گری در کادر این مبحث آمده است.'
  if i==8:b['common_errors'][1]['correction']='شماره‌های عکس پیشانی را با کلید همان عکس و جدول راهنمای آن به نام ساختار وصل کنید.'
  if i==10:b['comparison']['rows'][5][2]='برای مطالعهٔ این سطح از نمای داخلی استفاده کنید.'
  if i==12:card['domain']='زوائد مکسلا؛ ارتباط جهت زائده و نمای مناسب برای دیدن آن'
  if i==16:
   card['distinct_landmarks'][0]='در اصل جزوه، یک نمای طرفی و دو نمای قدامی با اندازه‌های متفاوت کنار هم قرار گرفته‌اند؛ دو نمای قدامی برای مقایسهٔ هم‌جهت مناسب‌اند.'
   b['common_errors'][0]['correction']='تاج روییده در دهان را از دندان نهفته درون استخوان جدا کنید؛ عکس سطح بسته، نمای درون استخوان نیست.'
   b['exam_claims'][0]['text']='در شکل دندان‌ها، «نهفته»، «روییده» و «در حال تشکیل» چه تفاوتی دارند؟'
   b['exam_claims'][0]['answer']='نهفته در استخوان است؛ روییده تاجش در دهان دیده می‌شود؛ تشکیل به فرایند پدیدآمدن اجزای دندان اشاره دارد. این سه اصطلاح را به جای هم به کار نبرید.'
 return a

class WriterBook(R.ReviewBook):
 def source_line(self,text):super().source_line(clean(text))
 def h3(self,text,keep_with=46):
  lines=self.wrap(clean(text),'VazirB',11.4,K.CONTENT_W-18)
  # Match the inherited heading's actual height plus the following block.
  super().h3(clean(text),keep_with=keep_with)
 def _furniture(self):
  # The running title stays the topic, not an internal build heading.
  super()._furniture()

def original_blocks():
 base,assets,outline=R.inputs()
 p=ROOT/'.cache/master_01_06/historical/headneck/content/hn01_update.json'
 hist={r['file']:r for r in R.load('historical_sources.json')['files']}
 if R.sha(p)!=hist['headneck/content/hn01_update.json']['sha256']:raise ValueError('Overlay changed')
 overlay=json.loads(p.read_text())['topics'];out={}
 for t in base:
  tid=t['topic_id'];spec=overlay[tid];out[tid]=[]
  for pos,b in enumerate(t['blocks']):
   x=copy.deepcopy(b)
   if pos==0:x['rows']+=copy.deepcopy(spec['card_rows'])
   # Retain source paragraph/list strings, including original spelling.
   for k in ['src','citation','footer','kicker','title']:
    if k in x:x[k]=clean(x[k])
   x['_origin']=f'base:{pos}';out[tid].append(x)
   for j,e in enumerate(spec['after'].get(str(pos),[])):
    z=copy.deepcopy(e);z['_origin']=f'old_overlay:{pos}:{j}';out[tid].append(z)
 return base,out,assets,outline

def prepare_plan(add):
 base,content,assets,outline=original_blocks()
 allplates={Path(b['asset']).name:copy.deepcopy(b) for rows in content.values() for b in rows if b['type']=='plate'}
 refs={(r['source_label'],r['pdf_page']):r for r in R.load('reference_page_observations.json')}
 stats=dict(base_blocks=187,old_overlay_blocks=sum(len(v) for t in json.loads((ROOT/'.cache/master_01_06/historical/headneck/content/hn01_update.json').read_text())['topics'].values() for v in t['after'].values()),source_text_sha256={},new_image_instruction_resolution=[],topics={},figures=[])
 plans={}
 for idx,t in enumerate(outline['topics'],1):
  tid=t['topic_id'];rows=content[tid];known={Path(b['asset']).name for b in rows if b['type']=='plate'};extra=[];guide={}
  raw=R.load('educational_additions.json')['topics'][tid]
  for q in raw['image_instructions']:
   ident=q.get('image_id');resolved=[]
   for name in W.IMAGE_ASSETS.get(ident,[]):
    if name not in known:extra.append(copy.deepcopy(allplates[name]));extra[-1]['_origin']='new_teaching_reuse';known.add(name)
    resolved.append(name)
    if ident in W.IMAGE_GUIDES:guide.setdefault(name,[]).append(W.IMAGE_GUIDES[ident])
   if ident:
    # Review cards on pp20–21 are already preserved as typed source blocks.
    stats['new_image_instruction_resolution'].append(dict(topic=tid,image_id=ident,figures=resolved,typed_review_card=not resolved))
  for label,pageno,plate in R.EXTRA.get(idx,[]):
   r=refs[(label,pageno)];p=ROOT/r['render']
   if R.sha(p)!=r['render_sha256']:raise ValueError('Reference render changed')
   # Preserve the original edition's frames. A complete atlas plate is a
   # complementary view, not an unlabelled internal image-code instruction.
   extra.append(dict(type='plate',book='netter',asset=str(p),title='نمای تکمیلی — '+{30:'سطح خارجی و داخلی سقف جمجمه',32:'سه فوسای قاعدهٔ داخلی جمجمه',25:'جمجمه از روبه‌رو و استخوان‌های اربیت',27:'نمای طرفی و نمای عمقی زیرگیجگاهی',111:'مسیر اشک و ارتباط با حفرهٔ بینی',29:'برش میانی جمجمه و دیوارهٔ بینی',61:'دیوارهٔ جانبی بینی و دهانه‌ها',62:'اجزای استخوانی دیوارهٔ جانبی بینی',40:'دندان‌های نهفته، روییده و قوس‌های دندانی',26:'دو نمای رادیوگرافی جمجمه'}[plate],citation=reference(dict(source_label=label,pdf_page=pageno,plate=plate)),en_caption='',fa_text='',labels=[],max_h=178,min_img_h=125,_origin='new_reference'))
  for r in rows:
   if r['type'] in ['p','ul','ol']:
    text=r.get('text',r.get('items'));stats['source_text_sha256'][tid+':'+r['_origin']]=hashlib.sha256(json.dumps(text,ensure_ascii=False).encode()).hexdigest()
  plans[tid]=dict(rows=rows,extra=extra,guide=guide)
 return plans,assets,outline,stats

def cover(book):
 c=book.c
 for text,size,y,color in [('HumsYar · جزوهٔ مادر آناتومی',11,.86,K.TEAL_L),('آناتومی سر و گردن',29,.64,K.CARD),('جلسهٔ ۱',27,.565,K.CARD),('جمجمه، پیشانی، بینی و فک فوقانی',14,.475,K.TEAL_L),('نسخهٔ نهاییِ جزوه‌نویسی',14,.365,K.TEAL_L),('متن درس · تصاویر جزوه و اطلس · جدول · نکتهٔ تستی · راهنمای نویسنده',10,.30,K.CARD),('بر پایهٔ جزوهٔ درس، نتر و گری',10,.255,K.TEAL_L)]:
  K.draw_shaped(c,K.A4W/2,K.A4H*y,K.shape(text),'VazirB' if size>13 else 'Vazir',size,color,align='center')

def graph(book,b,layout):
 # Reuse the audited geometry; supply reader-facing references and labels.
 x=copy.deepcopy(b);x['diagram']['reference']=compact_references(b['reference_links'])
 for node in x['diagram']['nodes']:node['text']=clean(node['text'])
 x['diagram']['title']=clean(x['diagram']['title']);x['diagram']['reading_task']=clean(x['diagram']['reading_task'])
 if 'مرور' in x['diagram']['title']:
  x['diagram']['title']='چرخهٔ مرور با متن و تصویر'
  x['diagram']['reading_task']='یک ساختار را انتخاب کنید؛ نام کامل، نمای مناسب، رابطهٔ فضایی و تفاوت آن با ساختار مشابه را بگویید و سپس پاسخ را با متن و شکل مقایسه کنید.'
  for n in x['diagram']['nodes']:
   if 'حدود شاهد' in n['text']:n['text']='مقایسهٔ پاسخ با متن و تصویر'
 R.draw_graph(book,x,layout,force_page=False)

def build(path,toc=None):
 add=reader_additions();plans,assets,outline,stats=prepare_plan(add)
 book=WriterBook(path,TITLE,footer='HumsYar · جزوهٔ مادر سر و گردن · جلسهٔ ۱',subject='نسخهٔ نهاییِ جزوه‌نویسی؛ جمجمه، پیشانی، بینی و فک فوقانی')
 book.measure_idcard=True;book.keep_parenthesized_latin=True;book.block_trace=[];book.trace_topic='';book.surface=[]
 SHELL.opening(book,1,outline,toc)
 book.h1('از نما تا استخوان',anchor='chapter',kicker='جلسهٔ اول')
 book.para(H.HN_SESSIONS['hn01']['outcome']);geometry=R.layouts(book,add)
 byasset={Path(k).name:v for k,v in assets.items()};cfg=H.HN_SESSIONS['hn01']
 for i,t in enumerate(outline['topics'],1):
  tid=t['topic_id'];b=add[tid];plan=plans[tid];source=compact_references(b['reference_links'])
  book.trace_topic=tid
  card=copy.deepcopy(plan['rows'][0]);rows=card['rows']
  card_h=book.card_height(rows,footer=clean(card.get('footer','')))
  H.topic_head(book,t,i,len(outline['topics']),after=card_h+35)
  stats['topics'][tid]=dict(page=book.page,title=t['title'])
  book.label_card('شناسنامهٔ مبحث',rows,kicker=clean(card.get('kicker','')),footer=clean(card.get('footer','')))
  figure_no=0;handoff=None
  def emit_figure(raw):
   nonlocal figure_no
   q=copy.deepcopy(raw);name=Path(q['asset']).name;figure_no+=1;title=q['title']
   q['title']='شکل '+K.fa_digits(str(i)+'–'+str(figure_no))+' — '+clean(title)
   if not Path(q['asset']).is_absolute():
    p=ROOT/byasset[name]['workspace_file']
    if R.sha(p)!=byasset[name]['sha256']:raise ValueError('Changed historical figure')
    q['asset']=str(p)
   for key in ['citation','src','fa_text','en_caption','view']:q[key]=clean(q.get(key,''))
   if name=='hn01_lec_p14_photo.jpeg':q['title']='شکل '+K.fa_digits(str(i)+'–'+str(figure_no))+' — نمونهٔ استخوانی از نمای طرفی/خلفی';q['fa_text']=W.IMAGE_GUIDES['IMG-009366']
   for meta in ['_origin']:q.pop(meta,None)
   before=book.page;H.render_blocks(book,[q],cfg)
   stat=dict(topic=tid,number=f'{i}–{figure_no}',title=title,page=book.page,asset=raw['asset'],sha256=R.sha(Path(q['asset'])),citation=q['citation']);stats['figures'].append(stat)
   tips=list(dict.fromkeys(plan['guide'].get(name,[])))
   for tip in tips:book.callout(tip,kind='info',title='راهنمای خواندن همین شکل')
   if name=='hn01_lec_p10_orbital.jpeg':
    H.emit_table(book,['شمارهٔ عکس','نام انگلیسی','نام فارسی'],W.KEY_FRONTAL,caption='کلید عکس استخوان پیشانی؛ مطابق راهنمای شکل جزوه',size=8.5)
   if name=='hn01_lec_p14_key.jpeg':
    H.emit_table(book,['حرف در عکس','نام انگلیسی','نام فارسی'],W.KEY_MAXILLA,caption='راهنمای اختصارات نمونهٔ مکسلا و استخوان بینی',size=8.5)
  for raw in plan['rows'][1:]:
   if raw['type']=='handoff':handoff=raw;continue
   if raw['type']=='plate':emit_figure(raw);continue
   q=copy.deepcopy(raw);origin=q.pop('_origin')
   for key in ['src','citation','title','footer','kicker']:
    if key in q:q[key]=clean(q[key])
   H.render_blocks(book,[q],cfg)
   if origin.startswith('base:'):
    pos=int(origin.split(':')[1])
    if (i,pos) in W.NOTES:
     title,text=W.NOTES[(i,pos)];book.callout(text,kind='info',title=title);book.source_line(source)
  for extra in plan['extra']:emit_figure(extra)
  book.h3('شرح و پیوند مفهومی');book.para(clean(b['plain_explanation']));book.source_line(source)
  book.h3('توضیح تکمیلی مبحث')
  for key,val in b['scientific_card'].items():
   if key in ['title','link_forward']:continue
   book.para(LABELS.get(key,key)+' — '+clean(R.flat(val)))
  book.source_line(source)
  book.h3('نکته‌های تستی و تمایزهای کلیدی');book.bullets([clean(x) for x in b['key_points']]);book.source_line(source)
  book.h3('روابط فضایی');book.bullets([clean(x) for x in b['spatial_relations']]);book.source_line(source)
  columns=[clean(x) for x in b['comparison']['columns']];table_rows=[[clean(x) for x in row] for row in b['comparison']['rows']]
  table_h=book.table_needs(columns,table_rows,None,'مقایسهٔ مفاهیم این مبحث',source,8.6)[3]
  book.h3('جدول مقایسه',keep_with=min(table_h+12,book.usable_height()-80))
  H.emit_table(book,columns,table_rows,caption='مقایسهٔ مفاهیم این مبحث',src=source,size=8.6)
  book.h3('اشتباه رایج و پاسخ درست')
  for e in b['common_errors']:
   book.callout('برداشت نادرست: '+clean(e['error'])+'\nتمایز درست: '+clean(e['correction']),kind='key',title='نکتهٔ مقایسه‌ای');book.source_line(source)
  book.h3('پرسش تستی و پاسخ')
  for q in b.get('exam_claims',[]):book.para(clean(q['text']));book.callout(clean(q.get('answer','')),title='پاسخ')
  book.h3('جمع‌بندی مبحث');book.para(clean(b['summary']))
  book.h3('راهنمای نگارش برای جزوه‌نویس');book.numbered(W.GUIDES[i])
  if b['scientific_card'].get('link_forward'):
   book.h3('پیوند با ادامهٔ درس');book.bullets([clean(x) for x in b['scientific_card']['link_forward']])
  stats['topics'][tid]['graph_page']=book.page;graph(book,b,geometry[tid])
  if handoff:
   book.note_box(28,title='یادداشت جزوه‌نویس')
   WH.emit(book,1,i,card,handoff,W,clean)
 book.new_page();book.h1('جمع‌بندی، چک‌لیست و برگهٔ تحویل',anchor='hn-summary',kicker='پایان جلسه')
 book.para('هر ردیف یک مبحث است. اگر می‌توانید نکتهٔ آن را بدون نگاه به متن توضیح دهید، مربع کنار آن را علامت بزنید؛ سپس برگهٔ تحویل هر مبحث را تکمیل کنید. برای تحویل، متن درس، عنوان و منبع شکل‌ها و نام‌های فارسی و انگلیسی را مرور کنید.')
 rows=[]
 for i,t in enumerate(outline['topics'],1):
  rows.append(['مبحث '+K.fa_digits(str(i))+' — '+t['title'],(t.get('gist') or t['title']).rstrip(' .')+'؟','☐'])
 H.emit_table(book,['چک‌لیست خودآزمایی','می‌توانم این را توضیح دهم؟','☐'],rows,widths=[K.CONTENT_W*.30,K.CONTENT_W*.58,K.CONTENT_W*.12],caption='چک‌لیست خودآزمایی جلسهٔ ۱',size=8.5)
 if book.missing_assets:raise ValueError(book.missing_assets)
 SHELL.next_section(book,1);SHELL.back(book,1)
 book.save();stats['pages']=book.page;return book.heading_pages,stats

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=OUT/'HumsYar_HeadNeck_Jalase1_FINAL.pdf');args=p.parse_args();args.out.parent.mkdir(exist_ok=True,parents=True)
 first,_=build(args.out);second,stats=build(args.out,first)
 if first!=second:raise ValueError('TOC not stable')
 H.drop_trailing_blank_page(args.out)
 qa=dict(outside_spans=[],empty_pages=[],leaks=[],body_near_footer=[])
 with pymupdf.open(args.out) as doc:
  stats['pages']=len(doc)
  for n,page in enumerate(doc,1):
   text=unicodedata.normalize('NFKC',page.get_text());hits=BAD.findall(text)
   if hits:qa['leaks'].append(dict(page=n,hits=hits))
   if not text.strip() and not page.get_images():qa['empty_pages'].append(n)
   for block in page.get_text('dict',clip=pymupdf.INFINITE_RECT())['blocks']:
    for line in block.get('lines',[]):
     for span in line['spans']:
      x0,y0,x1,y1=span['bbox']
      if x0<-.5 or y0<-.5 or x1>page.rect.width+.5 or y1>page.rect.height+.5:qa['outside_spans'].append(dict(page=n,text=span['text']))
      if n>1 and span['size']>=8 and y1>789 and y0<795:qa['body_near_footer'].append(dict(page=n,text=span['text']))
   page.get_pixmap(matrix=pymupdf.Matrix(1.25,1.25),alpha=False).save(str(args.out.parent/f'page-{n:03}.jpg'),jpg_quality=88)
  stats['bookmarks']=doc.get_toc()
 stats.update(file=str(args.out.relative_to(ROOT)),sha256=R.sha(args.out),bytes=args.out.stat().st_size,qa=qa,editorial_status='FINAL_FOR_NOTE_WRITERS',scientific_review_requested=False,scientific_clearance_claimed=False,master_final_gate_overridden=False,all_pages_rasterized=True,all_pages_visually_read=False)
 dump(args.out.parent/'manifest.json',stats)
 print(json.dumps(dict(pages=stats['pages'],figures=len(stats['figures']),sha256=stats['sha256'],qa=qa),ensure_ascii=False,indent=2))
 if any(qa.values()):raise SystemExit('Fix layout/leaks before delivery; see manifest')
if __name__=='__main__':main()

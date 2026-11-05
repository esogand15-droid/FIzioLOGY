"""Build session 8 writer booklet from the typed lecture and locally inspected atlases."""
from __future__ import annotations
import argparse,hashlib,json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'render'),str(Path(__file__).parent)]
import pymupdf
import build_headneck as H
import build_hn01_updated_review as R
import writer_shell as SHELL
import hn08_writer_copy as W
K=H.K
OUT=ROOT/'.cache/hn08_writer_update'
BAD=re.compile(r'IMG[-ـ]?\d+|SRC[-ـ]?\d+|hn\d\d[-–]T\d+|JSON|BLOCKED|NOT_YET|PENDING|INTEGRATED|غیرنهایی|پیش‌نویس|هوش مصنوعی',re.I)

class Book(R.ReviewBook):
 def source_line(self,s):super().source_line(str(s).replace('PDF','فایل'))

def source_pages():
 p=ROOT/'headneck/content/session08';one=(p/'source_page_01_transcription.txt').read_text().split('\n',1)[1].strip()
 pages={1:one}
 for filename in ['02-05.txt','06-09.txt','10-12.txt']:
  s=(p/filename).read_text()
  for header,body in re.findall(r'@@ صفحه ([۰-۹0-9]+)[^\n]*\n(.*?)(?=\n@@ صفحه |\Z)',s,re.S):
   n=int(header.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')))
   pages[n]=body.strip()
 assert sorted(pages)==list(range(1,13))
 return pages

# Captions are reading instructions, not claims that unreadable printed labels exist.
CAPTIONS={
1:['مسیرهای کاروتید و ساب‌کلاوین را در نمای روبه‌رو پیدا کنید.','منشأ سمت راست و چپ را نسبت به قوس آئورت مقایسه کنید.','کاروتید مشترک و شاخه‌های خارجی را در نمای شماتیک دنبال کنید.'],
2:['کاروتید مشترک، ورید داخلی و ساب‌کلاوین را در نمای گردن شناسایی کنید.','کاروتید داخلی و خارجی را نسبت به فک و تیروئید دنبال کنید.','سینوس و جسم کاروتید را در دو نمای کنار هم از هم جدا کنید.'],
3:['کاروتید داخلی را از گردن به سینوس کاورنوس و شاخه‌های مغزی دنبال کنید.'],
4:['کاروتید خارجی و داخلی را در نمای طرفی از هم جدا کنید.','در شماتیک، شاخه‌های کاروتید خارجی را از تنهٔ مشترک دنبال کنید.'],
5:['کاروتید خارجی و شاخه‌های چهره و غده را در نمای طرفی دنبال کنید.','رابطهٔ شریان زاویه‌ای و شبکهٔ چشم را در شماتیک بررسی کنید.','نمای بالا و پایین را برای تیروئیدی فوقانی، تحتانی و ارتباط آن‌ها مقایسه کنید.'],
6:['شاخه‌های فاسیال و ارتباط آن با کاروتید خارجی را در شکل پیدا کنید.','شریان زبانی را نسبت به هایوگلوس و زبان در نمای طرفی دنبال کنید.','فاسیال و شاخه‌های لبی و زاویه‌ای را در صورت دنبال کنید.'],
7:['پس‌سری و بطن خلفی دیگاستریک را در تصویر پیدا کنید.','گوشی خلفی و مجاورت دیگاستریک را در نمای دوم دنبال کنید.'],
8:['دو نمای تمپورال سطحی و شاخه‌های پیشانی، آهیانه‌ای و عرضی صورت را مقایسه کنید.'],
9:['سه بخش ساب‌کلاوین را نسبت به اسکالن قدامی دنبال کنید.','در نمای ریشهٔ گردن، ورتبرال و شاخه‌های ساب‌کلاوین را پیدا کنید.','چهار قسمت ورتبرال را از مبدأ تا بازیلار در شکل دنبال کنید.'],
10:['توراسیک داخلی را در کنار جناغ تا شاخه‌های انتهایی دنبال کنید.','در نمای دیگر توراسیک داخلی، پریکاردیوفرنیک و شاخه‌های انتهایی را مقایسه کنید.','تیروئیدی تحتانی و عصب راجعه را در ناحیهٔ مشخص‌شده پی بگیرید.'],
11:['کاستوسرویکال و شاخه‌های عمقی گردن و بین‌دنده‌ای فوقانی را بیابید.','دورسال اسکاپولار و ساختارهای اطراف ساب‌کلاوین را دنبال کنید.'],
12:['دو نمودار دندهٔ گردنی و مسیر ورتبرال در انسداد ساب‌کلاوین را جدا بخوانید.','وریدهای داخلی، خارجی و قدامی را در نمای روبه‌رو از هم تفکیک کنید.'],
13:['دو نمای وریدی را کنار هم بخوانید؛ سینوس سیگموئید و ژوگولار داخلی را دنبال کنید.']}
REFS={1:[('gray_fig8165','گری، بخش ۱۰۰۱–۱۱۸۹، صفحهٔ فایل ۳۸، چاپی ۱۰۱۰، شکل ۸.۱۶۵','مبدأ کاروتیدهای مشترک و ساب‌کلاوین‌ها را با محل اتصال وریدها مقایسه کنید.')],2:[('gray_fig8167','گری، بخش ۱۰۰۱–۱۱۸۹، صفحهٔ فایل ۴۰، چاپی ۱۰۱۲، شکل ۸.۱۶۷','دوشاخگی و سینوس را در کنار شاخه‌های کاروتید پیدا کنید.'),('netter_plate58','نتر، پلیت ۵۸، صفحهٔ فایل ۱۱۰','نمای طرفی بالا و طرح پایین را برای شاخه‌ها و مجاورات مقایسه کنید.')],3:[('netter_plate165','نتر، پلیت ۱۶۵، صفحهٔ فایل ۲۱۷','افتالمیک، کاروتید داخلی و شاخه‌های مغزی را در شماتیک دنبال کنید.')],5:[('netter_plate103','نتر، پلیت ۱۰۳، صفحهٔ فایل ۱۵۵','عروق تیروئیدی و شاخه‌های حنجره‌ای را در نمای قدامی مشخص کنید.')],6:[('netter_plate99','نتر، پلیت ۹۹، صفحهٔ فایل ۱۵۱','لینگوال و فاسیال را در ارتباط با عضلات و غدهٔ زیر فکی دنبال کنید.')],8:[('gray_fig8182','گری، بخش ۱۰۰۱–۱۱۸۹، صفحهٔ فایل ۵۴، چاپی ۱۰۲۶، شکل ۸.۱۸۲','قسمت‌های ساب‌کلاوین را نسبت به اسکالن و شبکهٔ بازویی جهت‌یابی کنید.')],9:[('gray_fig8187','گری، بخش ۱۰۰۱–۱۱۸۹، صفحهٔ فایل ۵۹، چاپی ۱۰۳۱، شکل ۸.۱۸۷','ورتبرال را از ریشهٔ گردن به بالا و ساب‌کلاوین را نسبت به دندهٔ اول دنبال کنید.')],10:[('netter_plate104','نتر، پلیت ۱۰۴، صفحهٔ فایل ۱۵۶','تیروئیدی تحتانی و عصب راجعه را در نمای خلفی تشخیص دهید.')]}

# Each image follows a specific passage of its own lecture page.  This avoids
# detaching a figure from the anatomical relationship it is intended to show.
FIGURE_ANCHORS={
 1:{1:'این دو تا شریان و شاخه',2:'• سمت چپ:',3:'• در جلو (Anterior):'},
 2:{1:'• در خارج (Lateral):',2:'۲. شریان کاروتید بیرونی',3:'۱. سینوس کاروتید'},
 3:{1:'بعد از اون از طریق کانال کاروتید'},
 4:{1:'شریان کاروتید بیرونی یا خارجی (ECA)',2:'شاخه‌های سطح خلفی'},
 5:{1:'نکته مجاورتی با عضله دیگاستریک',3:'• شاخه خلفی:'},
 6:{1:'• شاخه کریکوتیروئید:',2:'• قسمت انتهایی‌ش به شریان عمقی زبان',3:'شریان فاسیال (صورتی) و مسیر حرکت آن:'},
 7:{1:'شریان آکسیپیتال (پس‌سری)',2:'شریان گوشی خلفی (Posterior Auricular)'},
 8:{1:'شریان گیجگاهی سطحی (Superficial Temporal) — شاخه انتهایی:'},
 9:{1:'شاخه‌های بخش اول شریان ساب‌کلاوین',2:'۱. شریان ورتبرال یا مهره‌ای',3:'با توجه به این مسیر، شریان ورتبرال'},
 10:{1:'پایین میاد و در مقابل ششمین فضای',2:'• سایر شاخه‌های فرعی:',3:'• الف) شریان تیروئیدی تحتانی'},
 11:{1:'مسیر و شاخه‌ها: این تنه',2:'بخش سوم شریان ساب‌کلاوین و شریان کتفی خلفی:'},
 12:{1:'۲. سندرم دزدیدن ساب‌کلاوین',2:'• مسیر و ویژگی‌ها:'}}
REF_ANCHORS={
 1:{'gray_fig8165':'• سمت چپ:'},
 2:{'gray_fig8167':'۱. سینوس کاروتید','netter_plate58':'وقتی این شریان به موازات'},
 3:{'netter_plate165':'بعد از اون از طریق کانال کاروتید'},
 5:{'netter_plate103':'• شاخه خلفی:'},
 6:{'netter_plate99':'شریان فاسیال (صورتی) و مسیر حرکت آن:'},
 8:{'gray_fig8182':'• بخش سوم در سمت خارج'},
 9:{'gray_fig8187':'با توجه به این مسیر، شریان ورتبرال'},
 10:{'netter_plate104':'نکته بالینی و جراحی بسیار حیاتی:'}}

def outline():
 return {'session':'hn08','title':'عروق گردنی','topics':[{'topic_id':f'hn08-T{i:02}','title':title,'pages':([12,13] if i==12 else [i]),'gist':W.QUESTIONS[i], 'prereq':'شناخت جهت‌ها، لامی و فاسیای گردن'} for i,title in enumerate(W.TITLES,1)]}

def image_block(path,title,cite,guide):
 return {'type':'plate','book':'lecture','asset':str(path.relative_to(ROOT)),'title':title,'citation':cite,'src':cite,'fa_text':guide,'labels':[],'max_h':125,'min_img_h':65}

def graph_data():
 specs={1:('منشأ شریان‌های اصلی سمت راست',['قوس آئورت','تنهٔ براکیوسفالیک','کاروتید مشترک راست','ساب‌کلاوین راست'],[(0,1,'شاخه'),(1,2,'تقسیم به'),(1,3,'تقسیم به')],'جزوهٔ جلسهٔ ۸، صفحهٔ فایل ۱؛ گری، شکل ۸.۱۶۵، صفحهٔ فایل ۳۸، چاپی ۱۰۱۰'),9:('مسیر شریان مهره‌ای',['ساب‌کلاوین','شریان ورتبرال','فورامن مگنوم','ورتبرال داخل جمجمه','شریان بازیلار'],[(0,1,'مبدأ'),(1,2,'عبور از'),(2,3,'ادامهٔ مسیر'),(3,4,'اتحاد شریان‌های دو طرف')],'جزوهٔ جلسهٔ ۸، صفحهٔ فایل ۹؛ نتر، پلیت ۱۶۵، صفحهٔ فایل ۲۱۷')}
 graphs={}
 for idx,(title,items,connections,src) in specs.items():
  nodes=[{'id':f'n{i}','text':x} for i,x in enumerate(items)];edges=[[f'n{a}',f'n{b}'] for a,b,_ in connections]
  graphs[str(idx)]={'diagram':{'title':title,'nodes':nodes,'edges':edges,'edge_labels':{f'n{a}:n{b}':lab for a,b,lab in connections},'reading_task':'جهت هر رابطه را با متن و تصویر همین مبحث بخوانید.','reference':src}}
 return graphs

def emit_table(book,idx):
 data={3:('سینوس و جسم کاروتید',[['سینوس','گیرندهٔ فشار','در ناحیهٔ دوشاخگی و ابتدای کاروتید داخلی'],['جسم','گیرندهٔ شیمیایی','در ناحیهٔ دوشاخگی']],'گری، بخش ۱۰۰۱–۱۱۸۹، صفحهٔ فایل ۳۹، چاپی ۱۰۱۱'),4:('شاخه‌های کاروتید خارجی',[['قدامی','تیروئیدی فوقانی، زبانی، صورتی'],['خلفی','پس‌سری، گوشی خلفی'],['داخلی','حلقی صعودی'],['انتهایی','ماگزیلاری، تمپورال سطحی']],'گری، بخش ۱۰۰۱–۱۱۸۹، صفحهٔ فایل ۴۰، چاپی ۱۰۱۲، جدول ۸.۱۳؛ صفحهٔ فایل ۴۱، چاپی ۱۰۱۳'),8:('سه بخش ساب‌کلاوین نسبت به اسکالن قدامی',[['اول','داخلی'],['دوم','پشتی'],['سوم','خارجی']],'گری، بخش ۱۰۰۱–۱۱۸۹، صفحهٔ فایل ۵۴، چاپی ۱۰۲۶')}
 if idx not in data:return
 title,rows,source=data[idx];heads=['ساختار','کارکرد','جایگاه'] if idx==3 else ['دسته یا بخش','شاخه‌ها یا موقعیت']
 book.h3('مرور آموزشی — '+title,keep_with=90)
 H.emit_table(book,heads,rows,caption=title,src=source,size=8.7)

def build(path,toc=None):
 pages=source_pages();o=outline();cfg=H.HN_SESSIONS['hn08'];book=Book(path,'جزوهٔ مادر آناتومی سر و گردن — جلسهٔ ۸',footer='HumsYar · جزوهٔ مادر سر و گردن · جلسهٔ ۸',subject='جزوهٔ مادر')
 book.measure_idcard=True;book.keep_parenthesized_latin=True;book.block_trace=[];book.trace_topic=''
 SHELL.opening(book,8,o,toc);book.h1('عروق گردن',anchor='chapter',kicker='جلسهٔ هشتم');book.para('در شناسنامهٔ جزوهٔ اصلی: استاد میرزایی؛ ویس به متن: نرگس بنایی؛ تألیف: پوریا عبداللهی.')
 book.source_line('جزوهٔ جلسهٔ ۸، صفحهٔ فایل ۱');book.para('مسیر شریان‌های کاروتید و ساب‌کلاوین، شاخه‌ها و وریدهای گردن را در متن و شکل دنبال کنید.')
 graphs=graph_data();geometry=R.layouts(book,graphs);stats={'topics':{},'figures':[],'source_paragraphs':{}}
 for i,t in enumerate(o['topics'],1):
  book.trace_topic=t['topic_id'];card=[{'label':'جای این مبحث','text':t['title']},{'label':'هدف یادگیری','text':W.QUESTIONS[i]},{'label':'پیش‌نیاز','text':t['prereq']},{'label':'راهنمای خواندن شکل','text':W.GUIDES[i][0]}]
  H.topic_head(book,t,i,len(o['topics']),after=book.card_height(card)+35,part_labels=False);stats['topics'][t['topic_id']]={'page':book.page,'title':t['title']}
  book.label_card('شناسنامهٔ مبحث',card,kicker='قبل از شروع این مبحث بخوانید',footer='جزوهٔ جلسهٔ ۸، صفحهٔ فایل '+str(i))
  if i in (3,4,6,8,10,12):
   book.callout('عبارت‌های بالینی در ادامه نقل آموزشی جزوه‌اند؛ آن‌ها را دستور فشار بر گردن، مداخله یا تشخیص فردی ندانید.',kind='info',title='راهنمای خواندن متن درس')
  paras=[x.strip() for x in pages[i].split('\n') if x.strip()]
  # The marginal source note referring to a tool is preserved in the transcription file;
  # the subject's anatomical ambiguity is included separately in the reviewer sheet.
  paras=[x for x in paras if not x.startswith('یادداشت حاشیه‌ای منبع:')]
  stats['source_paragraphs'][str(i)]=len(paras)
  placed=set()
  def put(path,title,cite,guide):
   block=image_block(path,title,cite,guide);H.render_blocks(book,[block],cfg)
   stats['figures'].append({'asset':str(path.relative_to(ROOT)),'sha256':R.sha(path),'topic':t['topic_id'],'source':cite})
  for para in paras:
   H.render_blocks(book,[{'type':'p','text':para,'src':f'جزوهٔ جلسهٔ ۸، صفحهٔ فایل {i}'}],cfg)
   if i==6 and para.startswith('• شاخه سوپراهیوئید:'):
    book.callout('یادداشت حاشیه‌ای جزوه: در گفتهٔ استاد سوپراهیوئید آمده و دربارهٔ اینفراهیوئید اختلاف یادداشت شده است. '+W.NOTES[i][0],kind='info',title='یادداشت منبع و توضیح آموزشی')
    book.source_line('جزوهٔ جلسهٔ ۸، صفحهٔ فایل ۶؛ '+W.NOTES[i][1])
   if i==4 and '۲. از طریق آناستوموز' in para:
    path=ROOT/'headneck/images/hn08/lecture_p05_2.png';cite='جزوهٔ جلسهٔ ۸، صفحهٔ فایل ۵'
    put(path,'تصویر جزوه — آناستوموز کاروتید داخلی و خارجی',cite,CAPTIONS[5][1]);placed.add('lecture_p05_2')
   for j,anchor in FIGURE_ANCHORS[i].items():
    key=f'lecture_p{i:02}_{j}'
    if anchor in para and key not in placed:
     cite=f'جزوهٔ جلسهٔ ۸، صفحهٔ فایل {i}';path=ROOT/f'headneck/images/hn08/{key}.png'
     put(path,'تصویر جزوه — '+t['title'],cite,CAPTIONS[i][j-1]);placed.add(key)
   for name,anchor in REF_ANCHORS.get(i,{}).items():
    if anchor in para and name not in placed:
     ref=next(r for r in REFS[i] if r[0]==name);path=ROOT/f'headneck/images/hn08/{name}.png'
     put(path,'نمای مرجع — '+t['title'],ref[1],ref[2]);placed.add(name)
  expected={f'lecture_p{i:02}_{j}' for j in FIGURE_ANCHORS[i]} | set(REF_ANCHORS.get(i,{}))
  if i==4:expected.add('lecture_p05_2')
  if placed!=expected:raise ValueError(f'Missing figure anchors topic {i}: {expected-placed}')
  if i!=6:
   book.callout(W.NOTES[i][0],kind='info',title='توضیح آموزشی — جدا از متن جزوه');book.source_line(W.NOTES[i][1])
  emit_table(book,i)
  if i==12:
   cite='جزوهٔ جلسهٔ ۸، صفحهٔ فایل ۱۳'
   for name,guide in [('lecture_p13_1','دو نمای وریدی اصل را کنار هم بخوانید؛ مسیر ژوگولار داخلی را دنبال کنید.'),('lecture_p13_detail_sinus','بزرگ‌نمایی نیمهٔ چپ همان شکل: مسیر سینوس ساژیتال، سینوس عرضی و سیگموئید تا ژوگولار داخلی را دنبال کنید.'),('lecture_p13_detail_veins','بزرگ‌نمایی نیمهٔ راست همان شکل: وریدهای سطحی صورت و گردن را نسبت به ژوگولار داخلی شناسایی کنید.')]:
    put(ROOT/f'headneck/images/hn08/{name}.png','تصویر جزوه — وریدهای سر و گردن',cite,guide)
  if str(i) in graphs:R.draw_graph(book,graphs[str(i)],geometry[str(i)],force_page=True)
  book.note_box(24,title='یادداشت جزوه‌نویس')
  book.handoff_sheet('برگهٔ تحویل — مبحث '+str(i)+' — '+t['title'],f'جزوهٔ جلسهٔ ۸، صفحهٔ فایل {i}'+(' و ۱۳' if i==12 else '')+'؛ '+W.NOTES[i][1],W.GUIDES[i],W.REVIEW[i],kicker='برای تکمیل جزوه‌نویس',note='پرسش باز: '+W.QUESTIONS[i],writer_name=True)
 book.new_page();book.h1('جمع‌بندی و چک‌لیست',anchor='hn-summary',kicker='پایان جلسه')
 rows=[['مبحث '+K.fa_digits(str(i))+' — '+t['title'],W.GUIDES[i][0],'☐'] for i,t in enumerate(o['topics'],1)]
 H.emit_table(book,['چک‌لیست خودآزمایی','می‌توانم این را توضیح دهم؟','☐'],rows,widths=[K.CONTENT_W*.32,K.CONTENT_W*.56,K.CONTENT_W*.12],caption='چک‌لیست خودآزمایی جلسهٔ ۸',size=8.2)
 if book.missing_assets:raise ValueError(book.missing_assets)
 SHELL.next_section(book,8);SHELL.back(book,8);book.save();stats['pages']=book.page;return book.heading_pages,stats

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT/'HumsYar_HeadNeck_Jalase8_WRITER_FINAL.pdf');args=p.parse_args();out=args.out.resolve();out.parent.mkdir(parents=True,exist_ok=True)
 first,_=build(out);second,stats=build(out,first)
 if first!=second:raise ValueError('Unstable table of contents')
 H.drop_trailing_blank_page(out);qa={'outside_spans':[],'empty_pages':[],'leaks':[],'body_near_footer':[]}
 with pymupdf.open(out) as doc:
  for n,page in enumerate(doc,1):
   text=unicodedata.normalize('NFKC',page.get_text()).replace('\u200c','')
   if BAD.search(text):qa['leaks'].append({'page':n,'text':BAD.search(text).group()})
   if not text.strip() and not page.get_images():qa['empty_pages'].append(n)
   for b in page.get_text('dict',clip=pymupdf.INFINITE_RECT())['blocks']:
    for line in b.get('lines',[]):
     for span in line['spans']:
      x0,y0,x1,y1=span['bbox']
      if x0<-.5 or y0<-.5 or x1>page.rect.width+.5 or y1>page.rect.height+.5:qa['outside_spans'].append({'page':n,'text':span['text']})
      if n>1 and span['size']>=8 and y1>789 and y0<795:qa['body_near_footer'].append({'page':n,'text':span['text']})
   page.get_pixmap(matrix=pymupdf.Matrix(1.25,1.25),alpha=False).save(str(out.parent/f'page-{n:03}.jpg'),jpg_quality=88)
  stats['bookmarks']=doc.get_toc()
 stats.update(file=str(out.relative_to(ROOT)),sha256=R.sha(out),bytes=out.stat().st_size,qa=qa)
 (out.parent/'manifest.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'pages':stats['pages'],'figures':len(stats['figures']),'sha256':stats['sha256'],'qa':qa},ensure_ascii=False,indent=2))
 if any(qa.values()):raise SystemExit('QA failed; see manifest')
if __name__=='__main__':main()

"""Build the session-eleven writer booklet from typed lecture and local references."""
from __future__ import annotations
import argparse,json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'render'),str(Path(__file__).parent)]
import pymupdf
import build_headneck as H
import build_hn01_updated_review as R
import writer_shell as SHELL
import hn11_writer_copy as W
K=H.K
OUT=ROOT/'.cache/hn11_writer_update'
BAD=re.compile(r'IMG[-ـ]?\d+|SRC[-ـ]?\d+|hn\d\d[-–]T\d+|JSON|BLOCKED|NOT_YET|PENDING|INTEGRATED|غیرنهایی|پیش‌نویس|هوش مصنوعی',re.I)

class Book(R.ReviewBook):
 def source_line(self,s):super().source_line(str(s).replace('PDF','فایل'))

def source_pages():
 pages={}
 for p in sorted((ROOT/'headneck/content/session11').glob('source_page*.txt')):
  for n,body in re.findall(r'@@ صفحه ([۰-۹0-9]+)[^\n]*\n(.*?)(?=\n@@ صفحه |\Z)',p.read_text(),re.S):
   n=int(n.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')))
   if n in pages:raise ValueError(f'duplicate page {n}')
   pages[n]=body.strip()
 if sorted(pages)!=list(range(1,21)):raise ValueError(f'missing pages: {sorted(pages)}')
 return pages

FIGURES={
1:[('01','لایه‌های عضلات صورت را از پیشانی تا چانه دنبال کنید.')],
2:[('02','نمای سطحی و عمقی را از نظر تمپورالیس، ماستر و پتریگوئیدها مقایسه کنید.')],
5:[('03','بوکسیناتور را نسبت به مجرای پاروتید و ماستر پیدا کنید.')],
6:[('04','عضلات گوشی قدامی، فوقانی و خلفی را نسبت به لالهٔ گوش تشخیص دهید.')],
8:[('05','شاخه‌های گردنی فاسیال را نسبت به کاروتید خارجی و فک دنبال کنید.')],
9:[('06','شاخه‌های بینی، لبی و زاویه‌ای را نسبت به شریان فاسیال بیابید.')],
11:[('07','شریان اینفرااوربیتال را در نمای عمقی و نسبت به اربیت ببینید.'),('08','شریان اینفرااوربیتال را نسبت به پلک و گوشهٔ داخلی چشم در نمای قدامی بیابید.')],
12:[('09','وریدهای فاسیال و رترومندیبولار را تا ژوگولار دنبال کنید.')],
13:[('10','شاخه‌های عصب فاسیال را پس از خروج و نسبت به پاروتید و مجرا دنبال کنید.')],
15:[('11','شاخه‌های عصب فاسیال و شاخهٔ گوشی خلفی را نسبت به غده پیدا کنید.')],
17:[('12','در نمای طرفی شاخهٔ حسی گوشی‌گیجگاهی را از شاخه‌های حرکتی فاسیال جدا کنید.')],
18:[('13','عصب ماگزیلاری و شاخه‌های اینفرااوربیتال و زایگوماتیک را در عمق دنبال کنید.')],
19:[('14','غده و مجرای پاروتید را با عضلات، رگ‌ها و عصب صورت مقایسه کنید.')]}
# asset, exact citation, topic-specific reading instruction
REFS={
1:[('gray_853','گری، ویراست ۳، فصل ۸، صفحهٔ فایل ۱۳۲ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۰۴، شکل ۸.۵۳','عضلات سطحی را از پیشانی تا گردن با نمای اصل مقایسه کنید.'),('netter_100','نتر، ویراست ۸، پلیت ۴۸، صفحهٔ فایل ۱۰۰','عضلات سطحی، فاسیا و محل اتصال پوست را در نمای جانبی بیابید.')],
2:[('netter_124','نتر، پلیت ۷۲، صفحهٔ فایل ۱۲۴','دو نمای تمپورالیس و ماستر را با یکدیگر و با شکل درس مقایسه کنید.')],
3:[('gray_854','گری، فصل ۸، صفحهٔ فایل ۱۳۵ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۰۷، شکل ۸.۵۴','بخش پلکی و کاسه‌ای عضله و چین‌دهندهٔ ابرو را در نمای چشم مقایسه کنید.'),('gray_855','گری، فصل ۸، صفحهٔ فایل ۱۳۵ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۰۷، شکل ۸.۵۵','بخش عرضی و پره‌ای عضلهٔ بینی و پایین‌آورندهٔ تیغه را بیابید.')],
4:[('gray_856','گری، فصل ۸، صفحهٔ فایل ۱۳۶ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۰۸، شکل ۸.۵۶','عضلهٔ دور دهان و عضلات بالابرنده را نسبت به گوشهٔ دهان دنبال کنید.')],
5:[('gray_857','گری، فصل ۸، صفحهٔ فایل ۱۳۷ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۰۹، شکل ۸.۵۷','بوکسیناتور، رافهٔ پتریگومندیبولار و مجرای پاروتید را نسبت به فک مقایسه کنید.'),('gray_858','گری، فصل ۸، صفحهٔ فایل ۱۳۸ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۱۰، شکل ۸.۵۸','عضلات گوشی را در جلو، بالا و پشت لالهٔ گوش بیابید.')],
6:[('netter_151','نتر، پلیت ۹۹، صفحهٔ فایل ۱۵۱','شاخه‌های گردنی فاسیال را نسبت به مندیبل و کاروتید بیرونی دنبال کنید.')],
7:[('netter_112','نتر، پلیت ۶۰، صفحهٔ فایل ۱۱۲','شاخه‌های لبی، بینی و زاویه‌ای را نسبت به عضلات و اعصاب ببینید.'),('gray_864','گری، فصل ۸، صفحهٔ فایل ۱۴۶ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۱۸، شکل ۸.۶۴','نمای سطحی عروق صورت و نمای شاخه‌های ماگزیلاری را مقایسه کنید.')],
8:[('netter_167','نتر، پلیت ۱۱۵، صفحهٔ فایل ۱۶۷','سه نمای عروق اربیت و پلک را با شاخه‌های اینفرااوربیتال و افتالمیک مقایسه کنید.')],
9:[('netter_152','نتر، پلیت ۱۰۰، صفحهٔ فایل ۱۵۲','ورید فاسیال، رترومندیبولار و ژوگولارها را در نمای طرفی دنبال کنید.'),('gray_865','گری، فصل ۸، صفحهٔ فایل ۱۴۸ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۲۰، شکل ۸.۶۵','ارتباط ورید صورت با ورید افتالمیک و شبکهٔ پتریگوئیدی را دنبال کنید.'),('gray_866','گری، فصل ۸، صفحهٔ فایل ۱۴۸ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۲۰، شکل ۸.۶۶','گره‌های لنفی زیرچانه‌ای، تحت فکی و پاروتید را ببینید؛ این مسیر لنفی است، نه وریدی.')],
10:[('netter_202','نتر، پلیت ۱۵۰، صفحهٔ فایل ۲۰۲','شاخه‌های VII، رشتهٔ چشایی و مسیرهای خودکار را از هم تفکیک کنید.'),('netter_213','نتر، پلیت ۱۶۱، صفحهٔ فایل ۲۱۳','مسیر زوج IX، شبکهٔ تمپانیک، پتروزال کوچک و گانگلیون گوشی تا پاروتید را دنبال کنید.'),('gray_863','گری، فصل ۸، صفحهٔ فایل ۱۴۵ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۱۷، شکل ۸.۶۳','شاخه‌های قبل از ورود به پاروتید و شاخه‌های انتهایی عصب هفتم را در دو نما مقایسه کنید.')],
11:[('netter_131','نتر، پلیت ۷۹، صفحهٔ فایل ۱۳۱','شاخه‌های افتالمیک و ماگزیلاری را نسبت به اربیت و سوراخ‌ها دنبال کنید.'),('gray_861','گری، فصل ۸، صفحهٔ فایل ۱۴۲ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۱۴، شکل ۸.۶۱','خروج شاخه‌های سه‌قلو و شاخه‌های سطح صورت را نسبت به جمجمه دنبال کنید.'),('gray_862','گری، فصل ۸، صفحهٔ فایل ۱۴۳ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۱۵، شکل ۸.۶۲','قلمرو سه شاخهٔ حسی را با نواحی گردنی و گوش مقایسه کنید.')],
12:[('gray_860','گری، فصل ۸، صفحهٔ فایل ۱۴۱ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۱۳، شکل ۸.۶۰','برش محوری آموزشی را برای مقایسهٔ محل پاروتید، فک و کاروتید بخوانید؛ عنوان کتاب وجود ضایعه را در این نمونه نشان می‌دهد و جای تشخیص مستقل نیست.'),('netter_122','نتر، پلیت ۷۰، صفحهٔ فایل ۱۲۲','غده، مجرا، بوکسیناتور و عروق را در نمای طرفی مقایسه کنید.'),('gray_859','گری، فصل ۸، صفحهٔ فایل ۱۳۹ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۱۱، شکل ۸.۵۹','عصب، ورید و شریان درون غده را در مقطع عرضی با نمای جانبی مقایسه کنید.')]}

def outline():
 return {'session':'hn11','title':'صورت و ناحیهٔ پاروتید','topics':[{'topic_id':f'hn11-T{i:02}','title':title,'pages':W.GROUPS[i-1],'gist':W.QUESTIONS[i],'prereq':'حدود جمجمه، عضلات گردن و مسیر عروق و اعصاب سر و گردن'} for i,title in enumerate(W.TITLES,1)]}

def graph_data():
 specs={
 'veins':('تخلیهٔ وریدی صورت و رترومندیبولار',['سوپراتروکلئار و سوپرااوربیتال','ورید زاویه‌ای','ورید فاسیال','شاخهٔ قدامی رترومندیبولار','ورید صورتی مشترک','ژوگولار داخلی','شاخهٔ خلفی و اوریکولار خلفی','ژوگولار خارجی'],[(0,1,'اتحاد'),(1,2,'ادامه'),(2,4,'اتحاد'),(3,4,'اتحاد'),(4,5,'تخلیه'),(6,7,'اتحاد')],'جزوهٔ جلسهٔ ۱۱، صفحهٔ فایل ۱۳؛ نتر، پلیت ۱۰۰، صفحهٔ فایل ۱۵۲'),
 'facial':('تنه‌ها و شاخه‌های عصب فاسیال در صورت',['عصب فاسیال','تنهٔ گیجگاهی‌صورتی','تنهٔ گردنی‌صورتی','گیجگاهی و گونه‌ای','بوکال فوقانی','بوکال تحتانی','مارژینال مندیبولار و گردنی'],[(0,1,'تقسیم'),(0,2,'تقسیم'),(1,3,'شاخه'),(1,4,'شاخه'),(2,5,'شاخه'),(2,6,'شاخه')],'جزوهٔ جلسهٔ ۱۱، صفحهٔ فایل ۱۴ و ۱۶؛ گری، شکل ۸.۶۳، صفحهٔ فایل ۱۴۵، چاپی ۹۱۷')}
 out={}
 for key,(title,names,links,src) in specs.items():out[key]={'diagram':{'title':title,'nodes':[{'id':f'n{j}','text':s} for j,s in enumerate(names)],'edges':[[f'n{a}',f'n{b}'] for a,b,_ in links],'edge_labels':{f'n{a}:n{b}':v for a,b,v in links},'reading_task':'پیکان‌ها را با متن و تصویر همین مبحث تطبیق دهید.','reference':src}}
 return out

def build(path,toc=None):
 pages=source_pages();o=outline();cfg=H.HN_SESSIONS['hn11'];book=Book(path,'جزوهٔ مادر آناتومی سر و گردن — جلسهٔ ۱۱',footer='HumsYar · جزوهٔ مادر سر و گردن · جلسهٔ ۱۱',subject='جزوهٔ مادر')
 book.measure_idcard=True;book.keep_parenthesized_latin=True;book.block_trace=[];book.trace_topic=''
 SHELL.opening(book,11,o,toc);book.h1('صورت و ناحیهٔ پاروتید',anchor='chapter',kicker='جلسهٔ یازدهم');book.para('منبع درس: دکتر میرزایی، گروه تشریح دانشگاه علوم پزشکی هرمزگان.');book.source_line('جزوهٔ جلسهٔ ۱۱، صفحهٔ فایل ۱')
 graphs=graph_data();geometry=R.layouts(book,graphs);stats={'topics':{},'figures':[],'source_paragraphs':{}}
 for i,t in enumerate(o['topics'],1):
  book.trace_topic=t['topic_id'];card=[{'label':'جای این مبحث','text':t['title']},{'label':'هدف یادگیری','text':W.QUESTIONS[i]},{'label':'پیش‌نیاز','text':t['prereq']},{'label':'راهنمای خواندن شکل','text':W.GUIDES[i][0]}]
  H.topic_head(book,t,i,len(o['topics']),after=book.card_height(card)+35,part_labels=False);stats['topics'][t['topic_id']]={'page':book.page,'title':t['title']}
  label=' و '.join(str(n) for n in t['pages']);book.label_card('شناسنامهٔ مبحث',card,kicker='قبل از شروع این مبحث بخوانید',footer='جزوهٔ جلسهٔ ۱۱، صفحهٔ فایل '+label)
  def put(path,title,cite,guide):
   block={'type':'plate','book':'lecture','asset':str(path.relative_to(ROOT)),'title':title,'citation':cite,'src':cite,'fa_text':guide,'labels':[],'max_h':150,'min_img_h':65}
   H.render_blocks(book,[block],cfg);stats['figures'].append({'asset':str(path.relative_to(ROOT)),'sha256':R.sha(path),'topic':t['topic_id'],'source':cite})
  for n in t['pages']:
   placed=set();paras=[x.strip() for x in pages[n].splitlines() if x.strip()];stats['source_paragraphs'][str(n)]=len(paras)
   for para in paras:
    if para.startswith('من برای خواندن دقیق'):book.para('عبارت فنیِ مندرج در اصل جزوه، عیناً:')
    H.render_blocks(book,[{'type':'p','text':para,'src':f'جزوهٔ جلسهٔ ۱۱، صفحهٔ فایل {n}'}],cfg)
    for num,guide in FIGURES.get(n,[]):
     anchor='شکل ('+K.fa_digits(str(int(num)))+')'
     if anchor in para and num not in placed:
      put(ROOT/f'headneck/images/hn11_candidates/lecture_figure_{num}_p{n:02}.png','تصویر جزوه — '+t['title'],f'جزوهٔ جلسهٔ ۱۱، صفحهٔ فایل {n}، شکل {K.fa_digits(str(int(num)))}',guide);placed.add(num)
   if placed!={x[0] for x in FIGURES.get(n,[])}:raise ValueError(f'figure anchor missing source page {n}: {placed}')
  book.ensure(120);book.callout(W.EXTRA[i][1],kind='info',title='توضیح آموزشی — جدا از متن جزوه');book.source_line(W.EXTRA[i][0])
  if i==2:
   book.callout('متن درس دربارهٔ کمان حلقی عضلات جونده عبارتی دارد که باید جداگانه با منابع جنین‌شناسی مقابله شود؛ آن عبارت در متن درس بدون اصلاح پنهان حفظ شده است.',kind='info',title='پرسش باز برای بازبین');book.source_line('جزوهٔ جلسهٔ ۱۱، صفحهٔ فایل ۲')
  if i==9:
   book.callout('نقشهٔ لنفی و مسیرهای وریدی دو دستگاه متفاوت‌اند؛ تصویر لنفی افزوده‌ای آموزشی است، نه بخشی از فهرست وریدهای اصل.',kind='info',title='تفکیک تصویر تکمیلی');book.source_line('گری، فصل ۸، صفحهٔ فایل ۱۴۸ از بخش ۸۰۱–۱۰۰۰، چاپی ۹۲۰، شکل ۸.۶۶')
  if i==10:
   book.callout('در متن درس پیوند شاخهٔ ژنیکولوتیمپانیک با پتروزال کوچک بیان شده است. در شماتیک نتر، عصب تمپانیک از زوج نهم به شبکهٔ تمپانیک و پتروزال کوچک می‌رسد؛ نسبت و منشأ رشته‌ها را برای بازبین به‌طور مستقل مقایسه کنید.',kind='info',title='تفاوت برای بازبین');book.source_line('جزوهٔ جلسهٔ ۱۱، صفحهٔ فایل ۱۵؛ نتر، پلیت ۱۶۱، صفحهٔ فایل ۲۱۳')
  for name,cite,guide in REFS.get(i,[]):put(ROOT/f'headneck/images/hn11_refs/{name}.png','نمای مرجع — '+t['title'],cite,guide)
  graph={9:'veins',10:'facial'}.get(i)
  if graph:R.draw_graph(book,graphs[graph],geometry[graph],force_page=False)
  book.note_box(24,title='یادداشت جزوه‌نویس');book.handoff_sheet('برگهٔ تحویل — مبحث '+str(i)+' — '+t['title'],'جزوهٔ جلسهٔ ۱۱، صفحهٔ فایل '+label+'؛ '+W.EXTRA[i][0],W.GUIDES[i],W.EXTRA[i][1],kicker='برای تکمیل جزوه‌نویس',note='پرسش باز: '+W.QUESTIONS[i],writer_name=True)
 book.new_page();book.h1('جمع‌بندی و چک‌لیست',anchor='hn-summary',kicker='پایان جلسه')
 rows=[['مبحث '+K.fa_digits(str(i))+' — '+t['title'],W.GUIDES[i][0],'☐'] for i,t in enumerate(o['topics'],1)]
 H.emit_table(book,['چک‌لیست خودآزمایی','می‌توانم این را توضیح دهم؟','☐'],rows,widths=[K.CONTENT_W*.32,K.CONTENT_W*.56,K.CONTENT_W*.12],caption='چک‌لیست خودآزمایی جلسهٔ ۱۱',size=8.2)
 if book.missing_assets:raise ValueError(book.missing_assets)
 SHELL.next_section(book,11);SHELL.back(book,11);book.save();stats['pages']=book.page;return book.heading_pages,stats

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT/'HumsYar_HeadNeck_Jalase11_WRITER_FINAL.pdf');out=p.parse_args().out.resolve();out.parent.mkdir(parents=True,exist_ok=True)
 first,_=build(out);second,stats=build(out,first)
 if first!=second:raise ValueError('unstable table of contents')
 H.drop_trailing_blank_page(out);OUT.mkdir(parents=True,exist_ok=True);qa={'outside_spans':[],'empty_pages':[],'leaks':[],'body_near_footer':[]}
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
   page.get_pixmap(matrix=pymupdf.Matrix(1.25,1.25),alpha=False).save(str(OUT/f'page-{n:03}.jpg'),jpg_quality=88)
  stats['bookmarks']=doc.get_toc()
 stats.update(file=str(out.relative_to(ROOT)),sha256=R.sha(out),bytes=out.stat().st_size,qa=qa)
 (OUT/'manifest.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'pages':stats['pages'],'figures':len(stats['figures']),'sha256':stats['sha256'],'qa':qa},ensure_ascii=False,indent=2))
 if any(qa.values()):raise SystemExit('QA failed; see manifest')
if __name__=='__main__':main()

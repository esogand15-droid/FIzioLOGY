"""Build the session-nine writer booklet from typed lecture and local references."""
from __future__ import annotations
import argparse,json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'render'),str(Path(__file__).parent)]
import pymupdf
import build_headneck as H
import build_hn01_updated_review as R
import writer_shell as SHELL
import hn09_writer_copy as W
K=H.K
OUT=ROOT/'.cache/hn09_writer_update'
BAD=re.compile(r'IMG[-ـ]?\d+|SRC[-ـ]?\d+|hn\d\d[-–]T\d+|JSON|BLOCKED|NOT_YET|PENDING|INTEGRATED|غیرنهایی|پیش‌نویس|هوش مصنوعی',re.I)

class Book(R.ReviewBook):
 def source_line(self,s):super().source_line(str(s).replace('PDF','فایل'))

def source_pages():
 pages={}
 for p in sorted((ROOT/'headneck/content/session09').glob('source_pages_*.txt')):
  for n,body in re.findall(r'@@ صفحه ([۰-۹0-9]+)[^\n]*\n(.*?)(?=\n@@ صفحه |\Z)',p.read_text(),re.S):
   n=int(n.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')))
   if n in pages:raise ValueError(f'duplicate page {n}')
   pages[n]=body.strip()
 if sorted(pages)!=list(range(1,15)):raise ValueError(f'missing pages: {sorted(pages)}')
 return pages

# Figure 14 is physically on page 9 but captioned on 10; 19 is on 15 but captioned on 14.
FIGS={
1:[('01',1,'شکل (۱)','نمای قدامی: اعصاب شبکهٔ گردنی، واگ و فرنیک را در رابطه با مهره‌ها بیابید.')],
2:[('02',2,'شکل (۲)','ریشه‌های شبکه، آنسا و فرنیک را در شکل دنبال کنید.'),('03',2,'شکل (۳)','شاخه‌های جلدی و سطوح ریشه‌هایشان را از هم جدا کنید.')],
3:[('04',3,'شکل (۴)','قوس گردنی را نسبت به ورید و کاروتید دنبال کنید.'),('05',3,'شکل (۵)','مسیر شاخه‌های عضلانی و فرنیک را از ریشه‌ها تشخیص دهید.')],
4:[('06',4,'شکل (۶)','زوج‌های IX تا XII را در سطح ساقهٔ مغز مقایسه کنید.'),('07',4,'شکل (۷)','شاخه‌های IX و گانگلیون‌های آن را در شماتیک بخوانید.')],
5:[('08',5,'شکل (۸)','مسیر ترشحی پاروتید را از IX تا عصب گوشی‌گیجگاهی دنبال کنید.'),('09',5,'شکل (۹)','راه‌های حسی، سمپاتیک و پاراسمپاتیک را در اطراف اوتیک تفکیک کنید.')],
6:[('10',6,'شکل (۱۰)','شاخه‌های حلقی و حنجره‌ای واگ را نسبت به کاروتید و حنجره ببینید.')],
7:[],8:[('11',8,'شکل (۱۱)','ریشه‌های نشان‌داده‌شدهٔ XI و مقصد عضلانی را دنبال کنید.'),('12',8,'شکل (۱۲)','رشته‌های C1، عصب زیرزبانی و عضلات مقصد را جدا بخوانید.')],
9:[('13',9,'شکل (۱۳)','مجاورت عصب زیرزبانی با هیوگلوس، عصب زبانی و مجرا را ببینید.')],
10:[('14',9,'شکل (۱۴)','گانگلیون‌های سمپاتیک را نسبت به غلاف کاروتید و ریشهٔ گردن پیدا کنید.'),('15',10,'شکل (۱۵)','شاخه‌های خاکستری و قلبی و قوس ساب‌کلاوین را دنبال کنید.')],
11:[('extra11',11,'گانگلیون سمپاتیک تحتانی گردن:','قوس ساب‌کلاوین و ارتباط گانگلیون میانی و ستاره‌ای را مقایسه کنید.')],
12:[('16',12,'شکل (۱۶)','تیروئید و ایستموس را در نمای سطحی با لامی و حنجره مقایسه کنید.')],
13:[('17',13,'شکل (۱۷)','لوب هرمی و ارتباط غده با نای و کاروتید را در نمای قدامی بررسی کنید.')],
14:[('18',14,'شکل (۱۸)','عروق و وریدهای تیروئید را در نمای قدامی بیابید.'),('19',15,'شکل (۱۹)','در نمای خلفی، پاراتیروئید و عصب راجعه را با شاخه‌های تیروئیدی مقایسه کنید.')]}
REFS={1:[('netter_109','نتر، پلیت ۵۷، صفحهٔ فایل ۱۰۹','نقشهٔ شبکه و نمای قدامی ریشهٔ گردن را مقایسه کنید.')],2:[('netter_208','نتر، پلیت ۱۵۶، صفحهٔ فایل ۲۰۸','ریشه‌ها، شاخه‌های جلدی و عضلانی و آنسا را در نمای طرفی دنبال کنید.'),('gray_8184','گری، صفحهٔ فایل ۵۶، چاپی ۱۰۲۸، شکل ۸.۱۸۴','ریشه‌ها، فرنیک و قوس گردنی را در شماتیک تفکیک کنید.')],4:[('netter_204','نتر، پلیت ۱۵۲، صفحهٔ فایل ۲۰۴','مسیرهای آوران و وابران و شاخه‌های زوج IX را تفکیک کنید.'),('gray_8168','گری، صفحهٔ فایل ۴۲، چاپی ۱۰۱۴، شکل ۸.۱۶۸','زوج IX را نسبت به استایلوفارنژیوس و رگ‌ها دنبال کنید.')],6:[('netter_205','نتر، پلیت ۱۵۳، صفحهٔ فایل ۲۰۵','شاخه‌های گردنی واگ را از مسیرهای سینه‌ای و شکمی جدا کنید.'),('gray_8169','گری، صفحهٔ فایل ۴۲، چاپی ۱۰۱۴، شکل ۸.۱۶۹','واگ را نسبت به غلاف و شاخه‌های حنجره‌ای پیدا کنید.')],8:[('netter_206','نتر، پلیت ۱۵۴، صفحهٔ فایل ۲۰۶','مسیر شاخهٔ نخاعی XI را تا دو عضله دنبال کنید.')],9:[('netter_207','نتر، پلیت ۱۵۵، صفحهٔ فایل ۲۰۷','XII و رشته‌های C1 را نسبت به عضلات زبان مقایسه کنید.')],10:[('netter_209','نتر، پلیت ۱۵۷، صفحهٔ فایل ۲۰۹','گانگلیون‌ها و شاخه‌های سمپاتیک را نسبت به رگ‌ها دنبال کنید.'),('gray_8190','گری، صفحهٔ فایل ۶۴، چاپی ۱۰۳۶، شکل ۸.۱۹۰','اتصال گانگلیون‌ها و قوس ساب‌کلاوین را در طرح مقایسه کنید.')],12:[('netter_155','نتر، پلیت ۱۰۳، صفحهٔ فایل ۱۵۵','دو لوب و ایستموس را نسبت به حنجره و عروق بیابید.')],13:[('netter_156','نتر، پلیت ۱۰۴، صفحهٔ فایل ۱۵۶','در نمای خلفی غدد پاراتیروئید و اعصاب راجعه را نسبت به عروق دنبال کنید.')]}

def outline():
 return {'session':'hn09','title':'اعصاب گردن و غدهٔ تیروئید','topics':[{'topic_id':f'hn09-T{i:02}','title':title,'pages':([14,15] if i==14 else [i]),'gist':W.QUESTIONS[i],'prereq':'جهت‌های گردن، غلاف کاروتید و عضلات لامی'} for i,title in enumerate(W.TITLES,1)]}

def graph_data():
 specs={3:('ریشه‌ها و مقصد قوس گردنی',['C1 همراه XII','ریشهٔ فوقانی','ریشهٔ تحتانی C2–C3','قوس گردنی','عضلات زیرلامی به‌جز تیروهیوئید'],[(0,1,'تشکیل'),(1,3,'اتصال'),(2,3,'اتصال'),(3,4,'عصب‌دهی')],'جزوهٔ جلسهٔ ۹، صفحهٔ فایل ۳؛ نتر، پلیت ۵۷، صفحهٔ فایل ۱۰۹'),5:('مسیر ترشحی پاروتید',['عصب IX','شاخهٔ تمپانیک و شبکه','عصب پتروزال کوچک','گانگلیون اوتیک','عصب گوشی‌گیجگاهی','پاروتید'],[(0,1,'شاخه'),(1,2,'ادامه'),(2,3,'سیناپس'),(3,4,'رشتهٔ پس‌عقده‌ای'),(4,5,'ترشح')],'نتر، پلیت ۱۵۲، صفحهٔ فایل ۲۰۴؛ جزوهٔ جلسهٔ ۹، صفحهٔ فایل ۵')}
 out={}
 for i,(title,names,links,src) in specs.items():
  out[str(i)]={'diagram':{'title':title,'nodes':[{'id':f'n{j}','text':s} for j,s in enumerate(names)],'edges':[[f'n{a}',f'n{b}'] for a,b,_ in links],'edge_labels':{f'n{a}:n{b}':v for a,b,v in links},'reading_task':'رابطهٔ هر پیکان را با متن و شکل همین مبحث تطبیق دهید.','reference':src}}
 return out

def build(path,toc=None):
 pages=source_pages();o=outline();cfg=H.HN_SESSIONS['hn09'];book=Book(path,'جزوهٔ مادر آناتومی سر و گردن — جلسهٔ ۹',footer='HumsYar · جزوهٔ مادر سر و گردن · جلسهٔ ۹',subject='جزوهٔ مادر')
 book.measure_idcard=True;book.keep_parenthesized_latin=True;book.block_trace=[];book.trace_topic=''
 SHELL.opening(book,9,o,toc);book.h1('اعصاب گردن و تیروئید',anchor='chapter',kicker='جلسهٔ نهم');book.para('منبع درس: دکتر میرزایی، گروه تشریح دانشگاه علوم پزشکی هرمزگان.');book.source_line('جزوهٔ جلسهٔ ۹، صفحهٔ فایل ۱')
 graphs=graph_data();geometry=R.layouts(book,graphs);stats={'topics':{},'figures':[],'source_paragraphs':{}}
 for i,t in enumerate(o['topics'],1):
  book.trace_topic=t['topic_id'];card=[{'label':'جای این مبحث','text':t['title']},{'label':'هدف یادگیری','text':W.QUESTIONS[i]},{'label':'پیش‌نیاز','text':t['prereq']},{'label':'راهنمای خواندن شکل','text':W.GUIDES[i][0]}]
  H.topic_head(book,t,i,len(o['topics']),after=book.card_height(card)+35,part_labels=False);stats['topics'][t['topic_id']]={'page':book.page,'title':t['title']}
  book.label_card('شناسنامهٔ مبحث',card,kicker='قبل از شروع این مبحث بخوانید',footer=f'جزوهٔ جلسهٔ ۹، صفحهٔ فایل {i}')
  if i in (6,7,13,14):book.callout('عبارت‌های بالینی و جراحی در ادامه نقل درس‌اند؛ برای تصمیم‌گیری دربارهٔ بیمار یا انجام مداخله از آن‌ها به‌تنهایی استفاده نکنید.',kind='info',title='راهنمای خواندن متن درس')
  placed=set()
  def put(path,title,cite,guide):
   block={'type':'plate','book':'lecture','asset':str(path.relative_to(ROOT)),'title':title,'citation':cite,'src':cite,'fa_text':guide,'labels':[],'max_h':125,'min_img_h':65}
   H.render_blocks(book,[block],cfg);stats['figures'].append({'asset':str(path.relative_to(ROOT)),'sha256':R.sha(path),'topic':t['topic_id'],'source':cite})
  paras=[x.strip() for x in pages[i].splitlines() if x.strip()];stats['source_paragraphs'][str(i)]=len(paras)
  for para in paras:
   H.render_blocks(book,[{'type':'p','text':para,'src':f'جزوهٔ جلسهٔ ۹، صفحهٔ فایل {i}'}],cfg)
   for num,physical,anchor,guide in FIGS[i]:
    if anchor in para and num not in placed:
     path=ROOT/f'headneck/images/hn09_candidates/lecture_figure_{num}_p{physical:02}.png';cite=f'جزوهٔ جلسهٔ ۹، صفحهٔ فایل {physical}'
     put(path,'تصویر جزوه — '+t['title'],cite,guide);placed.add(num)
  if placed!={x[0] for x in FIGS[i]}:raise ValueError(f'figure anchor missing topic {i}: {placed}')
  book.ensure(120)
  book.callout(W.REF[i][1],kind='info',title='توضیح آموزشی — جدا از متن جزوه');book.source_line(W.REF[i][0])
  for name,cite,guide in REFS.get(i,[]):put(ROOT/f'headneck/images/hn09_refs/{name}.png','نمای مرجع — '+t['title'],cite,guide)
  if str(i) in graphs:R.draw_graph(book,graphs[str(i)],geometry[str(i)],force_page=False)
  book.note_box(24,title='یادداشت جزوه‌نویس');book.handoff_sheet('برگهٔ تحویل — مبحث '+str(i)+' — '+t['title'],f'جزوهٔ جلسهٔ ۹، صفحهٔ فایل {i}'+(' و ۱۵' if i==14 else '')+'؛ '+W.REF[i][0],W.GUIDES[i],W.REF[i][1],kicker='برای تکمیل جزوه‌نویس',note='پرسش باز: '+W.QUESTIONS[i],writer_name=True)
 book.new_page();book.h1('جمع‌بندی و چک‌لیست',anchor='hn-summary',kicker='پایان جلسه')
 rows=[['مبحث '+K.fa_digits(str(i))+' — '+t['title'],W.GUIDES[i][0],'☐'] for i,t in enumerate(o['topics'],1)]
 H.emit_table(book,['چک‌لیست خودآزمایی','می‌توانم این را توضیح دهم؟','☐'],rows,widths=[K.CONTENT_W*.32,K.CONTENT_W*.56,K.CONTENT_W*.12],caption='چک‌لیست خودآزمایی جلسهٔ ۹',size=8.2)
 if book.missing_assets:raise ValueError(book.missing_assets)
 SHELL.next_section(book,9);SHELL.back(book,9);book.save();stats['pages']=book.page;return book.heading_pages,stats

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT/'HumsYar_HeadNeck_Jalase9_WRITER_FINAL.pdf');out=p.parse_args().out.resolve();out.parent.mkdir(parents=True,exist_ok=True)
 first,_=build(out);second,stats=build(out,first)
 if first!=second:raise ValueError('unstable table of contents')
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

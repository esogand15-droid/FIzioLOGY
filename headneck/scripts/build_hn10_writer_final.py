"""Build the session-ten writer booklet from typed lecture and local references."""
from __future__ import annotations
import argparse,json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'render'),str(Path(__file__).parent)]
import pymupdf
import build_headneck as H
import build_hn01_updated_review as R
import writer_shell as SHELL
import hn10_writer_copy as W
K=H.K
OUT=ROOT/'.cache/hn10_writer_update'
BAD=re.compile(r'IMG[-ـ]?\d+|SRC[-ـ]?\d+|hn\d\d[-–]T\d+|JSON|BLOCKED|NOT_YET|PENDING|INTEGRATED|غیرنهایی|پیش‌نویس|هوش مصنوعی',re.I)

class Book(R.ReviewBook):
 def source_line(self,s):super().source_line(str(s).replace('PDF','فایل'))

def source_pages():
 pages={}
 for p in sorted((ROOT/'headneck/content/session10').glob('source_pages_*.txt')):
  for n,body in re.findall(r'@@ صفحه ([۰-۹0-9]+)[^\n]*\n(.*?)(?=\n@@ صفحه |\Z)',p.read_text(),re.S):
   n=int(n.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')))
   if n in pages:raise ValueError(f'duplicate page {n}')
   pages[n]=body.strip()
 if sorted(pages)!=list(range(1,9)):raise ValueError(f'missing pages: {sorted(pages)}')
 return pages

FIGS={
1:[('01',1,'شکل (۱)','لایه‌های سطحی و مقطع عمقی و نمای جانبی را با هم مقایسه کنید.')],
2:[('02',2,'شکل (۲)','فضای زیرآپونوروتیک را در امتداد پلک فوقانی و ملتحمه دنبال کنید.')],
3:[('03',3,'شکل (۳)','ورید خروجی را از لایهٔ سست تا سینوس وریدی دنبال کنید.'),('04_temporal_upper',3,'شکل (۴)','استخوان‌های محدودهٔ گیجگاهی و محل اتصال عضله به زائدهٔ کرونوئید را مقایسه کنید.'),('04_temporal_lower',3,'شکل (۴)','عضلهٔ تمپورالیس را نسبت به ماستر و بوکسیناتور در نمای جانبی ببینید.')],
4:[('04_vessels_nerves',4,'شکل (۴)','عروق یک سمت و اعصاب سمت دیگر را با لالهٔ گوش و خط میانی مقایسه کنید؛ ابتدای یک برچسب در خود اصل بریده است.')],
5:[('05_veins',5,'شکل (۵)','وریدهای صورت و دو شاخهٔ رترومندیبولار را تا وریدهای ژوگولار دنبال کنید.')],
6:[],
7:[('05_clinical',7,'شکل ۵','تصویر بالینی را در کنار توضیح جزوه دربارهٔ کیست‌های اسکالپ بخوانید، نه به‌عنوان تشخیص قطعی تصویر.'),('06_clinical',7,'شکل ۶','کبودی اطراف چشم را با امتداد فضای سست در شکل ۲ مقایسه کنید.')],}
REFS={1:[('netter_76',76,'۲۴','لایه‌های سطحی و رگ‌های تمپورال را در نمای جانبی بیابید.')],5:[('netter_152',152,'۱۰۰','ورید رترومندیبولار و دو شاخهٔ آن را نسبت به ژوگولارها دنبال کنید.')],6:[('netter_75',75,'۲۳','نقشهٔ اعصاب پوستی سه‌قلو و گردنی را نسبت به گوش مقایسه کنید.')]}

def outline():
 return {'session':'hn10','title':'اسکالپ و ناحیهٔ تمپورال','topics':[{'topic_id':f'hn10-T{i:02}','title':title,'pages':[i],'gist':W.QUESTIONS[i],'prereq':'جهت‌های سر، استخوان‌های جمجمه و شبکهٔ عروقی سر و گردن'} for i,title in enumerate(W.TITLES,1)]}

def graph_data():
 specs={
 'layers':('لایه‌ها و راه حرکت',['پوست','بافت همبند متراکم','آپونوروز اپی‌کرانیال','بافت همبند سست','پری‌کرانیوم'],[(0,1,'در عمق'),(1,2,'در عمق'),(2,3,'در عمق'),(3,4,'در عمق')],'جزوهٔ جلسهٔ ۱۰، صفحهٔ فایل ۲ و ۳، شکل‌های ۱ تا ۳'),
 'veins':('تخلیهٔ ورید رترومندیبولار',['تمپورال سطحی و ماگزیلاری','ورید رترومندیبولار','شاخهٔ قدامی و فاسیال','شاخهٔ خلفی و اوریکولار خلفی','ورید صورتی مشترک','ژوگولار خارجی','ژوگولار داخلی','ورید زیرترقوه‌ای'],[(0,1,'اتحاد'),(1,2,'تقسیم'),(1,3,'تقسیم'),(2,4,'اتحاد'),(3,5,'اتحاد'),(4,6,'تخلیه'),(5,7,'تخلیه')],'جزوهٔ جلسهٔ ۱۰، صفحهٔ فایل ۵؛ نتر، پلیت ۱۰۰، صفحهٔ فایل ۱۵۲')}
 out={}
 for key,(title,names,links,src) in specs.items():
  out[key]={'diagram':{'title':title,'nodes':[{'id':f'n{j}','text':s} for j,s in enumerate(names)],'edges':[[f'n{a}',f'n{b}'] for a,b,_ in links],'edge_labels':{f'n{a}:n{b}':v for a,b,v in links},'reading_task':'رابطهٔ هر پیکان را با متن و تصویر مبحث تطبیق دهید.','reference':src}}
 return out

def build(path,toc=None):
 pages=source_pages();o=outline();cfg=H.HN_SESSIONS['hn10'];book=Book(path,'جزوهٔ مادر آناتومی سر و گردن — جلسهٔ ۱۰',footer='HumsYar · جزوهٔ مادر سر و گردن · جلسهٔ ۱۰',subject='جزوهٔ مادر')
 book.measure_idcard=True;book.keep_parenthesized_latin=True;book.block_trace=[];book.trace_topic=''
 SHELL.opening(book,10,o,toc);book.h1('اسکالپ و ناحیهٔ تمپورال',anchor='chapter',kicker='جلسهٔ دهم');book.para('منبع درس: دکتر میرزایی، گروه تشریح دانشگاه علوم پزشکی هرمزگان.');book.source_line('جزوهٔ جلسهٔ ۱۰، صفحهٔ فایل ۱')
 graphs=graph_data();geometry=R.layouts(book,graphs);stats={'topics':{},'figures':[],'source_paragraphs':{}}
 for i,t in enumerate(o['topics'],1):
  book.trace_topic=t['topic_id'];card=[{'label':'جای این مبحث','text':t['title']},{'label':'هدف یادگیری','text':W.QUESTIONS[i]},{'label':'پیش‌نیاز','text':t['prereq']},{'label':'راهنمای خواندن شکل','text':W.GUIDES[i][0]}]
  H.topic_head(book,t,i,len(o['topics']),after=book.card_height(card)+35,part_labels=False);stats['topics'][t['topic_id']]={'page':book.page,'title':t['title']}
  book.label_card('شناسنامهٔ مبحث',card,kicker='قبل از شروع این مبحث بخوانید',footer=f'جزوهٔ جلسهٔ ۱۰، صفحهٔ فایل {i}')
  if i==7:book.callout('عبارت‌های بالینی در ادامه نقل درس‌اند؛ برای تصمیم‌گیری دربارهٔ بیمار یا انجام مداخله از آن‌ها به‌تنهایی استفاده نکنید.',kind='info',title='راهنمای خواندن متن درس')
  placed=set()
  def put(path,title,cite,guide):
   block={'type':'plate','book':'lecture','asset':str(path.relative_to(ROOT)),'title':title,'citation':cite,'src':cite,'fa_text':guide,'labels':[],'max_h':150,'min_img_h':65}
   H.render_blocks(book,[block],cfg);stats['figures'].append({'asset':str(path.relative_to(ROOT)),'sha256':R.sha(path),'topic':t['topic_id'],'source':cite})
  paras=[x.strip() for x in pages[i].splitlines() if x.strip()];stats['source_paragraphs'][str(i)]=len(paras)
  for para in paras:
   H.render_blocks(book,[{'type':'p','text':para,'src':f'جزوهٔ جلسهٔ ۱۰، صفحهٔ فایل {i}'}],cfg)
   for num,physical,anchor,guide in FIGS[i]:
    if anchor in para and num not in placed:
     put(ROOT/f'headneck/images/hn10_candidates/lecture_{num}_p{physical:02}.png','تصویر جزوه — '+t['title'],f'جزوهٔ جلسهٔ ۱۰، صفحهٔ فایل {physical}، شکل {"۴" if num.startswith("04") else "۵" if num.startswith("05") else num}',guide);placed.add(num)
  if placed!={x[0] for x in FIGS[i]}:raise ValueError(f'figure anchor missing topic {i}: {placed}')
  book.ensure(120);book.callout(W.REF[i][1],kind='info',title='توضیح آموزشی — جدا از متن جزوه');book.source_line(W.REF[i][0])
  if i==4:
   book.callout('در متن درس، دو شریان پشت گوش با عبارت «از عقب به جلو» و سپس به ترتیب اوریکولار خلفی و اکسیپیتال آمده‌اند. جهت این ترتیب را با نمای نتر و جهت گوش مقایسه کنید؛ این مورد برای بازبین باز می‌ماند.',kind='info',title='ابهام برای بازبین');book.source_line('جزوهٔ جلسهٔ ۱۰، صفحهٔ فایل ۴؛ نتر، پلیت ۲۴، صفحهٔ فایل ۷۶')
  if i==7:
   book.callout('جمله‌های مطلق دربارهٔ پخش‌نشدن خونریزی زیرپوستی و حفظ بخش‌های بدون رگ، عین محتوای درس‌اند؛ محدودهٔ اعتبار و تعبیر بالینی آن‌ها باید بررسی شود و نباید به‌تنهایی راهنمای درمان تلقی شوند.',kind='info',title='پرسش باز برای بازبین');book.source_line('جزوهٔ جلسهٔ ۱۰، صفحهٔ فایل ۷')
  for name,n,plate,guide in REFS.get(i,[]):put(ROOT/f'headneck/images/hn10_refs/{name}.png','نمای مرجع — '+t['title'],f'نتر، اطلس آناتومی انسان، ویراست ۸، پلیت {plate}، صفحهٔ فایل {n}',guide)
  graph={2:'layers',5:'veins'}.get(i)
  if graph:R.draw_graph(book,graphs[graph],geometry[graph],force_page=False)
  book.note_box(24,title='یادداشت جزوه‌نویس');book.handoff_sheet('برگهٔ تحویل — مبحث '+str(i)+' — '+t['title'],f'جزوهٔ جلسهٔ ۱۰، صفحهٔ فایل {i}؛ '+W.REF[i][0],W.GUIDES[i],W.REF[i][1],kicker='برای تکمیل جزوه‌نویس',note='پرسش باز: '+W.QUESTIONS[i],writer_name=True)
 book.new_page();book.h1('جمع‌بندی و چک‌لیست',anchor='hn-summary',kicker='پایان جلسه')
 rows=[['مبحث '+K.fa_digits(str(i))+' — '+t['title'],W.GUIDES[i][0],'☐'] for i,t in enumerate(o['topics'],1)]
 H.emit_table(book,['چک‌لیست خودآزمایی','می‌توانم این را توضیح دهم؟','☐'],rows,widths=[K.CONTENT_W*.32,K.CONTENT_W*.56,K.CONTENT_W*.12],caption='چک‌لیست خودآزمایی جلسهٔ ۱۰',size=8.2)
 if book.missing_assets:raise ValueError(book.missing_assets)
 SHELL.next_section(book,10);SHELL.back(book,10);book.save();stats['pages']=book.page;return book.heading_pages,stats

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT/'HumsYar_HeadNeck_Jalase10_WRITER_FINAL.pdf');out=p.parse_args().out.resolve();out.parent.mkdir(parents=True,exist_ok=True)
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

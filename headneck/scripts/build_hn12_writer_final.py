"""Session 12 booklet from the typed lecture and locally inspected atlas images."""
from __future__ import annotations
import argparse,json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'render'),str(Path(__file__).parent)]
import pymupdf
import build_headneck as H
import build_hn01_updated_review as R
import writer_shell as SHELL
K=H.K
OUT=ROOT/'.cache/hn12_writer_update'
TITLES=['منشأ دستگاه اسکلتی و سومیت‌ها','نوروکرانیوم غشایی و جمجمهٔ نوزاد','کندروکرانیوم و ویسروکرانیوم','صورت و ساختمان قوس‌های حلقی','قوس‌های حلقی و مشتقات آن‌ها','بن‌بست حلقی اول','بن‌بست‌های دوم، سوم و چهارم','شکاف‌های حلقی و نکات بالینی']
GROUPS=[[1],[2,3],[4],[5,6],[7,8],[9],[10,11],[12,13,14]]
GUIDES=[['سومیت و اسکلروتوم را در تصویر مقطع نسبت به لولهٔ عصبی پیدا کنید.','تمایز مزانشیم را از مسیرهای منشأ آن تفکیک کنید.','موقعیت سومیت در رویان را با برش مقایسه کنید.'],['منشأ نوروکرانیوم غشایی و مراحل استخوانی‌شدن را دنبال کنید.','درزها و ملاج‌های قدامی و خلفی را با نمای فوقانی شناسایی کنید.','ملاج‌های طرفی را در نمای جانبی پیدا کنید.'],['ناحیهٔ جلوی نوتوکورد و پشت آن را با نقشهٔ قاعده مقایسه کنید.','شکاف خارجی و بن‌بست داخلی را در نمای رویان تمیز دهید.','توالی آغاز قوس‌ها را با متن پی بگیرید.'],['برجستگی‌های صورت را نسبت به استومودئوم در نمای قدامی پیدا کنید.','هستهٔ قوس، پوشش‌های داخلی و خارجی و عصب آن را جدا کنید.','اجزای غضروفی، عصبی و عروقی را در شکل دنبال کنید.'],['غضروف، عصب و عضلات قوس‌های اول تا ششم را کنار هم مقایسه کنید.','مکل و رایچرت را در نمای رنگی جداگانه دنبال کنید.','مشتقات هیوئید و حنجره را نسبت به قوس‌ها ببینید.'],['تماس شکاف اول و بن‌بست اول را از مسیر لوله و حفرهٔ گوش میانی جدا کنید.','نمای قدامی و جانبی بن‌بست‌ها را با هم مقایسه کنید.','برچسب‌های رویان و محل تیروئید را بیابید.'],['بال پشتی و شکمی بن‌بست سوم را با مهاجرت تیموس مقایسه کنید.','پاراتیروئید فوقانی و تحتانی را در تصویر هفتهٔ پنجم و هفتم دنبال کنید.','بن‌بست چهارم و جسم اولتیموبرانشیال را مشخص کنید.'],['رشد قوس دوم روی شکاف‌ها و ایجاد سینوس گردنی را دنبال کنید.','محل کیست و مسیر فیستول را با استرنوکلیدوماستوئید مقایسه کنید.','نمونهٔ بالینی را صرفاً به‌عنوان تصویر آموزشی بخوانید.']]
REFS={2:[('netter_87','نتر، ویراست ۸، پلیت ۳۵، صفحهٔ فایل ۸۷','در جمجمهٔ نوزاد نمای جانبی و فوقانی و محل ملاج‌ها را با تصاویر اصل مقایسه کنید.')],5:[('netter_124','نتر، ویراست ۸، پلیت ۷۲، صفحهٔ فایل ۱۲۴','این نمای آناتومی بالغ، عضلات جونده و موقعیت آن‌ها را نشان می‌دهد؛ تصویر جنینی نیست.')],6:[('netter_202','نتر، ویراست ۸، پلیت ۱۵۰، صفحهٔ فایل ۲۰۲','شاخه‌های عصب فاسیال و ساختارهای گوش را در نمای آناتومی بالغ پیدا کنید؛ نقشهٔ مشتقات بن‌بست نیست.')],7:[('netter_213','نتر، ویراست ۸، پلیت ۱۶۱، صفحهٔ فایل ۲۱۳','نمای مسیر اعصاب جمجمه‌ای را با ناحیهٔ حلق و گوش مقایسه کنید؛ تصویر جنینی نیست.')]}
FIG_GUIDES={
'somite':'دیوارهٔ شکمی سومیت را در کنار نوتوکورد و شیار عصبی ببینید.',
'somite_development':'درماتوم و اسکلروتوم را در دو سوی سومیت نسبت به لولهٔ عصبی مقایسه کنید.',
'embryo_somites':'اولین سومیت گردنی و برجستگی‌های حلقی را در نمای جانبی رویان پیدا کنید.',
'skeletal_origins':'استخوان‌های آبی و قرمز و ساختارهای زرد را با راهنمای منشأ در زیرنویس اصل تطبیق دهید.',
'skull_ossification':'ناحیهٔ آیندهٔ ملاج قدامی و درز کرونال و مراکز استخوانی جمجمه را مشخص کنید.',
'anterior_posterior_fontanelles':'ملاج قدامی و خلفی را در اتصال درزهای کرونال، ساژیتال و لامبدوئید دنبال کنید.',
'sphenoid_mastoid_fontanelles':'ملاج‌های اسفنوئیدی و ماستوئیدی را در دو انتهای طرفی جمجمه پیدا کنید.',
'chondrocranium':'بخش آبی جلوی هیپوفیز و بخش قرمز خلف آن را با قاعدهٔ جمجمه مقایسه کنید.',
'arches_pouches_vessels':'بن‌بست و شکاف اول و قوس آئورتی را در کنار رویان و حلق بیابید.',
'stomodeum':'استومودئوم را زیر مغز پیشین و میان برجستگی‌های حلقی ببینید.',
'facial_prominences':'زائدهٔ فرونتونازال، برجستگی ماگزیلاری و بخش مندیبولار قوس اول را تفکیک کنید.',
'arch_components':'غضروف، عصب و شریان داخل هر قوس را در کنار لولهٔ عصبی مقایسه کنید.',
'arch_innervation':'شاخه‌های V و اعصاب VII، IX و X را به ترتیب روی قوس‌های حلقی پیدا کنید.',
'arch_cartilages':'غضروف مکل، ساختارهای قوس دوم و بخش‌های هیوئید و حنجره را به ترتیب رنگ دنبال کنید.',
'embryonic_arch_cartilages':'غضروف مکل را در قوس مندیبولار نسبت به قوس هیوئید و شکاف حلقی ببینید.',
'arch_derivatives':'استخوانچه‌های گوش، زائدهٔ استیلوئید و هیوئید را نسبت به استخوان‌های صورت پیدا کنید.',
'pharyngeal_pouches':'بن‌بست اول را نسبت به استومودئوم، حلق و زائدهٔ تیروئیدی در نمای جانبی دنبال کنید.',
'pouches_anterior_view':'چهار بن‌بست شماره‌دار و زائدهٔ تیروئیدی را در نمای قدامی حلق بیابید.',
'pouches_5_6_weeks':'مبدأ تیموس و پاراتیروئیدها را در بن‌بست‌های سوم و چهارم دنبال کنید.',
'pouch_development':'جابجایی تیموس و پاراتیروئیدهای تحتانی را از هفتهٔ پنجم تا هفتم مقایسه کنید.',
'pouches_median_section':'بازشدگی بن‌بست اول و بازشدگی‌های دوم تا چهارم را در برش میانی پیدا کنید.',
'grooves_6_7_weeks_a':'شکاف اول را از قوس دوم و قوس‌های سوم و چهارم در سینوس گردنی جدا کنید.',
'grooves_6_7_weeks_b':'لالهٔ گوش و مجرای گوش بیرونی را نسبت به زوائد بینی و فیلتروم ببینید.',
'pouch_groove_anomalies':'ستون منشأ را با خطوط منتهی به بقایا و غدد در گردن مقایسه کنید.',
'cervical_cyst_diagram':'کیست و فیستول خارجی را نسبت به عضلهٔ استرنوکلیدوماستوئید و لوزه پیدا کنید.',
'cervical_cyst_photo':'محل برجستگی طرفی گردن را با نمای شماتیک مقایسه کنید؛ تصویر به‌تنهایی ابزار تشخیص نیست.'}
class Book(R.ReviewBook):
 def source_line(self,s):super().source_line(str(s).replace('PDF','فایل'))
def get_pages():
 out={}
 for f in sorted((ROOT/'headneck/content/session12').glob('source_page*.txt')):
  for n,body in re.findall(r'صفحهٔ\s*([۰-۹]+)\s*اصل[^\n]*\n(.*?)(?=\nصفحهٔ\s*[۰-۹]+\s*اصل|\Z)',f.read_text(),re.S):
   n=int(n.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')))
   if n in out:raise ValueError(f'duplicate {n}')
   out[n]=body.strip()
 if sorted(out)!=list(range(1,15)):raise ValueError(f'pages {sorted(out)}')
 return out

def outline():
 return {'session':'hn12','title':'جنین‌شناسی جمجمه','topics':[{'topic_id':f'hn12-T{i:02}','title':title,'pages':GROUPS[i-1],'gist':GUIDES[i-1][0],'prereq':'استخوان‌ها و عضلات سر و گردن و آناتومی پایهٔ حلق'} for i,title in enumerate(TITLES,1)]}

def graphs():
 data={
 'arches':('قوس و عصب همراه در متن درس',['قوس اول','مندیبولار V','قوس دوم','فاسیال VII','قوس سوم','گلوسوفارنژیال IX','قوس چهارم','حنجره‌ای فوقانی واگ','قوس ششم','حنجره‌ای راجعه واگ'],[(0,1,'عصب عضلات'),(2,3,'عصب عضلات'),(4,5,'عصب عضله'),(6,7,'عصب عضلات'),(8,9,'عصب عضلات')],'جزوهٔ جلسهٔ ۱۲، صفحهٔ فایل ۸'),
 'pouches':('بال‌های بن‌بست سوم و چهارم',['بن‌بست سوم','بال پشتی','پاراتیروئید تحتانی','بال شکمی','تیموس','بن‌بست چهارم','بخش پشتی','پاراتیروئید فوقانی','بخش شکمی','جسم اولتیموبرانشیال'],[(0,1,'تقسیم'),(1,2,'تمایز'),(0,3,'تقسیم'),(3,4,'تمایز'),(5,6,'تقسیم'),(6,7,'تمایز'),(5,8,'تقسیم'),(8,9,'تمایز')],'جزوهٔ جلسهٔ ۱۲، صفحهٔ فایل ۱۰ و ۱۱')}
 return {k:{'diagram':{'title':title,'nodes':[{'id':f'n{i}','text':t} for i,t in enumerate(names)],'edges':[[f'n{a}',f'n{b}'] for a,b,_ in links],'edge_labels':{f'n{a}:n{b}':lab for a,b,lab in links},'reading_task':'پیکان‌ها را با متن اصل و شکل همین مبحث تطبیق دهید.','reference':cite}} for k,(title,names,links,cite) in data.items()}

def build(path,toc=None):
 pages=get_pages();o=outline();cfg=H.HN_SESSIONS['hn12'];book=Book(path,'جزوهٔ مادر آناتومی سر و گردن — جلسهٔ ۱۲',footer='HumsYar · جزوهٔ مادر سر و گردن · جلسهٔ ۱۲',subject='جزوهٔ مادر');book.measure_idcard=True;book.keep_parenthesized_latin=True;book.block_trace=[];book.trace_topic=''
 SHELL.opening(book,12,o,toc);book.h1('جنین‌شناسی جمجمه',anchor='chapter',kicker='جلسهٔ دوازدهم');book.para('منبع درس: دکتر میرزایی، گروه تشریح دانشگاه علوم پزشکی هرمزگان.');book.source_line('جزوهٔ جلسهٔ ۱۲، صفحهٔ فایل ۱')
 figs=json.loads((ROOT/'headneck/reports/hn12_evidence/figure_candidates.json').read_text())['figures'];graphs_=graphs();geometry=R.layouts(book,graphs_);stats={'topics':{},'figures':[],'source_paragraphs':{}}
 for i,t in enumerate(o['topics'],1):
  book.trace_topic=t['topic_id'];guides=GUIDES[i-1];card=[{'label':'جای این مبحث','text':t['title']},{'label':'هدف یادگیری','text':guides[0]},{'label':'پیش‌نیاز','text':t['prereq']},{'label':'راهنمای خواندن شکل','text':guides[1]}]
  H.topic_head(book,t,i,len(o['topics']),after=book.card_height(card)+35,part_labels=False);stats['topics'][t['topic_id']]={'page':book.page,'title':t['title']};label=' و '.join(map(str,t['pages']));book.label_card('شناسنامهٔ مبحث',card,kicker='قبل از شروع این مبحث بخوانید',footer='جزوهٔ جلسهٔ ۱۲، صفحهٔ فایل '+label)
  def put(path,cite,guide,title):
   H.render_blocks(book,[{'type':'plate','book':'lecture','asset':str(path.relative_to(ROOT)),'title':title,'citation':cite,'src':cite,'fa_text':guide,'labels':[],'max_h':110,'min_img_h':(95 if path.name=='netter_87.png' else 65)}],cfg);stats['figures'].append({'asset':str(path.relative_to(ROOT)),'sha256':R.sha(path),'topic':t['topic_id'],'source':cite})
  for n in t['pages']:
   paras=[x.strip() for x in pages[n].splitlines() if x.strip()];stats['source_paragraphs'][str(n)]=len(paras);placed=set()
   for para in paras:
    H.render_blocks(book,[{'type':'p','text':para,'src':f'جزوهٔ جلسهٔ ۱۲، صفحهٔ فایل {n}'}],cfg)
    if para.startswith('شکل ('):
     m=re.match(r'شکل \(([۰-۹]+)\)',para)
     if m:
      num=str(int(m.group(1).translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789'))));matches=[f for f in figs if f['source_page']==n and f['printed_figure']==num]
      for f in matches:
       put(ROOT/f['file'],f'جزوهٔ جلسهٔ ۱۲، صفحهٔ فایل {n}، شکل {K.fa_digits(num)}',FIG_GUIDES[f['name']],'تصویر جزوه — '+t['title']);placed.add(f['file'])
   expected={f['file'] for f in figs if f['source_page']==n}
   if placed!=expected:raise ValueError(f'page {n} missing figure: {expected-placed}')
  if i==5:
   book.callout('در اصل، جمله‌ای دربارهٔ استخوان‌سازی مندیبل و غضروف مکل آمده است. نسبت آن‌ها را با یک منبع جنین‌شناسی معتبر مستقل بررسی کنید؛ عبارت درس بدون اصلاح پنهان حفظ شده است.',kind='info',title='پرسش باز برای بازبین');book.source_line('جزوهٔ جلسهٔ ۱۲، صفحهٔ فایل ۸')
  if i==6:
   book.callout('در متن اصل، عبارت مربوط به تماس شکاف و بن‌بست اول و تشکیل سوراخ گوش نیازمند توجه به مرجع ضمیر است؛ مسیر هر کدام را با تصویر و منبع جنین‌شناسی مستقلاً مقابله کنید.',kind='info',title='پرسش باز برای بازبین');book.source_line('جزوهٔ جلسهٔ ۱۲، صفحهٔ فایل ۹')
  if i==8:
   book.callout('در زیرنویس اصل برای شکل‌های ۲۱ و ۲۲ سن ۶–۷ هفته آمده؛ نوشتهٔ انگلیسی داخل خود شکل‌ها را نیز جداگانه بخوانید.',kind='info',title='خواندن دقیق تصویر');book.source_line('جزوهٔ جلسهٔ ۱۲، صفحهٔ فایل ۱۲')
  for name,cite,guide in REFS.get(i,[]):put(ROOT/f'headneck/images/hn12_refs/{name}.png',cite,guide,'نمای مرجع — '+t['title'])
  graph={5:'arches',7:'pouches'}.get(i)
  if graph:R.draw_graph(book,graphs_[graph],geometry[graph],force_page=False)
  book.note_box(24,title='یادداشت جزوه‌نویس');book.handoff_sheet('برگهٔ تحویل — مبحث '+str(i)+' — '+t['title'],'جزوهٔ جلسهٔ ۱۲، صفحهٔ فایل '+label,guides,'روابط شکل و متن را کنار هم مرور کنید.',kicker='برای تکمیل جزوه‌نویس',note='پرسش: '+guides[0],writer_name=True)
 book.new_page();book.h1('جمع‌بندی و چک‌لیست',anchor='hn-summary',kicker='پایان جلسه');rows=[['مبحث '+K.fa_digits(str(i))+' — '+t['title'],GUIDES[i-1][0],'☐'] for i,t in enumerate(o['topics'],1)];H.emit_table(book,['چک‌لیست خودآزمایی','می‌توانم این را توضیح دهم؟','☐'],rows,widths=[K.CONTENT_W*.32,K.CONTENT_W*.56,K.CONTENT_W*.12],caption='چک‌لیست خودآزمایی جلسهٔ ۱۲',size=8.2)
 if book.missing_assets:raise ValueError(book.missing_assets)
 SHELL.next_section(book,12);SHELL.back(book,12);book.save();stats['pages']=book.page;return book.heading_pages,stats

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'pdf/HumsYar_HeadNeck_Jalase12_WRITER_FINAL.pdf');out=p.parse_args().out.resolve();out.parent.mkdir(parents=True,exist_ok=True)
 first,_=build(out);second,stats=build(out,first)
 if first!=second:raise ValueError('unstable toc')
 H.drop_trailing_blank_page(out)
 # Normalize the generated PDF streams to binary Flate rather than ASCII85.
 tmp=out.with_suffix('.normalized.pdf')
 with pymupdf.open(out) as doc:
  for x in range(1,doc.xref_length()):
   if doc.xref_is_stream(x) and 'ASCII85Decode' in doc.xref_get_key(x,'Filter')[1]:
    doc.update_stream(x,doc.xref_stream(x),compress=True)
  doc.save(tmp,garbage=4,deflate=True,clean=True)
 tmp.replace(out)
 OUT.mkdir(parents=True,exist_ok=True);qa={'outside_spans':[],'empty_pages':[],'leaks':[],'body_near_footer':[]};bad=re.compile(r'IMG[-ـ]?\d+|SRC[-ـ]?\d+|hn\d\d[-–]T\d+|JSON|BLOCKED|NOT_YET|PENDING|INTEGRATED|غیرنهایی|پیش‌نویس|هوش مصنوعی',re.I)
 with pymupdf.open(out) as doc:
  for n,page in enumerate(doc,1):
   text=unicodedata.normalize('NFKC',page.get_text()).replace('\u200c','')
   if bad.search(text):qa['leaks'].append({'page':n,'text':bad.search(text).group()})
   if not text.strip() and not page.get_images():qa['empty_pages'].append(n)
   for b in page.get_text('dict',clip=pymupdf.INFINITE_RECT())['blocks']:
    for line in b.get('lines',[]):
     for span in line['spans']:
      x0,y0,x1,y1=span['bbox']
      if x0<-.5 or y0<-.5 or x1>page.rect.width+.5 or y1>page.rect.height+.5:qa['outside_spans'].append({'page':n,'text':span['text']})
      if n>1 and span['size']>=8 and y1>789 and y0<795:qa['body_near_footer'].append({'page':n,'text':span['text']})
   page.get_pixmap(matrix=pymupdf.Matrix(1.1,1.1),alpha=False).save(str(OUT/f'page-{n:03}.jpg'),jpg_quality=85)
  stats['bookmarks']=doc.get_toc()
 stats.update(file=str(out.relative_to(ROOT)),sha256=R.sha(out),bytes=out.stat().st_size,qa=qa);(OUT/'manifest.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'pages':stats['pages'],'figures':len(stats['figures']),'sha256':stats['sha256'],'qa':qa},ensure_ascii=False,indent=2))
 if any(qa.values()):raise SystemExit('QA failed')
if __name__=='__main__':main()

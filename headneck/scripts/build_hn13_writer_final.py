"""Build session 13 from all four practical slide sets and selected local atlas plates."""
from __future__ import annotations
import argparse,base64,json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'render'),str(Path(__file__).parent)]
import pymupdf
import build_headneck as H
import build_hn01_updated_review as R
import writer_shell as SHELL
import hn13_writer_copy as W
K=H.K;OUT=ROOT/'.cache/hn13_writer_update'
PART_NAME={'1':'Practical anatomy 1.pdf','3':'Practical anatomy 3 .pdf','4':'Practical anatomy 4.pdf','5':'Practical anatomy اصلاحیه 5 .pdf'}
class Book(R.ReviewBook):
 def source_line(self,s):super().source_line(str(s).replace('PDF','فایل'))
def inventory():
 data=json.loads((ROOT/'headneck/reports/hn13_evidence/source_inventory.json').read_text())
 return {s['part']:s for s in data['sources']}
def labels(page):
 # Preserve all source spans in source extraction order. Adjacent lines at the
 # same x coordinate are joined only when their boxes directly touch vertically.
 spans=[s for s in page['spans'] if 'Dr Mirzaei' not in s['text'] and 'Hormozgan medical science university' not in s['text']]
 out=[];last=None
 for sp in spans:
  t=' '.join(sp['text'].split());b=sp['bbox'];
  if last is not None and abs(last[0]-b[0])<1 and -1<=b[1]-last[3]<=5:
   out[-1]+=' '+t
  else:out.append(t)
  last=b
 return out

def outline():
 return {'session':'hn13','title':'آناتومی عملی سر و گردن','topics':[{'topic_id':f'hn13-T{i:02}','title':title,'pages':[], 'gist':W.GUIDES[i-1][0], 'prereq':'استخوان‌ها، عضلات و روابط گردن در جلسات پیشین'} for i,title in enumerate(W.TITLES,1)]}
def graphs():
 specs={
 'mandible':('جهت‌یابی فک پایین در نماهای عملی',['مندیبل','سطح خارجی','سوراخ منتال','سطح داخلی','سوراخ مندیبولار','راموس','زائدهٔ کرونوئید','زائدهٔ کندیلی'],[(0,1,'نما'),(1,2,'نشانه'),(0,3,'نما'),(3,4,'نشانه'),(0,5,'بخش'),(5,6,'زائده'),(5,7,'زائده')],'اسلاید عملی ۱، صفحات فایل ۶–۹؛ نتر، پلیت ۳۹، صفحهٔ فایل ۹۱'),
 'triangles':('مثلث‌های قدامی و خلفی نسبت به جناغی‌چنبری‌پستانی',['استرنوکلیدوماستوئید','ناحیهٔ قدامی','کاروتید','زیرآرواره‌ای','عضلانی','زیرچانه‌ای','ناحیهٔ خلفی','پس‌سری','اوموکلاویکولار'],[(0,1,'سمت قدام'),(1,2,'مثلث'),(1,3,'مثلث'),(1,4,'مثلث'),(1,5,'مثلث'),(0,6,'سمت خلف'),(6,7,'مثلث'),(6,8,'مثلث')],'اسلاید عملی اصلاحیه، صفحات فایل ۱۴، ۱۵، ۲۰ و ۲۱؛ نتر، پلیت ۵۴، صفحهٔ فایل ۱۰۶')}
 return {k:{'diagram':{'title':t,'nodes':[{'id':f'n{i}','text':v} for i,v in enumerate(names)],'edges':[[f'n{a}',f'n{b}'] for a,b,_ in edges],'edge_labels':{f'n{a}:n{b}':lab for a,b,lab in edges},'reading_task':'این روابط را با مدل‌های عملی و نماهای همان مبحث دنبال کنید.','reference':src}} for k,(t,names,edges,src) in specs.items()}
def citation(part,page):return 'اسلاید عملی «'+PART_NAME[part]+'»، صفحهٔ فایل '+str(page)

def build(path,toc=None):
 inv=inventory();assets=json.loads((ROOT/'headneck/reports/hn13_evidence/asset_manifest.json').read_text());figs={(x['part'],x['page']):x for x in assets['figures']};refs={x['page']:x for x in assets['references']};out=outline();cfg=H.HN_SESSIONS['hn13']
 book=Book(path,'جزوهٔ مادر آناتومی سر و گردن — جلسهٔ ۱۳',footer='HumsYar · جزوهٔ مادر سر و گردن · جلسهٔ ۱۳',subject='جزوهٔ مادر عملی');book.measure_idcard=True;book.keep_parenthesized_latin=True;book.block_trace=[];book.trace_topic=''
 SHELL.opening(book,13,out,toc);book.h1('آناتومی عملی سر و گردن',anchor='chapter',kicker='جلسهٔ سیزدهم');book.para('منبع درس: اسلایدهای عملی دکتر میرزایی، دانشگاه علوم پزشکی هرمزگان. چهار فایل موجود با ذکر نام و شمارهٔ صفحهٔ فایل استفاده شده‌اند.');book.source_line('فایل‌های عملی ۱، ۳، ۴ و اصلاحیه')
 book.h2('عنوان‌ها و نقشهٔ اسلایدهای عملی');
 for part in ['1','3','4','5']:
  page=inv[part]['pages'][1];terms=labels(page);H.render_blocks(book,[{'type':'p','text':' | '.join(terms),'src':citation(part,2)}],cfg)
 graphs_=graphs();geom=R.layouts(book,graphs_);stats={'topics':{},'figures':[],'typed_spans':{},'header_spans':{part:labels(inv[part]['pages'][1]) for part in inv}}
 for i,t in enumerate(out['topics'],1):
  guide=W.GUIDES[i-1];book.trace_topic=t['topic_id'];card=[{'label':'جای این مبحث','text':t['title']},{'label':'هدف یادگیری','text':guide[0]},{'label':'پیش‌نیاز','text':t['prereq']},{'label':'راهنمای خواندن شکل','text':guide[1]}];H.topic_head(book,t,i,len(out['topics']),after=book.card_height(card)+35,part_labels=False);stats['topics'][t['topic_id']]={'page':book.page,'title':t['title']}
  firstpart,firstpage=W.GROUPS[i-1][0];book.label_card('شناسنامهٔ مبحث',card,kicker='قبل از شروع این مبحث بخوانید',footer=citation(firstpart,firstpage))
  book.callout(W.GLOSS[i-1],kind='info',title='واژگان راهنما — افزودهٔ آموزشی');n,plate=W.REFS[i][0];book.source_line(f'نتر، ویراست ۸، پلیت {plate}، صفحهٔ فایل {n}')
  def put(asset,title,cite,guide,maxh=115):
   path=ROOT/asset;block={'type':'plate','book':'lecture','asset':asset,'title':title,'citation':cite,'src':cite,'fa_text':guide,'labels':[],'max_h':maxh,'min_img_h':65};H.render_blocks(book,[block],cfg);stats['figures'].append({'asset':asset,'sha256':R.sha(path),'topic':t['topic_id'],'source':cite})
  for part,pn in W.GROUPS[i-1]:
   page=inv[part]['pages'][pn-1];fig=figs[(part,pn)];src=citation(part,pn);ls=labels(page);stats['typed_spans'][f'{part}:{pn}']=ls
   put(fig['asset'],'مدل عملی — '+t['title'],src,W.PAGE_GUIDE[part][pn])
   book.para('برچسب‌های تایپ‌شدهٔ همین تصویر:');H.render_blocks(book,[{'type':'p','text':' | '.join(ls),'src':src}],cfg)
  if i==7:
   book.ensure(110);book.callout('در اسلاید صفحهٔ ۱۳ فایل عملی ۴ عنوان C6 و در صفحهٔ ۱۰ فایل اصلاحیه عنوان C7 آمده، در حالی که تصویر پایه در هر دو فایل یکسان است. هر دو عنوان همان‌طور که در اصل آمده حفظ شده‌اند. برای تعیین نام صحیح این نمونه، مقایسهٔ مستقل لازم است؛ پلیت ۴۴ نتر مهرهٔ C7 را جداگانه نشان می‌دهد.',kind='info',title='اختلاف برای بازبین');book.source_line('اسلاید عملی ۴، صفحهٔ فایل ۱۳؛ اسلاید عملی اصلاحیه، صفحهٔ فایل ۱۰؛ نتر، پلیت ۴۴، صفحهٔ فایل ۹۶')
  firstn,firstplate=W.REFS[i][0];book.callout(W.EXTRA[i-1],kind='info',title='توضیح آموزشی — جدا از اسلاید');book.source_line(f'نتر، ویراست ۸، پلیت {firstplate}، صفحهٔ فایل {firstn}')
  for n,plate in W.REFS[i]:
   src=f'نتر، اطلس آناتومی انسان، ویراست ۸، پلیت {plate}، صفحهٔ فایل {n}';put(refs[n]['asset'],'نمای مرجع — '+t['title'],src,guide[2],maxh=120)
  graph={2:'mandible',9:'triangles'}.get(i)
  if graph:R.draw_graph(book,graphs_[graph],geom[graph],force_page=False)
  book.note_box(24,title='یادداشت جزوه‌نویس');book.handoff_sheet('برگهٔ تحویل — مبحث '+str(i)+' — '+t['title'],citation(firstpart,firstpage)+f'؛ نتر، پلیت {firstplate}، صفحهٔ فایل {firstn}',guide,W.EXTRA[i-1],kicker='برای تکمیل جزوه‌نویس',note='پرسش: '+guide[0],writer_name=True)
 book.new_page();book.h1('جمع‌بندی و چک‌لیست',anchor='hn-summary',kicker='پایان جلسه');rows=[['مبحث '+K.fa_digits(str(i))+' — '+t['title'],W.GUIDES[i-1][0],'☐'] for i,t in enumerate(out['topics'],1)];H.emit_table(book,['چک‌لیست خودآزمایی','می‌توانم این را توضیح دهم؟','☐'],rows,widths=[K.CONTENT_W*.32,K.CONTENT_W*.56,K.CONTENT_W*.12],caption='چک‌لیست خودآزمایی جلسهٔ ۱۳',size=8.2)
 if book.missing_assets:raise ValueError(book.missing_assets)
 SHELL.back(book,13);book.save();stats['pages']=book.page;return book.heading_pages,stats

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'pdf/HumsYar_HeadNeck_Jalase13_WRITER_FINAL.pdf');dest=parser.parse_args().out.resolve();dest.parent.mkdir(parents=True,exist_ok=True)
 first,_=build(dest);second,stats=build(dest,first)
 if first!=second:raise ValueError('unstable toc')
 H.drop_trailing_blank_page(dest);tmp=dest.with_suffix('.normalized.pdf')
 with pymupdf.open(dest) as doc:
  for x in range(1,doc.xref_length()):
   if doc.xref_is_stream(x) and 'ASCII85Decode' in doc.xref_get_key(x,'Filter')[1]:
    filters=doc.xref_get_key(x,'Filter')[1]
    if 'DCTDecode' in filters:
     decoded=base64.a85decode(doc.xref_stream_raw(x),adobe=True)
     doc.update_stream(x,decoded,compress=False);doc.xref_set_key(x,'Filter','/DCTDecode')
    else:doc.update_stream(x,doc.xref_stream(x),compress=True)
  doc.save(tmp,garbage=4,deflate=True,clean=True)
 tmp.replace(dest);OUT.mkdir(parents=True,exist_ok=True);qa={'outside_spans':[],'empty_pages':[],'leaks':[],'body_near_footer':[]};bad=re.compile(r'IMG[-ـ]?\d+|SRC[-ـ]?\d+|hn\d\d[-–]T\d+|JSON|BLOCKED|NOT_YET|PENDING|INTEGRATED|غیرنهایی|پیش‌نویس|هوش مصنوعی',re.I)
 with pymupdf.open(dest) as doc:
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
   page.get_pixmap(matrix=pymupdf.Matrix(.9,.9),alpha=False).save(str(OUT/f'page-{n:03}.jpg'),jpg_quality=82)
  stats['bookmarks']=doc.get_toc()
 stats.update(file=str(dest.relative_to(ROOT)),sha256=R.sha(dest),bytes=dest.stat().st_size,qa=qa);(OUT/'manifest.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'pages':stats['pages'],'figures':len(stats['figures']),'sha256':stats['sha256'],'qa':qa},ensure_ascii=False,indent=2))
 if any(qa.values()):raise SystemExit('QA failed')
if __name__=='__main__':main()

"""Session two writer edition, preserving the original topic sequence and source blocks."""
from __future__ import annotations
import argparse, copy, hashlib, json, re, sys, unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'render'),str(Path(__file__).parent)]
import pymupdf
import build_hn01_updated_review as R
import hn02_writer_copy as W
K,H=R.K,R.H
OUT=ROOT/'.cache/hn02_writer_final'
BAD=re.compile(r'IMG[-ـ]?\d+|SRC[-ـ]?\d+|hn\d\d[-–]T\d+|C-\d{3}|JSON|BLOCKED|NOT_YET|PENDING|INTEGRATED|غیرنهایی|پیش‌نویس|رونویسی در حال مقابله|بازبینی علمی',re.I)

def clean(s):
 s=str(s).replace(' — رونویسی در حال مقابله','').replace('PDF','فایل').replace('صفحهٔ صفحه','صفحه')
 return re.sub(r'hn\d\d[-–]T\d+','مبحث مرتبط',s,flags=re.I)

def inputs():
 hist={r['file']:r for r in R.load('historical_sources.json')['files']}
 def get(name):
  r=hist[name];p=ROOT/r['workspace_file']
  if R.sha(p)!=r['sha256']:raise ValueError('Historical input changed: '+name)
  return json.loads(p.read_text())
 base=get('headneck/content/hn02_a.json')+get('headneck/content/hn02_b.json')
 outline=get('headneck/content/outline/hn02_topics.json')
 overlay=get('headneck/content/hn02_update.json')['topics']
 assets={r['asset']:r for r in R.load('restored_assets.json')}
 result={};n_overlay=0
 for topic in base:
  tid=topic['topic_id'];spec=overlay[tid];rows=[]
  for i,raw in enumerate(topic['blocks']):
   q=copy.deepcopy(raw);q['_origin']=f'base:{i}'
   if i==0:q['rows']+=copy.deepcopy(spec['card_rows'])
   rows.append(q)
   for j,extra in enumerate(spec['after'].get(str(i),[])):
    z=copy.deepcopy(extra);z['_origin']=f'overlay:{i}:{j}';rows.append(z);n_overlay+=1
  result[tid]=rows
 assert len(base)==len(outline['topics'])==21 and len(W.GUIDES)==21
 return base,result,outline,assets,n_overlay

class Book(R.ReviewBook):
 def source_line(self,s):super().source_line(clean(s))
 def h3(self,s,keep_with=46):super().h3(clean(s),keep_with=keep_with)

def cover(book):
 c=book.c
 for text,size,y,color in [('HumsYar · جزوهٔ مادر آناتومی',11,.86,K.TEAL_L),('آناتومی سر و گردن',29,.64,K.CARD),('جلسهٔ ۲',27,.565,K.CARD),('گونه، فک تحتانی، گیجگاهی و آهیانه',14,.475,K.TEAL_L),('نسخهٔ نهاییِ جزوه‌نویسی',14,.365,K.TEAL_L),('متن درس · تصاویر · جدول · نکته · راهنمای نویسنده',10,.30,K.CARD),('بر پایهٔ جزوهٔ درس، نتر و گری',10,.255,K.TEAL_L)]:
  K.draw_shaped(c,K.A4W/2,K.A4H*y,K.shape(text),'VazirB' if size>13 else 'Vazir',size,color,align='center')

def graph_data(outline):
 meanings={4:['استخوان حامل','شرکت در ساخت','اتصال با','استخوان حامل'],5:['دارای شاخهٔ','منشأ','تقسیم به'],12:['ورود به','امتداد','خروج شاخه از'],19:['اتصال در','مرز قدامی','مرز خلفی','اتصال به']}
 graphs={}
 for i,steps in W.PATHS.items():
  ids=[f'n{j}' for j in range(len(steps))];edges=[[ids[j],ids[j+1]] for j in range(len(ids)-1)]
  graphs[str(i)]={'diagram':{'title':outline['topics'][i-1]['title'],'nodes':[{'id':j,'text':v} for j,v in zip(ids,steps)],'edges':edges,'edge_labels':{a+':'+b:lab for (a,b),lab in zip(edges,meanings[i])},'reading_task':'این مسیر را با متن و شکل همین مبحث دنبال کنید.','reference':'جزوهٔ درس، جلسهٔ ۲، صفحهٔ فایل '+H.page_range(outline['topics'][i-1].get('pages',[]))}}
 return graphs

def build(path,toc=None):
 base,plan,outline,assets,n_overlay=inputs();cfg=H.HN_SESSIONS['hn02']
 book=Book(path,'جزوهٔ مادر آناتومی سر و گردن — جلسهٔ ۲',footer='HumsYar · جزوهٔ مادر سر و گردن · جلسهٔ ۲',subject='نسخهٔ نهایی جزوه‌نویسی')
 book.measure_idcard=True;book.keep_parenthesized_latin=True;book.block_trace=[];book.trace_topic=''
 book.dark_page(cover,reuse_blank_page=True)
 book.h1('راهنمای استفادهٔ جزوه‌نویس')
 book.para('متن درس، شکل‌های مربوط، توضیح‌های آموزشی، جدول، تمرین و راهنمای نگارش در ترتیب مباحث جلسه قرار گرفته‌اند. متن درس و توضیح تکمیلی از هم جدا هستند؛ منبع هر متن یا شکل در کنار همان بخش آمده است.')
 book.para('ابتدا شناسنامه و متن درس را بخوانید؛ سپس جهت نمای شکل، مقایسه‌ها و مسیرها را با متن مرتبط کنید. در پایان هر مبحث برگهٔ تحویل و در پایان جلسه چک‌لیست مرور قرار دارد.')
 book.new_page();book.h1('فهرست مباحث')
 for i,t in enumerate(outline['topics'],1):book.toc_row(K.fa_digits(str(i)),t['title'],(toc or {}).get(t['topic_id'],'—'),step=23)
 book.toc_row('پ','جمع‌بندی، چک‌لیست و برگهٔ تحویل',(toc or {}).get('hn-summary','—'),step=23)
 book.new_page();book.h1('از گونه تا آهیانه',anchor='chapter',kicker='جلسهٔ دوم');book.para(cfg['outcome'])
 graphs=graph_data(outline);geometry=R.layouts(book,graphs)
 stats={'base_blocks':sum(len(t['blocks']) for t in base),'overlay_blocks':n_overlay,'topics':{},'figures':[],'source_text_sha256':{}}
 for idx,t in enumerate(outline['topics'],1):
  tid=t['topic_id'];blocks=plan[tid];book.trace_topic=tid;card=copy.deepcopy(blocks[0]);card_h=book.card_height(card['rows'],footer=clean(card.get('footer','')))
  H.topic_head(book,t,idx,len(outline['topics']),after=card_h+35)
  stats['topics'][tid]={'page':book.page,'title':t['title']};book.label_card('شناسنامهٔ مبحث',card['rows'],kicker=card.get('kicker',''),footer=clean(card.get('footer','')))
  handoff=None;fig=0
  for pos,raw in enumerate(blocks[1:],1):
   q=copy.deepcopy(raw);origin=q.pop('_origin');kind=q['type']
   if origin.startswith('base:') and kind in ('p','ul','ol'):
    stats['source_text_sha256'][tid+':'+origin]=hashlib.sha256(json.dumps(q.get('text',q.get('items')),ensure_ascii=False).encode()).hexdigest()
   if tid=='hn02-T20' and origin=='base:1':
    # The earlier mother edition scrambled this sentence; use the separately
    # retained lecture-page transcription, without changing historical inputs.
    quote=next(x['text'] for x in blocks if x.get('title')=='مقابله با متن منبع — افزوده')
    q['text']=quote.split('«',1)[1].split('»',1)[0]
   if tid=='hn02-T20' and q.get('title')=='مقابله با متن منبع — افزوده':continue
   if kind=='handoff':handoff=q;continue
   if kind=='callout' and q.get('title')=='یادداشت برای بازبینی علمی':continue
   if kind=='callout' and q.get('title')=='تعارض قابل بررسی در خود جزوه':
    q['title']='دو عبارت دربارهٔ زمان جوش‌خوردن';q['text']='در صفحهٔ ۱۳ جزوه عبارت «سی سالگی» آمده است؛ در صفحهٔ ۱۴ جوش‌خوردن دو نیمه در سال‌های اول تا سوم پس از تولد توصیف می‌شود. هر دو عبارت را همراه صفحهٔ مربوط بخوانید.';q['src']='جزوهٔ درس، جلسهٔ ۲، صفحه‌های فایل ۱۳ و ۱۴'
   if q.get('title')=='شناسنامهٔ جزوهٔ اصلی':q['text']=q['text'].replace(' بخشی از فهرست در تصویر منبع پوشیده شده است.','')
   if q.get('title')=='تکمیل متن منبع — افزوده':q['title']='عبارت کنار شکل';q['text']='«دو تا» — عبارت جداگانهٔ کنار شکل در صفحهٔ ۱۳ جزوه.'
   if q.get('title')=='مقابله با متن منبع — افزوده':q['title']='متن صفحهٔ ۲۷ جزوه';q['text']=q['text'].replace('نقل بخش مربوط از صفحهٔ ۲۷: ','').replace(' متن نسخهٔ پایه در بالا حفظ شده است.','')
   for key in ('src','citation','title','footer','kicker'):
    if key in q:q[key]=clean(q[key])
   if kind=='plate':
    fig+=1;a=assets[q['asset']];p=ROOT/a['workspace_file']
    if R.sha(p)!=a['sha256']:raise ValueError('Figure asset changed: '+q['asset'])
    original=q['asset'];q['asset']=str(p);q['title']='شکل '+K.fa_digits(str(idx)+'–'+str(fig))+' — '+q['title']
    H.render_blocks(book,[q],cfg);stats['figures'].append({'topic':tid,'asset':original,'page':book.page,'sha256':a['sha256']});continue
   if kind=='h3':
    following=blocks[pos+1] if pos+1<len(blocks) else None
    book.h3(q['text'],keep_with=min(H._block_height(book,following)+25,book.usable_height()-90))
    if q.get('src'):book.source_line(q['src'])
    continue
   if kind=='ul':q['type']='ol'
   if tid=='hn02-T16' and origin=='base:12':q['display_start']=2;q['display_items']=[v.split('. ',1)[1] for v in q['items']]
   H.render_blocks(book,[q],cfg)
   if tid=='hn02-T11' and origin=='base:8':
    book.callout('در متن این بند نام عصب زبانی آمده است. در ادامهٔ درس، صفحهٔ ۱۲، شیار مایلوهایوئید در ارتباط با شاخهٔ مایلوهایوئید توصیف شده است؛ نام دو عصب و جای آن‌ها را جداگانه بنویسید.',kind='info',title='تفکیک نام عصب‌ها')
    book.source_line('جزوهٔ درس، جلسهٔ ۲، صفحه‌های فایل ۱۱ و ۱۲')
  source='جزوهٔ درس، جلسهٔ ۲، صفحه‌های فایل '+H.page_range(t.get('pages',[]))
  if idx in W.TABLES:
   cols,rows=W.TABLES[idx];need=book.table_needs(cols,rows,None,'جدول آموزشی مبحث',source,8.5)[3]
   book.h3('جدول مقایسه',keep_with=min(need+12,book.usable_height()-80));H.emit_table(book,cols,rows,caption='جدول آموزشی مبحث',src=source,size=8.5)
  guide,question,answer=W.GUIDES[idx]
  book.h3('راهنمای نگارش و خواندن شکل');book.para(guide);book.source_line(source)
  book.h3('پرسش و پاسخ آموزشی');book.para(question);book.callout(answer,title='پاسخ');book.source_line(source)
  if idx in W.PATHS:R.draw_graph(book,graphs[str(idx)],geometry[str(idx)],force_page=False)
  if handoff:
   book.note_box(24,title='یادداشت جزوه‌نویس')
   book.h3('برگهٔ تحویل به مسئول جزوه')
   book.label_card('چک‌لیست نگارش',[{'label':'پیش از تحویل','items':handoff['checklist'],'tick':True}],accent=K.AMBER,tint=K.AMBER_BG)
   question=str(handoff.get('question','')).removeprefix('پرسش باز:').strip()
   if question:book.para('پرسش تکمیلی برای نویسنده: '+clean(question))
 book.new_page();book.h1('جمع‌بندی، چک‌لیست و برگهٔ تحویل',anchor='hn-summary',kicker='پایان جلسه')
 book.para('برای هر مبحث، توضیح را بدون نگاه به متن بازیابی کنید و مربع را علامت بزنید؛ سپس متن، عنوان شکل، منبع و نام‌های فارسی و انگلیسی را برای تحویل مرور کنید.')
 rows=[['مبحث '+K.fa_digits(str(i))+' — '+t['title'],(t.get('gist') or t['title']).rstrip(' .')+'؟','☐'] for i,t in enumerate(outline['topics'],1)]
 H.emit_table(book,['چک‌لیست خودآزمایی','می‌توانم این را توضیح دهم؟','☐'],rows,widths=[K.CONTENT_W*.30,K.CONTENT_W*.58,K.CONTENT_W*.12],caption='چک‌لیست خودآزمایی جلسهٔ ۲',size=8.2)
 if book.missing_assets:raise ValueError(book.missing_assets)
 book.save();stats['pages']=book.page;return book.heading_pages,stats

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT/'HumsYar_HeadNeck_Jalase2_FINAL.pdf');args=p.parse_args();args.out.parent.mkdir(parents=True,exist_ok=True)
 first,_=build(args.out);second,stats=build(args.out,first)
 if first!=second:raise ValueError('Unstable table of contents')
 H.drop_trailing_blank_page(args.out);qa={'outside_spans':[],'empty_pages':[],'leaks':[],'body_near_footer':[]}
 with pymupdf.open(args.out) as doc:
  stats['pages']=len(doc)
  for n,page in enumerate(doc,1):
   txt=unicodedata.normalize('NFKC',page.get_text());hits=BAD.findall(txt)
   if hits:qa['leaks'].append({'page':n,'hits':hits})
   if not txt.strip() and not page.get_images():qa['empty_pages'].append(n)
   for b in page.get_text('dict',clip=pymupdf.INFINITE_RECT())['blocks']:
    for line in b.get('lines',[]):
     for span in line['spans']:
      x0,y0,x1,y1=span['bbox']
      if x0<-.5 or y0<-.5 or x1>page.rect.width+.5 or y1>page.rect.height+.5:qa['outside_spans'].append({'page':n,'text':span['text']})
      if n>1 and span['size']>=8 and y1>789 and y0<795:qa['body_near_footer'].append({'page':n,'text':span['text']})
   page.get_pixmap(matrix=pymupdf.Matrix(1.25,1.25),alpha=False).save(str(args.out.parent/f'page-{n:03}.jpg'),jpg_quality=88)
  stats['bookmarks']=doc.get_toc()
 stats.update(file=str(args.out.relative_to(ROOT)),sha256=R.sha(args.out),bytes=args.out.stat().st_size,qa=qa)
 (args.out.parent/'manifest.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'pages':stats['pages'],'figures':len(stats['figures']),'sha256':stats['sha256'],'qa':qa},ensure_ascii=False,indent=2))
 if any(qa.values()):raise SystemExit('QA failed; see manifest')
if __name__=='__main__':main()

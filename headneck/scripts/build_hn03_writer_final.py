"""Session three: preserve historical topic blocks, transcription and figures."""
from __future__ import annotations
import argparse,copy,hashlib,json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'render'),str(Path(__file__).parent)]
import pymupdf
import build_hn01_updated_review as R
import hn03_writer_copy as W
import hn_updates
K,H=R.K,R.H
OUT=ROOT/'.cache/hn03_writer_final'
BAD=re.compile(r'IMG[-ـ]?\d+|SRC[-ـ]?\d+|hn\d\d[-–]T\d+|JSON|BLOCKED|NOT_YET|PENDING|INTEGRATED|غیرنهایی|پیش‌نویس|رونویسی در حال مقابله',re.I)

def clean(s):
 s=str(s).replace('\\u200c','\u200c').replace('\\u200d','\u200d').replace(' — رونویسی در حال مقابله','').replace('PDF','فایل').replace('فایل فایل','فایل')
 return re.sub(r'hn\d\d[-–]T\d+','مبحث مرتبط',s,flags=re.I)
def decoded(v):
 if isinstance(v,str):return v.replace('\\u200c','\u200c').replace('\\u200d','\u200d')
 if isinstance(v,list):return [decoded(x) for x in v]
 if isinstance(v,dict):return {k:decoded(x) for k,x in v.items()}
 return v

def inputs():
 hist={r['file']:r for r in R.load('historical_sources.json')['files']}
 def get(name):
  r=hist[name];p=ROOT/r['workspace_file']
  if R.sha(p)!=r['sha256']:raise ValueError('Historical input changed: '+name)
  return json.loads(p.read_text())
 base=get('headneck/content/hn03_a.json')+get('headneck/content/hn03_b.json')
 outline=get('headneck/content/outline/hn03_topics.json')
 overlay=get('headneck/content/hn03_update.json')['topics']
 transcription=get('headneck/content/hn03_source_transcription_wip.json')
 mapping=json.loads((ROOT/'.cache/master_01_06/historical/headneck/reports/HN_S03_TRANSCRIPTION_TOPIC_MAP_WIP.json').read_text())['topics']
 assets={r['asset']:r for r in R.load('restored_assets.json')}
 plan={};no=0;nt=0
 for t in base:
  tid=t['topic_id'];spec=overlay[tid];rows=[]
  for i,b in enumerate(t['blocks']):
   q=decoded(copy.deepcopy(b));q['_origin']=f'base:{i}'
   if i==0:q['rows']+=decoded(copy.deepcopy(spec['card_rows']))
   rows.append(q)
   if i==0:
    for j,x in enumerate(hn_updates._hn03_source_blocks(tid,mapping)):
     x=decoded(x);x['_origin']=f'transcription:{j}';rows.append(x);nt+=1
   for j,x in enumerate(spec['after'].get(str(i),[])):
    x=decoded(copy.deepcopy(x));x['_origin']=f'overlay:{i}:{j}';rows.append(x);no+=1
  plan[tid]=rows
 assert len(base)==len(outline['topics'])==len(W.GUIDES)==19 and set(mapping)==set(plan)
 return base,plan,outline,assets,no,nt,transcription

class Book(R.ReviewBook):
 def source_line(self,s):super().source_line(clean(s))
 def h3(self,s,keep_with=46):super().h3(clean(s),keep_with=keep_with)

def cover(book):
 for text,size,y,color in [('HumsYar · جزوهٔ مادر آناتومی',11,.86,K.TEAL_L),('آناتومی سر و گردن',29,.64,K.CARD),('جلسهٔ ۳',27,.565,K.CARD),('اسفنوئید، کامی و پس‌سری',16,.475,K.TEAL_L),('نسخهٔ جزوه‌نویسی',14,.365,K.TEAL_L),('متن درس · تصاویر · جدول · راهنمای نویسنده',10,.30,K.CARD)]:
  K.draw_shaped(book.c,K.A4W/2,K.A4H*y,K.shape(text),'VazirB' if size>13 else 'Vazir',size,color,align='center')

def graph_data():
 paths={14:('مسیر کامی بزرگ',['حفرهٔ پتریگوپالاتین','کانال کامی بزرگ','سوراخ کامی بزرگ','کام سخت'],['ورود به','خروج از','رسیدن به'],'۱۳ تا ۱۵'),
        18:('مسیر وریدی',['سینوس عرضی','سینوس سیگموئید','ورید ژوگولار داخلی'],['ادامه به','ادامه در'],'۱۹ و ۲۰')}
 graphs={}
 for idx,(title,steps,labels,pages) in paths.items():
  ids=[f'n{j}' for j in range(len(steps))];edges=[[ids[j],ids[j+1]] for j in range(len(ids)-1)]
  graphs[str(idx)]={'diagram':{'title':title,'nodes':[{'id':a,'text':v} for a,v in zip(ids,steps)],'edges':edges,'edge_labels':{a+':'+b:lab for (a,b),lab in zip(edges,labels)},'reading_task':'مسیر را با متن و تصویر مبحث دنبال کنید.','reference':'جزوهٔ درس، جلسهٔ ۳، صفحه‌های فایل '+pages}}
 return graphs

def build(path,toc=None):
 base,plan,outline,assets,no,nt,_=inputs();cfg=H.HN_SESSIONS['hn03']
 book=Book(path,'جزوهٔ مادر آناتومی سر و گردن — جلسهٔ ۳',footer='HumsYar · جزوهٔ مادر سر و گردن · جلسهٔ ۳',subject='جزوهٔ مادر')
 book.measure_idcard=True;book.keep_parenthesized_latin=True;book.block_trace=[];book.trace_topic=''
 book.dark_page(cover,reuse_blank_page=True)
 book.h1('راهنمای استفادهٔ جزوه‌نویس')
 book.para('شناسنامه، متن درس، تصویرها و توضیح‌های تکمیلی در ترتیب مباحث قرار دارند. منبع هر متن یا تصویر کنار همان بخش آمده است. در پایان هر مبحث برگهٔ تحویل و در پایان جلسه چک‌لیست مرور قرار دارد.')
 book.new_page();book.h1('فهرست مباحث')
 for i,t in enumerate(outline['topics'],1):book.toc_row(K.fa_digits(str(i)),t['title'],(toc or {}).get(t['topic_id'],'—'),step=23)
 book.toc_row('پ','جمع‌بندی و چک‌لیست',(toc or {}).get('hn-summary','—'),step=23)
 book.new_page();book.h1('اسفنوئید، کامی و پس‌سری',anchor='chapter',kicker='جلسهٔ سوم');book.para(cfg['outcome'])
 graphs=graph_data();geometry=R.layouts(book,graphs)
 stats={'base_blocks':sum(len(t['blocks']) for t in base),'overlay_blocks':no,'transcription_blocks':nt,'topics':{},'figures':[],'source_text_sha256':{}}
 for idx,t in enumerate(outline['topics'],1):
  tid=t['topic_id'];blocks=plan[tid];book.trace_topic=tid;card=copy.deepcopy(blocks[0]);card_h=book.card_height(card['rows'],footer=clean(card.get('footer','')))
  H.topic_head(book,t,idx,len(outline['topics']),after=card_h+35)
  stats['topics'][tid]={'page':book.page,'title':t['title']};book.label_card('شناسنامهٔ مبحث',card['rows'],kicker=card.get('kicker',''),footer=clean(card.get('footer','')))
  handoff=None;fig=0
  for pos,raw in enumerate(blocks[1:],1):
   q=copy.deepcopy(raw);origin=q.pop('_origin');kind=q['type']
   if origin.startswith(('base:','transcription:')) and kind in ('p','ul','ol'):
    stats['source_text_sha256'][tid+':'+origin]=hashlib.sha256(json.dumps(q.get('text',q.get('items')),ensure_ascii=False).encode()).hexdigest()
   if kind=='handoff':handoff=q;continue
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
   H.render_blocks(book,[q],cfg)
  source='جزوهٔ درس، جلسهٔ ۳، صفحه‌های فایل '+H.page_range(t.get('pages',[]))
  if str(idx) in graphs:R.draw_graph(book,graphs[str(idx)],geometry[str(idx)],force_page=True)
  if handoff:
   book.h3('پرسش و پاسخ آموزشی');book.para(clean(handoff.get('question','')));book.callout(W.ANSWERS[idx],title='پاسخ');book.source_line(source)
   book.note_box(24,title='یادداشت جزوه‌نویس')
   point=W.REVIEWS.get(idx,'نکته برای بررسی: '+card['rows'][0]['text']+'؛ جهت و روابط ساختارها با متن و شکل مبحث تطبیق داده شود.')
   question=clean(handoff.get('question','')).removeprefix('پرسش باز:').strip()
   book.handoff_sheet(clean(handoff['title'])+' — '+t['title'],clean(handoff.get('sources','')),W.GUIDES[idx],point,
      kicker='برای تکمیل جزوه‌نویس',note='پرسش باز: '+question,writer_name=True)
 book.new_page();book.h1('جمع‌بندی و چک‌لیست',anchor='hn-summary',kicker='پایان جلسه')
 book.para('برای هر مبحث، توضیح را بدون نگاه به متن بازیابی کنید و مربع را علامت بزنید؛ سپس متن، عنوان شکل و منبع را مرور کنید.')
 rows=[['مبحث '+K.fa_digits(str(i))+' — '+t['title'],(t.get('gist') or t['title']).rstrip(' .')+'؟','☐'] for i,t in enumerate(outline['topics'],1)]
 H.emit_table(book,['چک‌لیست خودآزمایی','می‌توانم این را توضیح دهم؟','☐'],rows,widths=[K.CONTENT_W*.30,K.CONTENT_W*.58,K.CONTENT_W*.12],caption='چک‌لیست خودآزمایی جلسهٔ ۳',size=8.2)
 if book.missing_assets:raise ValueError(book.missing_assets)
 book.save();stats['pages']=book.page;return book.heading_pages,stats

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT/'HumsYar_HeadNeck_Jalase3_WRITER_FINAL.pdf');args=p.parse_args();args.out=args.out.resolve();args.out.parent.mkdir(parents=True,exist_ok=True)
 first,_=build(args.out);second,stats=build(args.out,first)
 if first!=second:raise ValueError('Unstable table of contents')
 H.drop_trailing_blank_page(args.out);qa={'outside_spans':[],'empty_pages':[],'leaks':[],'body_near_footer':[]}
 with pymupdf.open(args.out) as doc:
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
   page.get_pixmap(matrix=pymupdf.Matrix(1.25,1.25),alpha=False).save(str(args.out.parent/f'page-{n:03}.jpg'),jpg_quality=88)
  stats['bookmarks']=doc.get_toc()
 stats.update(file=str(args.out.relative_to(ROOT)),sha256=R.sha(args.out),bytes=args.out.stat().st_size,qa=qa)
 (args.out.parent/'manifest.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'pages':stats['pages'],'figures':len(stats['figures']),'sha256':stats['sha256'],'qa':qa},ensure_ascii=False,indent=2))
 if any(qa.values()):raise SystemExit('QA failed; see manifest')
if __name__=='__main__':main()

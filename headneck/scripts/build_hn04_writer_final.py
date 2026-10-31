"""Session four writer edition: preserve the previously reconciled content and figures."""
from __future__ import annotations
import argparse,copy,hashlib,json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'render'),str(Path(__file__).parent)]
import pymupdf
import build_headneck as H
import hn04_writer_copy as W
import build_hn01_updated_review as R
K=H.K
OUT=ROOT/'.cache/hn04_writer_update'
BAD=re.compile(r'IMG[-ـ]?\d+|SRC[-ـ]?\d+|hn\d\d[-–]T\d+|JSON|BLOCKED|NOT_YET|PENDING|INTEGRATED|غیرنهایی|پیش‌نویس|رونویسی در حال مقابله',re.I)

def decoded(v):
 if isinstance(v,str):return v.replace('\\u200c','\u200c').replace('\\u200d','\u200d')
 if isinstance(v,list):return [decoded(x) for x in v]
 if isinstance(v,dict):return {k:decoded(x) for k,x in v.items()}
 return v

def clean(s):return decoded(str(s)).replace('PDF','فایل').replace('فایل فایل','فایل')

def inputs():
 cfg=H.HN_SESSIONS['hn04'];outline=H.load_json(H.CONTENT/'outline'/cfg['outline'])
 base=[]
 for name in cfg['content']:base+=H.load_json(H.CONTENT/name)
 content=H.apply_update('hn04',{t['topic_id']:t['blocks'] for t in base})
 assert len(outline['topics'])==len(content)==len(W.GUIDES)==len(W.REVIEW)==20
 return base,content,outline

class Book(R.ReviewBook):
 def source_line(self,s):super().source_line(clean(s))

def cover(book):
 for text,size,y,color in [('HumsYar · جزوهٔ مادر آناتومی',11,.86,K.TEAL_L),('آناتومی سر و گردن',29,.64,K.CARD),('جلسهٔ ۴',27,.565,K.CARD),('قاعدهٔ جمجمه و سوراخ‌های آن',16,.475,K.TEAL_L),('نسخهٔ جزوه‌نویسی',14,.365,K.TEAL_L),('متن درس · تصویر · جدول · برگهٔ تحویل',10,.30,K.CARD)]:
  K.draw_shaped(book.c,K.A4W/2,K.A4H*y,K.shape(text),'VazirB' if size>13 else 'Vazir',size,color,align='center')

def graph_data():
 paths={5:('مسیر مجرای اشکی',['مجرای اشکی‌بینی','دهانهٔ مجرای اشکی','مجرای تحتانی بینی'],['باز می‌شود از','در'],'جزوهٔ درس، بخش ۱، صفحهٔ فایل ۶؛ نتر، پلیت ۶۱، صفحهٔ فایل ۱۱۳'),
        9:('مجرای اندولنفاتیک',['لابیرنت غشایی','مجرای اندولنفاتیک','کیسهٔ اندولنفاتیک'],['ادامه به','رسیدن به'],'جزوهٔ درس، بخش ۱، صفحهٔ فایل ۱۵؛ نتر، پلیت ۱۲۵، صفحهٔ فایل ۱۷۷')}
 graphs={}
 for idx,(title,steps,labels,source) in paths.items():
  ids=[f'n{j}' for j in range(len(steps))];edges=[[ids[j],ids[j+1]] for j in range(len(ids)-1)]
  graphs[str(idx)]={'diagram':{'title':title,'nodes':[{'id':a,'text':v} for a,v in zip(ids,steps)],'edges':edges,'edge_labels':{a+':'+b:label for (a,b),label in zip(edges,labels)},'reading_task':'مسیر را با متن و شکل همین مبحث دنبال کنید.','reference':source}}
 return graphs

def build(path,toc=None):
 base,content,outline=inputs();cfg=H.HN_SESSIONS['hn04']
 book=Book(path,'جزوهٔ مادر آناتومی سر و گردن — جلسهٔ ۴',footer='HumsYar · جزوهٔ مادر سر و گردن · جلسهٔ ۴',subject='جزوهٔ مادر')
 book.measure_idcard=True;book.keep_parenthesized_latin=True;book.block_trace=[];book.trace_topic=''
 book.dark_page(cover,reuse_blank_page=True)
 book.h1('راهنمای استفادهٔ جزوه‌نویس')
 book.para('شناسنامه، متن درس، تصویرها و توضیح‌های تکمیلی در ترتیب مباحث قرار دارند. منبع هر متن یا تصویر کنار همان بخش آمده است. در پایان هر مبحث برگهٔ تحویل و در پایان جلسه چک‌لیست مرور قرار دارد.')
 book.new_page();book.h1('فهرست مباحث')
 for i,t in enumerate(outline['topics'],1):book.toc_row(K.fa_digits(str(i)),t['title'],(toc or {}).get(t['topic_id'],'—'),step=23)
 book.toc_row('پ','جمع‌بندی و چک‌لیست',(toc or {}).get('hn-summary','—'),step=23)
 book.new_page();book.h1('قاعدهٔ جمجمه',anchor='chapter',kicker='جلسهٔ چهارم');book.para(cfg['outcome'])
 graphs=graph_data();geometry=R.layouts(book,graphs)
 stats={'base_blocks':sum(len(t['blocks']) for t in base),'merged_blocks':sum(len(v) for v in content.values()),'topics':{},'figures':[],'block_sha256':{}}
 for idx,t in enumerate(outline['topics'],1):
  tid=t['topic_id'];blocks=decoded(copy.deepcopy(content[tid]));book.trace_topic=tid
  assert blocks[0]['type']=='idcard' and blocks[-1]['type']=='handoff'
  card=blocks[0];handoff=blocks[-1]
  for b in blocks:
   for key in ('src','citation','title','footer','kicker'):
    if key in b:b[key]=clean(b[key])
  card_h=book.card_height(card['rows'],footer=card.get('footer',''))
  H.topic_head(book,t,idx,len(outline['topics']),after=card_h+35,part_labels=True)
  stats['topics'][tid]={'page':book.page,'title':t['title']}
  book.label_card('شناسنامهٔ مبحث',card['rows'],kicker=card.get('kicker',''),footer=card.get('footer',''))
  for pos,b in enumerate(blocks[1:-1],1):
   stats['block_sha256'][tid+':'+str(pos)]=hashlib.sha256(json.dumps(b,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
   if b['type']=='plate':
    asset=ROOT/b['asset']
    if not asset.exists():raise FileNotFoundError(asset)
    stats['figures'].append({'topic':tid,'asset':b['asset'],'sha256':R.sha(asset)})
  H.render_blocks(book,blocks[1:-1],cfg)
  if str(idx) in graphs:R.draw_graph(book,graphs[str(idx)],geometry[str(idx)],force_page=True)
  book.note_box(24,title='یادداشت جزوه‌نویس')
  question=clean(handoff.get('question','')).removeprefix('پرسش باز:').strip()
  book.handoff_sheet(clean(handoff['title'])+' — '+t['title'],clean(handoff.get('sources','')),W.GUIDES[idx],W.REVIEW[idx],
    kicker='برای تکمیل جزوه‌نویس',note='پرسش باز: '+question,writer_name=True)
 book.new_page();book.h1('جمع‌بندی و چک‌لیست',anchor='hn-summary',kicker='پایان جلسه')
 book.para('برای هر مبحث، توضیح را بدون نگاه به متن بازیابی کنید و مربع را علامت بزنید؛ سپس متن، عنوان شکل و منبع را مرور کنید.')
 rows=[['مبحث '+K.fa_digits(str(i))+' — '+t['title'],(t.get('gist') or t['title']).rstrip(' .')+'؟','☐'] for i,t in enumerate(outline['topics'],1)]
 H.emit_table(book,['چک‌لیست خودآزمایی','می‌توانم این را توضیح دهم؟','☐'],rows,widths=[K.CONTENT_W*.30,K.CONTENT_W*.58,K.CONTENT_W*.12],caption='چک‌لیست خودآزمایی جلسهٔ ۴',size=8.2)
 if book.missing_assets:raise ValueError(book.missing_assets)
 book.save();stats['pages']=book.page;return book.heading_pages,stats

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT/'HumsYar_HeadNeck_Jalase4_WRITER_FINAL.pdf');args=p.parse_args();args.out=args.out.resolve();args.out.parent.mkdir(parents=True,exist_ok=True)
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

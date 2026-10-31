"""Build the explicitly requested, NON-FINAL session-one review PDF.

Does not run/override the six-session final gate, modify baselines, apply old
update overlays, or concatenate historical PDFs. It typesets every saved A block
and the current B material together per topic, with open C issues visible.
Dependencies: requirements.txt; npm install --prefix .cache/hn01_review_layout
@dagrejs/dagre@1.1.5. Historical sources/assets: the pinned inventory/restore tools.
The resulting ignored-cache artifact is published as a GitHub prerelease asset.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'render'))
import hn_kit as K
import build_headneck as H
from PIL import Image
import pymupdf
O=ROOT/'headneck/master_01_06';W=ROOT/'.cache/master_01_06'
CACHE=ROOT/'.cache/hn01_review_layout'
TITLE='جلسهٔ ۱ — نسخهٔ جدید برای بازبینی'
WARNING='نسخهٔ بازبینی — غیرنهایی؛ تأیید علمی و بررسی همهٔ تصاویر و صفحات کامل نشده است.'
LABELS={'title':'عنوان اختصاصی','domain':'دامنهٔ علمی','precise_definition':'تعریف دقیق','anatomical_position':'موقعیت آناتومیک','distinct_landmarks':'نشانه‌های متمایز','function':'کارکرد و کاربرد','boundary_of_topic':'حدود مبحث و شاهد','learning_objective':'هدف یادگیری','assessment_importance':'اهمیت آموزشی و حدود ادعای آزمونی','link_forward':'پیوند مباحث','observable_anchor':'شاهد قابل مشاهده','spatial_relations':'روابط فضایی','tissue_scope':'دامنهٔ بافتی','numerical_caveat':'اختلاف عددی','neurovascular_scope':'دامنهٔ عصبی‌عروقی','paragraph_sequence':'ترتیب نوشتن پاراگراف‌ها','diagram_instruction':'دستور رسم نمودار','image_selection':'انتخاب تصویر','quality_check':'کنترل اختصاصی','forbidden_shortcut':'میان‌بر نامعتبر'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((O/n).read_text())
def flat(v):
 if isinstance(v,list):return ' · '.join(flat(x) for x in v)
 if isinstance(v,dict):return '؛ '.join(f'{LABELS.get(k,k)}: {flat(x)}' for k,x in v.items())
 return str(v)
def citation(r):
 text=r.get('source_label','')
 if 'pdf_page' in r:text+=f" | PDF {r['pdf_page']}"
 if 'pdf_pages' in r:text+=' | PDF '+','.join(map(str,r['pdf_pages']))
 for k,lab in [('printed_page','چاپی'),('plate','پلیت'),('figure','شکل'),('table','جدول'),('panel','زیرنما')]:
  if k in r:text+=f' | {lab} {r[k]}'
 if r.get('section'):text+=' | '+r['section']
 return text
class ReviewBook(K.PDFBook):
 def source_line(self,text):
  if text:self.paragraph('منبع: '+text,K.TextStyle(size=7.6,leading=12,color=K.MUTED,justify=False,space_after=5))
 def label_card(self,title,rows,**kw):
  # Keep each measured row intact, repeating the card header when a long card
  # would exceed a page. Avoid the legacy method's oversized-card overflow.
  groups=[];group=[]
  for row in rows:
   if group and self.card_height(group+[row],footer=kw.get('footer',''))>self.usable_height()-75:
    groups.append(group);group=[]
   group.append(row)
  if group:groups.append(group)
  for i,g in enumerate(groups):
   super().label_card(title+(' — ادامه' if i else ''),g,**kw)
 def para(self,s,small=False):
  self.paragraph(s,K.TextStyle(size=8.8 if small else 10.3,leading=14 if small else 17.2,justify=not small))

def inputs():
 hist=load('historical_sources.json');index={r['file']:r for r in hist['files']}
 content=[]
 for name in ['hn01_a.json','hn01_b.json']:
  r=index['headneck/content/'+name];p=ROOT/r['workspace_file']
  if sha(p)!=r['sha256']:raise ValueError('Changed protected source '+str(p))
  content.extend(json.loads(p.read_text()))
 assets={r['asset']:r for r in load('restored_assets.json')}
 for t in content:
  for b in t['blocks']:
   if 'asset' in b:
    a=assets[b['asset']];p=ROOT/a['workspace_file']
    if sha(p)!=a['sha256']:raise ValueError('Changed baseline figure '+str(p))
 outline=json.loads((ROOT/index['headneck/content/outline/hn01_topics.json']['workspace_file']).read_text())
 return content,assets,outline

def layouts(book,additions):
 CACHE.mkdir(exist_ok=True,parents=True)
 js=CACHE/'layout.cjs'
 js.write_text("""const fs=require('fs'),dagre=require('@dagrejs/dagre');
const data=JSON.parse(fs.readFileSync(0,'utf8')),out={};
for(const [key,v] of Object.entries(data)) {out[key]={};for(const dir of ['TB','LR']) {
const g=new dagre.graphlib.Graph({multigraph:true});g.setGraph({rankdir:dir,nodesep:22,ranksep:24,marginx:12,marginy:12});g.setDefaultEdgeLabel(()=>({}));
for(const n of v.nodes) g.setNode(n.id,{width:n.width,height:n.height});
v.edges.forEach((e,i)=>g.setEdge(e[0],e[1],{width:18,height:15,labelpos:'c'},String(i)));dagre.layout(g);
out[key][dir]={width:g.graph().width,height:g.graph().height,nodes:Object.fromEntries(g.nodes().map(n=>[n,g.node(n)])),edges:g.edges().map(e=>({index:Number(e.name),...g.edge(e)}))};}}
process.stdout.write(JSON.stringify(out));""")
 data={}
 for tid,b in additions.items():
  nodes=[]
  for n in b['diagram']['nodes']:
   lines=book.wrap(n['text'],'VazirB',9.0,116)
   nodes.append(dict(id=n['id'],width=138,height=max(48,16+len(lines)*13)))
  data[tid]=dict(nodes=nodes,edges=b['diagram']['edges'])
 r=subprocess.run(['node',str(js)],input=json.dumps(data),text=True,capture_output=True,check=True)
 return json.loads(r.stdout)

def draw_graph(book,b,layout):
 graph=b['diagram'];book.new_page();book.h3('نمودار رابطه‌ها — '+graph['title'])
 area_h=500;area_w=K.CONTENT_W-12
 choices=[(min(area_w/x['width'],area_h/x['height'],1.12),x) for x in layout.values()]
 scale,g=max(choices,key=lambda x:x[0]);font=9*scale
 if font<6.8:raise ValueError('Diagram would be unreadable: '+graph['title'])
 c=book.c;start_y=book.y+8;start_x=K.M_LEFT+(K.CONTENT_W-g['width']*scale)/2
 def point(p):return start_x+p['x']*scale,book.py(start_y+p['y']*scale)
 for e in g['edges']:
  pts=e['points'];path=c.beginPath();path.moveTo(*point(pts[0]))
  for p in pts[1:]:path.lineTo(*point(p))
  c.setStrokeColor(K.TEAL_D);c.setLineWidth(.9);c.drawPath(path)
  x,y=point(pts[-1]);xx,yy=point(pts[-2]);angle=math.atan2(y-yy,x-xx);a=4.5
  arrow=c.beginPath();arrow.moveTo(x,y);arrow.lineTo(x-a*math.cos(angle-.48),y-a*math.sin(angle-.48));arrow.lineTo(x-a*math.cos(angle+.48),y-a*math.sin(angle+.48));arrow.close();c.setFillColor(K.TEAL_D);c.drawPath(arrow,fill=1,stroke=0)
  ex,ey=point(dict(x=e.get('x',pts[len(pts)//2]['x']),y=e.get('y',pts[len(pts)//2]['y'])))
  c.setFillColor(K.CARD);c.circle(ex,ey,8,stroke=0,fill=1)
  K.draw_shaped(c,ex,ey-2.5,str(e['index']+1),'VazirB',7.6,K.TEAL_D,align='center')
 for n in graph['nodes']:
  v=g['nodes'][n['id']];x,y=point(v);w=v['width']*scale;h=v['height']*scale
  c.setFillColor(K.TEAL_LL);c.setStrokeColor(K.TEAL);c.roundRect(x-w/2,y-h/2,w,h,5,stroke=1,fill=1)
  lines=book.wrap(n['text'],'VazirB',9,116)
  for i,line in enumerate(lines):K.draw_shaped(c,x,y+(len(lines)-1)*6.5*scale-i*13*scale-3*scale,K.shape(line),'VazirB',font,K.INK,align='center')
 book._touch();book.y=start_y+g['height']*scale+15
 book.para('اعداد کنار پیکان‌ها به راهنمای رابطه‌های زیر ارجاع دارند؛ پیکانِ مکانی با جریان مایع یا رابطهٔ شمارشی یکی نیست.',small=True)
 names={n['id']:n['text'] for n in graph['nodes']};labels=graph.get('edge_labels',{})
 for i,(a,z) in enumerate(graph['edges'],1):book.para(f"{i}. {names[a]} ← {names[z]} | رابطهٔ پیکان از گرهٔ اول به دوم: {labels.get(a+':'+z,'رابطهٔ شاخه طبق نمودار و توضیح مبحث')}",small=True)
 book.para('تمرین خواندن نمودار: '+graph['reading_task'])
 book.source_line(graph.get('reference',''))
 return dict(page=book.heading_pages.get(''),scale=scale,node_font=font)

# Targeted figure additions from pages actually observed, not a claim to have
# closed every relevant atlas page. Reference pages are allowed; lecture pages
# are never pasted as substitutes for typed A paragraphs.
EXTRA={2:[('SRC-648',82,30)],4:[('SRC-648',84,32)],6:[('SRC-648',77,25)],9:[('SRC-648',79,27)],13:[('SRC-648',163,111)],14:[('SRC-648',81,29)],15:[('SRC-648',113,61),('SRC-648',114,62)],16:[('SRC-648',92,40),('SRC-648',78,26)]}
def build(path,toc=None):
 baseline,assets,outline=inputs();additions=load('educational_additions.json')['topics'];issues=load('scientific_issues.json')['issues'];refs={(r['source_label'],r['pdf_page']):r for r in load('reference_page_observations.json')}
 book=ReviewBook(path,TITLE,footer='HumsYar · جلسهٔ ۱ · نسخهٔ بازبینی — غیرنهایی',subject=WARNING)
 book.measure_idcard=True;book.keep_parenthesized_latin=True;book.block_trace=[];book.trace_topic=''
 cfg=copy.deepcopy(H.HN_SESSIONS['hn01']);cfg['cover_title']=['آناتومی سر و گردن','جلسهٔ ۱ — نسخهٔ بازبینی'];cfg['cover_topic']='متن پایهٔ محفوظ + تکمیل مستقل هر ۱۷ مبحث'
 def cover(b):
  H.cover_page(b,cfg)
  K.draw_shaped(b.c,K.A4W/2,K.A4H*.245,K.shape('غیرنهایی — تأیید علمی و تصویری کامل نشده است'),'VazirB',13,K.ROSE_LINE,align='center')
 book.dark_page(cover,reuse_blank_page=True)
 book.h1('وضعیت و روش خواندن این نسخه')
 book.callout(WARNING,kind='warn',title='مهم: انتشار برای مشاهده و بازبینی، نه تأیید نهایی')
 book.para('این PDF بنا به درخواست جدید شما برای دانلود جلسهٔ اول تهیه شده است. متن و تصویرهای پایه از JSON و دارایی‌های محفوظ بازچینی شده‌اند؛ PDF قدیمی ضمیمه یا چسبانده نشده است. تکمیل‌های جدید در هر مبحث با عنوان لایهٔ B جدا شده‌اند و اختلاف‌ها پیش از متن پایه دیده می‌شوند.')
 book.para('این نسخه جایگزین هدف نهاییِ جزوهٔ جامع جلسات۱–۶ نیست. ۷۵ بلوک نقل از نظر محتوایی مقایسه شده، اما مقابلهٔ حرف‌به‌حرف، نام نویسندگان، تمام تصاویر مرتبط و بازبینی بصری همهٔ صفحات نهایی کامل نشده‌اند. صفر مبحث تأیید نهایی دارد. وجود یک ادعا در بخش پایه، تأیید علمی تازهٔ آن نیست.')
 book.para('منابع با کد مشخص‌اند: SRC-649 اصل جلسه۱، SRC-648 نتر، SRC-632 گریِ بخش۸۰۱–۱۰۰۰ و SRC-628 گریِ بخش۱۰۰۱–۱۱۸۹. PDF page یک‌مبنا و جدا از صفحهٔ چاپی/پلیت است. شکل‌های قدیمیِ بخش A هنوز همه در مأموریت جدید بازتأیید نشده‌اند. Junqueira،Langman،Moore و اطلس مستقل «نثر» در دسترس شناسایی‌شده نبوده‌اند.')
 book.para('تاریخ: ۳۱ اکتبر۲۰۲۶. نسخهٔ بازبینیِ قابل اصلاح؛ نمودارهای رابطه‌ای تألیفی‌اند. سؤال‌های افزوده، تمرین تألیفی‌اند نه شاهد سؤال پرتکرار آزمونی.')
 book.new_page();book.h1('فهرست مبحث‌ها')
 for i,t in enumerate(outline['topics'],1):book.toc_row(K.fa_digits(str(i)),t['title'],(toc or {}).get(t['topic_id'],'—'),step=27)
 geometry=layouts(book,additions);bystopic={t['topic_id']:t for t in baseline};stats=dict(topics=17,baseline_blocks=0,new_graphs=0,extra_reference_figures=0,topic_pages={},graph_pages={},figure_pages=[])
 for i,t in enumerate(outline['topics'],1):
  tid=t['topic_id'];b=additions[tid];book.new_page();book.h1(t['title'],anchor=tid,kicker='جلسهٔ ۱ · '+tid+' · بازبینی غیرنهایی');stats['topic_pages'][tid]=book.page
  relevant=[r for r in issues if r['topic']==tid or r['id'] in b.get('scientific_issue_links',[])]
  if relevant:
   book.h3('اختلاف‌ها و حدود شاهد — پیش از خواندن متن پایه')
   for r in relevant:
    book.callout(r['finding'],kind='warn',title=r['id']+' — نیازمند توجه')
    book.para(r['editorial_action'],small=True)
  book.h3('لایهٔ A — متن و مواد پایهٔ محفوظ، بدون ادعای بازتأیید کامل')
  blocks=copy.deepcopy(bystopic[tid]['blocks'])
  for block in blocks:
   if 'asset' in block:block['asset']=str(ROOT/assets[block['asset']]['workspace_file'])
  book.trace_topic=tid;H.render_blocks(book,blocks,cfg);stats['baseline_blocks']+=len(blocks)
  book.new_page();book.h2('لایهٔ B — تکمیل اختصاصی و مستقل از نقل اصل',keep_with=100)
  rows=[dict(label=LABELS.get(k,k),text=flat(v)) for k,v in b['scientific_card'].items()]
  book.label_card('شناسنامهٔ علمیِ '+tid,rows,accent=K.BLUE_D,tint=K.BLUE_BG)
  book.h3('توضیح روان');book.para(b['plain_explanation'])
  book.h3('نکته‌های کلیدی');book.bullets(b['key_points'])
  book.h3('روابط فضایی');book.bullets(b['spatial_relations'])
  book.h3('اشتباه‌های قابل پیشگیری')
  for e in b['common_errors']:book.callout('اشتباه: '+e['error']+'\nتمایز درست: '+e['correction'],kind='warn')
  H.emit_table(book,b['comparison']['columns'],b['comparison']['rows'],caption='جدول مقایسهٔ اختصاصی '+tid,size=8.6)
  stats['graph_pages'][tid]=book.page+1;draw_graph(book,b,geometry[tid]);stats['new_graphs']+=1
  reference_notes=[]
  for label,n,plate in EXTRA.get(i,[]):
   r=refs[(label,n)];p=ROOT/r['render']
   if sha(p)!=r['render_sha256']:raise ValueError('Reference render changed')
   book.new_page();book.h3(f'شاهد تصویری تکمیلی — نتر، پلیت {plate}')
   book.figure(p,caption=f'{label} | PDF {n} | Plate {plate}',max_h=560,width=K.CONTENT_W-8)
   stats['figure_pages'].append(dict(topic=tid,page=book.page,source_label=label,pdf_page=n,plate=plate));stats['extra_reference_figures']+=1
   reference_notes.append((plate,r['observations']))
  if reference_notes:book.new_page()
  for plate,note in reference_notes:
   book.h3(f'دستور خواندن شاهد پلیت {plate}');book.para(note)
  book.h3('راهنمای اختصاصی نویسنده و تصویر')
  for k,v in b['writer_guide'].items():
   book.h3(LABELS.get(k,k));book.para(flat(v))
  for r in b['image_instructions']:
   ident=r.get('image_id',citation(r));book.para(ident+' — '+r['instruction'],small=True)
  book.h3('خودآزمایی تألیفی')
  for q in b.get('exam_claims',[]):
   book.para(q['text']);book.callout(q.get('answer',''),title='پاسخ آموزشی')
  book.h3('جمع‌بندی');book.para(b['summary']);book.h3('ارجاع‌های تکمیل')
  for r in b['reference_links']:book.source_line(citation(r))
 book.new_page();book.h1('موارد باز و حدود انتشار')
 book.callout(WARNING,kind='warn')
 book.para('این انتشار فقط جلسهٔ۱ را برای بررسی در اختیار شما می‌گذارد. تکمیل علمی موارد باز، همهٔ شکل‌ها و زیرنماها، مقابلهٔ کامل نقل و نام‌ها و بازبینی بصری تک‌تک صفحات پیش‌شرط نهایی‌شدن‌اند. روال نهاییِ جلسات۱–۶ همچنان مسدود است و این PDF از دروازهٔ نهایی عبور داده نشده است.')
 for r in issues:book.para(r['id']+' | '+r['status']+' | '+r['editorial_action'],small=True)
 if book.missing_assets:raise ValueError('Missing assets: '+str(book.missing_assets))
 book.save();stats['pages']=book.page
 return book.heading_pages,stats

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=W/'publication/HumsYar_HeadNeck_Jalase1_UPDATED_REVIEW.pdf');a=parser.parse_args();a.out.parent.mkdir(exist_ok=True,parents=True)
 first,stats=build(a.out);second,stats=build(a.out,first)
 if first!=second:raise ValueError('TOC not stable')
 H.drop_trailing_blank_page(a.out)
 with pymupdf.open(a.out) as doc:
  stats['pages']=len(doc);stats['empty_pages']=[i+1 for i,p in enumerate(doc) if not p.get_text().strip() and not p.get_images()]
  if stats['empty_pages']:raise ValueError('Unexpected empty page')
 stats.update(file=str(a.out.relative_to(ROOT)),sha256=sha(a.out),bytes=a.out.stat().st_size,status='NON_FINAL_REVIEW_FOR_USER_INSPECTION',all_pages_visually_reviewed=False,scientific_clearance=False,master_final_gate_overridden=False,source_inputs_sha256={n:sha(O/n) for n in ['educational_additions.json','scientific_issues.json','historical_sources.json','restored_assets.json']})
 (a.out.parent/'build_metrics.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(json.dumps(stats,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

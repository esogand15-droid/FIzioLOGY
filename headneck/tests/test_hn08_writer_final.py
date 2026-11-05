"""Regression and provenance checks for the session-eight writer edition."""
import hashlib,io,json,re,sys,unittest,unicodedata
from pathlib import Path
from PIL import Image
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'headneck/scripts'),str(ROOT/'render')]
import build_hn08_writer_final as B

class SessionEightWriterTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.out=ROOT/'pdf/HumsYar_HeadNeck_Jalase8_AUDITED.pdf'
  cls.manifest=ROOT/'headneck/reports/hn08_evidence/audit_manifest.json'
 def test_original_source_and_transcription_coverage(self):
  src=next((ROOT/'علوم تشریح سر و گردن/جلسه 8 - عروق گردنی').glob('*.pdf'))
  self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),'bee4f56e1a034522776b1a9827aa9c03686ff9bc72f3b64832cd38eb71b4d9df')
  pages=B.source_pages();self.assertEqual(sorted(pages),list(range(1,13)))
  self.assertIn('جسم کاروتید',pages[3]);self.assertIn('شریان لینگوال',pages[6]);self.assertIn('دزدیدن',pages[12])
  self.assertEqual(len(B.CAPTIONS[13]),1)
 def test_all_topics_specific_and_no_missing_files(self):
  self.assertEqual(len(B.outline()['topics']),12)
  self.assertEqual(len(set(tuple(x) for x in B.W.GUIDES.values())),12)
  self.assertEqual(len(set(B.W.REVIEW.values())),12)
  self.assertTrue(all(len(x)==3 for x in B.W.GUIDES.values()))
  for n,captions in B.CAPTIONS.items():
   for j in range(1,len(captions)+1):self.assertTrue((ROOT/f'headneck/images/hn08/lecture_p{n:02}_{j}.png').exists())
  for refs in B.REFS.values():
   for name,_,_ in refs:self.assertTrue((ROOT/f'headneck/images/hn08/{name}.png').exists())
 def test_rendered_figure_pixels_and_qa(self):
  if not self.out.exists() or not self.manifest.exists():self.skipTest('Generated booklet not present')
  data=json.loads(self.manifest.read_text());self.assertEqual(len(data['figures']),40);self.assertFalse(any(data['qa'].values()))
  with pymupdf.open(self.out) as doc:
   xrefs={im[0] for p in doc for im in p.get_images()};hashes=set()
   for xref in xrefs:
    im=Image.open(io.BytesIO(doc.extract_image(xref)['image'])).convert('RGB')
    hashes.add((im.size,hashlib.sha256(im.tobytes()).hexdigest()))
  for rec in data['figures']:
   p=ROOT/rec['asset'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),rec['sha256'])
   im=Image.open(p).convert('RGB');self.assertIn((im.size,hashlib.sha256(im.tobytes()).hexdigest()),hashes)
 def test_each_figure_has_a_matching_source_anchor(self):
  pages=B.source_pages()
  for n,figs in B.FIGURE_ANCHORS.items():
   for j,anchor in figs.items():
    self.assertEqual(sum(anchor in p for p in pages[n].splitlines()),1,(n,j,anchor))
  for n,figs in B.REF_ANCHORS.items():
   for name,anchor in figs.items():
    self.assertEqual(sum(anchor in p for p in pages[n].splitlines()),1,(n,name,anchor))
  # The page-five collateral image is deliberately placed by the relevant page-four text.
  self.assertIn('۲. از طریق آناستوموز',pages[4])
  orig={(n,j) for n,figs in B.CAPTIONS.items() for j in range(1,len(figs)+1)}
  mapped={(n,j) for n,figs in B.FIGURE_ANCHORS.items() for j in figs}|{(5,2),(13,1)}
  self.assertEqual(orig,mapped)
 def test_source_persian_words_are_present_in_pdf(self):
  if not self.out.exists():self.skipTest('Generated booklet not present')
  def clean(s):
   s=unicodedata.normalize('NFKC',s).replace('\u200c','').replace('ي','ی').replace('ك','ک')
   return ''.join(c for c in s if not unicodedata.combining(c))
  with pymupdf.open(self.out) as doc:body=clean(' '.join(p.get_text() for p in doc))
  for credit in ['استاد میرزایی','نرگس بنایی','پوریا عبداللهی','یادداشت حاشیهای جزوه']:
   self.assertIn(clean(credit),body)
  for page,source in B.source_pages().items():
   source='\n'.join(line for line in source.splitlines() if not line.startswith('یادداشت حاشیه‌ای منبع:'))
   for word in set(re.findall(r'[ء-غف-یپچژگ]{4,}',clean(source))):
    self.assertIn(word,body,(page,word))
 def test_shell_forms_and_chapter_destinations(self):
  if not self.out.exists():self.skipTest('Generated booklet not present')
  def norm(s):return unicodedata.normalize('NFKC',s).replace('\u200c','').replace('ٔ','')
  with pymupdf.open(self.out) as doc:
   pages=[norm(p.get_text()) for p in doc];self.assertIn(norm('ساختار این جزوه و قاعدهٔ خواندن آن'),pages[1]);self.assertIn('فهرست مطالب',pages[2]);self.assertIn('HumsYar',pages[-1])
   forms=[p for p in pages if norm('نام جزوه‌نویس') in p];self.assertEqual(len(forms),12)
   for p in forms:
    for field in ['امضای نویسنده','تاریخ','شمارهٔ نسخه','اختلاف یا ابهام علمی برای بازبین','منابع این مبحث','پرسش باز']:self.assertIn(norm(field),p)
   self.assertTrue(any(norm('چک‌لیست خودآزمایی جلسه') in p for p in pages[-4:]))
   self.assertTrue(any(norm('قدم بعدی') in p for p in pages[-4:]))
   bookmarks=doc.get_toc();self.assertTrue(bookmarks)
   for topic in B.outline()['topics']:self.assertTrue(any(norm(topic['title']) in norm(x[1]) for x in bookmarks),topic['title'])

if __name__=='__main__':unittest.main()

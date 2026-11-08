"""Regression checks for session-ten source coverage and writer PDF."""
import hashlib,io,json,re,sys,unicodedata,unittest
from pathlib import Path
from PIL import Image
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'headneck/scripts'),str(ROOT/'render')]
import build_hn10_writer_final as B

def clean(s):
 s=unicodedata.normalize('NFKC',s).replace('\u200c','').replace('ي','ی').replace('ك','ک')
 return ''.join(c for c in s if not unicodedata.combining(c))

class SessionTenWriter(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pdf=ROOT/'pdf/HumsYar_HeadNeck_Jalase10_WRITER_FINAL.pdf'
  cls.manifest=ROOT/'headneck/reports/hn10_evidence/writer_manifest.json'
 def test_source_pages_and_figures(self):
  pages=B.source_pages();self.assertEqual(sorted(pages),list(range(1,9)))
  self.assertEqual(len(B.outline()['topics']),7)
  for n,figures in B.FIGS.items():
   for number,source,anchor,_ in figures:
    self.assertTrue(any(anchor in p for p in pages[n].splitlines()),(n,number,anchor))
    self.assertTrue((ROOT/f'headneck/images/hn10_candidates/lecture_{number}_p{source:02}.png').is_file())
  self.assertEqual(sum(len(x) for x in B.FIGS.values()),9)
  self.assertEqual(len(set(tuple(x) for x in B.W.GUIDES.values())),7)
 def test_pdf_includes_all_figures_pixel_exact(self):
  self.assertTrue(self.pdf.exists());m=json.loads(self.manifest.read_text());self.assertEqual(len(m['figures']),12);self.assertFalse(any(m['qa'].values()))
  with pymupdf.open(self.pdf) as doc:
   refs={im[0] for p in doc for im in p.get_images()};hashes=set()
   for ref in refs:
    im=Image.open(io.BytesIO(doc.extract_image(ref)['image'])).convert('RGB');hashes.add((im.size,hashlib.sha256(im.tobytes()).hexdigest()))
  for item in m['figures']:
   p=ROOT/item['asset'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),item['sha256'])
   im=Image.open(p).convert('RGB');self.assertIn((im.size,hashlib.sha256(im.tobytes()).hexdigest()),hashes)
 def test_source_words_and_marginal_layout(self):
  with pymupdf.open(self.pdf) as doc:
   self.assertEqual(len(doc),30);out=clean(' '.join(p.get_text() for p in doc))
   for n,s in B.source_pages().items():
    if n==8: continue
    for word in set(re.findall(r'[ء-غف-یپچژگ]{4,}',clean(s))):self.assertIn(word,out,(n,word))
   for i,p in enumerate(doc):
    if i not in (0,len(doc)-1):self.assertTrue(len(p.get_text().strip())>100 or p.get_images(),i+1)
 def test_front_handoffs_and_bookmarks(self):
  with pymupdf.open(self.pdf) as doc:
   pages=[clean(p.get_text()) for p in doc];self.assertIn(clean('ساختار این جزوه و قاعدهٔ خواندن آن'),pages[1]);self.assertIn('فهرست مطالب',pages[2])
   forms=[p for p in pages if clean('نام جزوه‌نویس') in p];self.assertEqual(len(forms),7)
   for p in forms:
    for field in ['امضای نویسنده','تاریخ','شمارهٔ نسخه','اختلاف یا ابهام علمی برای بازبین','منابع این مبحث','پرسش باز']:self.assertIn(clean(field),p)
   self.assertTrue(any(clean('چک‌لیست خودآزمایی جلسه') in p for p in pages[-4:]))
   for topic in B.outline()['topics']:self.assertTrue(any(clean(topic['title']) in clean(x[1]) for x in doc.get_toc()),topic['title'])
if __name__=='__main__':unittest.main()

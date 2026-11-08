"""Session-eleven coverage and writer-booklet regression checks."""
import hashlib,io,json,re,sys,unicodedata,unittest
from pathlib import Path
from PIL import Image
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'headneck/scripts'),str(ROOT/'render')]
import build_hn11_writer_final as B

def clean(s):
 s=unicodedata.normalize('NFKC',s).replace('\u200c','').replace('ي','ی').replace('ك','ک')
 return ''.join(c for c in s if not unicodedata.combining(c))
class SessionElevenWriter(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pdf=ROOT/'pdf/HumsYar_HeadNeck_Jalase11_WRITER_FINAL.pdf';cls.manifest=json.loads((ROOT/'headneck/reports/hn11_evidence/writer_manifest.json').read_text())
 def test_source_figure_and_reference_coverage(self):
  pages=B.source_pages();self.assertEqual(sorted(pages),list(range(1,21)));self.assertEqual(len(B.outline()['topics']),12)
  self.assertEqual(sum(len(x) for x in B.FIGURES.values()),14);self.assertEqual(sum(len(x) for x in B.REFS.values()),24)
  self.assertEqual(len(self.manifest['figures']),38);self.assertFalse(any(self.manifest['qa'].values()))
  self.assertEqual({f'hn11-T{i:02}' for i in range(1,13)},{x['topic'] for x in self.manifest['figures'] if 'hn11_refs/' in x['asset']})
  for n,figures in B.FIGURES.items():
   for num,_ in figures:self.assertTrue((ROOT/f'headneck/images/hn11_candidates/lecture_figure_{num}_p{n:02}.png').is_file())
 def test_all_images_present_pixel_exact(self):
  with pymupdf.open(self.pdf) as d:
   hashes=set()
   for ref in {im[0] for p in d for im in p.get_images()}:
    im=Image.open(io.BytesIO(d.extract_image(ref)['image'])).convert('RGB');hashes.add((im.size,hashlib.sha256(im.tobytes()).hexdigest()))
  for item in self.manifest['figures']:
   path=ROOT/item['asset'];self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),item['sha256'])
   im=Image.open(path).convert('RGB');self.assertIn((im.size,hashlib.sha256(im.tobytes()).hexdigest()),hashes,item['asset'])
 def test_source_words_forms_and_toc(self):
  with pymupdf.open(self.pdf) as d:
   self.assertEqual(len(d),63);pages=[clean(p.get_text()) for p in d];text=' '.join(pages)
   for n,s in B.source_pages().items():
    for word in set(re.findall(r'[ء-غف-یپچژگ]{4,}',clean(s))):self.assertIn(word,text,(n,word))
   self.assertIn(clean('ساختار این جزوه و قاعدهٔ خواندن آن'),pages[1]);self.assertIn('فهرست مطالب',pages[2])
   forms=[p for p in pages if clean('نام جزوه‌نویس') in p];self.assertEqual(len(forms),12)
   for p in forms:
    for field in ['امضای نویسنده','تاریخ','شمارهٔ نسخه','اختلاف یا ابهام علمی برای بازبین','منابع این مبحث','پرسش باز']:self.assertIn(clean(field),p)
   for t in B.outline()['topics']:self.assertTrue(any(clean(t['title']) in clean(x[1]) for x in d.get_toc()))
if __name__=='__main__':unittest.main()

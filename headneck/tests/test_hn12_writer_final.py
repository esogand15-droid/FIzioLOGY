import hashlib,io,json,re,sys,unicodedata,unittest
from pathlib import Path
import pymupdf
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'headneck/scripts'),str(ROOT/'render')]
import build_hn12_writer_final as B
def clean(s):
 s=unicodedata.normalize('NFKC',s).replace('\u200c','').replace('ي','ی').replace('ك','ک')
 return ''.join(c for c in s if not unicodedata.combining(c))
class Session12(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pdf=ROOT/'pdf/HumsYar_HeadNeck_Jalase12_WRITER_FINAL.pdf';cls.m=json.loads((ROOT/'headneck/reports/hn12_evidence/writer_manifest.json').read_text())
 def test_coverage(self):
  self.assertEqual(sorted(B.get_pages()),list(range(1,15)));self.assertEqual(len(B.outline()['topics']),8);self.assertEqual(len(self.m['figures']),30);self.assertFalse(any(self.m['qa'].values()));self.assertEqual(sum('hn12_candidates/' in i['asset'] for i in self.m['figures']),26)
 def test_images(self):
  with pymupdf.open(self.pdf) as d:
   hashes=set()
   for ref in {im[0] for p in d for im in p.get_images()}:
    im=Image.open(io.BytesIO(d.extract_image(ref)['image'])).convert('RGB');hashes.add((im.size,hashlib.sha256(im.tobytes()).hexdigest()))
  for item in self.m['figures']:
   path=ROOT/item['asset'];self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),item['sha256']);im=Image.open(path).convert('RGB');self.assertIn((im.size,hashlib.sha256(im.tobytes()).hexdigest()),hashes,item['asset'])
 def test_text_and_forms(self):
  with pymupdf.open(self.pdf) as d:
   pages=[clean(p.get_text()) for p in d];text=' '.join(pages);self.assertEqual(len(d),46)
   for n,s in B.get_pages().items():
    for w in set(re.findall(r'[ء-غف-یپچژگ]{4,}',clean(s))):self.assertIn(w,text,(n,w))
   self.assertIn(clean('ساختار این جزوه و قاعدهٔ خواندن آن'),pages[1]);self.assertIn('فهرست مطالب',pages[2]);self.assertEqual(sum(clean('نام جزوه‌نویس') in p for p in pages),8)
   for t in B.outline()['topics']:self.assertTrue(any(clean(t['title']) in clean(x[1]) for x in d.get_toc()))
if __name__=='__main__':unittest.main()

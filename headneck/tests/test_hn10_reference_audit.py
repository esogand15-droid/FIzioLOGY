"""Checks for the session-ten reference-image audit and preservation."""
import hashlib,io,json,re,sys,unicodedata,unittest
from pathlib import Path
from PIL import Image
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'headneck/scripts'),str(ROOT/'render')]
import build_hn10_reference_audit as B

def clean(s):
 s=unicodedata.normalize('NFKC',s).replace('\u200c','').replace('ي','ی').replace('ك','ک')
 return ''.join(c for c in s if not unicodedata.combining(c))

class ReferenceAudit(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pdf=ROOT/'pdf/HumsYar_HeadNeck_Jalase10_REFERENCE_AUDITED.pdf'
  cls.manifest=json.loads((ROOT/'headneck/reports/hn10_evidence/reference_audit_manifest.json').read_text())
 def test_coverage_and_citations(self):
  m=self.manifest;self.assertFalse(any(m['qa'].values()));self.assertEqual(len(m['figures']),25)
  self.assertEqual({f'hn10-T{i:02}' for i in range(1,8)}, {x['topic'] for x in m['figures'] if 'hn10_refs' in x['asset']})
  self.assertEqual(sum('hn10_candidates' in f['asset'] for f in m['figures']),9)
  self.assertEqual(sum('hn10_refs' in f['asset'] for f in m['figures']),16)
  old=json.loads((ROOT/'headneck/reports/hn10_evidence/writer_manifest.json').read_text())
  self.assertTrue({x['asset'] for x in old['figures']} <= {x['asset'] for x in m['figures']})
  for f in m['figures']:self.assertTrue(f['source'])
 def test_image_pixels(self):
  with pymupdf.open(self.pdf) as d:
   hashes=set()
   for ref in {img[0] for p in d for img in p.get_images()}:
    im=Image.open(io.BytesIO(d.extract_image(ref)['image'])).convert('RGB');hashes.add((im.size,hashlib.sha256(im.tobytes()).hexdigest()))
  for item in self.manifest['figures']:
   p=ROOT/item['asset'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),item['sha256'])
   im=Image.open(p).convert('RGB');self.assertIn((im.size,hashlib.sha256(im.tobytes()).hexdigest()),hashes,item['asset'])
 def test_text_structure(self):
  with pymupdf.open(self.pdf) as d:
   self.assertEqual(len(d),42);pages=[clean(p.get_text()) for p in d];text=' '.join(pages)
   self.assertIn(clean('ساختار این جزوه و قاعدهٔ خواندن آن'),pages[1]);self.assertIn('فهرست مطالب',pages[2])
   self.assertEqual(sum(clean('نام جزوه‌نویس') in p for p in pages),7)
   for n,s in B.source_pages().items():
    if n==8:continue
    for word in set(re.findall(r'[ء-غف-یپچژگ]{4,}',clean(s))):self.assertIn(word,text,(n,word))
   for topic in B.outline()['topics']:self.assertTrue(any(clean(topic['title']) in clean(x[1]) for x in d.get_toc()))
 def test_audit_assets_and_source_rects(self):
  records=json.loads((ROOT/'headneck/reports/hn10_evidence/reference_audit_candidates.json').read_text());self.assertEqual(len(records),13)
  for x in records:
   self.assertTrue((ROOT/x['source']).exists());self.assertEqual(hashlib.sha256((ROOT/x['asset']).read_bytes()).hexdigest(),x['sha256'])
   with pymupdf.open(ROOT/x['source']) as d:self.assertLessEqual(x['page'],len(d))
if __name__=='__main__':unittest.main()

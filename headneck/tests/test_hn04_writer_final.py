"""Regression checks for the session-four writer edition."""
import collections,hashlib,json,sys,unittest,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'headneck/scripts'))
import pymupdf
import build_hn04_writer_final as B

class SessionFourWriterTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.base,cls.content,cls.outline=B.inputs()
 def test_preserves_reconciled_content_and_topic_checks(self):
  self.assertEqual(len(self.outline['topics']),20)
  self.assertEqual(sum(len(v) for v in self.content.values()),699)
  self.assertEqual(sum(b['type']=='plate' for rows in self.content.values() for b in rows),69)
  self.assertEqual(len(set(tuple(c) for c in B.W.GUIDES.values())),20)
  self.assertEqual(len(set(B.W.REVIEW.values())),20)
  for i,t in enumerate(self.outline['topics'],1):
   rows=self.content[t['topic_id']]
   self.assertEqual(rows[0]['type'],'idcard');self.assertEqual(rows[-1]['type'],'handoff')
   self.assertEqual(len(B.W.GUIDES[i]),3);self.assertTrue(rows[-1]['question'])
  self.assertTrue(any('пирамид' in x.get('text','') for x in self.content['hn04-T20']))
  self.assertTrue(any('Lesser Palatine Foramina & Greater' in x.get('text','') for x in self.content['hn04-T16']))
  self.assertTrue(any('Canal & Posterior Condylar Fossa' in x.get('text','') for x in self.content['hn04-T18']))
 def test_prior_figures_preserved_and_embedded(self):
  path=ROOT/'.cache/hn04_writer_update/HumsYar_HeadNeck_Jalase4_WRITER_FINAL.pdf'
  manifest=ROOT/'.cache/hn04_writer_update/manifest.json'
  if not path.exists() or not manifest.exists():self.skipTest('Generated output not present')
  old=json.loads((ROOT/'headneck/reports/hn04_final_evidence/machine_manifest.json').read_text())['figures']
  new=json.loads(manifest.read_text())['figures']
  self.assertEqual(collections.Counter((r['topic_id'],r['asset'],r['asset_sha256']) for r in old),collections.Counter((r['topic'],r['asset'],r['sha256']) for r in new))
  with pymupdf.open(path) as doc:
   xrefs={im[0] for p in doc for im in p.get_images()}
   hashes={hashlib.sha256(doc.extract_image(x)['image']).hexdigest() for x in xrefs}
  self.assertTrue(all(r['sha256'] in hashes for r in new))
 def test_fields_and_closing_checklist(self):
  path=ROOT/'.cache/hn04_writer_update/HumsYar_HeadNeck_Jalase4_WRITER_FINAL.pdf'
  if not path.exists():self.skipTest('Generated output not present')
  def norm(s):return unicodedata.normalize('NFKC',s).replace('\u200c','').replace('ٔ','')
  with pymupdf.open(path) as doc:
   pages=[norm(p.get_text()) for p in doc]
   forms=[p for p in pages if norm('نام جزوه‌نویس') in p]
   self.assertEqual(len(forms),20)
   for form in forms:
    for field in ['امضای نویسنده','تاریخ','شمارهٔ نسخه','اختلاف یا ابهام علمی برای بازبین','منابع این مبحث','پرسش باز']:
     self.assertIn(norm(field),form)
   self.assertIn(norm('چک‌لیست خودآزمایی جلسه'),pages[-1])
   self.assertGreaterEqual(len(doc),100)
 def test_original_final_unchanged(self):
  path=ROOT/'pdf/HumsYar_HeadNeck_Jalase4_FINAL.pdf'
  if not path.exists():self.skipTest('Original PDF not in checkout')
  self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),'85e6c0b234f14592d399f234039138d15eee870fdc2e4f22cece234c7e72714b')

if __name__=='__main__':unittest.main()

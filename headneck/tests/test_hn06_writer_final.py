"""Regression tests for the session-six writer edition."""
import collections,hashlib,json,sys,unittest,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'headneck/scripts'),str(ROOT/'render')]
import pymupdf
import build_hn06_writer_final as B

class SessionSixWriterTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.base,cls.content,cls.outline=B.inputs()
 def test_all_topics_and_distinct_delivery_material(self):
  self.assertEqual(len(self.outline['topics']),11)
  self.assertEqual(sum(len(v) for v in self.content.values()),316)
  self.assertEqual(len(set(tuple(v) for v in B.W.GUIDES.values())),11)
  self.assertEqual(len(set(B.W.QUESTIONS.values())),11)
  self.assertEqual(len(set(B.W.REVIEW.values())),11)
  for i,t in enumerate(self.outline['topics'],1):
   self.assertEqual(len(B.W.GUIDES[i]),3)
   self.assertEqual(self.content[t['topic_id']][0]['type'],'idcard')
   self.assertEqual(self.content[t['topic_id']][-1]['type'],'handoff')
 def test_figure_and_block_coverage(self):
  path=ROOT/'.cache/hn06_writer_update/HumsYar_HeadNeck_Jalase6_WRITER_FINAL.pdf';manifest=ROOT/'.cache/hn06_writer_update/manifest.json'
  if not path.exists() or not manifest.exists():self.skipTest('Generated PDF not present')
  data=json.loads(manifest.read_text());old=json.loads((ROOT/'headneck/reports/hn06_final_evidence/machine_manifest.json').read_text())['figures']
  expected={}
  for tid,blocks in self.content.items():
   for pos,block in enumerate(B.decoded(blocks)[1:-1],1):
    for key in ('src','citation','title','footer','kicker'):
     if key in block:block[key]=B.clean(block[key])
    expected[tid+':'+str(pos)]=hashlib.sha256(json.dumps(block,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
  self.assertEqual(len(expected),316-22)
  self.assertEqual(data['block_sha256'],expected)
  self.assertEqual(collections.Counter((r['topic'],r['asset'],r['asset_sha256']) for r in old),collections.Counter((r['topic'],r['asset'],r['sha256']) for r in data['figures']))
  with pymupdf.open(path) as d:
   xrefs={im[0] for p in d for im in p.get_images()}
   hashes={hashlib.sha256(d.extract_image(x)['image']).hexdigest() for x in xrefs}
  self.assertTrue(all(r['sha256'] in hashes for r in data['figures']))
  self.assertFalse(any(data['qa'].values()))
 def test_form_fields_and_shared_shell(self):
  path=ROOT/'.cache/hn06_writer_update/HumsYar_HeadNeck_Jalase6_WRITER_FINAL.pdf'
  if not path.exists():self.skipTest('Generated PDF not present')
  def norm(s):return unicodedata.normalize('NFKC',s).replace('\u200c','').replace('ٔ','')
  with pymupdf.open(path) as doc:
   pages=[norm(p.get_text()) for p in doc]
   self.assertIn(norm('ساختار این جزوه و قاعدهٔ خواندن آن'),pages[1]);self.assertIn(norm('فهرست مطالب'),pages[2]);self.assertIn('HumsYar',pages[-1])
   forms=[p for p in pages if norm('نام جزوه‌نویس') in p];self.assertEqual(len(forms),11)
   for p in forms:
    for field in ['امضای نویسنده','تاریخ','شمارهٔ نسخه','اختلاف یا ابهام علمی برای بازبین','منابع این مبحث','پرسش باز']:self.assertIn(norm(field),p)
   self.assertTrue(any(norm('چک‌لیست خودآزمایی جلسه') in p for p in pages[-4:]))
 def test_previous_final_not_overwritten(self):
  path=ROOT/'pdf/HumsYar_HeadNeck_Jalase6_FINAL.pdf'
  self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),'d05692679a604d622dd43dc6b87ef1d985e968d06df85fd3926f572b80721204')

if __name__=='__main__':unittest.main()

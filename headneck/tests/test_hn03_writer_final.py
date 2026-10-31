"""Coverage and presentation checks for the session-three writer edition."""
import collections,json,sys,unittest,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'headneck/scripts'))
import pymupdf
import build_hn03_writer_final as B

class SessionThreeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.base,cls.plan,cls.outline,cls.assets,cls.overlay,cls.transcription_count,cls.transcription=B.inputs()
 def test_topics_checklists_and_educational_answers(self):
  self.assertEqual(len(self.outline['topics']),19)
  self.assertEqual(len(set(tuple(v) for v in B.W.GUIDES.values())),19)
  for i,t in enumerate(self.outline['topics'],1):
   self.assertEqual(len(B.W.GUIDES[i]),3)
   self.assertTrue(B.W.ANSWERS[i])
   self.assertEqual(sum(x['type']=='handoff' for x in self.plan[t['topic_id']]),1)
 def test_all_transcription_blocks_assigned_once(self):
  file=ROOT/'.cache/master_01_06/historical/headneck/reports/HN_S03_TRANSCRIPTION_TOPIC_MAP_WIP.json'
  mapping=json.loads(file.read_text())['topics']
  def key(page,b):return page,json.dumps(b,ensure_ascii=False,sort_keys=True)
  original=collections.Counter(key(p['pdf_page'],b) for p in self.transcription['pages'] for b in p['blocks'] if b['type']!='image')
  mapped=collections.Counter(key(r['source_pdf_page'],r['block']) for rows in mapping.values() for r in rows)
  self.assertEqual(original,mapped)
 def test_figures_are_all_carried_into_output(self):
  manifest=ROOT/'.cache/hn03_writer_update/manifest.json'
  if not manifest.exists():self.skipTest('Generated output not present')
  actual={x['asset'] for x in json.loads(manifest.read_text())['figures']}
  expected={b['asset'] for p in self.transcription['pages'] for b in p['blocks'] if b['type']=='image'}
  self.assertEqual(len(expected),26);self.assertTrue(expected.issubset(actual))
  self.assertEqual(len(json.loads(manifest.read_text())['figures']),43)
 def test_form_fields_and_final_checklist_in_pdf(self):
  path=ROOT/'.cache/hn03_writer_update/HumsYar_HeadNeck_Jalase3_WRITER_FINAL.pdf'
  if not path.exists():self.skipTest('Generated output not present')
  def norm(s):return unicodedata.normalize('NFKC',s).replace('\u200c','').replace('ٔ','')
  with pymupdf.open(path) as doc:
   pages=[norm(p.get_text()) for p in doc]
   forms=[p for p in pages if norm('نام جزوه‌نویس') in p]
   self.assertEqual(len(forms),19)
   for form in forms:
    for field in ['امضای نویسنده','تاریخ','شمارهٔ نسخه','اختلاف یا ابهام علمی برای بازبین','منابع این مبحث','پرسش باز']:
     self.assertIn(norm(field),form)
   self.assertIn(norm('چک‌لیست خودآزمایی جلسه'),pages[-1])
   self.assertGreaterEqual(len(doc),98)

if __name__=='__main__':unittest.main()

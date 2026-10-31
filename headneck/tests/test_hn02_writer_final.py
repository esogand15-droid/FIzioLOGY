"""Session-two writer edition structure and preserved source inputs."""
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'headneck/scripts'))
import build_hn02_writer_final as B

class SessionTwoWriterTests(unittest.TestCase):
 def test_original_blocks_and_overlay(self):
  base,plan,outline,_,count=B.inputs()
  self.assertEqual((len(base),len(outline['topics']),sum(len(t['blocks']) for t in base),count),(21,21,253,94))
  for topic in base:
   rows=plan[topic['topic_id']]
   self.assertEqual(sum(x['type']=='idcard' for x in rows),1)
   self.assertEqual(len(rows[0]['rows']),5)
   for i,old in enumerate(topic['blocks']):
    new=next(x for x in rows if x['_origin']==f'base:{i}')
    if old['type'] in ('p','ul','ol'):
     for key in ('text','items'):
      if key in old:self.assertEqual(old[key],new[key])

 def test_every_topic_has_writer_guide_and_question(self):
  self.assertEqual(set(B.W.GUIDES),set(range(1,22)))
  self.assertTrue(all(all(x) for x in B.W.GUIDES.values()))
  self.assertEqual(len(B.W.TABLES),5)
  self.assertEqual(len(B.W.PATHS),4)

 def test_t20_source_sentence_not_silently_discarded(self):
  _,plan,_,_,_=B.inputs()
  rows=plan['hn02-T20']
  self.assertTrue(any('نقل بخش مربوط از صفحهٔ ۲۷' in q.get('text','') for q in rows))
  script=(ROOT/'headneck/scripts/build_hn02_writer_final.py').read_text()
  self.assertIn("quote.split('«',1)[1].split('»',1)[0]",script)
  self.assertIn("tid=='hn02-T11' and origin=='base:8'",script)

 def test_output_and_checklist(self):
  manifest=ROOT/'.cache/hn02_writer_final/manifest.json'
  if not manifest.exists():self.skipTest('Local build not present')
  m=json.loads(manifest.read_text())
  self.assertEqual(len(m['topics']),21)
  self.assertEqual(len(m['figures']),65)
  self.assertFalse(any(m['qa'].values()))
  self.assertEqual(B.R.sha(ROOT/m['file']),m['sha256'])
  self.assertTrue(any(x[1]=='جمع‌بندی، چک‌لیست و برگهٔ تحویل' for x in m['bookmarks']))

if __name__=='__main__':unittest.main()

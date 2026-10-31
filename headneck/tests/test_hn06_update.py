"""Session-six regression checks; not a substitute for source/scientific reading."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'render'),str(ROOT/'headneck/scripts')]
import hn_updates as U
import build_headneck as B
from prepare_hn06_update import build

class SessionSix(unittest.TestCase):
 def setUp(self):
  self.base={t['topic_id']:t['blocks'] for name in ('hn06_a.json','hn06_b.json') for t in json.loads((ROOT/'headneck/content'/name).read_text())}
  self.overlay=json.loads((ROOT/'headneck/content/hn06_update.json').read_text())
 def test_baseline_bytes_unchanged(self):
  for name in ('hn06_a.json','hn06_b.json','hn06_transcription.json'):
   path='headneck/content/'+name
   old=subprocess.check_output(['git','show','026cbcc1191751a491bcb37675adcb2cb8c827d0:'+path],cwd=ROOT)
   self.assertEqual(old,(ROOT/path).read_bytes())
  self.assertEqual(hashlib.sha256((ROOT/'pdf/HumsYar_HeadNeck_Jalase6.pdf').read_bytes()).hexdigest(),'fd92b99026629cff963965eea6d5b8546f6b9eff6f91b48a958cd8fdf37dd50f')
 def test_deterministic_generation(self):self.assertEqual(build(),self.overlay)
 def test_eleven_topic_additions(self):
  self.assertEqual(set(self.base),set(self.overlay['topics']))
  self.assertEqual(len(self.base),11)
  for spec in self.overlay['topics'].values():
   blocks=[b for bs in spec['after'].values() for b in bs]
   self.assertEqual(sum(b['type']=='table' for b in blocks),1)
   self.assertEqual(sum(b['type']=='callout' for b in blocks),1)
   self.assertTrue(all(b.get('src') for b in blocks if b['type'] in ('table','callout')))
 def test_original_blocks_and_order_preserved(self):
  snapshot=copy.deepcopy(self.base);out=U.apply_update('hn06',self.base)
  self.assertEqual(snapshot,self.base)
  for tid,blocks in self.base.items():
   spec=self.overlay['topics'][tid];cursor=0
   for i,b in enumerate(blocks):
    expected=copy.deepcopy(b)
    if i==0:expected['rows']+=spec['card_rows']
    expected.update(spec.get('plate_overrides',{}).get(str(i),{}))
    self.assertEqual(out[tid][cursor],expected,(tid,i))
    cursor+=1+len(spec['after'].get(str(i),[]))
   self.assertEqual(cursor,len(out[tid]));self.assertEqual(out[tid][-1]['type'],'handoff')
 def test_assets_and_twenty_nine_plates(self):
  out=U.apply_update('hn06',self.base)
  plates=[b for bs in out.values() for b in bs if b['type']=='plate']
  self.assertEqual(len(plates),29)
  idx={x['path']:x for x in json.loads((ROOT/'headneck/images/INDEX.json').read_text())['assets']}
  for b in plates:
   self.assertTrue((ROOT/b['asset']).is_file());self.assertIn(b['asset'],idx)
   if '_u_' in b['asset']:
    self.assertIn('PDF',b['citation']);self.assertTrue(b.get('en_caption'))
    self.assertGreaterEqual(len(b['labels']),3)
    a=idx[b['asset']];self.assertTrue((ROOT/a['source_file']).is_file())
 def test_separate_published_path(self):
  import qa_headneck as Q
  self.assertEqual(B.HN_SESSIONS['hn06']['pdf_name'],'HumsYar_HeadNeck_Jalase6_FINAL.pdf')
  self.assertEqual(Q.SESSIONS['hn06']['pdf'].name,'HumsYar_HeadNeck_Jalase6_FINAL.pdf')
  self.assertNotEqual(Q.SESSIONS['hn06']['report'].name,'HN_S06_QA_REPORT.md')

 def test_reference_coordinates_inside_pages(self):
  import pymupdf
  from hn06_update_assets import SPECS
  for slug,path,page,box,*_ in SPECS:
   with pymupdf.open(path) as doc:
    self.assertTrue(doc[page-1].rect.contains(pymupdf.Rect(box)),slug)
 def test_recorded_evidence_is_byte_consistent(self):
  from verify_hn06_final_evidence import verify
  self.assertEqual(verify()['pages'],60)
 def test_transcription_preserved_in_order(self):
  source=[b['text'] for p in json.loads((ROOT/'headneck/content/hn06_transcription.json').read_text())['pages'] for b in p['blocks']]
  body=[]
  for blocks in self.base.values():
   for b in blocks:
    if b['type'] in ('p','h3'):body.append(b['text'])
    elif b['type']=='table':body.extend([' | '.join(b['head'])]+[' | '.join(row) for row in b['rows']])
  self.assertEqual(body,source)

if __name__=='__main__':unittest.main()

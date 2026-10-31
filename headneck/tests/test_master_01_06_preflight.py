"""Coverage/anti-false-final checks; not a scientific or visual approval test."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('master_audit',ROOT/'headneck/scripts/audit_master_01_06.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
OUT=ROOT/'headneck/master_01_06'
class MasterPreflight(unittest.TestCase):
 def test_all_topics_include_both_content_parts(self):
  m=json.loads((OUT/'topic_matrix.json').read_text());self.assertEqual(len(m['topics']),102)
  for n,count in [(1,17),(2,21),(3,19),(4,20),(5,14),(6,11)]:
   self.assertEqual(sum(t['session']==n for t in m['topics']),count)
  self.assertEqual(sum(t['A']['block_count'] for t in m['topics']),1950)
  for n in range(1,4):self.assertTrue(any(t['session']==n and t['A']['baseline_file'].endswith('_b.json') for t in m['topics']))
 def test_all_primary_sources_in_inventory(self):
  ex=json.loads((OUT/'extraction_inventory.json').read_text());ps=[s for s in ex['files'] if s['role']=='PRIMARY_LECTURE']
  self.assertEqual(len(ps),7);self.assertEqual(sum(s['pages'] for s in ps),179)
  self.assertEqual({s['session'] for s in ps},set(range(1,7)))
 def test_current_state_cannot_be_called_final(self):
  r=A.audit();self.assertEqual(r['status'],'BLOCKED_DO_NOT_BUILD_OR_PUBLISH_FINAL')
  self.assertTrue(any('content review not cleared' in e for e in r['errors']))
  self.assertTrue(any('individual images/subpanels' in e for e in r['errors']))
  self.assertEqual(r['information']['topics_cleared'],0)
 def test_changed_live_source_is_not_blessed_by_saved_manifest(self):
  target=ROOT/'pdf/HumsYar_HeadNeck_Jalase4.pdf';original=A.sha
  def altered(path):return 'not-the-recorded-source-hash' if path==target else original(path)
  with patch.object(A,'sha',altered):r=A.audit()
  self.assertTrue(any('Extraction source changed: pdf/HumsYar_HeadNeck_Jalase4.pdf' in e for e in r['errors']))
 def test_published_filename_is_one_unified_document(self):
  self.assertEqual(A.FINAL_NAME,'HumsYar_Master_Sessions_01-06_Updated.pdf')
 def test_prebuild_is_not_a_final_pdf_review(self):
  r=A.audit('final');self.assertTrue(any('single requested final PDF' in e for e in r['errors']))
  self.assertTrue(any('every page of this exact SHA' in e for e in r['errors']))
 def test_missing_clearance_and_unsupported_frequency_are_blocking(self):
  original=A.load
  def load(name,default=None):
   if name=='educational_additions.json':return {'topics':{'hn01-T01':{'exam_claims':[{'kind':'FREQUENT_IN_EXAMS','text':'unsupported'}]}}}
   return original(name,default)
  with patch.object(A,'load',load):r=A.audit()
  self.assertTrue(any('unsupported exam frequency claim' in e for e in r['errors']))
 def test_images_and_pages_are_separate_units(self):
  rows=[json.loads(l) for l in (OUT/'vision_reviews.jsonl').read_text().splitlines()]
  self.assertEqual(len(rows),11);self.assertEqual(len({r['image_id'] for r in rows}),11)
  self.assertEqual(sum(len(r['analysis']['subpanels']) for r in rows),16)
  self.assertTrue(all(r['analysis']['final_pdf_location'] is None for r in rows))
 def test_hard_palate_conflict_is_not_silently_corrected(self):
  r=next(r for r in json.loads((OUT/'scientific_issues.json').read_text())['issues'] if r['id']=='C-005')
  self.assertEqual(r['status'],'INTRA_REFERENCE_DISCREPANCY_DOCUMENTED_NOT_YET_INTEGRATED')
  self.assertEqual({x['pdf_page'] for x in r['verified_references']},{116,133})
  self.assertEqual({x['printed_page'] for x in r['verified_references']},{1088,1105})
 def test_no_automatic_topic_approval_from_ocr(self):
  r=json.loads((OUT/'ocr_run.json').read_text());self.assertEqual(r['status'],'OCR_COMPLETE_NOT_VERIFIED')
  self.assertEqual(r['completed'],1394)
if __name__=='__main__':unittest.main()

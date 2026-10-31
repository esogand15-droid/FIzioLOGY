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
  self.assertGreaterEqual(len(rows),53);self.assertEqual(len({r['image_id'] for r in rows}),len(rows))
  seed_ids={f'IMG-{n:06}' for n in [9266,9279,9280,9288,9289,9297,9301,9302,9303,9304,9305]}
  self.assertEqual(sum(len(r['analysis']['subpanels']) for r in rows if r['image_id'] in seed_ids),16)
  self.assertTrue(all(r['analysis']['final_pdf_location'] is None for r in rows))
  keyed={r['image_id']:r for r in rows}
  self.assertEqual(keyed['IMG-009341']['analysis']['decision'],'KEEP_AS_REQUIRED_FIGURE_LEGEND')
  self.assertEqual(keyed['IMG-009366']['analysis']['decision'],'HOLD_UNLABELLED_POINTER_TARGET')
  self.assertTrue(any(p['status']=='PENDING_DETAIL' for p in keyed['IMG-009315']['analysis']['subpanels']))
 def test_session_one_authoring_is_substantive_but_not_clearance(self):
  additions=json.loads((OUT/'educational_additions.json').read_text())['topics']
  self.assertTrue({f'hn01-T{i:02}' for i in range(1,18)}<=set(additions))
  for tid,b in additions.items():
   self.assertTrue(A.REQUIRED_B.issubset(b),tid)
   self.assertTrue(b['comparison']['rows'],tid)
   self.assertTrue(b['diagram']['edges'],tid)
   nodes={r['id'] for r in b['diagram']['nodes']}
   for edge in b['diagram']['edges']:self.assertTrue(set(edge)<=nodes,tid)
   self.assertNotIn('CLEARED_AFTER_CONTENT_AND_FIGURE_REVIEW',b['status'])
 def test_reconciliation_does_not_rewrite_or_bless_baseline(self):
  d=json.loads((OUT/'source_reconciliation_hn01.json').read_text())
  self.assertEqual(len(d['blocks']),75)
  self.assertFalse(d['proposed_typographic_corrections'])
  self.assertEqual(d['retracted_typographic_candidates'][0]['status'],'RETRACTED_AFTER_ACTUAL_SOURCE_CROP_REVIEW')
  self.assertTrue(all(r['comparison']=='CONTENT_COMPARED_WITH_ORIGINAL_PAGE_IMAGES_NOT_VERBATIM_CERTIFIED' for r in d['blocks']))
 def test_new_evidence_does_not_claim_birth_development_or_fourth_fossa(self):
  issues={r['id']:r for r in json.loads((OUT/'scientific_issues.json').read_text())['issues']}
  self.assertEqual(issues['C-011']['status'],'DIRECT_DEVELOPMENTAL_REFERENCE_STILL_NEEDED')
  self.assertEqual(issues['C-010']['status'],'TERMINOLOGY_SCOPE_UNRESOLVED_LIMITATION_AUTHORED')
 def test_hard_palate_conflict_is_not_silently_corrected(self):
  r=next(r for r in json.loads((OUT/'scientific_issues.json').read_text())['issues'] if r['id']=='C-005')
  self.assertEqual(r['status'],'INTRA_REFERENCE_DISCREPANCY_DOCUMENTED_NOT_YET_INTEGRATED')
  self.assertEqual({x['pdf_page'] for x in r['verified_references']},{116,133})
  self.assertEqual({x['printed_page'] for x in r['verified_references']},{1088,1105})
 def test_no_automatic_topic_approval_from_ocr(self):
  r=json.loads((OUT/'ocr_run.json').read_text());self.assertEqual(r['status'],'OCR_COMPLETE_NOT_VERIFIED')
  self.assertEqual(r['completed'],1394)
if __name__=='__main__':unittest.main()

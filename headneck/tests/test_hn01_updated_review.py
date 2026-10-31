"""The requested review must never impersonate the final six-session release."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'headneck/scripts/build_hn01_updated_review.py'
DATA = ROOT / 'headneck/master_01_06'

class ReviewPublicationTests(unittest.TestCase):
    def test_all_saved_baseline_blocks_and_current_teaching_topics(self):
        spec = importlib.util.spec_from_file_location('hn01_review', SCRIPT)
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        # Reuse the verified historical sources when cache is present; absence
        # of an ignored cache is not mistaken for a missing committed artifact.
        history = json.loads((DATA / 'historical_sources.json').read_text())
        rows = [r for r in history['files'] if r['file'] in
                ['headneck/content/hn01_a.json','headneck/content/hn01_b.json']]
        if all((ROOT / r['workspace_file']).exists() for r in rows):
            baseline, assets, outline = builder.inputs()
            self.assertEqual(sum(len(t['blocks']) for t in baseline), 187)
            self.assertEqual([t['topic_id'] for t in baseline],
                             [t['topic_id'] for t in outline['topics']])
        topics = builder.load('educational_additions.json')['topics']
        self.assertEqual(len(topics), 17)
        for t in topics.values():
            ids = {n['id'] for n in t['diagram']['nodes']}
            self.assertTrue(all(a in ids and b in ids for a,b in t['diagram']['edges']))

    def test_no_old_overlay_or_pdf_concatenation(self):
        tree = ast.parse(SCRIPT.read_text())
        calls = {n.func.attr for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertNotIn('apply_update', calls)
        self.assertNotIn('insert_pdf', calls)
        self.assertIn('render_blocks', calls)

    def test_receipt_never_claims_final_clearance(self):
        r = json.loads((DATA / 'hn01_review_publication.json').read_text())
        b = r['build']
        self.assertFalse(b['scientific_clearance'])
        self.assertFalse(b['all_pages_visually_reviewed'])
        self.assertFalse(b['master_final_gate_overridden'])
        self.assertTrue(r['master_final_gate_unchanged'])
        self.assertEqual(r['cleared_topics'], 0)
        self.assertEqual(b['baseline_blocks'], 187)
        self.assertEqual(b['new_graphs'], 17)
        self.assertEqual(len(r['visual_review']['pages']), 13)
        self.assertEqual(r['visual_review']['pdf_sha256'], b['sha256'])
        self.assertEqual(r['mechanical_checks']['pdf_sha256'], b['sha256'])
        pdf = ROOT / b['file']
        if pdf.exists():
            self.assertEqual(hashlib.sha256(pdf.read_bytes()).hexdigest(), b['sha256'])

    def test_every_topic_still_uncleared(self):
        matrix = json.loads((DATA / 'topic_matrix.json').read_text())
        self.assertTrue(all(t['current_mission_review'] == 'NOT_COMPLETE'
                            for t in matrix['topics']))
        self.assertIn('غیرنهایی', SCRIPT.read_text())

if __name__ == '__main__':
    unittest.main()

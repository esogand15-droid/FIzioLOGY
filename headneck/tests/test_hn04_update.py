"""Integration checks of the additive layer, not a source transcription/science audit."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'render'))
sys.path.insert(0,str(ROOT/'headneck/scripts'))
import hn_updates as U
import build_headneck as B
from prepare_hn04_update import build

class SessionFour(unittest.TestCase):
    def setUp(self):
        self.base={t['topic_id']:t['blocks'] for t in json.loads((ROOT/'headneck/content/hn04_a.json').read_text())}
        self.overlay=json.loads((ROOT/'headneck/content/hn04_update.json').read_text())
    def test_default_does_not_overwrite_published_baseline(self):
        import qa_headneck as Q
        self.assertEqual(B.HN_SESSIONS["hn04"]["pdf_name"],"HumsYar_HeadNeck_Jalase4_FINAL.pdf")
        self.assertEqual(Q.SESSIONS["hn04"]["pdf"].name,"HumsYar_HeadNeck_Jalase4_FINAL.pdf")

    def test_baseline_fingerprint(self):
        self.assertEqual(hashlib.sha256((ROOT/'headneck/content/hn04_a.json').read_bytes()).hexdigest(),
                         '551817b682eef44694452b445cc761a5d294aab40b73259c625075c08fc5faf3')
    def test_deterministic_generator(self):
        self.assertEqual(build(),self.overlay)
    def test_all_twenty_topics(self):
        self.assertEqual(set(self.base),set(self.overlay['topics']))
        self.assertEqual(len(self.base),20)
        for spec in self.overlay['topics'].values():
            added=[b for blocks in spec['after'].values() for b in blocks]
            self.assertEqual(sum(b['type']=='table' for b in added),1)
            for b in added:
                if b['type'] in ('p','table','callout'):self.assertTrue(b.get('src'))
    def test_pure_addition_and_lecture_text_order(self):
        snapshot=copy.deepcopy(self.base)
        result=U.apply_update('hn04',self.base)
        self.assertEqual(self.base,snapshot)
        for tid,original in self.base.items():
            spec=self.overlay['topics'][tid];cursor=0
            for i,b in enumerate(original):
                actual=result[tid][cursor]; expected=copy.deepcopy(b)
                if i==0:expected['rows']+=spec['card_rows']
                if str(i) in spec.get('plate_overrides',{}):expected.update(spec['plate_overrides'][str(i)])
                if str(i) in spec.get('source_reconciliation',{}):
                    patch=spec['source_reconciliation'][str(i)]
                    self.assertEqual(expected['text'],patch['expected_text'])
                    expected['text']=patch['text']
                    expected['src']=f"مقابلهٔ تیتر با اصل منبع؛ بخش ۲، صفحهٔ واقعی PDF {patch['source_pdf_page']}"
                self.assertEqual(actual,expected,f'{tid} base block {i}')
                cursor+=1+len(spec['after'].get(str(i),[]))
            self.assertEqual(cursor,len(result[tid]))
            self.assertEqual(result[tid][-1]['type'],'handoff')
    def test_unrelated_sessions_noop(self):
        for session in ('hn03','hn07','hn08','hn09','hn10','hn11','hn12','hn13'):
            with patch.dict(os.environ,{'HUMSYAR_HN03_WIP':'0'}):
                self.assertIs(U.apply_update(session,self.base),self.base)
    def test_prior_overlay_sessions_still_work(self):
        # Exercise unchanged hn01/hn02 behavior using an isolated tiny fixture.
        with tempfile.TemporaryDirectory() as d:
            fixture={'topics':{'t':{'card_rows':[], 'after':{'1':[{'type':'h3','text':'added'}]}}}}
            for session in ('hn01','hn02'):
                Path(d,f'{session}_update.json').write_text(json.dumps(fixture))
                original={'t':[{'type':'idcard','rows':[]},{'type':'ul','items':['one']},{'type':'handoff'}]}
                with patch.object(U,'CONTENT',Path(d)):
                    result=U.apply_update(session,original)
                self.assertEqual(result['t'][1]['type'],'ol')
                self.assertEqual(result['t'][2]['text'],'added')
                self.assertEqual(original['t'][1]['type'],'ul')
    def test_two_independent_pdf_page_ranges(self):
        self.assertEqual(B.page_range([2,3],part_labels=True),'بخش ۱: ۲–۳')
        self.assertEqual(B.page_range([102,103],part_labels=True),'بخش ۲: ۲–۳')
        self.assertEqual(B.page_range([2,102],part_labels=True),'بخش ۱: ۲ · بخش ۲: ۲')
        self.assertEqual(B.page_range([2,3]),'۲–۳')
    def test_reference_assets_exist_and_pdf_pages_are_explicit(self):
        result=U.apply_update('hn04',self.base)
        idx={a['path']:a for a in json.loads((ROOT/'headneck/images/INDEX.json').read_text())['assets']}
        plates=[b for bs in result.values() for b in bs if b['type']=='plate']
        self.assertEqual(len(plates),69)
        for b in plates:
            self.assertTrue((ROOT/b['asset']).is_file())
            self.assertIn(b['asset'],idx)
            if b['book']=='grays':self.assertIn('PDF',b['citation'])
        self.assertEqual(idx['headneck/images/hn04_grays_f825.jpeg']['page'],93)
        self.assertEqual(idx['headneck/images/hn04_grays_f826.jpeg']['page'],95)
    def test_explicit_heading_reconciliation_only(self):
        patches=[(tid,k,p) for tid,s in self.overlay['topics'].items() for k,p in s.get('source_reconciliation',{}).items()]
        self.assertEqual(len(patches),3)
        for tid,k,p in patches:
            self.assertEqual(self.base[tid][int(k)]['type'],'h3')
            self.assertEqual(p['expected_text'],self.base[tid][int(k)]['text'])
            self.assertTrue(p['reason'])
        self.assertIn('пирамид',self.overlay['topics']['hn04-T20']['source_reconciliation']['10']['text'])
    def test_stale_reconciliation_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            malformed=copy.deepcopy(self.overlay)
            malformed['topics']['hn04-T20']['source_reconciliation']['10']['expected_text']='stale'
            Path(d,'hn04_update.json').write_text(json.dumps(malformed))
            with patch.object(U,'CONTENT',Path(d)),self.assertRaises(ValueError):
                U.apply_update('hn04',self.base)
    def test_bad_insertion_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            malformed=copy.deepcopy(self.overlay)
            malformed['topics']['hn04-T01']['after']['99999']=[]
            Path(d,'hn04_update.json').write_text(json.dumps(malformed))
            with patch.object(U,'CONTENT',Path(d)),self.assertRaises(ValueError):
                U.apply_update('hn04',self.base)


class FinalEvidence(unittest.TestCase):
    def test_final_evidence_identity_and_coverage(self):
        from verify_hn04_final_evidence import verify
        result = verify()
        self.assertEqual(result['output_pages'], 122)
        self.assertEqual(result['source_pages'], 39)
        self.assertEqual(result['reference_pages'], 20)

    def test_ear_section_has_no_redundant_double_break_hint(self):
        overlay = json.loads((ROOT/'headneck/content/hn04_update.json').read_text())
        ear = overlay['topics']['hn04-T08']['plate_overrides']['28']
        self.assertTrue(ear['fresh'])
        self.assertNotIn('min_img_h', ear)

    def test_source_figure_paths_resolve_in_current_checkout(self):
        inventory = json.loads((ROOT/'headneck/reports/hn04_final_evidence/machine_manifest.json').read_text())
        for figure in inventory['figures']:
            self.assertTrue((ROOT/figure['source_file']).is_file(), figure['source_file'])

if __name__=='__main__':unittest.main()

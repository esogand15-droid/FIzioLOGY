import hashlib, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
class Candidates(unittest.TestCase):
 def test_source_and_figures(self):
  m=json.loads((ROOT/'headneck/reports/hn12_evidence/figure_candidates.json').read_text())
  self.assertEqual(sha(ROOT/m['source']),m['source_sha256'])
  self.assertEqual(len(m['figures']),26)
  self.assertEqual([(x['source_page'],x['printed_figure']) for x in m['figures'] if x['printed_figure']=='13'],[(6,'13'),(7,'13')])
  for x in m['figures']:
   self.assertEqual(sha(ROOT/x['file']),x['sha256'])
   a,b,c,d=x['rect_normalized'];self.assertTrue(0<=a<c<=1 and 0<=b<d<=1)
if __name__=='__main__':unittest.main()

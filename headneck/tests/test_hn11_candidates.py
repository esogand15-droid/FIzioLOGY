"""Source integrity and figure-candidate inventory for session eleven."""
import hashlib,json,unittest
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
class SessionElevenCandidates(unittest.TestCase):
 def test_source_and_candidates(self):
  data=json.loads((ROOT/'headneck/reports/hn11_evidence/figure_candidates.json').read_text())
  source=ROOT/data['source'];self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),data['source_sha256'])
  with pymupdf.open(source) as doc:self.assertEqual(len(doc),20)
  self.assertEqual([x['figure'] for x in data['figures']],[f'{i:02}' for i in range(1,15)])
  for figure in data['figures']:
   asset=ROOT/figure['asset'];self.assertTrue(asset.is_file())
   self.assertEqual(hashlib.sha256(asset.read_bytes()).hexdigest(),figure['sha256'])
   self.assertTrue(1 <= figure['pdf_page'] <= 20)
if __name__=='__main__':unittest.main()

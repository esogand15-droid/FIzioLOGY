"""Verify provenance of the first session-nine source candidates."""
import hashlib,json,unittest
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
class SessionNineSources(unittest.TestCase):
 def test_source_manifest_and_candidate_pixels_exist(self):
  manifest=json.loads((ROOT/'headneck/reports/hn09_evidence/figure_candidates.json').read_text())
  source=ROOT/manifest['source'];self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),'ee55fa8ece5de95cdcb2baf4a68e7c26b54c3d6e2a18f684965540865860ca5f')
  self.assertEqual(manifest['source_sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
  with pymupdf.open(source) as doc:self.assertEqual(len(doc),15)
  items=manifest['candidates'];self.assertEqual(len(items),20)
  self.assertEqual({x['figure'] for x in items},{f'{i:02}' for i in range(1,20)}|{'extra11'})
  for item in items:
   file=ROOT/item['asset'];self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),item['sha256'])
   pix=pymupdf.Pixmap(str(file));self.assertGreater(pix.width,100);self.assertGreater(pix.height,100)
  by_id={x['figure']:x for x in items}
  self.assertEqual((by_id['14']['pdf_page'],by_id['14']['caption_pdf_page']),(9,10))
  self.assertEqual((by_id['19']['pdf_page'],by_id['19']['caption_pdf_page']),(15,14))
  self.assertIsNone(by_id['extra11']['caption_pdf_page'])
 def test_transcription_scope(self):
  text=(ROOT/'headneck/content/session09/source_pages_01-03.txt').read_text()
  self.assertEqual(text.count('@@ صفحه '),3)
  for key in ['شبکه گردنی','Ansa cervicalis','phrenic','proprioceptive']:self.assertIn(key,text)
if __name__=='__main__':unittest.main()

import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
class Inventory(unittest.TestCase):
 def test_sources_pages_and_figures(self):
  data=json.loads((ROOT/'headneck/reports/hn13_evidence/source_inventory.json').read_text())['sources']
  self.assertEqual([s['part'] for s in data],['1','3','4','5'])
  self.assertEqual([s['page_count'] for s in data],[17,5,13,21])
  for source in data:
   self.assertEqual(digest(ROOT/source['source']),source['sha256'])
   self.assertEqual([p['page'] for p in source['pages']],list(range(1,source['page_count']+1)))
  self.assertEqual(sum('figure' in p for s in data for p in s['pages']),48)
  self.assertIn('C6',[x['text'] for x in data[2]['pages'][12]['spans']])
  self.assertIn('C7',[x['text'] for x in data[3]['pages'][9]['spans']])
if __name__=='__main__':unittest.main()

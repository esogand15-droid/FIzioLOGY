"""Validate the shared front matter, contents and back covers of sessions 1–4."""
import collections,json,sys,unittest,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'headneck/scripts'),str(ROOT/'render')]
import pymupdf
import writer_shell as S

PREVIOUS={1:'hn01_handoff_update',2:'hn02_handoff_update',3:'hn03_writer_update',4:'hn04_writer_update'}
COUNTS={1:17,2:21,3:19,4:20}
def norm(s):return unicodedata.normalize('NFKC',s).replace('\u200c','').replace('ٔ','')
class WriterShellTests(unittest.TestCase):
 def test_content_and_image_assets_retained(self):
  for n in range(1,5):
   oldpath=ROOT/f'.cache/{PREVIOUS[n]}/manifest.json';newpath=ROOT/f'.cache/hn0{n}_shell/manifest.json'
   if not oldpath.exists() or not newpath.exists():self.skipTest('Build manifests unavailable')
   old=json.loads(oldpath.read_text());new=json.loads(newpath.read_text())
   self.assertEqual(len(new['figures']),S.NFIG[n])
   self.assertEqual(collections.Counter(x['sha256'] for x in old['figures']),collections.Counter(x['sha256'] for x in new['figures']))
   for key in ('source_text_sha256','block_sha256'):
    if key in old:self.assertEqual(old[key],new[key])
   self.assertFalse(any(new['qa'].values()))
 def test_front_toc_back_and_form_counts(self):
  for n in range(1,5):
   path=ROOT/f'.cache/hn0{n}_shell/HumsYar_HeadNeck_Jalase{n}.pdf'
   if not path.exists():self.skipTest('Generated booklet unavailable')
   with pymupdf.open(path) as d:
    pages=[norm(p.get_text()) for p in d]
    self.assertIn(norm('آناتومی سر و گردن'),pages[0])
    for text in ['ساختار این جزوه و قاعدهٔ خواندن آن','این جزوه چگونه ساخته شده است','قاعدهٔ ارجاع و علامت‌گذاری','منابع تصویر','واحد شمارش']:
     self.assertIn(norm(text),pages[1])
    for text in ['فهرست مطالب','شناسنامهٔ سند','قاعدهٔ ارجاع به تصویر و متن','جمع‌بندی','قدم بعدی']:
     self.assertIn(norm(text),pages[2])
    self.assertIn('HumsYar',pages[-1]);self.assertIn(norm('جزوهٔ مادر آناتومی سر و گردن'),pages[-1])
    self.assertEqual(sum(norm('نام جزوه‌نویس') in p for p in pages),COUNTS[n])
    toc=d.get_toc();self.assertTrue(any('قدم بعدی' in row[1] for row in toc))
    self.assertTrue(any('جمع‌بندی' in row[1] for row in toc))
    self.assertTrue(all(1<=row[2]<=len(d) for row in toc))

if __name__=='__main__':unittest.main()

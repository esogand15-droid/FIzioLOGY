"""Mechanical regression checks, not a claim of a human transcription audit."""
import hashlib,io,json,re,subprocess,sys,unittest
from pathlib import Path
import pymupdf
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'headneck/scripts'),str(ROOT/'render')]
import build_hn13_writer_final as B
PDF=ROOT/'pdf/HumsYar_HeadNeck_Jalase13_WRITER_FINAL.pdf'
def canon(s):return re.sub(r'[^a-z0-9]','',s.lower())
def pixel_hash(im):
 im=im.convert('RGB');return im.size,hashlib.sha256(im.tobytes()).hexdigest()
class Session13(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.manifest=json.loads((ROOT/'headneck/reports/hn13_evidence/writer_manifest.json').read_text());cls.assets=json.loads((ROOT/'headneck/reports/hn13_evidence/asset_manifest.json').read_text());cls.inv=B.inventory()
  if not all((ROOT/a['asset']).exists() for a in cls.assets['figures']+cls.assets['references']):subprocess.run([sys.executable,str(ROOT/'headneck/scripts/prepare_hn13_assets.py')],check=True)
  cls.doc=pymupdf.open(PDF)
 @classmethod
 def tearDownClass(cls):cls.doc.close()
 def test_structure_and_hash(self):
  self.assertEqual(self.manifest['sha256'],hashlib.sha256(PDF.read_bytes()).hexdigest());self.assertEqual(self.manifest['pages'],len(self.doc));self.assertEqual(len(self.manifest['topics']),9);self.assertEqual(len(self.manifest['figures']),58);self.assertTrue(all(not v for v in self.manifest['qa'].values()))
 def test_all_page_models_and_exact_coverage(self):
  expected={(p['part'],q['page']) for p in self.inv.values() for q in p['pages'] if 'figure' in q};actual={(a['part'],a['page']) for a in self.assets['figures']};mapped={x for group in B.W.GROUPS for x in group};self.assertEqual(len(expected),48);self.assertEqual(expected,actual);self.assertEqual(expected,mapped);self.assertEqual(sum(map(len,B.W.GROUPS)),48)
 def test_source_labels_and_images_together(self):
  # Compare decoded pixels of the committed PDF to each prepared JPEG, then
  # locate source phrases on its page or the following page. This checks
  # mechanical transfer, not correctness of the original extracted text.
  images={};pages={}
  for n,page in enumerate(self.doc):
   for entry in page.get_images():
    x=entry[0];pages.setdefault(x,[]).append(n)
    if x not in images:
     try:images[x]=pixel_hash(Image.open(io.BytesIO(self.doc.extract_image(x)['image'])))
     except Exception:pass
  for ref in self.assets['references']:
   with self.subTest(reference=ref['page']):
    self.assertIn(pixel_hash(Image.open(ROOT/ref['asset'])),images.values())
  for a in self.assets['figures']:
   with self.subTest(part=a['part'],page=a['page']):
    f=ROOT/a['asset'];self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),a['sha256']);h=pixel_hash(Image.open(f));matches=[x for x in images if images[x]==h];self.assertTrue(matches)
    terms=B.labels(self.inv[a['part']]['pages'][a['page']-1]);matched=False
    for x in matches:
     for n in pages[x]:
      text=canon(' '.join(self.doc[j].get_text() for j in range(n,min(n+2,len(self.doc)))));matched |= all(not canon(t) or canon(t) in text for t in terms)
    self.assertTrue(matched)
 def test_reference_images_and_localization(self):
  self.assertEqual({(x['page'],x['plate']) for x in self.assets['references']},{(77,25),(91,39),(79,27),(90,38),(84,32),(83,31),(95,43),(96,44),(105,53),(106,54)})
  for a in self.assets['references']:self.assertEqual(hashlib.sha256((ROOT/a['asset']).read_bytes()).hexdigest(),a['sha256'])
 def test_figures_include_label_bounds(self):
  for a in self.assets['figures']:
   clip=pymupdf.Rect(a['clip']);page=self.inv[a['part']]['pages'][a['page']-1]
   for span in page['spans']:
    if 'Dr Mirzaei' in span['text'] or 'Hormozgan medical science university' in span['text']:continue
    b=pymupdf.Rect(span['bbox']);self.assertGreaterEqual((b&clip).get_area(),b.get_area()*.99,(a['part'],a['page'],span['text']))
 def test_source_disagreement_is_preserved(self):
  self.assertIn('C6',B.labels(self.inv['4']['pages'][12]));self.assertIn('C7',B.labels(self.inv['5']['pages'][9]));
  with pymupdf.open(ROOT/self.inv['4']['source']) as a, pymupdf.open(ROOT/self.inv['5']['source']) as b:
   aa=a.extract_image(a[12].get_images()[0][0])['image'];bb=b.extract_image(b[9].get_images()[0][0])['image'];self.assertEqual(hashlib.sha256(aa).digest(),hashlib.sha256(bb).digest())
if __name__=='__main__':unittest.main()

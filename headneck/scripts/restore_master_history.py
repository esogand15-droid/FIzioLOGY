"""Reconstruct missing historical assets with expected SHA checks; no overwrite.

Run inventory_master_01_06.py first to recreate the pinned historical JSON/PDFs.
Historical figures are reconstructed only under ignored .cache, never into the
published assets directory. Existing mismatching files raise rather than change.
"""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'headneck/master_01_06';WORK=ROOT/'.cache/master_01_06/historical'
COMMIT='026cbcc1191751a491bcb37675adcb2cb8c827d0'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 rows=json.loads((OUT/'restored_assets.json').read_text());count=0
 for r in rows:
  p=ROOT/r['workspace_file']
  if p.exists():
   if sha(p.read_bytes())!=r['sha256']:raise ValueError('Existing asset differs: '+str(p))
   continue
  if r['origin']=='CURRENT_CHECKOUT':raise FileNotFoundError('Tracked asset is missing: '+str(p))
  data=subprocess.check_output(['git','show',COMMIT+':'+r['asset']],cwd=ROOT)
  if sha(data)!=r['sha256']:raise ValueError('Historical asset differs: '+r['asset'])
  p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(data);count+=1
 print('Restored',count,'assets; checked',len(rows),'without overwriting.')
if __name__=='__main__':main()

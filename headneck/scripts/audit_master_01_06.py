"""Fail-closed prebuild/final gates for the 1–6 mission; never writes a PDF.

Machine consistency is necessary, never a substitute for substantive review.
A passing file/field check does not certify scientific truth or independent review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'headneck/master_01_06'
FINAL_NAME='HumsYar_Master_Sessions_01-06_Updated.pdf'
REQUIRED_B={'scientific_card','plain_explanation','key_points','common_errors','comparison','writer_guide','spatial_relations','image_instructions','summary','reference_links'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,default=None):
 p=OUT/name
 return json.loads(p.read_text()) if p.exists() else default

def audit(phase='prebuild'):
 errors=[];info={}
 protected=load('protected_baselines.json',[])
 for r in protected:
  p=ROOT/r['file']
  if not p.is_file():errors.append('Protected baseline missing (reconstruct pinned Git object): '+r['file'])
  elif sha(p)!=r['sha256']:errors.append('Protected baseline changed: '+r['file'])
 info['protected_files']=len(protected)
 matrix=load('topic_matrix.json',{}).get('topics',[])
 if len(matrix)!=102 or len({t['topic_id'] for t in matrix})!=102:errors.append('All 102 unique topics must be represented across both a and b files.')
 for n,expected in [(1,17),(2,21),(3,19),(4,20),(5,14),(6,11)]:
  if sum(t['session']==n for t in matrix)!=expected:errors.append(f'Session {n}: topic coverage mismatch')
 completed=load('topic_clearances.json',{});additions=load('educational_additions.json',{}).get('topics',{})
 for topic in matrix:
  tid=topic['topic_id'];clearance=completed.get(tid,{})
  if clearance.get('status')!='CLEARED_AFTER_CONTENT_AND_FIGURE_REVIEW':errors.append(tid+': content review not cleared')
  if clearance.get('baseline_sha256')!=topic['A']['baseline_sha256']:errors.append(tid+': clearance not bound to exact baseline')
  b=additions.get(tid,{})
  if not REQUIRED_B.issubset(b) or any(not b[k] for k in REQUIRED_B if k in b):errors.append(tid+': topic-specific teaching/writer/reference material incomplete')
  if not b.get('diagram') and not b.get('diagram_not_applicable_reason'):errors.append(tid+': diagram or specific non-applicability rationale missing')
  for claim in b.get('exam_claims',[]):
   if claim.get('kind')=='FREQUENT_IN_EXAMS' and not claim.get('evidence'):errors.append(tid+': unsupported exam frequency claim')
 info['topics']=len(matrix);info['topics_cleared']=sum(v.get('status')=='CLEARED_AFTER_CONTENT_AND_FIGURE_REVIEW' for v in completed.values())
 extraction=load('extraction_inventory.json',{});pages=load('lecture_page_observations.json',[]);pseen={(r['source_label'],r['pdf_page']):r for r in pages}
 # Saved manifests alone must not bless a changed source PDF on disk.
 for source in extraction.get('files',[]):
  p=ROOT/source['file']
  if not p.is_file() and source['role']=='HISTORICAL_MASTER':p=ROOT/'.cache/master_01_06/historical'/source['file']
  if not p.is_file():errors.append('Extraction source missing: '+source['file'])
  elif sha(p)!=source['sha256']:errors.append('Extraction source changed: '+source['file'])
 expected_pages=[]
 for r in extraction.get('files',[]):
  if r['role']=='PRIMARY_LECTURE':expected_pages.extend((r,n) for n in range(1,r['pages']+1))
 for source,n in expected_pages:
  review=pseen.get((source['label'],n),{})
  if review.get('whole_page_vision')!='OBSERVED' or review.get('source_sha256')!=source['sha256']:errors.append(f'{source["label"]}:{n}: missing SHA-bound page observation')
  if review.get('typed_text_reconciliation')!='VISUALLY_RECONCILED':errors.append(f'{source["label"]}:{n}: typed source text not visually reconciled')
  if not review.get('all_individual_images_closed'):errors.append(f'{source["label"]}:{n}: not all image/panel decisions closed')
 info['primary_pages']=len(expected_pages);info['primary_pages_observed']=sum(r.get('whole_page_vision')=='OBSERVED' for r in pages)
 reference_scope=load('reference_scope_clearance.json',{})
 if reference_scope.get('status')!='ALL_AVAILABLE_REFERENCE_DOMAINS_TRIAGED_AND_RELEVANT_ITEMS_REVIEWED':errors.append('Reference-domain triage and all related illustrations are not cleared.')
 image_clearance=load('image_clearances.json',{})
 if image_clearance.get('registry_sha256')!=extraction.get('image_registry_sha256') or image_clearance.get('status')!='ALL_REQUIRED_OCCURRENCES_AND_SUBPANELS_DISPOSITIONED':errors.append('Required individual images/subpanels are not cleared against the exact registry.')
 issues=load('scientific_issues.json',{}).get('issues',[])
 unresolved=[x['id'] for x in issues if x.get('status') not in {'INTEGRATED_WITH_REFERENCE','EXPLICIT_LIMITATION_INTEGRATED_AND_ACCEPTED'}]
 if unresolved:errors.append('Scientific issues still need integration/disposition: '+', '.join(unresolved))
 if phase=='final':
  publication=load('final_publication.json',{});pdf=ROOT/publication.get('file','__NO_PDF__')
  if pdf.name!=FINAL_NAME or not pdf.is_file():errors.append('The single requested final PDF is absent or incorrectly named.')
  elif sha(pdf)!=publication.get('sha256'):errors.append('Final PDF SHA does not match publication evidence.')
  review=load('final_page_reviews.json',{});rows=review.get('pages',[]);count=publication.get('pages',0)
  if not count or review.get('pdf_sha256')!=publication.get('sha256') or len(rows)!=count or {r.get('pdf_page') for r in rows}!=set(range(1,count+1)):errors.append('Final page observations must cover every page of this exact SHA, with no sampling.')
  if any(r.get('vision_status')!='OBSERVED_AND_LAYOUT_CLEARED' for r in rows):errors.append('Final-page layout issues remain.')
  if publication.get('hard_layout_errors',1)!=0:errors.append('Hard final-layout errors remain.')
  if not publication.get('text_audit_report'):errors.append('Text audit report is missing.')
 return dict(status='PASS_STRUCTURAL_GATES_ONLY' if not errors else 'BLOCKED_DO_NOT_BUILD_OR_PUBLISH_FINAL',phase=phase,information=info,errors=errors,limits='Checks enforce evidence coverage/consistency; they do not perform Vision, reconcile OCR or certify scientific correctness.')

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=['prebuild','final'],default='prebuild');parser.add_argument('--write',action='store_true');args=parser.parse_args();result=audit(args.phase)
 if args.write:(OUT/'gate_status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if not result['errors'] else 2)
if __name__=='__main__':main()

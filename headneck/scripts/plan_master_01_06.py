"""Build an honest topic/block index, not new anatomy prose or approval evidence."""
from pathlib import Path
import hashlib,json
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'headneck/master_01_06'
HIST=ROOT/'.cache/master_01_06/historical'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 matrix=[];sources=[]
 for n in range(1,7):
  prefix=HIST if n<4 else ROOT;key=f'hn{n:02}'
  paths={s:prefix/f'headneck/content/{key}_{s}.json' for s in ['a','b','update']}
  outline=prefix/f'headneck/content/outline/{key}_topics.json'
  for role,p in list(paths.items())+[('outline',outline)]:sources.append(dict(session=n,role=role,file=str(p.relative_to(ROOT)),sha256=h(p)))
  base=[];topic_paths={}
  for suffix in ['a','b']:
   part=json.loads(paths[suffix].read_text());base.extend(part)
   for t in part:
    if t['topic_id'] in topic_paths:raise ValueError('Duplicate topic '+t['topic_id'])
    topic_paths[t['topic_id']]=paths[suffix]
  out=json.loads(outline.read_text());titles={t['id'] if 'id' in t else t['topic_id']:t for t in out['topics']}
  if {t['topic_id'] for t in base}!=set(titles):raise ValueError('Outline/content mismatch '+key)
  for t in base:
   tid=t['topic_id'];blocks=t['blocks'];topic=titles[tid];baseline_path=topic_paths[tid]
   text_blocks=[dict(index=i,type=b['type'],src=b.get('src'),block_sha256=hashlib.sha256(json.dumps(b,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),preservation='KEEP_UNCHANGED_UNLESS_EXPLICIT_RECONCILIATION',source_transcription_review='NOT_REVIEWED_IN_THIS_MISSION',origin_candidate='LECTURE_QUOTE' if b.get('src','').startswith('متن جزوه') else 'EXISTING_EDITORIAL_OR_UNCLASSIFIED') for i,b in enumerate(blocks)]
   matrix.append(dict(session=n,topic_id=tid,title=topic['title'],outline_source=topic,A=dict(baseline_file=str(baseline_path.relative_to(ROOT)),baseline_sha256=h(baseline_path),block_count=len(blocks),block_types=dict(Counter(b['type'] for b in blocks)),blocks=text_blocks,lecture_reconciliation='PENDING'),B=dict(prior_overlay_file=str(paths['update'].relative_to(ROOT)),prior_overlay_sha256=h(paths['update']),topic_specific_additions=[],reference_links=[],image_links=[],scientific_card='PENDING',writer_guide='PENDING',diagram='PENDING',exam_claim_evidence=[]),C=dict(issues=[],review='PENDING'),current_mission_review='NOT_COMPLETE'))
 (OUT/'topic_matrix.json').write_text(json.dumps(dict(status='COVERAGE_PLAN_NOT_APPROVAL',topics=matrix,totals=dict(topics=len(matrix),by_session=dict(Counter(t['session'] for t in matrix)))),ensure_ascii=False,indent=2)+'\n')
 (OUT/'protected_baselines.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
 print('Indexed',len(matrix),'topics; no baseline modified; no topic auto-approved.')
if __name__=='__main__':main()

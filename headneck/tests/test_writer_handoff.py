"""Topic-specific writer handoff sheets for sessions one and two."""
import sys, unittest, unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'headneck/scripts'))
import pymupdf
import build_hn01_writer_final as S1
import build_hn02_writer_final as S2
import writer_handoff as WH


def normalized(text):
 return unicodedata.normalize('NFKC',text).replace('\u200c','').replace('ٔ','')

class HandoffTests(unittest.TestCase):
 def test_all_topics_have_unique_specific_checklists(self):
  for session,module in ((1,S1),(2,S2)):
   if session==1:
    _,plans,_,_=module.original_blocks()
   else:
    _,plans,_,_,_=module.inputs()
   values=[]
   for idx,rows in enumerate(plans.values(),1):
    card=rows[0];h=next(x for x in rows if x['type']=='handoff')
    checks=WH.checklist(session,idx,card,module.W)
    self.assertGreaterEqual(len(checks),2)
    self.assertTrue(all(item.strip() for item in checks))
    values.append(tuple(checks))
    self.assertTrue(WH.review_point(session,idx,h,module.W))
    self.assertTrue(h.get('question'))
   self.assertEqual(len(values),len(set(values)))

 def test_original_open_points_and_question_remain_available(self):
  _,plans,_,_=S1.original_blocks()
  rows=plans['hn01-T01'];handoff=next(x for x in rows if x['type']=='handoff')
  self.assertEqual(WH.review_point(1,1,handoff,S1.W),handoff['open'])
  self.assertIn('هیوئید',handoff['question'])

 def test_session_two_first_review_point_does_not_repeat_old_claim(self):
  point=WH.review_point(2,1,{'open':'نام پس‌سری در فهرست آمده است'},S2.W)
  self.assertIn('برگهٔ تحویل پیشین',point)
  self.assertIn('پیشانی، گونه‌ای، آهیانه‌ای و گیجگاهی',point)

 def test_pdf_forms_contain_all_fields(self):
  fields=['نام جزوه‌نویس','امضای نویسنده','تاریخ','شمارهٔ نسخه','اختلاف یا ابهام علمی برای بازبین','منابع این مبحث']
  for sn,count in ((1,17),(2,21)):
   path=ROOT/f'.cache/hn0{sn}_handoff_update/HumsYar_HeadNeck_Jalase{sn}.pdf'
   if not path.exists():self.skipTest('Local generated PDF not present')
   with pymupdf.open(path) as doc:
    pages=[normalized(p.get_text()) for p in doc]
    forms=[p for p in pages if normalized('نام جزوه‌نویس') in p]
    self.assertEqual(len(forms),count)
    for form in forms:
     for field in fields:self.assertIn(normalized(field),form)
     self.assertIn(normalized('پرسش باز'),form)

if __name__=='__main__':unittest.main()

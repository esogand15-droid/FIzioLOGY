#!/usr/bin/env python3
"""Crop each figure from session 12 source; coordinates normalized to the source page."""
import hashlib, json
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'علوم تشریح سر و گردن/جلسه 12 - جنین شناسی/Skull embryology .pdf'
OUT=ROOT/'headneck/images/hn12_candidates'
REPORT=ROOT/'headneck/reports/hn12_evidence/figure_candidates.json'
# (page, figure as printed, descriptive name, rectangle x0,y0,x1,y1)
FIGS=[
(1,'1','somite',(0.06,0.10,0.40,0.29)),(1,'2','somite_development',(0.05,0.36,0.39,0.58)),(1,'3','embryo_somites',(0.06,0.65,0.40,0.86)),
(2,'4','skeletal_origins',(0.53,0.48,0.96,0.68)),(2,'5','skull_ossification',(0.03,0.39,0.46,0.57)),
(3,'6','anterior_posterior_fontanelles',(0.06,0.09,0.39,0.36)),(3,'7','sphenoid_mastoid_fontanelles',(0.06,0.43,0.39,0.66)),
(4,'8','chondrocranium',(0.06,0.08,0.39,0.35)),(4,'9','arches_pouches_vessels',(0.04,0.69,0.42,0.87)),
(5,'10','stomodeum',(0.05,0.10,0.41,0.37)),(5,'11','facial_prominences',(0.05,0.41,0.41,0.70)),
(6,'12','arch_components',(0.06,0.09,0.40,0.34)),(6,'13','arch_innervation',(0.05,0.42,0.41,0.59)),
(7,'13','arch_cartilages',(0.08,0.08,0.48,0.38)),(7,'14','embryonic_arch_cartilages',(0.52,0.45,0.91,0.72)),(7,'15','arch_derivatives',(0.06,0.47,0.47,0.74)),
(9,'16','pharyngeal_pouches',(0.05,0.09,0.42,0.29)),(9,'17','pouches_anterior_view',(0.03,0.34,0.45,0.57)),(9,'18','pouches_5_6_weeks',(0.03,0.63,0.45,0.83)),
(10,'19','pouch_development',(0.12,0.09,0.85,0.54)),(11,'20','pouches_median_section',(0.15,0.48,0.85,0.83)),
(12,'21','grooves_6_7_weeks_a',(0.20,0.14,0.91,0.48)),(12,'22','grooves_6_7_weeks_b',(0.23,0.55,0.91,0.87)),
(13,'23','pouch_groove_anomalies',(0.14,0.37,0.89,0.83)),
(14,'24','cervical_cyst_diagram',(0.36,0.59,0.95,0.84)),(14,'25','cervical_cyst_photo',(0.05,0.59,0.36,0.84)),
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.parent.mkdir(parents=True,exist_ok=True);doc=pymupdf.open(SOURCE);items=[]
 for page,n,name,coords in FIGS:
  p=doc[page-1];r=p.rect;rect=pymupdf.Rect(coords[0]*r.width,coords[1]*r.height,coords[2]*r.width,coords[3]*r.height);dest=OUT/f'p{page:02}_fig{n}_{name}.png'
  p.get_pixmap(matrix=pymupdf.Matrix(2.5,2.5),clip=rect,alpha=False).save(dest)
  items.append({'source_page':page,'printed_figure':n,'name':name,'rect_normalized':coords,'file':str(dest.relative_to(ROOT)),'sha256':sha(dest)})
 REPORT.write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)),'source_sha256':sha(SOURCE),'figure_count':len(items),'figures':items},ensure_ascii=False,indent=2)+'\n')
 print(len(items),'figures; source',sha(SOURCE))
if __name__=='__main__':main()

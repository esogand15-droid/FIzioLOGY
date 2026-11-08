"""Extract figures reviewed in the face section of local Netter and Gray."""
from pathlib import Path
import hashlib,json
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
N='علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1/Netter Atlas of Human Anatomy Classic Regional Approach.pdf'
G="علوم تشریح دستگاه اعصاب/user - Gray's Anatomy For Students, 3rd Edition-801-1000.pdf"
# Coordinates below refer to renders 630×810 (Netter) and 704×912 (Gray).
ITEMS=[
 ('netter_100',N,100,(630,810),(30,65,600,745)),('netter_124',N,124,(630,810),(30,65,600,745)),
 ('netter_112',N,112,(630,810),(30,65,600,745)),('netter_122',N,122,(630,810),(30,65,600,745)),
 ('netter_131',N,131,(630,810),(30,65,600,745)),('netter_151',N,151,(630,810),(30,65,600,745)),
 ('netter_152',N,152,(630,810),(30,65,600,745)),('netter_167',N,167,(630,810),(30,65,600,745)),
 ('netter_202',N,202,(630,810),(30,65,600,745)),('netter_213',N,213,(630,810),(30,65,600,745)),
 ('gray_853',G,132,(704,912),(65,220,645,830)),('gray_854',G,135,(704,912),(55,70,645,315)),
 ('gray_855',G,135,(704,912),(350,375,645,720)),('gray_856',G,136,(704,912),(60,405,645,720)),
 ('gray_857',G,137,(704,912),(55,340,345,825)),('gray_860',G,141,(704,912),(350,95,645,510)),
 ('gray_858',G,138,(704,912),(355,70,645,490)),('gray_859',G,139,(704,912),(65,230,645,825)),
 ('gray_861',G,142,(704,912),(55,375,645,825)),('gray_862',G,143,(704,912),(55,305,645,825)),
 ('gray_863',G,145,(704,912),(55,70,645,620)),('gray_864',G,146,(704,912),(55,70,645,790)),
 ('gray_865',G,148,(704,912),(60,480,350,830)),('gray_866',G,148,(704,912),(360,480,645,830)),
]
def main():
 target=ROOT/'headneck/images/hn11_refs';target.mkdir(parents=True,exist_ok=True);docs={};out=[]
 for name,source,n,(w,h),(x0,y0,x1,y1) in ITEMS:
  if source not in docs:docs[source]=pymupdf.open(ROOT/source)
  page=docs[source][n-1];clip=pymupdf.Rect(x0*page.rect.width/w,y0*page.rect.height/h,x1*page.rect.width/w,y1*page.rect.height/h)
  path=target/(name+'.png');page.get_pixmap(matrix=pymupdf.Matrix(2,2),clip=clip,alpha=False).save(path)
  out.append({'asset':str(path.relative_to(ROOT)),'source':source,'page':n,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'render_size':[w,h],'rectangle':[x0,y0,x1,y1]})
 p=ROOT/'headneck/reports/hn11_evidence/reference_candidates.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(len(out),'reference images')
if __name__=='__main__':main()

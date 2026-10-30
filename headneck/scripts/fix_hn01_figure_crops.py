"""Recover clean embedded source figures for several lecture-1 figure crops.

Direct embedded images avoid including adjacent lecture text. The orbital figure
is assembled from the photo and its separate, original numbered key. The maxilla
figure is re-rendered tightly because its highlighted label and pointer are PDF
overlays. These are figure crops, never whole lecture pages.
"""
from __future__ import annotations
import json
from pathlib import Path
import pymupdf
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'علوم تشریح سر و گردن'/'جلسه 1 - سر و گردن 1'/'جلسه_اول_علوم_تشریح_سر_و_گردن_مهر_1404.pdf'
index=ROOT/'headneck/images/INDEX.json'


def pix_image(doc, xref):
    pix=pymupdf.Pixmap(doc,xref)
    if pix.alpha or pix.n not in (1,3): pix=pymupdf.Pixmap(pymupdf.csRGB,pix)
    return Image.frombytes('RGB' if pix.n==3 else 'L',(pix.width,pix.height),pix.samples).convert('RGB')


def main():
    doc=pymupdf.open(source); data=json.loads(index.read_text(encoding='utf-8'))
    specs={
      'hn01_lec_p03_append': (3,102,'تصویر اصلی xref 102، بدون متن مجاور'),
      'hn01_lec_p05_facial': (5,148,'تصویر اصلی xref 148، بدون متن مجاور'),
      'hn01_lec_p06_roofbase': (6,161,'تصویر اصلی xref 161، بدون هم‌پوشانی شکل مجاور'),
      'hn01_lec_p07_cavities': (7,183,'تصویر اصلی xref 183، بدون تکهٔ شکل مجاور'),
      'hn01_lec_p07_frankfurt': (7,182,'تصویر اصلی xref 182، بدون متن و حاشیهٔ صفحه'),
      'hn01_lec_p08_norma': (8,198,'تصویر اصلی xref 198؛ برچسب کناری در خود جزوه ناقص است'),
      'hn01_lec_p13_facial': (13,294,'تصویر اصلی xref 294، بدون حاشیهٔ صفحه'),
      'hn01_lec_p16_palate': (16,328,'تصویر اصلی xref 328، بدون حاشیهٔ صفحه'),
      'hn01_lec_p18_hiatus': (18,357,'تصویر اصلی xref 357، بدون حاشیهٔ صفحه'),
      'hn01_lec_p07_acoustic': (7,187,'تصویر اصلی xref 187، بدون تکهٔ تصویر مجاور'),
      'hn01_lec_p12_nasalcavity': (12,267,'تصویر اصلی xref 267، بدون متن مجاور'),
      'hn01_lec_p15_eye': (15,315,'تصویر اصلی xref 315، بدون تکهٔ شکل مجاور'),
      'hn01_lec_p15_sac': (15,316,'تصویر اصلی xref 316، بدون تکهٔ شکل مجاور'),
    }
    for ident,(page,xref,note) in specs.items():
        img=pix_image(doc,xref);path=ROOT/'headneck/images'/f'{ident}.jpeg';img.save(path,quality=96,subsampling=0)
        a=next(a for a in data['assets'] if a['asset_id']==ident);a.update(bbox=list(doc[page-1].get_image_rects(xref)[0]),w=img.width,h=img.height,px=img.width*img.height,bytes=path.stat().st_size,note=note)
    # Two separate, nonoverlapping details of the source hyoid composition.
    hyoid = pix_image(doc,145)
    for ident, box, bbox in (
        ('hn01_lec_p05_hyoid', (0,0,270,318), [80.2,498.4,209.8,651.0]),
        ('hn01_lec_p05_hyoidneck', (300,0,600,318), [224.2,498.4,368.2,651.0]),
    ):
        img=hyoid.crop(box);path=ROOT/'headneck/images'/f'{ident}.jpeg';img.save(path,quality=96,subsampling=0)
        a=next(a for a in data['assets'] if a['asset_id']==ident);a.update(bbox=bbox,w=img.width,h=img.height,px=img.width*img.height,bytes=path.stat().st_size,note='بخشی از تصویر اصلی xref 145، ص ۵؛ نماهای تکراری جدا شده‌اند')
    # Remove two lines from another article/paragraph at the top of the crop.
    gray=ROOT/'علوم تشریح دستگاه اعصاب'/"user - Gray's Anatomy For Students, 3rd Edition-801-1000.pdf"
    gd=pymupdf.open(gray);clip=pymupdf.Rect(112,390,548,728)
    pix=gd[87].get_pixmap(matrix=pymupdf.Matrix(2.78,2.78),clip=clip,alpha=False)
    img=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);path=ROOT/'headneck/images/hn01_grays_p860.jpeg';img.save(path,quality=96,subsampling=0)
    a=next(a for a in data['assets'] if a['asset_id']=='hn01_grays_p860');a.update(bbox=list(clip),w=img.width,h=img.height,px=img.width*img.height,bytes=path.stat().st_size,note='گری ص ۸۶۰، نمای فوقانی جمجمه؛ متن بریدهٔ مجاور حذف شده است')
    photo=pix_image(doc,241);key=pix_image(doc,242)
    img=Image.new('RGB',(photo.width+key.width+20,photo.height),'white');img.paste(photo,(0,0));img.paste(key,(photo.width+20,55))
    path=ROOT/'headneck/images/hn01_lec_p10_orbital.jpeg';img.save(path,quality=96,subsampling=0)
    a=next(a for a in data['assets'] if a['asset_id']=='hn01_lec_p10_orbital');a.update(bbox=[29,153,394,333],w=img.width,h=img.height,px=img.width*img.height,bytes=path.stat().st_size,note='ترکیب جداگانهٔ عکس xref 241 و راهنمای اصلی شماره‌ها xref 242 در صفحهٔ ۱۰')
    clip=pymupdf.Rect(29,126,243,341);pix=doc[14].get_pixmap(matrix=pymupdf.Matrix(2.78,2.78),clip=clip,alpha=False)
    img=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);path=ROOT/'headneck/images/hn01_lec_p15_maxilla.jpeg';img.save(path,quality=96,subsampling=0)
    a=next(a for a in data['assets'] if a['asset_id']=='hn01_lec_p15_maxilla');a.update(bbox=list(clip),w=img.width,h=img.height,px=img.width*img.height,bytes=path.stat().st_size,note='برش محصور شکل صفحهٔ ۱۵ با حفظ برچسب و خط راهنمای روی‌هم‌گذاری‌شده')
    index.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print('recovered clean lecture and reference figures')

if __name__=='__main__':main()

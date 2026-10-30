"""Recover selected session-2 figures from embedded lecture images.

The original image XObjects preserve labels and remove page-border or nearby
text fragments accidentally included by raster page crops. No page is copied.
"""
from __future__ import annotations
import json
from pathlib import Path
import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'علوم تشریح سر و گردن/جلسه 2 - سر و گردن 2/جلسه_دوم_علوم_تشریح_سر_و_گردن_مهر_1404.pdf'
INDEX = ROOT / 'headneck/images/INDEX.json'
SPECS = {
    'hn02_lec_p20_tmj': (20, 178),
    'hn02_lec_p22_infratemp': (22, 187),
    'hn02_lec_p22_deep': (22, 188),
    'hn02_lec_p23_tempbone': (23, 192),
    'hn02_lec_p23_suprameatal': (23, 193),
    'hn02_lec_p26_parietal': (26, 205),
    'hn02_lec_p27_inner': (27, 209),
    'hn02_lec_p29_fetal': (29, 217),
    'hn02_lec_p29_pforamen': (29, 218),
    'hn02_lec_p30_font_sup': (30, 223),
    'hn02_lec_p30_font_lat': (30, 224),
}


def main():
    doc = pymupdf.open(SOURCE)
    index = json.loads(INDEX.read_text(encoding='utf8'))
    for ident, (page, xref) in SPECS.items():
        pix = pymupdf.Pixmap(doc, xref)
        if pix.alpha or pix.n not in (1, 3):
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        image = Image.frombytes('RGB' if pix.n == 3 else 'L', (pix.width, pix.height), pix.samples).convert('RGB')
        path = ROOT / 'headneck/images' / (ident + '.jpeg')
        image.save(path, quality=96, subsampling=0)
        entry = next(item for item in index['assets'] if item['asset_id'] == ident)
        entry.update(bbox=list(doc[page-1].get_image_rects(xref)[0]), w=image.width,
                     h=image.height, px=image.width*image.height, bytes=path.stat().st_size,
                     note=f'تصویر اصلی جزوه، ص {page}، xref {xref}؛ بدون حاشیهٔ صفحه و متن مجاور')
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1)+'\n', encoding='utf8')
    print(f'recovered {len(SPECS)} embedded lecture figures')


if __name__ == '__main__':
    main()

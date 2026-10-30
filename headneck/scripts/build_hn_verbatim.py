"""Build sessions 1–2 with original lecture pages and adjacent reference figures.

The original lecture pages are copied as PDF pages, not OCR'd or rewritten.
Reference pages are separately identified; the old authored JSON is not used
as lecture text. Verification checks source-page rendering and extracted text.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import pymupdf
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'render'))
import hn_kit as K

CONFIG = {
    'hn01': {
        'source': ROOT / 'علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1/جلسه_اول_علوم_تشریح_سر_و_گردن_مهر_1404.pdf',
        'output': ROOT / 'pdf/HumsYar_HeadNeck_Jalase1.pdf',
        'num': '۱', 'expected_pages': 22,
        'sections': [(3, 'اسکلت و تقسیم‌بندی استخوان‌ها'), (6, 'تقسیم‌های جمجمه و حفره‌ها'),
                     (8, 'نمای قدامی و استخوان پیشانی'), (12, 'استخوان بینی'),
                     (13, 'فک فوقانی و زوائد'), (16, 'کام و سینوس فک فوقانی'),
                     (19, 'رادیوگرافی'), (20, 'مرور پایانی جزوه')],
    },
    'hn02': {
        'source': ROOT / 'علوم تشریح سر و گردن/جلسه 2 - سر و گردن 2/جلسه_دوم_علوم_تشریح_سر_و_گردن_مهر_1404.pdf',
        'output': ROOT / 'pdf/HumsYar_HeadNeck_Jalase2.pdf',
        'num': '۲', 'expected_pages': 33,
        'sections': [(3, 'استخوان گونه و قوس گونه‌ای'), (7, 'استخوان مندیبل'),
                     (11, 'سطح داخلی و تغییرات سنی مندیبل'), (16, 'سوراخ‌های نمای قدامی'),
                     (18, 'نمای طرفی و استخوان گیجگاهی'), (20, 'مفصل گیجگاهی‌مندیبلی'),
                     (26, 'استخوان آهیانه و درزها'), (30, 'ملاج‌ها'), (31, 'مرور پایانی جزوه')],
    },
}


def text(c, x, y, s, size=11, color=K.BODY, font='Vazir', align='right'):
    K.draw_shaped(c, x, y, K.shape(s), font, size, color, align=align)


def make_cards(session: str, cfg: dict, figs: list[dict], page_map: dict[int, int]) -> bytes:
    K.register_fonts()
    out = io.BytesIO()
    c = canvas.Canvas(out, pagesize=A4, pageCompression=1)
    w, h = A4
    # Cover matches the existing dark, teal/blue HumsYar palette.
    c.setFillColor(K.DARK_1); c.rect(0, 0, w, h, fill=1, stroke=0)
    c.linearGradient(0, h, w, 0, (K.DARK_1, K.DARK_2, K.DARK_3), (0, .55, 1))
    text(c, w/2, h-110, 'HumsYar · جزوهٔ مادر آناتومی', 11, HexColor('#8fa5c8'), 'VazirM', 'center')
    text(c, w/2, h/2+42, 'آناتومی سر و گردن', 23, HexColor('#f8fafc'), 'VazirB', 'center')
    text(c, w/2, h/2-3, f"جلسهٔ {cfg['num']} — متن اصلی جزوه", 19, HexColor('#f8fafc'), 'VazirB', 'center')
    c.setStrokeColor(K.TEAL); c.setLineWidth(2); c.line(180, h/2-27, w-180, h/2-27)
    text(c, w/2, h/2-66, 'صفحات جزوه بدون بازنویسی · تصاویر منتخب نتر و گری', 10.5,
         HexColor('#cbd5e1'), 'Vazir', 'center')
    text(c, w/2, 78, 'متن منبع عین صفحهٔ اصلی است؛ درستی علمی آن مستقل تأیید نشده است.', 8.3,
         HexColor('#aabbd0'), 'Vazir', 'center')
    c.showPage()
    # Reader guide + compact source-page index.
    text(c, w-45, h-58, 'راهنمای جزوه و فهرست', 18, K.INK, 'VazirB')
    c.setFillColor(K.TEAL_L); c.roundRect(42, h-190, w-84, 100, 8, fill=1, stroke=0)
    for i, line in enumerate([
        'صفحه‌های جزوهٔ درس به همان صورت اصلی و با تصویرهای خودشان درج شده‌اند.',
        'صفحه‌های سبزآبیِ «تصویر مرجع تکمیلی» جدا از متن جزوه‌اند.',
        'شمارهٔ منبع در جدول، شمارهٔ واقعی صفحهٔ فایل PDF جزوه است.',
        'شکل‌های نتر و گری منتخب‌اند؛ بازبینی علمی تخصصی جایگزین این جزوه نیست.',
    ]):
        text(c, w-54, h-114-20*i, line, 9.1, K.BODY)
    text(c, w-45, h-225, 'موضوع', 11, K.TEAL_D, 'VazirB')
    text(c, 195, h-225, 'صفحهٔ منبع', 10, K.TEAL_D, 'VazirB')
    text(c, 105, h-225, 'صفحهٔ این PDF', 10, K.TEAL_D, 'VazirB')
    y = h-250
    for page, title in cfg['sections']:
        c.setStrokeColor(K.LINE); c.line(45, y-8, w-45, y-8)
        text(c, w-45, y, title, 10.2)
        text(c, 180, y, str(page).translate(K.FA_DIGITS), 10, align='center')
        text(c, 95, y, str(page_map[page]).translate(K.FA_DIGITS), 10, align='center')
        y -= 35
    text(c, w-45, 75, 'برای دیدن همهٔ صفحات جزوه از نشانک‌های فایل نیز استفاده کنید.', 9, K.MUTED)
    c.showPage()
    for fig in figs:
        image_path = ROOT / 'headneck/images' / fig['asset']
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        c.setFillColor(K.TEAL_LL); c.rect(0, h-110, w, 110, stroke=0, fill=1)
        text(c, w-45, h-48, 'تصویر مرجع تکمیلی', 16, K.TEAL_D, 'VazirB')
        text(c, w-45, h-74, fig['topic'], 11, K.INK, 'VazirM')
        text(c, w-45, h-94, fig['citation'], 9, K.MUTED)
        from PIL import Image
        im = Image.open(image_path)
        if 'crop' in fig:
            im = im.crop(tuple(fig['crop']))
        image = ImageReader(im)
        iw, ih = image.getSize()
        scale = min((w-90)/iw, (h-205)/ih)
        dw, dh = iw*scale, ih*scale
        c.drawImage(image, (w-dw)/2, 77+(h-205-dh)/2, dw, dh,
                    preserveAspectRatio=True, mask='auto')
        text(c, w-45, 49, f"مرتبط با صفحهٔ {str(fig['after']).translate(K.FA_DIGITS)} جزوهٔ درس · این صفحه متن جزوه نیست", 8.6, K.MUTED)
        c.showPage()
    c.save()
    return out.getvalue()


def expected_mapping(session: str) -> dict:
    cfg = CONFIG[session]
    figs = json.loads((ROOT / 'headneck/content/hn_verbatim_figures.json').read_text())[session]
    by_page = defaultdict(list)
    for fig in figs:
        if not 1 <= fig['after'] <= cfg['expected_pages']:
            raise ValueError(fig)
        by_page[fig['after']].append(fig)
    source_pages, references, next_page = {}, [], 3
    for page in range(1, cfg['expected_pages'] + 1):
        source_pages[page] = next_page
        next_page += 1
        for fig in by_page[page]:
            references.append({'asset': fig['asset'], 'after_source_page': page,
                               'output_page': next_page, 'citation': fig['citation']})
            next_page += 1
    return {'session': session, 'source': str(cfg['source'].relative_to(ROOT)),
            'source_pages': source_pages, 'references': references,
            'output_pages': next_page - 1}


def build(session: str, out: Path) -> dict:
    cfg = CONFIG[session]
    figs = json.loads((ROOT / 'headneck/content/hn_verbatim_figures.json').read_text()) [session]
    source = pymupdf.open(cfg['source'])
    if len(source) != cfg['expected_pages']:
        raise ValueError(f'Unexpected source length: {len(source)}')
    by_page = defaultdict(list)
    for idx, fig in enumerate(figs):
        if not 1 <= fig['after'] <= len(source):
            raise ValueError(fig)
        by_page[fig['after']].append((idx, fig))
    page_map, reference_map = {}, []
    next_page = 3  # first two pages are cover and guide
    for i in range(1, len(source)+1):
        page_map[i] = next_page
        next_page += 1 + len(by_page[i])
    cards = pymupdf.open(stream=make_cards(session, cfg, figs, page_map), filetype='pdf')
    dest = pymupdf.open()
    dest.insert_pdf(cards, from_page=0, to_page=1, final=0)
    toc = [[1, f"جلسه {cfg['num']} — فهرست", 2]]
    for i in range(1, len(source)+1):
        dest.insert_pdf(source, from_page=i-1, to_page=i-1, final=0)
        assert len(dest) == page_map[i]
        toc.append([1, f'جزوهٔ اصلی — صفحهٔ PDF {i}', len(dest)])
        for card_idx, fig in by_page[i]:
            dest.insert_pdf(cards, from_page=card_idx+2, to_page=card_idx+2, final=0)
            reference_map.append({'asset': fig['asset'], 'after_source_page': i,
                                  'output_page': len(dest), 'citation': fig['citation']})
            toc.append([2, f"تصویر مرجع — {fig['topic']}", len(dest)])
    dest.set_toc(toc)
    out.parent.mkdir(parents=True, exist_ok=True)
    # pypdf writes a binary marker with a NUL early in the header, avoiding
    # accidental PDF byte transcoding by snapshot/patch systems.
    tmp = io.BytesIO(dest.tobytes(garbage=4, deflate=True))
    reader = PdfReader(tmp, strict=True)
    writer = PdfWriter()
    writer.append(reader, import_outline=True)
    writer.add_metadata({'/Title': f'HumsYar Head and Neck Session {session[-2:]}',
                         '/Subject': 'Original lecture pages and supplemental atlas figures'})
    writer.pdf_header = '%PDF-1.7\n%binary\x00'
    with out.open('wb') as f:
        writer.write(f)
    dest.close(); cards.close(); source.close()
    return {'session': session, 'source': str(cfg['source'].relative_to(ROOT)),
            'source_pages': page_map, 'references': reference_map, 'output_pages': next_page-1}


def verify(session: str, out: Path, mapping: dict) -> None:
    src, result = pymupdf.open(CONFIG[session]['source']), pymupdf.open(out)
    if len(result) != mapping['output_pages']:
        raise AssertionError('Unexpected number of pages')
    for page_no, target in mapping['source_pages'].items():
        a, b = src[int(page_no)-1], result[target-1]
        if a.rect != b.rect:
            raise AssertionError(f'{session} page {page_no}: page geometry changed')
        # Compare decoded page content streams: text drawing operators and
        # characters remain byte-for-byte unchanged. Text extraction order may
        # still vary because document-level PDF tagging is not copied.
        source_streams = [src.xref_stream(ref) for ref in a.get_contents()]
        output_streams = [result.xref_stream(ref) for ref in b.get_contents()]
        if source_streams != output_streams:
            raise AssertionError(f'{session} page {page_no}: content streams changed')
        x, y = a.get_pixmap(alpha=False), b.get_pixmap(alpha=False)
        if (x.width, x.height) != (y.width, y.height):
            raise AssertionError(f'{session} page {page_no}: raster dimensions changed')
        if x.samples != y.samples:
            from PIL import Image, ImageChops, ImageStat
            before = Image.frombytes('RGB', (x.width, x.height), x.samples)
            after = Image.frombytes('RGB', (y.width, y.height), y.samples)
            diff = ImageChops.difference(before, after)
            # Some PDFs round color conversion differently on copied pages.
            # Permit only tiny per-channel rounding, not changed layout/content.
            if max(high for _, high in diff.getextrema()) > 2 or max(ImageStat.Stat(diff).mean) > 0.1:
                raise AssertionError(f'{session} page {page_no}: page rendering changed')
    expected = expected_mapping(session)
    if mapping != expected:
        raise AssertionError('Page mapping does not match current reference manifest')
    figs = json.loads((ROOT / 'headneck/content/hn_verbatim_figures.json').read_text())[session]
    from PIL import Image
    for fig, spec in zip(mapping['references'], figs):
        if not result[fig['output_page']-1].get_images():
            raise AssertionError(f'Missing reference image on output page {fig["output_page"]}')
        next_source = mapping['source_pages'].get(fig['after_source_page'] + 1, len(result) + 1)
        if not mapping['source_pages'][fig['after_source_page']] < fig['output_page'] < next_source:
            raise AssertionError(f'Reference is not adjacent to its source page: {fig}')
        with Image.open(ROOT / 'headneck/images' / fig['asset']) as img:
            original = img.convert('RGB')
        if 'crop' in spec:
            original = original.crop(tuple(spec['crop']))
        candidates = [im for im in result[fig['output_page']-1].get_images()
                      if (im[2], im[3]) == original.size]
        if not candidates:
            raise AssertionError(f'Reference image dimensions differ: {fig}')
        def same_image(image):
            pix = pymupdf.Pixmap(result, image[0])
            decoded = Image.frombytes('RGBA' if pix.alpha else 'RGB',
                                      (pix.width, pix.height), pix.samples).convert('RGB')
            return decoded.tobytes() == original.tobytes()
        if not any(same_image(image) for image in candidates):
            raise AssertionError(f'Reference image pixels differ from asset: {fig}')
    print(f'{session}: {len(src)} source page content streams identical and visually equivalent (max pixel delta 2); '
          f'{len(mapping["references"])} reference pages; {len(result)} total pages')
    src.close(); result.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', choices=CONFIG, required=True)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--mapping', type=Path)
    args = ap.parse_args()
    out = args.out or CONFIG[args.session]['output']
    if out.exists() and not args.force:
        raise SystemExit(f'{out} already exists; pass --force to replace it')
    mapping = build(args.session, out)
    verify(args.session, out, mapping)
    if args.mapping:
        args.mapping.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n')
    print(f'written: {out}')


if __name__ == '__main__':
    main()

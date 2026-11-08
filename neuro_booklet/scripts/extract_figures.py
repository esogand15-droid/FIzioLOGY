# -*- coding: utf-8 -*-
"""استخراج تصاویر و جدول‌های منابع جلسه ۱ با محدودهٔ ثبت‌شده."""
import pymupdf, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "neuro_booklet", "assets", "figs")
os.makedirs(OUT, exist_ok=True)

SRC = {
    "1404": os.path.join(ROOT, "فیزیولوژی اعصاب حواس ویژه", "جلسه 1", "جلسه 1 نوروفیزیولوژی مهر 1404.pdf"),
    "1402": os.path.join(ROOT, "فیزیولوژی اعصاب حواس ویژه", "جلسه 1", "نوروفیزیولوژی 01 نهایی بهمن 1402.pdf"),
    "ganong": os.path.join(ROOT, "جزوه حواس ویژه", "1-400 ganong.pdf"),
}

# (key, source, page(1-based), image_index or None=full-width band, dpi, note)
JOBS = [
    ("f01_general_design",      "1404", 2,  0, 200),
    ("f02_neuron_parts",        "1404", 9,  0, 200),
    ("f03_shape_class",         "1404", 14, 0, 200),
    ("f04_function_class",      "1404", 17, 0, 200),
    ("f05_peptide_transport",   "1404", 20, 0, 200),
    ("f06_nt_table_1",          "1404", 23, 0, 200),
    ("f07_nt_table_2",          "1404", 29, 0, 200),
    ("f08_nt_table_3",          "1404", 34, 0, 200),
    ("f09_pharm_table_1",       "1404", 35, 0, 200),
    ("f10_pharm_table_2",       "1404", 36, 0, 200),
    ("f11_cotrans_A",           "1404", 38, 2, 220),
    ("f12_cotrans_B",           "1404", 38, 1, 220),
    ("f13_cotrans_C",           "1404", 38, 0, 220),
    ("f14_cotrans_main",        "1402", 12, 1, 220),
    ("f15_cotrans_cholinergic", "1402", 13, 2, 220),
    ("f16_guyton_t45_1_en",     "1402", 6,  1, 220),
    ("f17_guyton_t45_2_fa",     "1402", 7,  1, 220),
]

def crop_from_image(p, idx, dpi):
    infos = [x for x in p.get_image_info() if x['width'] > 150 and x['height'] > 150]
    infos.sort(key=lambda x: -(x['width']*x['height']))
    x = infos[idx]
    r = pymupdf.Rect(x['bbox'])
    r.x0 -= 3; r.y0 -= 3; r.x1 += 3; r.y1 += 3
    r = r & p.rect
    return p.get_pixmap(clip=r, dpi=dpi), r

manifest = []
for key, src, page, idx, dpi in JOBS:
    d = pymupdf.open(SRC[src])
    p = d[page-1]
    pix, rect = crop_from_image(p, idx, dpi)
    fn = os.path.join(OUT, key + ".png")
    pix.save(fn)
    manifest.append(dict(key=key, source=src, page=page, image_index=idx, dpi=dpi,
                         px=[pix.width, pix.height], rect=[round(v,1) for v in rect]))
    print(key, src, page, pix.width, pix.height)
json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), ensure_ascii=False, indent=1)

# ---- برش‌های اصلاحی و برش‌های کتاب گانونگ (مستطیل دستی، واحد point) ----
MANUAL = [
    ("f06_nt_table_1", "1404", 23, (68, 66, 581, 300), 200),
    ("f14_cotrans_main", "1402", 12, (34, 29, 486, 280), 220),
    ("g01_ganong_fig7_1", "ganong", 336, (70, 172, 308, 578), 200),
    ("g02_ganong_fig7_6", "ganong", 348, (70, 152, 444, 562), 200),
    ("g03_ganong_fig7_7", "ganong", 351, (70, 148, 474, 604), 200),
    ("g04_ganong_fig7_9", "ganong", 356, (70, 148, 474, 604), 200),
]
for key, src, page, r, dpi in MANUAL:
    d = pymupdf.open(SRC[src]); p = d[page-1]
    pix = p.get_pixmap(clip=pymupdf.Rect(*r), dpi=dpi)
    pix.save(os.path.join(OUT, key + ".png"))
    print(key, pix.width, pix.height)

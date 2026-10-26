"""برش شکل‌های جلسهٔ ۹ (تلانسفال) از جزوهٔ درس، گری و اسنل.

جزوهٔ درس شکل‌ها را کوچک جاسازی می‌کند و برچسب‌های انگلیسی را جدا نگه می‌دارد،
گری هم در این پیمانه لایهٔ متنی سالمی ندارد. پس این دو با رندر کردن همان ناحیه از
صفحه ساخته می‌شوند تا برچسب‌ها داخل قاب بمانند. شکل‌های اسنل خودشان تصویر
جاسازی‌شدهٔ مستقل‌اند و مستقیم استخراج می‌شوند.

    .venv/bin/python work/scripts/s09_crop.py
    .venv/bin/python work/scripts/s09_crop.py --only lect9_a13_c1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REF = REPO / "_refs"
OUT = REPO / "images_anatomy"

LEC1 = REF / "lectures/جلسه 9 پارت 1.pdf"
LEC2 = REF / "lectures/جلسه 9 پارت 2.pdf"
GRAYS = REF / "Grays 801-1000.pdf"
SNELL = REF / "Snells Clinical Neuroanatomy 9e.pdf"

# asset_id -> (فایل، شمارهٔ صفحهٔ PDF، مستطیل برش به نقطه، کتاب، توضیح کوتاه)
CROPS: dict[str, tuple[Path, int, tuple[float, float, float, float], str, str]] = {
    # ── جزوهٔ درس، بخش نخست (صفحه‌های ۱۳ تا ۱۷) ─────────────────────────────
    "lect9_a13_c1": (LEC1, 13, (36, 85, 308, 267), "lecture",
                     "تلانسفال در برش ساژیتال: جای آن میان دیانسفال و مخچه"),
    "lect9_a13_c2": (LEC1, 13, (311, 91, 559, 272), "lecture",
                     "سطح داخلی نیمکره: فورامن بین‌بطنی، فورنیکس و جسم پینه‌ای"),
    "lect9_a13_c3": (LEC1, 13, (38, 422, 359, 611), "lecture",
                     "نمای فوقانی نیمکره‌ها و شیار طولی میانی"),
    "lect9_a14_c1": (LEC1, 14, (36, 78, 371, 294), "lecture",
                     "برش افقی مغز: مادهٔ خاکستری، مادهٔ سفید و بطن جانبی"),
    "lect9_a14_c2": (LEC1, 14, (40, 648, 557, 769), "lecture",
                     "سه سطح نیمکره: فوقانی‌طرفی، داخلی و تحتانی"),
    "lect9_a15_c1": (LEC1, 15, (263, 150, 540, 341), "lecture",
                     "مرزهای نیمکره روی برش ساژیتال"),
    "lect9_a15_c2": (LEC1, 15, (92, 472, 503, 681), "lecture",
                     "سه قطب نیمکره و بخش‌های برش‌خوردهٔ آن"),
    "lect9_a16_c1": (LEC1, 16, (48, 162, 532, 420), "lecture",
                     "درجه‌بندی شیارها و جاویوس‌ها روی سطح لترال"),
    "lect9_a17_c1": (LEC1, 17, (36, 332, 534, 806), "lecture",
                     "هفت لوب مغز و جزیره در عمق شیار لترال"),
    # ── جزوهٔ درس، بخش دوم (صفحه‌های ۱ تا ۱۳) ──────────────────────────────
    "lect9_b01_c1": (LEC2, 1, (36, 188, 291, 362), "lecture",
                     "سطح لترال: شیار مرکزی، لترال و مرز لوب‌ها"),
    "lect9_b01_c2": (LEC2, 1, (36, 362, 290, 531), "lecture",
                     "سطح داخلی: دیانسفال، تالاموس و ساختارهای خط وسط"),
    "lect9_b02_c1": (LEC2, 2, (41, 87, 237, 236), "lecture",
                     "لوب‌های مغز در دو نمای رنگی"),
    "lect9_b02_c2": (LEC2, 2, (22, 251, 307, 431), "lecture",
                     "نواحی عملکردی قشر و شماره‌های برودمن"),
    "lect9_b03_c1": (LEC2, 3, (34, 148, 221, 301), "lecture",
                     "جاویوس‌های اوربیتال و مثلثی در نمای تحتانی"),
    "lect9_b03_c2": (LEC2, 3, (19, 347, 257, 494), "lecture",
                     "نقشهٔ نواحی حرکتی قشر پیشانی"),
    "lect9_b03_c3": (LEC2, 3, (16, 489, 256, 656), "lecture",
                     "هومونکولوس حرکتی و حسی روی دو جاویوس مجاور"),
    "lect9_b04_c1": (LEC2, 4, (40, 484, 211, 657), "lecture",
                     "ناحیهٔ ۴۴ و ۴۵ برودمن: جایگاه ناحیهٔ حرکتی گفتار"),
    "lect9_b05_c1": (LEC2, 5, (36, 628, 243, 781), "lecture",
                     "مدارهای زبان: بروکا، ورنیکه و آفازی هدایتی"),
    "lect9_b06_c1": (LEC2, 6, (92, 82, 503, 328), "lecture",
                     "نواحی عملکردی قشر و ارتباطشان با لوب‌ها"),
    "lect9_b06_c2": (LEC2, 6, (72, 550, 511, 807), "lecture",
                     "هومونکولوس حرکتی و حسی با اندازهٔ نسبی اندام‌ها"),
    "lect9_b07_c1": (LEC2, 7, (34, 53, 228, 342), "lecture",
                     "نقشهٔ برودمن روی سطح داخلی و لترال"),
    "lect9_b08_c1": (LEC2, 8, (34, 83, 273, 550), "lecture",
                     "نواحی حسی قشر آهیانه‌ای و بخش‌های برودمن"),
    "lect9_b10_c1": (LEC2, 10, (34, 122, 356, 350), "lecture",
                     "سطح داخلی لوب اکسیپیتال: کوینئوس، لینگوال و پروکونئوس"),
    "lect9_b11_c1": (LEC2, 11, (9, 157, 318, 410), "lecture",
                     "شیارهای اکسیپیتال روی سطح لترال و داخلی"),
    "lect9_b11_c2": (LEC2, 11, (26, 408, 291, 625), "lecture",
                     "نمای تحتانی نیمکره: جاویوس‌های اکسیپیتوتمپورال"),
    "lect9_b12_c1": (LEC2, 12, (23, 84, 208, 176), "lecture",
                     "اسکوتوم مرکزی: لکهٔ تیره در مرکز میدان بینایی"),
    "lect9_b12_c2": (LEC2, 12, (22, 190, 210, 300), "lecture",
                     "همی‌آنوپی هم‌نام: افت نیمهٔ میدان بینایی"),
    "lect9_b12_c3": (LEC2, 12, (27, 303, 333, 496), "lecture",
                     "نواحی زبانی روی سطح لترال و ارتباطشان با هم"),
    "lect9_b12_c4": (LEC2, 12, (22, 504, 330, 745), "lecture",
                     "نمای تحتانی مغز: جاویوس‌های لوب تمپورال"),
    "lect9_b13_c1": (LEC2, 13, (34, 266, 272, 746), "lecture",
                     "نواحی شنوایی اولیه و ثانویه و بخش‌های برودمن"),
    # ── گری ────────────────────────────────────────────────────────────────
    "grays3_801_1000_p0879_fig836b": (GRAYS, 106, (100, 412, 530, 716), "grays",
                                      "Fig. 8.36 — نمای جانبی مغز و لوب‌های آن"),
}

# asset_id -> (شمارهٔ صفحهٔ PDF اسنل، شمارهٔ تصویر در صفحه، فصل، توضیح)
SNELLS: dict[str, tuple[int, int, int, str]] = {
    "snell_ch13_p0870_img01": (870, 1, 13, "Fig. 13-6 — نمای فوقانی نیمکره‌های مغز"),
    "snell_ch13_p0871_img01": (871, 1, 13, "Fig. 13-7 — نمای جانبی نیمکرهٔ راست"),
    "snell_ch13_p0872_img01": (872, 1, 13, "Fig. 13-8 — نمای داخلی نیمکرهٔ راست"),
    "snell_ch13_p0875_img01": (875, 1, 13, "Fig. 13-10 — مرزهای لوب‌ها روی دو نما"),
    "snell_ch13_p0878_img01": (878, 1, 13, "Fig. 13-11 — نمای تحتانی مغز و شیارهای سطح کف"),
    "snell_ch13_p0889_img01": (889, 1, 13, "Fig. 13-18 — الیاف ارتباطی و نمای برش‌خورده"),
    "snell_ch13_p0890_img01": (890, 1, 13, "Fig. 13-19 — کپسول داخلی و تاج تابشی"),
}


def export_snell(idx: dict, only: list[str], written: int) -> int:
    d = pymupdf.open(SNELL)
    have = {x["asset_id"] for x in idx["assets"]}
    for aid, (page, order, chapter, note) in SNELLS.items():
        if only and aid not in only:
            continue
        imgs = d[page - 1].get_images(full=True)
        info = d.extract_image(imgs[order - 1][0])
        name = f"{aid}.{info['ext']}"
        (OUT / name).write_bytes(info["image"])
        row = dict(asset_id=aid, path=f"images_anatomy/{name}",
                   bytes=len(info["image"]), w=info["width"], h=info["height"],
                   page=page, session=None, chapter=chapter, kind="figure")
        if aid in have:
            idx["assets"] = [row if x["asset_id"] == aid else x for x in idx["assets"]]
        else:
            idx["assets"].append(row)
        written += 1
        print(f"{aid:30s} p{page:<5d} {info['width']}x{info['height']} "
              f"{row['bytes']//1024:>4d}KB  {note}")
    d.close()
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--dpi", type=int, default=300)
    a = ap.parse_args()

    idx_path = OUT / "INDEX.json"
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    have = {x["asset_id"] for x in idx["assets"]}
    docs: dict[Path, pymupdf.Document] = {}
    written = 0
    for aid, (src, page, clip, book, note) in CROPS.items():
        if a.only and aid not in a.only:
            continue
        if src not in docs:
            docs[src] = pymupdf.open(src)
        d = docs[src]
        rect = pymupdf.Rect(*clip)
        pix = d[page - 1].get_pixmap(dpi=a.dpi, clip=rect)
        name = f"{aid}.jpeg"
        pix.save(OUT / name, jpg_quality=88)
        pct = round(100 * rect.width * rect.height
                    / (d[page - 1].rect.width * d[page - 1].rect.height), 1)
        row = dict(asset_id=aid, book=book, session="s09",
                   source_file=(src.name + " (page render, labels included)"),
                   page=page, w=pix.width, h=pix.height, px=pix.width * pix.height,
                   area_pct=pct, bytes=(OUT / name).stat().st_size,
                   path=f"images_anatomy/{name}")
        if aid in have:
            idx["assets"] = [row if x["asset_id"] == aid else x for x in idx["assets"]]
        else:
            idx["assets"].append(row)
        written += 1
        print(f"{aid:32s} p{page:<3d} {pix.width}x{pix.height} "
              f"{row['bytes']//1024:>4d}KB  {note}")
    for d in docs.values():
        d.close()
    written = export_snell(idx, a.only, written)
    idx["assets"].sort(key=lambda x: x["asset_id"])
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"assets {written} · index total {len(idx['assets'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

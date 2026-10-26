"""برش شکل‌های جلسهٔ ۱۰ (هسته‌های قاعده‌ای) از جزوهٔ درس، اسنل و گری.

جزوهٔ درس شکل‌ها را کوچک جاسازی می‌کند، پس هر شکل با رندر کردن همان ناحیه از
صفحه ساخته می‌شود تا برچسب‌های انگلیسی که بیرون کادر تصویر نشسته‌اند هم داخل
قاب بمانند. شکل‌های اسنل خودشان تصویر جاسازی‌شدهٔ مستقل‌اند و مستقیم استخراج
می‌شوند؛ شکل گری هم چون لایهٔ متنی سالمی ندارد، از همان صفحه رندر می‌شود.

    .venv/bin/python work/scripts/s10_crop.py
    .venv/bin/python work/scripts/s10_crop.py --only lect10_p3_c1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REF = REPO / "_refs"
OUT = REPO / "images_anatomy"

LEC = REF / "lectures/جلسه 10.pdf"
GRAYS = REF / "Grays 801-1000.pdf"
SNELL = REF / "Snells Clinical Neuroanatomy 9e.pdf"

# asset_id -> (فایل، شمارهٔ صفحه، مستطیل برش، کتاب، توضیح کوتاه)
CROPS: dict[str, tuple[Path, int, tuple[float, float, float, float], str, str]] = {
    # ── جزوهٔ درس، صفحه‌های ۱ تا ۹ ─────────────────────────────────────────────
    "lect10_p1_c1": (LEC, 1, (28, 168, 322, 318), "lecture",
                     "برش ساژیتال: سینگولیت و اینسولا با رنگ مشخص شده‌اند"),
    "lect10_p1_c2": (LEC, 1, (28, 502, 322, 720), "lecture",
                     "نمای جانبی پس از برداشتن دو لب شیار لترال: اینسولا"),
    "lect10_p2_c1": (LEC, 2, (28, 236, 299, 540), "lecture",
                     "پنج نوع سلول قشر و شش لایه روی یک طرح"),
    "lect10_p3_c1": (LEC, 3, (18, 304, 339, 578), "lecture",
                     "برش کرونال با هسته‌های قاعده‌ای، کپسول داخلی و تالاموس"),
    "lect10_p4_c1": (LEC, 4, (28, 96, 331, 482), "lecture",
                     "الیاف ارتباطی روی نمای جانبی و طرح دسته‌های بلند"),
    "lect10_p5_c1": (LEC, 5, (11, 182, 361, 456), "lecture",
                     "سطح داخلی نیمکره: بخش‌های جسم پینه‌ای و برش آن"),
    "lect10_p5_c2": (LEC, 5, (405, 196, 588, 438), "lecture",
                     "نمای فوقانی جسم پینه‌ای و ایندیزیوم گریزئوم"),
    "lect10_p5_c3": (LEC, 5, (26, 566, 334, 790), "lecture",
                     "برش عرضی: فورسپس مینور و ماژور"),
    "lect10_p6_c1": (LEC, 6, (36, 272, 232, 528), "lecture",
                     "فورنیکس روی برش عرضی و سپتوم پلیوسیدوم"),
    "lect10_p6_c2": (LEC, 6, (243, 350, 514, 554), "lecture",
                     "فورنیکس و هیپوکمپ در نمای سه‌بعدی"),
    "lect10_p7_c1": (LEC, 7, (71, 46, 567, 226), "lecture",
                     "بطن‌های مغز و نسبت فورنیکس با سپتوم"),
    "lect10_p7_c2": (LEC, 7, (34, 567, 567, 810), "lecture",
                     "برش کرونال با سپتوم پلیوسیدوم و بطن‌های جانبی"),
    "lect10_p8_c1": (LEC, 8, (28, 86, 355, 317), "lecture",
                     "تاج تابشی: الیاف پروجکشن از قشر تا ساقهٔ مغز"),
    "lect10_p8_c2": (LEC, 8, (30, 520, 334, 810), "lecture",
                     "کپسول داخلی و سه دستهٔ الیاف آن در طرح سه‌بعدی"),
    "lect10_p9_c1": (LEC, 9, (27, 540, 595, 814), "lecture",
                     "دو برش کرونال و افقی با کپسول داخلی و هسته‌های قاعده‌ای"),
    # ── گری، صفحهٔ ۸۸۴ چاپی (شکل ۸.۴۰) ─────────────────────────────────────────
    "grays3_801_1000_p0884_fig840": (GRAYS, 112, (82, 88, 580, 614), "grays",
                                     "Fig. 8.40 — تصویربرداری سکته: سیتی و ام‌آر"),
}

# asset_id -> (شمارهٔ صفحه، ترتیب تصویر، فصل، توضیح کوتاه)
SNELLS: dict[str, tuple[int, int, int, str]] = {
    "snell_ch13_p0879_img01": (879, 1, 13, "Fig. 13-12 — برش افقی: عدسی، دمی و کپسول داخلی"),
    "snell_ch13_p0882_img01": (882, 1, 13, "Fig. 13-14 — نمای جانبی برش‌خورده: جای هسته‌ها"),
    "snell_ch13_p0888_img01": (888, 1, 13, "Fig. 13-17 — برش افقی و اجزای کپسول داخلی"),
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
    ap.add_argument("--only", nargs="*", default=None)
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
        row = dict(asset_id=aid, book=book, session="s10",
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

"""برش شکل‌های جلسهٔ ۶ از رندر صفحه (جزوهٔ درس و گری).

جزوهٔ درس شکل‌ها را کوچک جاسازی کرده و برچسب‌های انگلیسی را جدا نگه می‌دارد؛
گری هم لایهٔ متنی سالمی ندارد. پس هر شکل با رندر کردن همان ناحیه از صفحه و در
۳۰۰ dpi ساخته می‌شود تا برچسب‌ها داخل قاب بمانند.

    .venv/bin/python work/scripts/s06_crop.py
    .venv/bin/python work/scripts/s06_crop.py --only lect6_p002_c1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REF = Path("/home/user/_refs")
OUT = REPO / "images_anatomy"

LECTURE = REF / "lectures/نورو آناتومی جلسه ۶ مهر 1404.pdf"
GRAYS = REF / "user - Gray's Anatomy For Students, 3rd Edition-801-1000.pdf"

# asset_id -> (فایل، شمارهٔ صفحهٔ PDF، مستطیل برش به نقطه، کتاب، توضیح کوتاه)
CROPS: dict[str, tuple[Path, int, tuple[float, float, float, float], str, str]] = {
    # ── جزوهٔ درس ───────────────────────────────────────────────────────────
    "lect6_p002_c1": (LECTURE, 2, (333, 343, 598, 528), "lecture",
                      "تقسیم پونز به بخش قاعده‌ای و تگمنتوم"),
    "lect6_p003_c1": (LECTURE, 3, (18, 352, 283, 526), "lecture",
                      "مقطع پل در سطح فاسیل کولیکولوس"),
    "lect6_p005_c1": (LECTURE, 5, (22, 262, 302, 468), "lecture",
                      "مقطع فوقانی پل در سطح هسته‌های عصب سه‌قلو"),
    "lect6_p006_c1": (LECTURE, 6, (25, 245, 300, 460), "lecture",
                      "نمای قدامی ساقهٔ مغز و خروج اعصاب جمجمه‌ای"),
    "lect6_p007_c1": (LECTURE, 7, (335, 338, 595, 505), "lecture",
                      "نمای پشتی مغز میانی و چهار کولیکولوس"),
    "lect6_p007_c2": (LECTURE, 7, (25, 485, 300, 665), "lecture",
                      "نمای جانبی مغز میانی و بازوهای ارتباطی"),
    "lect6_p008_c1": (LECTURE, 8, (22, 100, 282, 218), "lecture",
                      "مقطع سطح کولیکولوس فوقانی"),
    "lect6_p008_c2": (LECTURE, 8, (22, 222, 282, 325), "lecture",
                      "مقطع سطح کولیکولوس تحتانی"),
    "lect6_p014_c1": (LECTURE, 14, (20, 245, 316, 396), "lecture",
                      "مدار رفلکس نوری مردمک"),
    "lect6_p014_c3": (LECTURE, 14, (6, 402, 314, 526), "lecture",
                      "برش‌های تصویری ساقهٔ مغز در ناهنجاری آرنولد-کیاری"),
    "lect6_p014_c2": (LECTURE, 14, (320, 256, 582, 505), "lecture",
                      "دو مقطع مغز میانی در سطح کولیکولوس فوقانی و تحتانی"),
    "lect6_p017_c1": (LECTURE, 17, (386, 224, 610, 432), "lecture",
                      "مقطع بصل‌النخاع در سطح سندروم والنبرگ"),
    "lect6_p017_c2": (LECTURE, 17, (18, 528, 335, 700), "lecture",
                      "مقطع بصل‌النخاع در سندروم مدولاری داخلی"),
    "lect6_p020_c1": (LECTURE, 20, (18, 52, 312, 182), "lecture",
                      "مقطع مغز میانی در سندروم وبر"),
    "lect6_p020_c2": (LECTURE, 20, (18, 188, 312, 262), "lecture",
                      "مقطع مغز میانی در سندروم بندیکت"),
    # ── گری ────────────────────────────────────────────────────────────────
    "grays3_801_1000_p0880_fig837": (GRAYS, 108, (60, 60, 575, 365), "grays",
                                     "Fig. 8.37 — برش ساژیتال مغز"),
    "grays3_801_1000_p0882_fig839": (GRAYS, 110, (78, 468, 582, 700), "grays",
                                     "Fig. 8.39 — شریان‌های قاعدهٔ مغز"),
    "grays3_801_1000_p0885_fig841": (GRAYS, 113, (30, 500, 600, 790), "grays",
                                     "Fig. 8.41 — آنوریسم نوک شریان بازیلار"),
}


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
        row = dict(asset_id=aid, book=book, session="s06",
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
    idx["assets"].sort(key=lambda x: x["asset_id"])
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"crops {written} · index total {len(idx['assets'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

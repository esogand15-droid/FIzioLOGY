"""برش شکل‌های جلسهٔ ۷ (مخچه) از رندر صفحه (جزوهٔ درس و گری).

جزوهٔ درس شکل‌ها را کوچک جاسازی می‌کند و برچسب‌های انگلیسی را جدا نگه می‌دارد؛
گری هم لایهٔ متنی سالمی ندارد. پس هر شکل با رندر کردن همان ناحیه از صفحه و در
۳۰۰ dpi ساخته می‌شود تا برچسب‌ها داخل قاب بمانند.

    .venv/bin/python work/scripts/s07_crop.py
    .venv/bin/python work/scripts/s07_crop.py --only lect7_p002_c1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REF = Path("/home/user/_refs")
OUT = REPO / "images_anatomy"

LECTURE = REF / "lectures/نورو آناتومی جلسه 7 بهمن 1402.pdf"
GRAYS = REF / "user - Gray's Anatomy For Students, 3rd Edition-801-1000.pdf"

# asset_id -> (فایل، شمارهٔ صفحهٔ PDF، مستطیل برش به نقطه، کتاب، توضیح کوتاه)
CROPS: dict[str, tuple[Path, int, tuple[float, float, float, float], str, str]] = {
    # ── جزوهٔ درس ───────────────────────────────────────────────────────────
    "lect7_p002_c1": (LECTURE, 2, (28, 100, 570, 288), "lecture",
                      "سطح فوقانی و سطح تحتانی مخچه"),
    "lect7_p002_c2": (LECTURE, 2, (24, 396, 318, 572), "lecture",
                      "نمای پهن‌شدهٔ مخچه و شیارهای اصلی"),
    "lect7_p004_c1": (LECTURE, 4, (28, 436, 578, 692), "lecture",
                      "سه لایهٔ قشر مخچه و سلول‌های هر لایه"),
    "lect7_p005_c1": (LECTURE, 5, (30, 336, 325, 536), "lecture",
                      "مدار سلولی قشر مخچه: الیاف خزه‌ای و بالارونده"),
    "lect7_p006_c1": (LECTURE, 6, (44, 246, 340, 468), "lecture",
                      "هسته‌های عمقی مخچه از خارج به داخل"),
    "lect7_p007_c1": (LECTURE, 7, (30, 152, 208, 420), "lecture",
                      "الیاف وابران مخچه و مقصد آن‌ها"),
    "lect7_p008_c1": (LECTURE, 8, (80, 148, 512, 372), "lecture",
                      "مدارهای ارکئوسربلوم و دستگاه دهلیزی"),
    "lect7_p009_c1": (LECTURE, 9, (46, 216, 566, 470), "lecture",
                      "مدارهای پالئوسربلوم و مسیرهای نخاعی-مخچه‌ای"),
    "lect7_p010_c1": (LECTURE, 10, (50, 76, 544, 356), "lecture",
                      "مدارهای نئوسربلوم: حلقهٔ قشر-پل-مخچه-تالاموس"),
    "lect7_p010_c2": (LECTURE, 10, (32, 506, 258, 712), "lecture",
                      "سه پایک مخچه‌ای و اتصال به سه بخش ساقهٔ مغز"),
    "lect7_p011_c1": (LECTURE, 11, (72, 210, 520, 466), "lecture",
                      "پایک فوقانی: آوران و وابران"),
    "lect7_p011_c2": (LECTURE, 11, (28, 466, 240, 700), "lecture",
                      "پایک میانی و الیاف پونتو-مخچه‌ای"),
    "lect7_p012_c1": (LECTURE, 12, (30, 218, 486, 492), "lecture",
                      "پایک تحتانی: آوران و وابران"),
    # ── گری ────────────────────────────────────────────────────────────────
    "grays3_801_1000_p0869_fig827": (GRAYS, 97, (38, 56, 604, 330), "grays",
                                     "Fig. 8.27 — حفرهٔ کرانیال خلفی"),
    "grays3_801_1000_p0879_fig836": (GRAYS, 107, (38, 405, 604, 742), "grays",
                                     "Fig. 8.36 — نمای جانبی مغز و جایگاه مخچه"),
    "grays3_801_1000_p0880_fig837b": (GRAYS, 108, (58, 50, 606, 392), "grays",
                                      "Fig. 8.37 — برش ساژیتال و جایگاه مخچه"),
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
        row = dict(asset_id=aid, book=book, session="s07",
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

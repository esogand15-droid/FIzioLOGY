"""برش شکل‌های جلسهٔ ۸ (دیانسفال) از جزوهٔ درس، گری و اسنل.

جزوهٔ درس شکل‌ها را کوچک جاسازی می‌کند و برچسب‌های انگلیسی را جدا نگه می‌دارد،
گری هم در این پیمانه لایهٔ متنی سالمی ندارد. پس این دو با رندر کردن همان ناحیه از
صفحه ساخته می‌شوند تا برچسب‌ها داخل قاب بمانند. شکل‌های اسنل خودشان تصویر
جاسازی‌شدهٔ مستقل‌اند و مستقیم استخراج می‌شوند.

    .venv/bin/python work/scripts/s08_crop.py
    .venv/bin/python work/scripts/s08_crop.py --only lect8_p002_c1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REF = REPO / "_refs"
OUT = REPO / "images_anatomy"

LECT1 = REF / "lectures/نورو آناتومی جلسه 8 پارت 1 بهمن 1402.pdf"
LECT2 = REF / "lectures/نورو آناتومی جلسه 8 پارت 2 و جلسه 9 پارت 1 بهمن 1402.pdf"
GRAYS = REF / "Grays 801-1000.pdf"
SNELL = REF / "Snells Clinical Neuroanatomy 9e.pdf"

# asset_id -> (فایل، شمارهٔ صفحهٔ PDF، مستطیل برش به نقطه، کتاب، توضیح کوتاه)
CROPS: dict[str, tuple[Path, int, tuple[float, float, float, float], str, str]] = {
    # ── جزوهٔ درس، بخش ۱ ────────────────────────────────────────────────────
    "lect8_p001_c1": (LECT1, 1, (42, 166, 566, 342), "lecture",
                      "بطن چهارم: سقف، پرده‌های مدولاری و برش ساژیتال"),
    "lect8_p001_c2": (LECT1, 1, (32, 532, 314, 762), "lecture",
                      "دیوارهٔ بطن سوم و ساختارهای اطراف آن"),
    "lect8_p002_c1": (LECT1, 2, (38, 540, 392, 802), "lecture",
                      "دستگاه بطنی مغز در نمای شفاف جانبی"),
    "lect8_p004_c1": (LECT1, 4, (33, 80, 342, 320), "lecture",
                      "برش کرونال بطن‌ها از نمای خلفی"),
    "lect8_p004_c2": (LECT1, 4, (95, 410, 502, 792), "lecture",
                      "نمای تحتانی مغز: کف بطن سوم و ساختارهای آن"),
    "lect8_p006_c1": (LECT1, 6, (34, 52, 562, 460), "lecture",
                      "برش ساژیتال: تالاموس، هیپوتالاموس و بطن سوم"),
    "lect8_p006_c2": (LECT1, 6, (28, 626, 236, 806), "lecture",
                      "طرح تالاموس با سه گروه هسته‌ای"),
    "lect8_p007_c1": (LECT1, 7, (74, 378, 558, 792), "lecture",
                      "سطح فوقانی تالاموس در برش کرونال"),
    "lect8_p009_c1": (LECT1, 9, (22, 54, 344, 316), "lecture",
                      "سطح لترال تالاموس و کپسول داخلی"),
    "lect8_p009_c2": (LECT1, 9, (22, 318, 316, 626), "lecture",
                      "مادهٔ سفید تالاموس: زونولا، تیغه‌های مدولاری"),
    "lect8_p010_c1": (LECT1, 10, (46, 260, 562, 706), "lecture",
                      "طرح تالاموس: هسته‌های لترال، مدیال و آنتریور"),
    "lect8_p011_c1": (LECT1, 11, (71, 120, 524, 578), "lecture",
                      "مقطع تالاموس: هستهٔ رتیکولار و اینترالامینار"),
    "lect8_p012_c1": (LECT1, 12, (34, 54, 372, 320), "lecture",
                      "اتصالات تالاموس با بخش‌های مختلف قشر مغز"),
    "lect8_p012_c2": (LECT1, 12, (34, 316, 338, 578), "lecture",
                      "نقشهٔ قشر مغز برای هسته‌های تالاموس"),
    # ── جزوهٔ درس، بخش ۲ ────────────────────────────────────────────────────
    "lect8b_p002_c1": (LECT2, 2, (34, 82, 328, 322), "lecture",
                       "نشانه‌های ضایعهٔ تالاموس: دست تالاموسی و تصویربرداری"),
    "lect8b_p003_c1": (LECT2, 3, (110, 508, 506, 794), "lecture",
                       "تقسیم‌بندی سه‌بعدی هیپوتالاموس"),
    "lect8b_p004_c1": (LECT2, 4, (38, 178, 370, 402), "lecture",
                       "هسته‌های هیپوتالاموس در برش ساژیتال"),
    "lect8b_p006_c1": (LECT2, 6, (47, 186, 335, 458), "lecture",
                       "وابران‌های هیپوتالاموس به ساقهٔ مغز و نخاع"),
    "lect8b_p007_c1": (LECT2, 7, (70, 52, 276, 290), "lecture",
                       "مسیر شنوایی از گیرنده تا قشر"),
    "lect8b_p007_c2": (LECT2, 7, (283, 52, 548, 298), "lecture",
                       "مسیر بینایی از شبکیه تا جسم ژنیکولیت لترال"),
    "lect8b_p007_c3": (LECT2, 7, (38, 334, 358, 518), "lecture",
                       "اپی‌تالاموس در برش ساژیتال"),
    "lect8b_p007_c4": (LECT2, 7, (52, 512, 354, 734), "lecture",
                       "هستهٔ هابنولا و غدهٔ صنوبری روی نمونه"),
    "lect8b_p008_c1": (LECT2, 8, (98, 336, 497, 594), "lecture",
                       "اپی‌تالاموس از نمای فوقانی و اتصالات آن"),
    "lect8b_p009_c1": (LECT2, 9, (16, 324, 318, 518), "lecture",
                       "جایگاه غدهٔ صنوبری در بطن سوم"),
    "lect8b_p010_c1": (LECT2, 10, (26, 52, 308, 280), "lecture",
                       "عملکرد غدهٔ صنوبری و ملاتونین"),
    "lect8b_p010_c2": (LECT2, 10, (43, 314, 360, 518), "lecture",
                       "ساب‌تالاموس: مادهٔ سفید و مسیرهای آن"),
    "lect8b_p011_c1": (LECT2, 11, (26, 282, 342, 506), "lecture",
                       "مادهٔ خاکستری ساب‌تالاموس و چهار هستهٔ آن"),
    # ── گری ────────────────────────────────────────────────────────────────
    "grays3_801_1000_p0880_fig837c": (GRAYS, 108, (110, 60, 556, 352), "grays",
                                      "Fig. 8.37 — دیانسفال در برش ساژیتال"),
    "grays3_801_1000_p0882_fig839": (GRAYS, 110, (86, 424, 536, 720), "grays",
                                     "Fig. 8.39 — شریان‌های قاعدهٔ مغز"),
}

# asset_id -> (شمارهٔ صفحهٔ PDF اسنل، شمارهٔ تصویر در صفحه، فصل، توضیح)
SNELLS: dict[str, tuple[int, int, int, str]] = {
    "snell_ch13_p0857_img01": (857, 1, 13, "Fig. 13-1 — برش افقی مغز: بطن سوم و بطن‌های جانبی"),
    "snell_ch13_p0858_img01": (858, 1, 13, "Fig. 13-2 — نمای تحتانی مغز: اجزای دیانسفال"),
    "snell_ch13_p0859_img01": (859, 1, 13, "Fig. 13-3 — برش ساژیتال: سطح داخلی دیانسفال"),
    "snell_ch13_p0861_img01": (861, 1, 13, "Fig. 13-4 — هسته‌های تالاموس"),
    "snell_ch13_p0864_img01": (864, 1, 13, "Fig. 13-5 — غدهٔ صنوبری در مقطع بافتی"),
    "snell_ch16_p1027_img01": (1027, 1, 16, "Fig. 16-7 — برش ساژیتال بطن چهارم"),
    "snell_ch16_p1032_img01": (1032, 1, 16, "Fig. 16-11 — نمای خلفی حفرهٔ بطن چهارم"),
    "snell_ch16_p1033_img01": (1033, 1, 16, "Fig. 16-13 — سقف بطن چهارم پس از برداشتن مخچه"),
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
        row = dict(asset_id=aid, book=book, session="s08",
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

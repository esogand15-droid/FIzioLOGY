"""برش شکل‌های جلسهٔ ۱۱ (دستگاه لیمبیک و رتیکولار فورمیشن).

جزوهٔ این جلسه شکل‌ها را به‌صورت تصویر جاسازی کرده و برچسب‌های انگلیسی بیرون
کادر تصویر نشسته‌اند؛ پس شکل‌ها با رندر همان ناحیه از صفحه ساخته می‌شوند تا
برچسب‌ها داخل قاب بمانند. شکل‌های اسنل تصویر مستقل‌اند و مستقیم استخراج
می‌شوند؛ شکل گری هم از صفحه رندر می‌شود.

    .venv/bin/python work/scripts/s11_crop.py
    .venv/bin/python work/scripts/s11_crop.py --only lect11_p2_c1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REF = REPO / "_refs"
OUT = REPO / "images_anatomy"

LEC = REF / "lectures/جلسه 11.pdf"
GRAYS = REF / "Grays 801-1000.pdf"
SNELL = REF / "Snells Clinical Neuroanatomy 9e.pdf"

CROPS: dict[str, tuple[Path, int, tuple[float, float, float, float], str, str]] = {
    # ── جزوهٔ درس، صفحه‌های ۱ تا ۲۰ ────────────────────────────────────────────
    "lect11_p2_c1": (LEC, 2, (226, 146, 545, 409), "lecture",
                     "لوب لیمبیک روی سطح داخلی، با رنگ نارنجی"),
    "lect11_p2_c2": (LEC, 2, (28, 485, 545, 704), "lecture",
                     "طرح سه‌بخشی: لیمبیک، اینترالیمبیک و کمان داخلی"),
    "lect11_p4_c1": (LEC, 4, (26, 66, 545, 394), "lecture",
                     "برش عرضی: هیپوکمپ و فورنیکس در دو طرف"),
    "lect11_p5_c1": (LEC, 5, (33, 66, 545, 300), "lecture",
                     "نمای تحتانی مغز: پاراهیپوکمپال، آنکوس و شیارها"),
    "lect11_p5_c2": (LEC, 5, (34, 401, 545, 646), "lecture",
                     "اسب دریایی و طرح لایه‌های هیپوکمپال فورمیشن"),
    "lect11_p7_c1": (LEC, 7, (61, 66, 545, 297), "lecture",
                     "طرح دست‌نویس: فورنیکس، میلیاری بادی، آمیگدال و هیپوکمپ"),
    "lect11_p7_c2": (LEC, 7, (40, 496, 545, 699), "lecture",
                     "نمای سه‌بعدی فورنیکس و ساختمان‌های اطراف"),
    "lect11_p8_c1": (LEC, 8, (37, 171, 545, 398), "lecture",
                     "استریای طولی میانی و طرفی روی جسم پینه‌ای"),
    "lect11_p10_c1": (LEC, 10, (31, 66, 545, 309), "lecture",
                     "آمیگدال با هشت برچسب و دو بخش آن"),
    "lect11_p11_c1": (LEC, 11, (72, 122, 545, 326), "lecture",
                     "مسیر میلیاری-تالامیک، فورنیکس و آمیگدال"),
    "lect11_p12_c1": (LEC, 12, (34, 66, 545, 359), "lecture",
                     "برش کرونال با استریا ترمینالیس و آلوئولوس"),
    "lect11_p13_c1": (LEC, 13, (35, 66, 545, 278), "lecture",
                     "حلقهٔ لیمبیک با هشت برچسب الف تا ح"),
    "lect11_p15_c1": (LEC, 15, (117, 66, 545, 305), "lecture",
                     "حلقهٔ لیمبیک در طرح رنگی، همان ساختارها"),
    "lect11_p18_c1": (LEC, 18, (33, 66, 545, 329), "lecture",
                     "ستون‌های رتیکولار در ساقهٔ مغز"),
    # ── گری، صفحهٔ ۸۸۰ چاپی (شکل ۸.۳۷) ─────────────────────────────────────────
    "grays3_801_1000_p0880_fig837": (GRAYS, 108, (38, 62, 572, 359), "grays",
                                     "Fig. 8.37 — برش ساژیتال مغز و جایگاه لوب لیمبیک"),
}

# asset_id -> (شمارهٔ صفحه، ترتیب تصویر، فصل، توضیح کوتاه)
SNELLS: dict[str, tuple[int, int, int, str]] = {
    "snell_ch08_p0667_img01": (667, 1, 8, "Fig. 8-1 — سه ستون رتیکولار در ساقهٔ مغز"),
    "snell_ch08_p0672_img01": (672, 1, 8, "Fig. 8-3 — ساختارهای لوب لیمبیک در نمای داخلی"),
    "snell_ch08_p0673_img01": (673, 1, 8, "Fig. 8-4 — هیپوکمپ، دنتیت و فورنیکس"),
    "snell_ch08_p0677_img01": (677, 1, 8, "Fig. 8-7 — آوران و وابران دستگاه لیمبیک"),
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
        row = dict(asset_id=aid, book=book, session="s11",
                   source_file=(src.name + " (page render, labels included)"),
                   page=page, w=pix.width, h=pix.height, px=pix.width * pix.height,
                   area_pct=pct, bytes=(OUT / name).stat().st_size,
                   path=f"images_anatomy/{name}")
        if aid in have:
            idx["assets"] = [row if x["asset_id"] == aid else x for x in idx["assets"]]
        else:
            idx["assets"].append(row)
        written += 1
        print(f"{aid:30s} p{page:<3d} {pix.width}x{pix.height} "
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

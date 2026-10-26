"""برش شکل‌های جلسهٔ ۱۲ (دستگاه عصبی خودکار و خون‌رسانی مغز).

شکل‌های جزوه با رندر همان ناحیه از صفحه ساخته می‌شوند تا برچسب‌های انگلیسی
که بیرون کادر تصویر نشسته‌اند داخل قاب بمانند. شکل‌های اسنل تصویر مستقل‌اند و
مستقیم استخراج می‌شوند؛ شکل‌های گری هم از صفحه رندر می‌شوند.

    .venv/bin/python work/scripts/s12_crop.py
    .venv/bin/python work/scripts/s12_crop.py --only lect12_p1_c1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REF = REPO / "_refs"
OUT = REPO / "images_anatomy"

LEC = REF / "lectures/جلسه 12.pdf"
GRAYS = REF / "Grays 801-1000.pdf"
SNELL = REF / "Snells Clinical Neuroanatomy 9e.pdf"

CROPS: dict[str, tuple[Path, int, tuple[float, float, float, float], str, str]] = {
    # ── جزوهٔ درس، صفحه‌های ۱ تا ۱۴ ────────────────────────────────────────────
    "lect12_p1_c1": (LEC, 1, (26, 368, 302, 742), "lecture",
                     "شکل ۱ — مقایسهٔ دو سیستم سمپاتیک و پاراسمپاتیک"),
    "lect12_p2_c1": (LEC, 2, (26, 260, 382, 636), "lecture",
                     "شکل ۲ — سیستم سمپاتیک با زنجیره و اندام‌ها"),
    "lect12_p3_c1": (LEC, 3, (26, 30, 286, 206), "lecture",
                     "شکل ۳ — شاخ طرفی در قطعات نخاعی"),
    "lect12_p3_c2": (LEC, 3, (26, 238, 386, 577), "lecture",
                     "شکل ۴ — سرنوشت الیاف سمپاتیک پس از خروج"),
    "lect12_p4_c1": (LEC, 4, (12, 12, 352, 266), "lecture",
                     "شکل ۶ — مسیر سمپاتیک تا سرخرگ کاروتید"),
    "lect12_p4_c2": (LEC, 4, (342, 12, 572, 315), "lecture",
                     "شکل ۵ — شاخه‌های ارتباطی سفید و خاکستری"),
    "lect12_p4_c3": (LEC, 4, (16, 486, 214, 788), "lecture",
                     "شکل ۸ — اعصاب اسپلانکنیک و گانگلیون‌های شکمی"),
    "lect12_p5_c1": (LEC, 5, (26, 472, 326, 782), "lecture",
                     "شکل ۹ — توزیع الیاف پاراسمپاتیک همراه اعصاب مغزی"),
    "lect12_p6_c1": (LEC, 6, (34, 356, 300, 584), "lecture",
                     "شکل ۱۰ — گانگلیون‌های سر و گردن و عصب سه‌قلو"),
    "lect12_p7_c1": (LEC, 7, (26, 30, 366, 327), "lecture",
                     "شکل ۱۱ — توزیع عصب واگ در گردن و قفسهٔ سینه"),
    "lect12_p7_c2": (LEC, 7, (292, 411, 574, 783), "lecture",
                     "شکل ۱۲ — توزیع پاراسمپاتیک از هسته تا اندام"),
    "lect12_p7_c3": (LEC, 7, (23, 408, 300, 781), "lecture",
                     "شکل ۱۳ — سیستم پاراسمپاتیک و اندام‌های هدف"),
    "lect12_p8_c1": (LEC, 8, (90, 56, 507, 462), "lecture",
                     "شکل ۱۴ — منشأ شریان‌های مهره‌ای و کاروتید داخلی"),
    "lect12_p9_c1": (LEC, 9, (98, 301, 490, 730), "lecture",
                     "شکل ۱۵ — خون‌رسانی مغز در نمای تحتانی"),
    "lect12_p10_c1": (LEC, 10, (26, 464, 254, 776), "lecture",
                      "شکل ۱۶ — حلقهٔ ویلیس با رنگ‌آمیزی"),
    "lect12_p11_c2": (LEC, 11, (32, 412, 293, 619), "lecture",
                      "شکل ۱۸ — نواحی قشری روی سطح داخلی"),
    "lect12_p12_c1": (LEC, 12, (30, 88, 562, 354), "lecture",
                      "شکل ۱۹ — نواحی خون‌رسانی شاخه‌های قشری"),
    "lect12_p12_c2": (LEC, 12, (25, 460, 372, 766), "lecture",
                      "شکل ۲۰ — شاخه‌های مرکزی و نواحی عمقی"),
    "lect12_p13_c1": (LEC, 13, (26, 334, 374, 764), "lecture",
                      "شکل ۲۱ — تخلیهٔ وریدی مغز"),
    "lect12_p14_c1": (LEC, 14, (26, 30, 370, 356), "lecture",
                      "شکل ۲۲ — سینوس‌های وریدی و وریدهای عمقی"),
    "lect12_p14_c2": (LEC, 14, (53, 495, 566, 784), "lecture",
                      "شکل ۲۳ — خون‌رسانی نخاع"),
    # ── گری، فصل ۸ ────────────────────────────────────────────────────────────
    "grays3_801_1000_p0882_fig839b": (GRAYS, 110, (60, 412, 560, 718), "grays",
                                     "Fig. 8.39 — شریان‌های قاعدهٔ مغز"),
    "grays3_801_1000_p0887_fig844": (GRAYS, 115, (38, 50, 548, 362), "grays",
                                     "Fig. 8.44 — وریدها، سخت‌شامه و سینوس‌های وریدی"),
}

# asset_id -> (شمارهٔ صفحه، ناحیهٔ برش، فصل، توضیح کوتاه)
SNELLS: dict[str, tuple[int, tuple[float, float, float, float], int, str]] = {
    "snell_ch12_p0782_img01": (783, (102, 66, 566, 440), 12,
                               "Fig. 12-2 — بخش وابران دستگاه عصبی خودکار"),
    "snell_ch12_p0791_img01": (792, (162, 246, 448, 592), 12,
                               "Fig. 12-5 — میانجی‌های شیمیایی در پایانه‌ها"),
    "snell_ch12_p0806_img01": (807, (120, 226, 506, 558), 12,
                               "Fig. 12-9 — عصب‌گیری خودکار قلب و شش"),
    "snell_ch17_p1080_img01": (1081, (118, 66, 494, 404), 17,
                               "Fig. 17-2 — شریان‌های سطح تحتانی مغز"),
    "snell_ch17_p1082_img01": (1083, (104, 44, 500, 520), 17,
                               "Fig. 17-3 — نواحی خون‌رسانی شریان‌های مغزی"),
    "snell_ch17_p1093_img01": (1094, (136, 112, 576, 372), 17,
                               "Fig. 17-7 — خون‌رسانی شریان‌های نخاع"),
}


def export_snell(idx: dict, only: list[str] | None, written: int,
                 dpi: int = 300) -> int:
    d = pymupdf.open(SNELL)
    have = {x["asset_id"] for x in idx["assets"]}
    for aid, (page, clip, chapter, note) in SNELLS.items():
        if only and aid not in only:
            continue
        rect = pymupdf.Rect(*clip)
        pix = d[page - 1].get_pixmap(dpi=dpi, clip=rect)
        name = f"{aid}.jpeg"
        pix.save(OUT / name, jpg_quality=88)
        pct = round(100 * rect.width * rect.height
                    / (d[page - 1].rect.width * d[page - 1].rect.height), 1)
        row = dict(asset_id=aid, book="snell", session="s12",
                   source_file=(SNELL.name + " (page render, labels included)"),
                   page=page, w=pix.width, h=pix.height, px=pix.width * pix.height,
                   area_pct=pct, bytes=(OUT / name).stat().st_size,
                   chapter=chapter, kind="figure",
                   path=f"images_anatomy/{name}")
        if aid in have:
            idx["assets"] = [row if x["asset_id"] == aid else x for x in idx["assets"]]
        else:
            idx["assets"].append(row)
        written += 1
        print(f"{aid:28s} p{page:<5d} {pix.width}x{pix.height} "
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
        row = dict(asset_id=aid, book=book, session="s12",
                   source_file=(src.name + " (page render, labels included)"),
                   page=page, w=pix.width, h=pix.height, px=pix.width * pix.height,
                   area_pct=pct, bytes=(OUT / name).stat().st_size,
                   path=f"images_anatomy/{name}")
        if aid in have:
            idx["assets"] = [row if x["asset_id"] == aid else x for x in idx["assets"]]
        else:
            idx["assets"].append(row)
        written += 1
        print(f"{aid:28s} p{page:<3d} {pix.width}x{pix.height} "
              f"{row['bytes']//1024:>4d}KB  {note}")
    for d in docs.values():
        d.close()
    written = export_snell(idx, a.only, written, a.dpi)
    idx["assets"].sort(key=lambda x: x["asset_id"])
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"assets {written} · index total {len(idx['assets'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

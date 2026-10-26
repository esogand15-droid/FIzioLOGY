"""برش شکل‌های جلسهٔ ۱۳ (تکامل دستگاه عصبی).

شکل‌های جزوه با رندر همان ناحیه از صفحه ساخته می‌شوند تا متن انگلیسی روی
شکل و زیرنویسش داخل قاب بمانند. شکل‌های اسنل و گری هم از صفحه رندر می‌شوند،
چون در این دو کتاب شکل و زیرنویس به هم چسبیده‌اند و بریدن تصویر خام،
زیرنویس را از دست می‌دهد.

    .venv/bin/python work/scripts/s13_crop.py
    .venv/bin/python work/scripts/s13_crop.py --only lect13_p1_c1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REF = REPO / "_refs"
OUT = REPO / "images_anatomy"

LEC = REF / "lectures/جلسه 13.pdf"
GRAYS = REF / "Grays 801-1000.pdf"
SNELL = REF / "Snells Clinical Neuroanatomy 9e.pdf"

CROPS: dict[str, tuple[Path, int, tuple[float, float, float, float], str, str]] = {
    # ── جزوهٔ درس، صفحه‌های ۱ تا ۲۷ ────────────────────────────────────────────
    "lect13_p1_c1": (LEC, 1, (42, 298, 570, 670), "lecture",
                     "شکل ۱۹.۱ — صفحه و شیار عصبی در رویان ۱۸ و ۲۰ روزه"),
    "lect13_p2_c1": (LEC, 2, (150, 82, 460, 456), "lecture",
                     "شکل ۱۹.۲ — برش عرضی: از شیار تا لولهٔ عصبی و تاج عصبی"),
    "lect13_p3_c1": (LEC, 3, (70, 58, 540, 434), "lecture",
                     "شکل ۱۹.۳ — بسته شدن دو نوروپور در روز ۲۲ و ۲۳"),
    "lect13_p4_c1": (LEC, 4, (72, 80, 540, 336), "lecture",
                     "جدول وزیکول‌های اولیه و ثانویه و ساختارهای بالغ"),
    "lect13_p5_c1": (LEC, 5, (38, 232, 574, 690), "lecture",
                     "شکل ۱۹.۴ — برش ساژیتال مغز جنین با سه وزیکول"),
    "lect13_p6_c1": (LEC, 6, (112, 28, 500, 316), "lecture",
                     "شکل ۱۹.۵ — تفکیک وزیکول‌ها به پنج بخش در روز ۳۲"),
    "lect13_p6_c2": (LEC, 6, (150, 364, 462, 746), "lecture",
                     "شکل ۱۹.۶ — سلول‌های نورواپی‌تلیال دیوارهٔ لوله"),
    "lect13_p7_c1": (LEC, 7, (162, 82, 450, 406), "lecture",
                     "شکل ۱۹.۷ — نوروبلاست‌ها در دیوارهٔ لولهٔ عصبی"),
    "lect13_p7_c2": (LEC, 7, (158, 434, 452, 741), "lecture",
                     "شکل ۱۹.۸ — صفحات آلار و بازال و شاخ‌های نخاع"),
    "lect13_p8_c1": (LEC, 8, (106, 474, 506, 672), "lecture",
                     "شکل ۱۹.۹ — از نوروبلاست آپولار تا نورون مالتی‌پولار"),
    "lect13_p9_c1": (LEC, 9, (62, 104, 550, 434), "lecture",
                     "شکل ۱۹.۱۰ — رشد آکسون حرکتی و تشکیل عصب نخاعی"),
    "lect13_p10_c1": (LEC, 10, (122, 28, 490, 292), "lecture",
                      "شکل ۱۹.۱۱ — منشأ نورون و انواع سلول‌های گلیال"),
    "lect13_p10_c2": (LEC, 10, (78, 528, 534, 744), "lecture",
                      "شکل ۱۹.۱۲ — میلین‌سازی در مرکز و در محیط"),
    "lect13_p12_c1": (LEC, 12, (162, 28, 450, 253), "lecture",
                      "بالا آمدن نخاع نسبت به ستون مهره‌ها"),
    "lect13_p12_c2": (LEC, 12, (144, 528, 468, 752), "lecture",
                      "شکل ۱۹.۱۵ — انواع اسپاینا بیفیدا"),
    "lect13_p14_c1": (LEC, 14, (136, 82, 476, 318), "lecture",
                      "شکل ۱۹.۱۶ — نوزادان با ضایعهٔ اسپاینا بیفیدا"),
    "lect13_p14_c2": (LEC, 14, (120, 420, 492, 738), "lecture",
                      "شکل ۱۹.۱۸ ب و ج — تفکیک هسته‌های بصل النخاع"),
    "lect13_p16_c1": (LEC, 16, (122, 338, 490, 570), "lecture",
                      "شکل ۱۹.۱۹ — هسته‌های پل و هسته‌های حرکتی و حسی"),
    "lect13_p17_c1": (LEC, 17, (100, 128, 512, 487), "lecture",
                      "صفحات رومبیک و تشکیل لولهٔ مخچه"),
    "lect13_p17_c2": (LEC, 17, (132, 482, 480, 729), "lecture",
                      "مراحل رشد قشر مخچه و هستهٔ دندانه‌ای"),
    "lect13_p18_c1": (LEC, 18, (102, 398, 510, 557), "lecture",
                      "برش مغز میانی و ستون‌های بصل النخاع"),
    "lect13_p18_c2": (LEC, 18, (66, 554, 546, 732), "lecture",
                      "لایهٔ گرانولار خارجی و مهاجرت سلول‌های پورکنژ"),
    "lect13_p20_c1": (LEC, 20, (146, 82, 468, 457), "lecture",
                      "شکل ۱۹.۲۶ — کیسهٔ راتکه و تکامل هیپوفیز"),
    "lect13_p21_c1": (LEC, 21, (108, 28, 504, 289), "lecture",
                      "شکل ۱۹.۱۷ — نمای جانبی وزیکول‌های مغزی در هفتهٔ هشتم"),
    "lect13_p21_c2": (LEC, 21, (134, 426, 478, 619), "lecture",
                      "شکل ۱۹.۲۴ — دیانسفال و صفحهٔ تالاموس"),
    "lect13_p22_c1": (LEC, 22, (178, 28, 436, 369), "lecture",
                      "شکل ۱۹.۲۷ — بطن جانبی و هسته‌های قاعده‌ای"),
    "lect13_p22_c2": (LEC, 22, (100, 462, 512, 684), "lecture",
                      "شکل ۱۹.۲۸ — شکل‌گیری شکنج و شیار در ماه ۷ و ۹"),
    "lect13_p23_c1": (LEC, 23, (40, 202, 572, 487), "lecture",
                      "شکل ۱۹.۲۹ — کمیسورها و پیاز بویایی در ماه چهارم"),
    "lect13_p24_c1": (LEC, 24, (204, 156, 408, 364), "lecture",
                      "ناهنجاری خط وسط در تصویر مقطعی مغز"),
    "lect13_p24_c2": (LEC, 24, (86, 412, 526, 630), "lecture",
                      "شکل ۱۹.۳۵ — انواع فتق مغز و سخت‌شامه"),
    "lect13_p25_c1": (LEC, 25, (220, 28, 392, 305), "lecture",
                      "مننگوسل در سونوگرافی و در نوزاد"),
    "lect13_p25_c2": (LEC, 25, (96, 414, 516, 668), "lecture",
                      "شکل ۱۹.۳۷ — نوزاد بی‌مغز در دو نما"),
    "lect13_p26_c1": (LEC, 26, (140, 28, 472, 298), "lecture",
                      "هیدروسفالی با بزرگ شدن سر"),
    "lect13_p26_c2": (LEC, 26, (110, 422, 502, 682), "lecture",
                      "مالفورماسیون کیاری در مقایسه با مغز طبیعی"),
    "lect13_p27_c1": (LEC, 27, (182, 28, 430, 317), "lecture",
                      "میکروسفالی با سر کوچک‌تر از حد معمول"),
    # ── اسنل، فصل ۱ و ۱۸ ──────────────────────────────────────────────────────
    "snell_ch01_p0045_img01": (SNELL, 45, (158, 194, 454, 562), 1,
                               "Fig. 1-16 — صفحه، شیار و لولهٔ عصبی و مشتقات تاج عصبی"),
    "snell_ch01_p0047_img01": (SNELL, 47, (140, 66, 472, 358), 1,
                               "Fig. 1-17 — وزیکول‌های مغزی و دیوارهٔ لولهٔ عصبی"),
    "snell_ch18_p1150_img01": (SNELL, 1150, (176, 540, 434, 724), 18,
                               "Fig. 18-8 — تقسیم پروزنسفالون به تلانسفال و دیانسفال"),
    "snell_ch18_p1159_img01": (SNELL, 1159, (130, 66, 482, 508), 18,
                               "Fig. 18-12 — انواع اسپاینا بیفیدا در برش عرضی"),
    "snell_ch18_p1162_img01": (SNELL, 1162, (194, 452, 418, 636), 18,
                               "Fig. 18-14 — هیدروسفالی و بزرگی سر"),
    # ── گری، فصل ۸ ────────────────────────────────────────────────────────────
    "grays3_801_1000_p0879_fig836d": (GRAYS, 107, (56, 408, 562, 746), "grays",
                                      "Fig. 8.36 — نمای جانبی مغز بالغ و لوب‌های آن"),
    "grays3_801_1000_p0890_fig846": (GRAYS, 118, (48, 58, 566, 774), "grays",
                                     "Fig. 8.46 — پوست سر، سخت‌شامه و سینوس‌ها"),
}


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
    for aid, spec in CROPS.items():
        if a.only and aid not in a.only:
            continue
        src, page, clip, note = spec[0], spec[1], spec[2], spec[4]
        if src not in docs:
            docs[src] = pymupdf.open(src)
        d = docs[src]
        rect = pymupdf.Rect(*clip)
        pix = d[page - 1].get_pixmap(dpi=a.dpi, clip=rect)
        name = f"{aid}.jpeg"
        pix.save(OUT / name, jpg_quality=88)
        pct = round(100 * rect.width * rect.height
                    / (d[page - 1].rect.width * d[page - 1].rect.height), 1)
        book = spec[3]
        chapter = spec[5] if len(spec) > 5 else (1 if src == SNELL else 8)
        row = dict(asset_id=aid, book=book, session="s13",
                   source_file=(src.name + " (page render, labels included)"),
                   page=page, w=pix.width, h=pix.height, px=pix.width * pix.height,
                   area_pct=pct, bytes=(OUT / name).stat().st_size,
                   chapter=chapter, kind="figure",
                   path=f"images_anatomy/{name}")
        if aid in have:
            idx["assets"] = [row if x["asset_id"] == aid else x for x in idx["assets"]]
        else:
            idx["assets"].append(row)
        written += 1
        print(f"{aid:30s} p{page:<5d} {pix.width}x{pix.height} "
              f"{row['bytes']//1024:>4d}KB  {note}")
    for d in docs.values():
        d.close()
    idx["assets"].sort(key=lambda x: x["asset_id"])
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"assets {written} · index total {len(idx['assets'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

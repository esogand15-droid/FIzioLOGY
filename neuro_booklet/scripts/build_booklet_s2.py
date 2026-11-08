# -*- coding: utf-8 -*-
"""ساخت جزوهٔ جلسهٔ ۲ — سیناپس، انتقال سیناپسی و مدارهای نورونی."""
import os
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NB = os.path.join(ROOT, "neuro_booklet")
sys.path.insert(0, NB)
sys.path.insert(0, os.path.join(NB, "render"))
sys.path.insert(0, os.path.join(NB, "content"))
os.chdir(ROOT)

from rtl_kit import Kit, fa  # noqa: E402
import furniture  # noqa: E402
from content_render import render_mabhas  # noqa: E402
import s2_front as front  # noqa: E402
from s2_m01_m07 import MABAHES_S2_A  # noqa: E402
from s2_m08_m14 import MABAHES_S2_B  # noqa: E402

OUT_DIR = os.path.join(ROOT, "pdf")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "HumsYar_NeuroSpecialSenses_Jalase02.pdf")
TOC_CACHE = os.path.join(NB, "build", "toc_cache_s2.json")

META = dict(
    pdf_title="HumsYar — جزوهٔ مادر فیزیولوژی اعصاب و حواس ویژه — جلسهٔ ۲",
    author="HumsYar",
    subject="جزوهٔ مادر جلسهٔ ۲: سیناپس، انتقال سیناپسی و مدارهای نورونی",
    header_right="جزوهٔ مادر · فیزیولوژی اعصاب و حواس ویژه · جلسهٔ ۲",
    header_left="HumsYar",
    footer_right="سیناپس، انتقال سیناپسی و مدارهای نورونی",
    footer_left="HumsYar · جزوهٔ مادر",
)

CLUSTERS = {
    0: ("خوشهٔ ۱ — سیناپس: الکتریکی، شیمیایی، گیرنده و پتانسیل‌های موضعی", "مباحث ۱–۵"),
    5: ("خوشهٔ ۲ — یکپارچگی سیناپسی و دندریت", "مباحث ۶–۱۰"),
    10: ("خوشهٔ ۳ — تنظیم آزادسازی و مدارهای نورونی", "مباحث ۱۱–۱۴"),
}


def build(entries, out_path):
    k = Kit(out_path, os.path.join(ROOT, "assets", "fonts"), META)
    furniture.cover(k, front.COVER)
    furniture.guide_page(k, front.GUIDE)
    furniture.toc(k, entries, CLUSTERS)
    furniture.session_opener(k, front.OPENER)
    furniture.closing_note(k, "یادداشت برنامه‌ریزی: تقسیم کار تیم روی ۱۴ مبحث")
    for blocks in MABAHES_S2_A:
        render_mabhas(k, blocks)
    for blocks in MABAHES_S2_B:
        render_mabhas(k, blocks)
    furniture.checklist_page(k, front.CHECK)
    furniture.closing_note(k, "یادداشت پایانی جلسه")
    furniture.back_cover(k, front.BACK)
    k.save()
    return k


def main():
    entries = []
    if os.path.exists(TOC_CACHE):
        entries = json.load(open(TOC_CACHE))
    k = None
    for i in range(5):
        k = build(entries, OUT)
        new = [list(e) for e in k.toc]
        stable = [list(e) for e in entries] == new
        entries = new
        json.dump(entries, open(TOC_CACHE, "w"), ensure_ascii=False, indent=1)
        print(f"pass {i+1}: pages={k.page_no} toc={len(new)} stable={stable}")
        if stable and i >= 1:
            break
    print("OUT:", OUT, "pages:", k.page_no)


if __name__ == "__main__":
    main()

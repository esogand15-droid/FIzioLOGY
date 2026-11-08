# -*- coding: utf-8 -*-
"""ساخت جزوهٔ جلسهٔ ۱ — فیزیولوژی اعصاب و حواس ویژه (نسخهٔ راست‌به‌چپ)."""
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
import front  # noqa: E402
from m01_m10 import MABAHES_A  # noqa: E402
from m11_m23 import MABAHES_B  # noqa: E402
import fig_patch  # noqa: E402

fig_patch.apply_extra([MABAHES_A, MABAHES_B])

OUT_DIR = os.path.join(ROOT, "pdf")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "HumsYar_NeuroSpecialSenses_Jalase01.pdf")
TOC_CACHE = os.path.join(NB, "build", "toc_cache.json")

META = dict(
    pdf_title="HumsYar — جزوهٔ مادر فیزیولوژی اعصاب و حواس ویژه — جلسهٔ ۱",
    author="HumsYar",
    subject="جزوهٔ مادر جلسهٔ ۱: سازمان‌دهی دستگاه عصبی، نورون و ناقلین عصبی",
    header_right="جزوهٔ مادر · فیزیولوژی اعصاب و حواس ویژه · جلسهٔ ۱",
    header_left="HumsYar",
    footer_right="سازمان‌دهی دستگاه عصبی، نورون و ناقلین عصبی",
    footer_left="HumsYar · جزوهٔ مادر",
)


CLUSTERS = {
    0: ("خوشهٔ ۱ — سازمان‌دهی دستگاه عصبی، نورون و گلیا", "مباحث ۱–۱۰"),
    10: ("خوشهٔ ۲ — ناقلین عصبی: نوروپپتیدها، آمین‌ها، استیل‌کولین", "مباحث ۱۱–۱۷"),
    17: ("خوشهٔ ۳ — گابا، گلوتامات، گلیسین، گازها، گیرنده‌ها، کوترانسمیترها", "مباحث ۱۸–۲۳"),
}


def build(entries, out_path):
    k = Kit(out_path, os.path.join(ROOT, "assets", "fonts"), META)
    furniture.cover(k, front.COVER)
    furniture.guide_page(k, front.GUIDE)
    furniture.toc(k, entries, CLUSTERS)
    furniture.session_opener(k, front.OPENER)
    furniture.closing_note(k, "یادداشت برنامه‌ریزی: تقسیم کار تیم روی ۲۳ مبحث")
    for blocks in MABAHES_A:
        render_mabhas(k, blocks)
    for blocks in MABAHES_B:
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
    hist = []
    for i in range(5):
        k = build(entries, OUT)
        new = [list(e) for e in k.toc]
        hist.append((len(new), len(entries)))
        stable = [list(e) for e in entries] == new
        entries = new
        json.dump(entries, open(TOC_CACHE, "w"), ensure_ascii=False, indent=1)
        print(f"pass {i+1}: pages={k.page_no} toc_entries={len(new)} stable={stable}")
        if stable and i >= 1:
            break
    print("OUT:", OUT)
    print("pages:", k.page_no)


if __name__ == "__main__":
    main()

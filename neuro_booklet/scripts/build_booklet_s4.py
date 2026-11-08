# -*- coding: utf-8 -*-
"""ساخت جزوهٔ جلسهٔ ۴ — مسیرهای حسی، قشر حسی-پیکری، درد و حرارت."""
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
import s4_front as front  # noqa: E402
from s4_m01_m06 import MABAHES_S4_A  # noqa: E402
from s4_m07_m12 import MABAHES_S4_B  # noqa: E402
from s4_m13_m18 import MABAHES_S4_C  # noqa: E402
from s4_m19_m26 import MABAHES_S4_D  # noqa: E402
from s4_appendix import APPENDIX_1402  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402

OUT_DIR = os.path.join(ROOT, "pdf")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "HumsYar_NeuroSpecialSenses_Jalase04.pdf")
TOC_CACHE = os.path.join(NB, "build", "toc_cache_s4.json")

META = dict(
    pdf_title="HumsYar — جزوهٔ مادر فیزیولوژی اعصاب و حواس ویژه — جلسهٔ ۴",
    author="HumsYar",
    subject="جزوهٔ مادر جلسهٔ ۴: مسیرهای حسی، قشر حسی-پیکری، درد و حرارت",
    header_right="جزوهٔ مادر · فیزیولوژی اعصاب و حواس ویژه · جلسهٔ ۴",
    header_left="HumsYar",
    footer_right="مسیرهای حسی، قشر، درد و حرارت",
    footer_left="HumsYar · جزوهٔ مادر",
)

CLUSTERS = {
    0: ("خوشهٔ ۱ — از نخاع تا قشر", "مباحث ۱–۶"),
    6: ("خوشهٔ ۲ — سازمان قشر", "مباحث ۷–۱۲"),
    12: ("خوشهٔ ۳ — کنترل، آسیب و کدگذاری", "مباحث ۱۳–۱۸"),
    18: ("خوشهٔ ۴ — درد و حرارت + پیوست", "مباحث ۱۹–۲۶، پیوست و چک‌لیست"),
}


def appendix_page(k, data):
    """پیوست: نقشهٔ مقابلهٔ بندبه‌بند با جزوهٔ ۱۴۰۲."""
    k.new_page("body")
    k.h_section_band(data["kicker"], data["title"], key=data["key"], sub=data["sub"])
    k.toc.append((1, "پیوست — " + data["title"], k.page_no, data["key"]))
    k.para(data["intro"], size=9.2, space_after=2 * mm)
    k.para(data["legend"], size=8.6, color="#3c4757", space_after=2.4 * mm)
    k.table(data["headers"], data["rows"], widths=data["widths"], size=7.7,
            caption=data["table_caption"], source=data["table_source"])
    k.box(data["added_title"], data["added_body"], source=data["added_source"],
          kind="note", size=8.6, icon="")
    k.box(data["verdict_title"], data["verdict_body"], source=data["verdict_source"],
          kind="amber", size=8.6, icon="")
    furniture.closing_note(k, "یادداشت بازبین مقابله")


def build(entries, out_path):
    k = Kit(out_path, os.path.join(ROOT, "assets", "fonts"), META)
    furniture.cover(k, front.COVER)
    furniture.guide_page(k, front.GUIDE)
    furniture.toc(k, entries, CLUSTERS, entry_step=7.0, cluster_step=7.8)
    furniture.session_opener(k, front.OPENER)
    furniture.closing_note(k, "یادداشت برنامه‌ریزی: تقسیم کار تیم روی ۲۶ مبحث")
    for blocks in MABAHES_S4_A:
        render_mabhas(k, blocks)
    for blocks in MABAHES_S4_B:
        render_mabhas(k, blocks)
    for blocks in MABAHES_S4_C:
        render_mabhas(k, blocks)
    for blocks in MABAHES_S4_D:
        render_mabhas(k, blocks)
    appendix_page(k, APPENDIX_1402)
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

# -*- coding: utf-8 -*-
"""ساخت جزوهٔ آناتومی جلسهٔ ۴ — عروق و اعصاب چشم + بافت‌شناسی چشم و گوش."""
import os
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NB = os.path.join(ROOT, "neuro_booklet")
sys.path.insert(0, NB)
sys.path.insert(0, os.path.join(NB, "render"))
sys.path.insert(0, os.path.join(NB, "content"))
os.chdir(ROOT)

from rtl_kit import Kit  # noqa: E402
import furniture  # noqa: E402
from content_render import render_mabhas  # noqa: E402
import anat4_front as front  # noqa: E402
from anat4_m01_m05 import MABAHES_A4_A  # noqa: E402
from anat4_m06_m10 import MABAHES_A4_B  # noqa: E402
from anat4_m11_m13 import MABAHES_A4_C  # noqa: E402
from anat4_m14_m18 import MABAHES_A4_D  # noqa: E402
from anat4_m19_m23 import MABAHES_A4_E  # noqa: E402
from anat4_appendix import APPENDIX_A4  # noqa: E402
from anat4_summary import SUMMARY_A4, EXAM_A4  # noqa: E402
from anat4_refs import REF_BLOCKS, SRC_FIGS  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402

OUT_DIR = os.path.join(ROOT, "pdf")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "HumsYar_AnatHawas_Jalase04.pdf")
TOC_CACHE = os.path.join(NB, "build", "toc_cache_anat4.json")
os.makedirs(os.path.dirname(TOC_CACHE), exist_ok=True)

META = dict(
    pdf_title="HumsYar — جزوهٔ مادر آناتومی حواس ویژه — جلسهٔ ۴",
    author="HumsYar",
    subject="جزوهٔ مادر آناتومی جلسهٔ ۴: عروق و اعصاب چشم + بافت‌شناسی چشم و گوش",
    header_right="جزوهٔ مادر · آناتومی حواس ویژه · جلسهٔ ۴",
    header_left="HumsYar",
    footer_right="عروق و اعصاب چشم + بافت‌شناسی",
    footer_left="HumsYar · جزوهٔ مادر",
)

CLUSTERS = {
    0: ("خوشهٔ ۱ — شریان‌ها، آناستوموزها و وریدها", "مباحث ۱–۵"),
    5: ("خوشهٔ ۲ — عصب افتالمیک، عصب بینایی و زوج III", "مباحث ۶–۱۰"),
    10: ("خوشهٔ ۳ — زوج IV و VI و سینوس کاورنوس", "مباحث ۱۱–۱۳"),
    13: ("خوشهٔ ۴ — بافت‌شناسی چشم و گوش + خلاصه و پیوست", "مباحث ۱۴–۲۳، خلاصه، پیوست، آزمون و چک‌لیست"),
}


def appendix_page(k, data):
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


def summary_page(k, data):
    k.new_page("body")
    k.h_section_band(data["kicker"], data["title"], key=data["key"], sub=data["sub"])
    k.toc.append((1, data["title"], k.page_no, data["key"]))
    k.para(data["intro"], size=9.2, space_after=2 * mm)
    k.table(data["headers1"], data["rows1"], widths=data["widths1"], size=7.8,
            caption=data["caption1"], source=data["source1"])
    k.table(data["headers2"], data["rows2"], widths=data["widths2"], size=7.8,
            caption=data["caption2"], source=data["source2"])
    k.box(data["box_title"], data["box_body"], source=data["box_source"], kind="note", size=8.6, icon="")


def exam_page(k, data):
    k.new_page("body")
    k.h_section_band(data["kicker"], data["title"], key=data["key"], sub=data["sub"])
    k.toc.append((1, data["title"], k.page_no, data["key"]))
    k.para(data["intro"], size=9.2, space_after=1.5 * mm)
    k.para(data["note"], size=8.6, color="#3c4757", space_after=2.0 * mm)
    k.box(data["amber_title"], data["amber_body"], source=data["amber_source"], kind="amber", size=8.1, icon="")
    for q, opts, ans in data["questions"]:
        k.para(q, size=9.0, font="sb", space_after=0.6 * mm)
        opt_txt = "  ".join("%s) %s" % (n, o) for n, o in zip(["۱", "۲", "۳", "۴"], opts))
        k.para(opt_txt, size=8.1, color="#3c4757", space_after=0.4 * mm)
        k.para(ans, size=8.1, color="#0d9488", space_after=1.9 * mm)
    ak = data["answer_key"]
    k.gap(2 * mm)
    k.para("پاسخ‌نامهٔ رسمی آزمون تألیفی", size=9.2, font="sb", space_after=1.2 * mm)
    for i in range(0, len(ak), 5):
        k.para("   ·   ".join(ak[i:i + 5]), size=8.6, color="#0d9488", space_after=0.8 * mm)
    k.source_line(data["answer_note"])


def build(entries, out_path):
    k = Kit(out_path, os.path.join(ROOT, "assets", "fonts"), META)
    furniture.cover(k, front.COVER)
    furniture.guide_page(k, front.GUIDE)
    furniture.toc(k, entries, CLUSTERS, entry_step=7.0, cluster_step=7.8)
    furniture.session_opener(k, front.OPENER)
    furniture.closing_note(k, "یادداشت برنامه‌ریزی: تقسیم کار تیم روی ۲۳ مبحث")
    for group in (MABAHES_A4_A, MABAHES_A4_B, MABAHES_A4_C, MABAHES_A4_D, MABAHES_A4_E):
        for blocks in group:
            b2 = list(blocks)
            num = blocks[0][1] if blocks and blocks[0][0] == "mabhas" else None
            figs = SRC_FIGS.get(num)
            if figs:
                pos = 2 if len(b2) > 2 and b2[1][0] == "p" and b2[2][0] == "src" else 1
                b2[pos:pos] = list(figs)
            extra = REF_BLOCKS.get(num)
            if extra:
                idx = next((i for i, x in enumerate(b2) if x[0] == "note"), len(b2))
                b2[idx:idx] = list(extra)
            render_mabhas(k, b2)
    summary_page(k, SUMMARY_A4)
    appendix_page(k, APPENDIX_A4)
    exam_page(k, EXAM_A4)
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

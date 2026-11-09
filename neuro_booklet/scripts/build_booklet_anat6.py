# -*- coding: utf-8 -*-
"""ساخت جزوهٔ آناتومی جلسهٔ ۶ — آناتومی عملی (مولاژها و لام‌ها)."""
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
import anat6_front as front  # noqa: E402
from anat6_m01_m07 import MABAHES_A6_A  # noqa: E402
from anat6_m08_m12 import MABAHES_A6_B  # noqa: E402
from anat6_m13_m19 import MABAHES_A6_C  # noqa: E402
from anat6_m20_m25 import MABAHES_A6_D  # noqa: E402
from anat6_appendix import APPENDIX_A6  # noqa: E402
from anat6_summary import SUMMARY_A6, EXAM_A6  # noqa: E402
from anat6_refs import REF_BLOCKS, SRC_FIGS  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402

OUT_DIR = os.path.join(ROOT, "pdf")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "HumsYar_AnatHawas_Jalase06.pdf")
TOC_CACHE = os.path.join(NB, "build", "toc_cache_anat6.json")
os.makedirs(os.path.dirname(TOC_CACHE), exist_ok=True)

META = dict(
    pdf_title="HumsYar — جزوهٔ مادر آناتومی حواس ویژه — جلسهٔ ۶",
    author="HumsYar",
    subject="جزوهٔ مادر آناتومی جلسهٔ ۶: آناتومی عملی — مولاژهای چشم و گوش و لام‌های بافتی",
    header_right="جزوهٔ مادر · آناتومی حواس ویژه · جلسهٔ ۶",
    header_left="HumsYar",
    footer_right="آناتومی عملی · مولاژ و لام",
    footer_left="HumsYar · جزوهٔ مادر",
)

CLUSTERS = {
    0: ("خوشهٔ ۱ — مولاژهای چشم: کره، عضلات، اشکی، عروق و اعصاب", "مباحث ۱–۷"),
    7: ("خوشهٔ ۲ — قلهٔ اوربیت، سینوس کاورنوس، اوربیت استخوانی و داخل کره", "مباحث ۸–۱۲"),
    12: ("خوشهٔ ۳ — مولاژهای گوش: لاله تا لابیرنت و حلزون", "مباحث ۱۳–۱۹"),
    19: ("خوشهٔ ۴ — لام‌های بافتی چشم و گوش + خلاصه و پیوست", "مباحث ۲۰–۲۵، خلاصه، پیوست، آزمون و چک‌لیست"),
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
    furniture.toc(k, entries, CLUSTERS, entry_step=6.0, cluster_step=6.8)
    furniture.session_opener(k, front.OPENER)
    furniture.closing_note(k, "یادداشت برنامه‌ریزی: تقسیم کار تیم روی ۲۵ مبحث")
    for group in (MABAHES_A6_A, MABAHES_A6_B, MABAHES_A6_C, MABAHES_A6_D):
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
    summary_page(k, SUMMARY_A6)
    appendix_page(k, APPENDIX_A6)
    exam_page(k, EXAM_A6)
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

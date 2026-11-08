# -*- coding: utf-8 -*-
"""استخراج شکل‌های تکمیلی از گانونگ (ویراست ۲۶) و اسنل (ویراست ۹) برای جلسهٔ ۱."""
import os
import glob
import json
import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "neuro_booklet", "assets", "figs")
os.makedirs(OUT, exist_ok=True)

GANONG = os.path.join(ROOT, "جزوه حواس ویژه", "1-400 ganong.pdf")
SNELL = glob.glob(os.path.join(ROOT, "علوم تشریح دستگاه اعصاب", "*Snell*"))[0]

TARGETS = [
    # key,                       source, page, min_px, note
    ("g05_ganong_fig7_3", "ganong", 341, 300, "Fig 7-3 fate of monoamines"),
    ("g06_ganong_fig7_2", "ganong", 337, 300, "Fig 7-2 four diffuse systems"),
    ("g07_ganong_tab7_1", "ganong", 339, 300, "Table 7-1 transmembrane signaling"),
    ("g08_ganong_fig7_4", "ganong", 343, 300, "Fig 7-4 glutamatergic synapse"),
    ("g09_ganong_fig7_5", "ganong", 345, 300, "Fig 7-5 NMDA receptor"),
    ("g10_ganong_fig7_8", "ganong", 353, 300, "Fig 7-8 nicotinic ACh receptor"),
    ("g11_ganong_fig7_10", "ganong", 362, 300, "Fig 7-10 serotonin synapse"),
    ("g12_ganong_opioid", "ganong", 368, 300, "opioid receptor table"),
    ("s01_snell_fig2_1", "snell", 91, 300, "Fig 2-1 neuron"),
    ("s02_snell_fig2_3", "snell", 93, 300, "Fig 2-3 classification by neurites"),
    ("s03_snell_fig2_28", "snell", 134, 300, "Fig 2-28 neuroglial cells"),
    ("s04_snell_fig3_12", "snell", 193, 300, "Fig 3-12 peripheral nerve"),
    ("s05_snell_fig3_15", "snell", 197, 300, "Fig 3-15 ganglion photomicrograph"),
    ("s06_snell_fig3_14", "snell", 196, 300, "Fig 3-14 sensory ganglion"),
]


def crop(doc, page_no, min_px, dpi=220, pad=1.2):
    page = doc[page_no - 1]
    infos = [i for i in page.get_image_info(xrefs=True)
             if i["width"] >= min_px and i["height"] >= min_px * 0.5]
    if not infos:
        raise RuntimeError(f"no image on page {page_no}")
    # بزرگ‌ترین تصویر بر اساس مساحت روی صفحه (نه ابعاد پیکسلی)
    info = max(infos, key=lambda i: (i["bbox"][2] - i["bbox"][0]) * (i["bbox"][3] - i["bbox"][1]))
    x0, y0, x1, y1 = info["bbox"]
    clip = pymupdf.Rect(max(x0 - pad, 0), max(y0 - pad, 0), x1 + pad, y1 + pad)
    pm = page.get_pixmap(dpi=dpi, clip=clip)
    return pm, [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)], info


def main():
    docs = {"ganong": pymupdf.open(GANONG), "snell": pymupdf.open(SNELL)}
    man = []
    for key, src, page, min_px, note in TARGETS:
        pm, rect, info = crop(docs[src], page, min_px)
        path = os.path.join(OUT, key + ".png")
        pm.save(path)
        man.append(dict(key=key, source=src, page=page, fig=note,
                        px=[pm.width, pm.height], rect=rect, src_px=[info["width"], info["height"]]))
        print(f"{key:26s} p{page:<4d} {pm.width}x{pm.height}  rect={rect}")
    with open(os.path.join(OUT, "manifest_more.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مرحله ۹ — تولید تصویر صفحه برای منابعی که متن استخراجی آن‌ها مخدوش است

این تصویرها در «پیوست» هر فصل قرار می‌گیرند تا محتوای آموزشی جزوه‌های
۱۴۰۲ (که متن آن‌ها با OCR ناقص تولید شده) از دست نرود.
خروجی: images/appendix/<SID>_pNN.jpg و work/appendix_pages.json
"""
import json
import os

import pypdfium2 as p

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "extracted")
OUT = os.path.join(ROOT, "images", "appendix")
WORK = os.path.join(ROOT, "work")
os.makedirs(OUT, exist_ok=True)

TARGETS = ["SRC-0012", "SRC-0058", "SRC-0014", "SRC-0016", "SRC-0030", "SRC-0034", "SRC-0038",
           "SRC-0042", "SRC-0048", "SRC-0050", "SRC-0052"]
MAX_WIDTH = 720


def main():
    reg = {r["source_id"]: r for r in json.load(open(os.path.join(WORK, "source_registry.json")))}
    out = {}
    for sid in TARGETS:
        rec = reg.get(sid)
        if not rec or rec["type"] != "pdf":
            continue
        doc = p.PdfDocument(os.path.join(SRC, rec["rel_path"]))
        pages = []
        for i, page in enumerate(doc):
            w = page.get_size()[0]
            scale = MAX_WIDTH / w
            img = page.render(scale=scale).to_pil().convert("RGB")
            fn = f"{sid}_p{i + 1:02d}.jpg"
            img.save(os.path.join(OUT, fn), "JPEG", quality=58, optimize=True)
            pages.append({"page": i + 1, "file": f"images/appendix/{fn}"})
        out[sid] = {"filename": rec["filename"], "rel_path": rec["rel_path"], "pages": pages}
        print(sid, len(pages), "صفحه")
    json.dump(out, open(os.path.join(WORK, "appendix_pages.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

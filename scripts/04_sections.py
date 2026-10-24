#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مرحله ۴ — قطعه‌بندی منابع به قطاع قابل‌ارجاع (section spans)

خروجی: work/sections.json
  { "SRC-0009#S03": {"source_id","title","kind","span",...,"chars"} }
هر قطعه، ارجاع پایدار برای نقشه منابع و داده‌های فصل‌ها فراهم می‌کند.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
PAGE_NOISE = re.compile(r"^[\d\s|Page/٫،.]+$|^\d+\s*\|\s*P\s*a\s*g\s*e", re.I)


def md_sections(rec):
    data = json.load(open(os.path.join(WORK, "extracted_text", rec["source_id"] + ".json")))
    blocks = data["blocks"]
    secs = []
    cur = None
    idx = 0

    def flush(cur):
        if cur and cur["blocks"]:
            secs.append(cur)

    for b in blocks:
        t = b["text"].strip()
        is_head = b["type"] == "heading" and len(t) > 4 and not PAGE_NOISE.match(t)
        if is_head:
            flush(cur)
            idx += 1
            cur = {"sec_ref": f"{rec['source_id']}#S{idx:02d}",
                   "source_id": rec["source_id"], "kind": "md_section",
                   "title": re.sub(r"^\*+|\*+$", "", t).strip(),
                   "blocks": [{"type": "subheading", "text": re.sub(r"^\*+|\*+$", "", t).strip()}]}
        else:
            if cur is None:
                idx += 1
                cur = {"sec_ref": f"{rec['source_id']}#S{idx:02d}",
                       "source_id": rec["source_id"], "kind": "md_section", "title": "مقدمه", "blocks": []}
            cur["blocks"].append(b)
    flush(cur)
    return secs


def pdf_sections(rec):
    data = json.load(open(os.path.join(WORK, "page_data", rec["source_id"] + ".json")))
    secs = []
    for pg in data["pages"]:
        txt = pg["text"].strip()
        if len(txt) < 40:
            continue
        lines = [l.strip() for l in txt.split("\n") if l.strip()]
        title = lines[1] if len(lines) > 1 and len(lines[0]) < 8 else (lines[0] if lines else "")
        secs.append({"sec_ref": f"{rec['source_id']}#P{pg['page_number']:02d}",
                     "source_id": rec["source_id"], "kind": "pdf_page",
                     "title": title[:80], "page": pg["page_number"],
                     "blocks": [{"type": "paragraph", "text": txt}]})
    return secs


def main():
    reg = json.load(open(os.path.join(WORK, "source_registry.json")))
    out = {}
    for rec in reg:
        if "Guyton" in rec["rel_path"]:
            continue
        secs = md_sections(rec) if rec["type"] == "md" else pdf_sections(rec)
        for s in secs:
            chars = sum(len(b.get("text", "")) for b in s["blocks"])
            s["chars"] = chars
            if chars >= 30:
                out[s["sec_ref"]] = s
    json.dump(out, open(os.path.join(WORK, "sections.json"), "w"), ensure_ascii=False)
    print(len(out), "قطعه")
    per = {}
    for k, v in out.items():
        per.setdefault(v["source_id"], []).append(k)
    for sid in sorted(per):
        print(sid, len(per[sid]))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مرحله ۵ — بازچینش متن (reflow) و شناسه‌گذاری پاراگراف‌ها

خروجی: work/flows/<SRC>.json
  {"source_id","paragraphs":[{"p":0,"page":3|None,"text":"..."}],"chars":n}

- Markdown: سطرهای شکسته به پاراگراف تبدیل می‌شوند و نشانگرهای صفحه
  («۳ | Page») برای انتساب شماره صفحه ردیابی می‌شوند.
- PDF: متن هر صفحه به پاراگراف‌ها شکسته می‌شود و صفحه‌اش ثبت می‌گردد.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
OUT = os.path.join(WORK, "flows")
os.makedirs(OUT, exist_ok=True)

PAGE_MARK = re.compile(r"^[\s|]*(\d{1,3})\s*[|\\/]\s*P\s*[aا]\s*g\s*e\.?[\s|]*$", re.I)
ONLY_NUM = re.compile(r"^\s*(\d{1,3})\s*$")
SENT_END = re.compile(r"[.؟!؛:]\s*$")


def reflow(lines):
    """lines: [(text, page_or_None)] → paragraphs با حفظ شماره صفحه اولین سطر"""
    paras, buf, buf_page = [], [], None

    def push():
        nonlocal buf, buf_page
        txt = " ".join(buf).strip()
        txt = re.sub(r"\s+", " ", txt)
        if len(txt) >= 25:
            paras.append({"page": buf_page, "text": txt})
        buf, buf_page = [], None

    for txt, page in lines:
        t = txt.strip()
        if not t:
            if buf:
                push()
            continue
        if t.startswith("\x01"):  # عنوان واقعی: پاراگراف مستقل
            if buf:
                push()
            paras.append({"page": page, "text": t[1:].strip(), "heading": True})
            continue
        if buf_page is None:
            buf_page = page
        # جمله‌های پایان‌یافته را به پاراگراف تبدیل کن، مگر سطر ادامه‌دار کوتاه
        buf.append(t)
        joined = " ".join(buf)
        if SENT_END.search(t) and len(joined) > 220:
            push()
    if buf:
        push()
    # شکستن پاراگراف‌های بسیار بلند روی مرز جمله
    out = []
    for p in paras:
        t = p["text"]
        if len(t) <= 900:
            out.append(p)
            continue
        chunks = re.split(r"(?<=[.؟!])\s+", t)
        cur = ""
        for c in chunks:
            if len(cur) + len(c) > 800 and cur:
                out.append({"page": p["page"], "text": cur.strip()})
                cur = c
            else:
                cur += (" " if cur else "") + c
        if cur.strip():
            out.append({"page": p["page"], "text": cur.strip()})
    for i, p in enumerate(out):
        p["p"] = i
    return out


def md_flow(rec):
    data = json.load(open(os.path.join(WORK, "extracted_text", rec["source_id"] + ".json")))
    lines, page = [], None
    for b in data["blocks"]:
        t = b["text"].strip()
        t = t.replace("**", "").strip()
        m = PAGE_MARK.match(t)
        if m:
            page = int(m.group(1))
            continue
        if ONLY_NUM.match(t) and len(t) < 5:
            continue
        if b["type"] == "heading" and b.get("level") == 1 and len(t) > 8:
            lines.append(("\x01" + t, page))
            continue
        lines.append((t, page))
    return reflow(lines)


def pdf_flow(rec):
    data = json.load(open(os.path.join(WORK, "page_data", rec["source_id"] + ".json")))
    lines = []
    for pg in data["pages"]:
        first = True
        for raw in pg["text"].split("\n"):
            t = raw.strip()
            if not t:
                continue
            if first and ONLY_NUM.match(t):
                first = False
                continue
            first = False
            lines.append((t, pg["page_number"]))
    return reflow(lines)


def main():
    reg = json.load(open(os.path.join(WORK, "source_registry.json")))
    summary = []
    for rec in reg:
        if "Guyton" in rec["rel_path"]:
            continue
        paras = md_flow(rec) if rec["type"] == "md" else pdf_flow(rec)
        json.dump({"source_id": rec["source_id"], "rel_path": rec["rel_path"],
                   "paragraphs": paras, "chars": sum(len(p["text"]) for p in paras)},
                  open(os.path.join(OUT, rec["source_id"] + ".json"), "w"), ensure_ascii=False)
        summary.append((rec["source_id"], len(paras), sum(len(p["text"]) for p in paras)))
    for s in summary:
        print(f"{s[0]} paras={s[1]:5d} chars={s[2]:7d}")
    print("total chars", sum(s[2] for s in summary))


if __name__ == "__main__":
    main()

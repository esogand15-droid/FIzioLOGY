#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مرحله ۷ — تطبیق پاراگراف‌های Markdown با صفحات PDF (برای شماره صفحه)

برای هر جفت (md, pdf) که محتوای یکسانی دارند، با SequenceMatcher روی
واژه‌ها، هر پاراگراف MD به صفحه PDF متناظر نسبت داده می‌شود.
خروجی: work/pages_map.json  {sid_md: {"pdf_sid": sid, "pages":[..], "match":0.0-1.0}}
"""
import difflib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
WORD = re.compile(r"[\w\u0600-\u06FF\u200c]+")

# جفت‌های md ↔ pdf هم‌محتوا (شناسه منبع)
PAIRS = [
    ("SRC-0009", "SRC-0010"), ("SRC-0027", "SRC-0028"), ("SRC-0031", "SRC-0032"),
    ("SRC-0035", "SRC-0036"), ("SRC-0039", "SRC-0040"), ("SRC-0043", "SRC-0044"),
    ("SRC-0045", "SRC-0046"), ("SRC-0023", "SRC-0024"), ("SRC-0025", "SRC-0026"),
    ("SRC-0013", "SRC-0014"), ("SRC-0015", "SRC-0016"), ("SRC-0017", "SRC-0018"),
    ("SRC-0019", "SRC-0020"), ("SRC-0029", "SRC-0030"), ("SRC-0033", "SRC-0034"),
    ("SRC-0037", "SRC-0038"), ("SRC-0041", "SRC-0042"), ("SRC-0047", "SRC-0048"),
    ("SRC-0049", "SRC-0050"), ("SRC-0051", "SRC-0052"), ("SRC-0057", "SRC-0058"),
]


def words_of(paras):
    out, owner = [], []
    for i, p in enumerate(paras):
        for w in WORD.findall(p["text"]):
            out.append(w)
            owner.append(i)
    return out, owner


def main():
    res = {}
    for md, pdf in PAIRS:
        mp = os.path.join(WORK, "flows_norm", md + ".json")
        pp = os.path.join(WORK, "flows_norm", pdf + ".json")
        if not (os.path.exists(mp) and os.path.exists(pp)):
            continue
        m = json.load(open(mp))["paragraphs"]
        q = json.load(open(pp))["paragraphs"]
        mw, mown = words_of(m)
        qw, qown = words_of(q)
        if not mw or not qw:
            continue
        sm = difflib.SequenceMatcher(None, mw, qw, autojunk=False)
        pages = [None] * len(m)
        for a, b, size in sm.get_matching_blocks():
            for k in range(size):
                pi = mown[a + k]
                pages[pi] = q[qown[b + k]]["page"]
        # پر کردن خانه‌های خالی با نزدیک‌ترین مقدار معتبر
        last = None
        for i in range(len(pages)):
            if pages[i] is None:
                pages[i] = last
            else:
                last = pages[i]
        last = None
        for i in range(len(pages) - 1, -1, -1):
            if pages[i] is None:
                pages[i] = last
            else:
                last = pages[i]
        ratio = sm.ratio()
        res[md] = {"pdf_sid": pdf, "pages": [p or 1 for p in pages], "match": round(ratio, 3),
                   "paragraphs": len(m)}
        print(md, "→", pdf, f"match={ratio:.2f}", f"paras={len(m)}")
    json.dump(res, open(os.path.join(WORK, "pages_map.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

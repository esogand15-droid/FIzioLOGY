#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مرحله ۲ — استخراج متن و تصاویر از تمام فایل‌های منبع

خروجی‌ها:
  work/source_registry.json        فهرست منابع با شناسه یکتا و فرا‌داده
  work/page_data/<SRC>.json        متن صفحه‌به‌صفحه PDFها + محور تصاویر
  work/extracted_text/<SRC>.json   بلوک‌های متن MD
  images/extracted/*               تصاویر خام استخراج‌شده از PDF
  images/INDEX.json                نمایه تصاویر
  work/checkpoints/step2_extract.json
"""
import hashlib
import json
import os
import re
import sys

import pypdfium2 as p
import pypdfium2.raw as raw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "extracted")
WORK = os.path.join(ROOT, "work")
IMGDIR = os.path.join(ROOT, "images", "extracted")
for d in (WORK, os.path.join(WORK, "page_data"), os.path.join(WORK, "extracted_text"),
          IMGDIR, os.path.join(WORK, "checkpoints")):
    os.makedirs(d, exist_ok=True)

PERSIAN = re.compile(r"[\u0600-\u06FF\u200c]")
COMMON = set("""از که در به این است را با برای سیستم سلول عصب مغز می شود نیست دارد اثر عمل
های ها یک آن خود بر تا هم نیز بود شد کند کنند دهد وجود دارد دارد بین شود شود.""".split())


def strip_nullsp(t):
    return t.replace("\x00", " ").replace("\r", "\n")


def quality(text):
    """سنجه ساده سلامت متن فارسی: نسبت واژه‌های پرتکرار + میانگین طول واژه + نرخ تکرار حروف."""
    words = re.findall(r"[\u0600-\u06FF\u200c]+", text)
    if not words:
        return {"n_words": 0, "common_ratio": 0.0, "avg_len": 0.0,
                "repeat_ratio": 0.0, "score": 0.0, "verdict": "خالی/غیرفارسی"}
    hits = sum(1 for w in words if w in COMMON)
    repeat = len(re.findall(r"([\u0600-\u06FF])\1{2,}", text))
    avg = sum(len(w) for w in words) / len(words)
    ratio = hits / len(words)
    score = ratio * 100 + min(avg, 5) * 2 - min(repeat / max(1, len(words)) * 100, 10)
    if ratio >= 0.10 and avg >= 3.2:
        verdict = "قابل استفاده"
    elif ratio >= 0.05:
        verdict = "نیمه‌مخدوش"
    else:
        verdict = "مخدوش/نیازمند OCR دستی"
    return {"n_words": len(words), "common_ratio": round(ratio, 4),
            "avg_len": round(avg, 2), "repeat_ratio": round(repeat / len(words), 4),
            "score": round(score, 2), "verdict": verdict}


HEAD_RE = re.compile(r"^\s*(?:#{1,6}\s+|(\*\*)?[^\n]{2,80}$)")


def md_blocks(path):
    """تبدیل Markdown به بلوک‌های ساختاریافته با حفظ متن اصلی."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    txt = strip_nullsp(txt)
    # حذف بلوک‌های تصویر-متنی که در تبدیل PDF به MD ساخته شده‌اند (متادیتا، نه محتوا)
    pic_blocks = re.findall(r"<!-- Start of picture text -->(.*?)<!-- End of picture text -->", txt, re.S)
    txt = re.sub(r"<!-- Start of picture text -->.*?<!-- End of picture text -->", "", txt, flags=re.S)
    blocks = []
    for line in txt.split("\n"):
        s = line.strip()
        if not s:
            continue
        if re.match(r"^#{1,6}\s", s):
            blocks.append({"type": "heading", "level": len(re.match(r"^(#+)", s).group(1)),
                           "text": re.sub(r"^#{1,6}\s*", "", s).strip()})
        elif re.match(r"^([-*•]|\d+[\.\)])\s", s):
            blocks.append({"type": "list_item", "text": re.sub(r"^([-*•]|\d+[\.\)])\s*", "", s).strip()})
        elif re.match(r"^(\|.*\|)\s*$", s):
            blocks.append({"type": "md_row", "text": s})
        else:
            blocks.append({"type": "paragraph", "text": s})
    # ادغام سطرهای مدیا و پاراگراف‌های پشت‌سرهم
    out = []
    for b in blocks:
        if out and b["type"] == "paragraph" and out[-1]["type"] == "paragraph" \
                and len(out[-1]["text"]) < 90 and not out[-1]["text"].endswith((".", "؛", ":", "؟")):
            out[-1]["text"] = out[-1]["text"].rstrip() + " " + b["text"]
        else:
            out.append(b)
    return out, pic_blocks, txt


def pdf_pages(path):
    doc = p.PdfDocument(path)
    pages = []
    for i, page in enumerate(doc):
        tp = page.get_textpage()
        txt = strip_nullsp(tp.get_text_range())
        imgs = []
        for obj in page.get_objects(filter=(raw.FPDF_PAGEOBJ_IMAGE,)):
            try:
                l, b, r, t = obj.get_bounds()
                w, h = page.get_size()
                if r - l < 8 or t - b < 8:
                    continue
                imgs.append({"bbox": [round(l, 1), round(b, 1), round(r, 1), round(t, 1)],
                             "area_ratio": round(((r - l) * (t - b)) / max(1.0, w * h), 4),
                             "px": list(obj.get_px_size())})
            except Exception:  # noqa: BLE001
                continue
        pages.append({"page_number": i + 1, "text": txt, "images": imgs,
                      "width": page.get_size()[0], "height": page.get_size()[1]})
    return pages


def main():
    reg = []
    idx = 0
    for dirpath, _dn, fns in os.walk(SRC):
        for fn in sorted(fns):
            ext = os.path.splitext(fn)[1].lower()
            if ext not in (".pdf", ".md"):
                continue
            idx += 1
            path = os.path.join(dirpath, fn)
            sid = f"SRC-{idx:04d}"
            rel = os.path.relpath(path, SRC)
            rec = {"source_id": sid, "rel_path": rel, "filename": fn,
                   "type": ext.lstrip("."), "size": os.path.getsize(path),
                   "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}
            if ext == ".pdf":
                pages = pdf_pages(path)
                rec["pages"] = len(pages)
                text_all = "\n".join(pg["text"] for pg in pages)
                rec["n_figures"] = sum(len(pg["images"]) for pg in pages)
                json.dump({"source_id": sid, "filename": fn, "pages": pages},
                          open(os.path.join(WORK, "page_data", sid + ".json"), "w"),
                          ensure_ascii=False)
            else:
                blocks, pic_blocks, text_all = md_blocks(path)
                rec["blocks"] = len(blocks)
                rec["n_figures"] = 0
                json.dump({"source_id": sid, "filename": fn, "blocks": blocks,
                           "picture_text_metadata": pic_blocks},
                          open(os.path.join(WORK, "extracted_text", sid + ".json"), "w"),
                          ensure_ascii=False)
            rec["quality"] = quality(text_all)
            reg.append(rec)
            print(f"{sid} {rec['type']:3s} p/blk={rec.get('pages', rec.get('blocks')):4d} "
                  f"figs={rec['n_figures']:3d} q={rec['quality']['common_ratio']:.3f} "
                  f"{rec['quality']['verdict']:22s} {rel}")
    json.dump(reg, open(os.path.join(WORK, "source_registry.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"step": 2, "sources": len(reg),
               "verdicts": {v: sum(1 for r in reg if r["quality"]["verdict"] == v)
                            for v in set(r["quality"]["verdict"] for r in reg)}},
              open(os.path.join(WORK, "checkpoints", "step2_extract.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

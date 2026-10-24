#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مرحله ۹ب — نمایه‌گذاری نسخه متنی گایتون (انگلیسی)

فایل PDF گایتون در مخزن Git LFS است و در این اجرا دریافت نشد، اما نسخه Markdown
کامل کتاب موجود است. این اسکریپت از آن استفاده می‌کند تا:
  ۱) فهرست فصل‌ها و صفحه چاپی هر فصل را استخراج کند؛
  ۲) برای هر مفهوم درس (شنوایی، بینایی، تعادل، درد، ...) فصل‌های مرتبط گایتون را
     با شمارش کلیدواژه مشخص کند؛
  ۳) شماره صفحه چاپی اولین فصل مرتبط را ثبت کند (شماره صفحه چاپی، نه صفحه PDF).

خروجی: work/guyton_index.json و inventory/GUYTON_INDEX.md
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
INV = os.path.join(ROOT, "inventory")
SRC = os.path.join(ROOT, "src", "extracted", "رفرنس گایتون",
                   "Guyton and Hall Textbook of Medical Physiology English.md")

# concepts: (نام فارسی مبحث, [کلیدواژه‌های انگلیسی])
CONCEPTS = [
    ("سازمان سیستم عصبی و سیناپس", ["synapse", "neurotransmitter", "action potential", "synaptic cleft"]),
    ("گیرنده‌های حسی و مسیرهای صعودی", ["sensory receptor", "dorsal column", "spinothalamic", "dermatome"]),
    ("درد و کنترل درد", ["pain", "nociceptor", "referred pain", "analgesia"]),
    ("بینایی", ["retina", "rod", "cone", "rhodopsin", "visual cortex", "photoreceptor"]),
    ("شنوایی", ["cochlea", "organ of Corti", "hair cell", "tympanic", "auditory"]),
    ("تعادل و سیستم دهلیزی", ["semicircular", "utricle", "saccule", "vestibular", "otolith"]),
    ("چشایی و بویایی", ["taste", "olfactory", "smell", "gustatory"]),
    ("نخاع و رفلکس‌ها", ["spinal cord", "stretch reflex", "muscle spindle", "Golgi tendon"]),
    ("حرکت و قشر حرکتی", ["motor cortex", "corticospinal", "pyramidal", "reticulospinal"]),
    ("مخچه", ["cerebellum", "Purkinje", "ataxia", "cerebellar"]),
    ("عقده‌های قاعده‌ای", ["basal ganglia", "substantia nigra", "Parkinson", "putamen"]),
    ("حافظه و یادگیری", ["memory", "hippocampus", "long-term potentiation", "learning"]),
    ("لیمبیک و هیجان", ["limbic", "amygdala", "hypothalamus", "emotion"]),
    ("EEG، خواب و صرع", ["electroencephalogram", "sleep", "epilepsy", "seizure", "REM"]),
    ("سیستم اتونوم", ["autonomic", "sympathetic", "parasympathetic", "acetylcholine"]),
    ("اعمال برتر مغز و تکلم", ["Wernicke", "Broca", "cerebral dominance", "speech"]),
]


def main():
    txt = open(SRC, encoding="utf-8", errors="replace").read()

    # ۱) فهرست فصل‌ها از بخش TOC نسخه متنی
    chapters = []
    toc_matches = list(re.finditer(r"CHAPTER\s+(\d{1,2})\s*\n", txt[:260000]))
    for i, m in enumerate(toc_matches):
        num = int(m.group(1))
        end = toc_matches[i + 1].start() if i + 1 < len(toc_matches) else m.start() + 800
        block_lines = [ln.replace("```", "").strip() for ln in txt[m.end():end].split("\n")]
        block_lines = [ln for ln in block_lines if ln]
        title_parts, page = [], None
        for ln in block_lines:
            pm = re.match(r"^(.*?)\s*(\d{1,4})$", ln)
            if pm and pm.group(1).strip():
                title_parts.append(pm.group(1).strip(" ."))
                page = int(pm.group(2))
                break
            if re.match(r"^(Contents|xvi|UNIT|CHAPTER)", ln):
                break
            title_parts.append(ln)
        title = re.sub(r"\s+", " ", " ".join(title_parts)).strip(" .")
        if page and title and num <= 62 and not any(c["num"] == num for c in chapters):
            chapters.append({"num": num, "title": title[:110], "printed_page": page})
    chapters.sort(key=lambda c: c["num"])

    # ۲) مرز فصل‌ها در متن اصلی (سرتیترهای «chapter NN» در بدنه)
    marks = []
    for m in re.finditer(r"(?m)^chapter\s+(\d{1,2})\s*$", txt):
        num = int(m.group(1))
        if not marks or marks[-1][0] != num:
            marks.append((num, m.start()))
    bounds = {}
    for i, (num, pos) in enumerate(marks):
        nxt = len(txt)
        for num2, pos2 in marks[i + 1:]:
            if num2 > num:
                nxt = pos2
                break
        bounds.setdefault(num, (pos, nxt))

    lower = txt.lower()
    concepts = []
    for name, kws in CONCEPTS:
        hits = []
        for ch in chapters:
            seg = bounds.get(ch["num"])
            if not seg:
                continue
            body = lower[seg[0]:seg[1]]
            score = sum(body.count(k.lower()) for k in kws)
            if score >= 8:
                hits.append({"chapter": ch["num"], "title": ch["title"],
                             "printed_page": ch["printed_page"], "hits": score})
        hits.sort(key=lambda h: -h["hits"])
        total = sum(lower.count(k.lower()) for k in kws)
        concepts.append({"concept_fa": name, "keywords": kws, "total_hits": total,
                         "chapters": hits[:4]})

    out = {"source_file": os.path.basename(SRC), "edition": "Twelfth Edition (2011)",
           "note": "شماره صفحه‌ها چاپی است (بر اساس فهرست کتاب)؛ PDF گایتون به‌دلیل Git LFS "
                   "در این اجرا دریافت نشد.",
           "chapters": chapters, "concepts": concepts}
    json.dump(out, open(os.path.join(WORK, "guyton_index.json"), "w"), ensure_ascii=False, indent=1)

    lines = ["# نمایه تطبیق موضوعی با گایتون (نسخه انگلیسی، ویرایش دوازدهم)", "",
             "نسخه PDF گایتون در مخزن، Git LFS است و در این اجرا دریافت نشد؛ این نمایه از "
             "نسخه متنی کامل کتاب ساخته شده است. شماره صفحه‌ها چاپی هستند.", "",
             "| مبحث درس | فصل‌های مرتبط گایتون (صفحه چاپی) | تعداد کلیدواژه در کل کتاب |",
             "|---|---|---|"]
    for c in concepts:
        chs = "، ".join(f"فصل {h['chapter']} ({h['printed_page']})" for h in c["chapters"]) or "—"
        lines.append(f"| {c['concept_fa']} | {chs} | {c['total_hits']:,} |")
    lines += ["", "## فهرست فصل‌های مرتبط با نوروفیزیولوژی و حواس ویژه", "",
              "| فصل | عنوان | صفحه چاپی |", "|---|---|---|"]
    for ch in chapters:
        if 44 <= ch["num"] <= 63:
            lines.append(f"| {ch['num']} | {ch['title']} | {ch['printed_page']} |")
    open(os.path.join(INV, "GUYTON_INDEX.md"), "w").write("\n".join(lines))
    print(f"{len(chapters)} فصل، {len(concepts)} مفهوم → work/guyton_index.json")


if __name__ == "__main__":
    main()

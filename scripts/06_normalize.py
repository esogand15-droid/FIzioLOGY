#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مرحله ۶ — نرمال‌سازی محافظه‌کارانه متن (اصلاح خطاهای رایج استخراج)

قواعد فقط روی منابعی اعمال می‌شوند که سنجه سلامت آن‌ها ≥ 0.13 باشد؛ متن‌های
مخدوش (جزوه‌های OCR-شده ۱۴۰۲) دست‌نخورده می‌مانند و به‌جای آن‌ها تصویر
صفحه‌ها ارائه می‌شود.

هر جایگزینی در work/normalization_log.json ثبت می‌شود (قابل‌ردیابی).
خروجی: work/flows_norm/<SRC>.json
"""
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
OUT = os.path.join(WORK, "flows_norm")
os.makedirs(OUT, exist_ok=True)

# قاعده‌های عمومی (فقط الگوهای قطعی)
GENERIC = [
    (r"اطالع", "اطلاع"),
    (r"الً", "لاً"),                 # مثالً → مثلاً ، کامالً → کاملاً
    (r"\bباال", "بالا"),              # باال، باالتر، باالیی
    (r"\bالیه", "لایه"),
    (r"\bعضالت", "عضلات"),
    (r"\bعضالنی", "عضلانی"),
    (r"\bاختالالش\b", "اختلالش"),
    (r"\bاختالل", "اختلال"),
    (r"\bاختالف", "اختلاف"),
    (r"\bتاالموس", "تالاموس"),
    (r"\bهیپوتاالموس", "هیپوتالاموس"),
    (r"\bیپوتاالموس", "هیپوتالاموس"),
    (r"اسپاینوتاالمیک", "اسپاینوتالامیک"),
    (r"\bحاال", "حالا"),
    (r"\bطوالنی", "طولانی"),
    (r"\bعالوه", "علاوه"),
    (r"\bعالئم", "علائم"),
    (r"\bعالمت", "علامت"),
    (r"\bتشکیالت", "تشکیلات"),
    (r"\bدپوالریز", "دپلاریز"),
    (r"\bهایپرپوالریز", "هایپرپلاریز"),
    (r"\bکالم", "کلام"),
    (r"\bمعموال", "معمولا"),
    (r"\bقبالً", "قبلاً"),
    (r"\bاصطالح", "اصطلاح"),
    (r"\bسالمت", "سلامت"),
    (r"\bمولکوالر", "مولکولار"),
    (r"\bگالیسین", "گلیسین"),
    (r"\bمالنین", "ملانین"),
    (r"\bآمیصدال", "آمیگدال"),
    (r"\bپروستاگالندین", "پروستاگلاندین"),
    (r"\bکالسیک", "کلاسیک"),
    (r"\bکالس\b", "کلاس"),
    (r"\bسئوال", "سؤال"),
    (r"\bژالتینی", "ژلاتینی"),
    (r"\bزیرالیه", "زیرلایه"),
    (r"\bسیصنال", "سیگنال"),
    (r"\bبالک\b", "بلوک"),
    (r"\bالکتروتونیک", "الکتروتونیک"),
    (r"\)([^(){}\[\]]{1,80})\(", r"(\1)"),
    (r"\(\s+([^()]{1,70}?)\s+\)", r"(\1)"),
    # جاافتادگی/جابه‌جایی نقطه در متن استخراج‌شده
    (r"\b(می)\s+\.\s*(شود|شوند|کند|کنند|دهد|گیرد|یابد|رسد|رود|ماند|بینیم|شه|دن)\b", r"\1‌\2."),
    (r"\b(نمی)\s+\.\s*(شود|شوند|کند|کنند|دهد|گیرد)\b", r"\1‌\2."),
    (r"\s+\.", "."),
    (r"\s+،", "،"),
    (r"\.\.\.+", "…"),
    (r"([،؛])\1+", r"\1"),
    (r"\s{2,}", " "),
    # نشانگرهای صفحه که در متن PDF/MD ادغام شده‌اند
    (r"\s*\b\d{0,3}\s*\|\s*P\s*a\s*g\s*e\.?\b\s*", " "),
    (r"\bP\s*a\s*g\s*e\s*\d{1,3}\b", " "),
]

GENERIC_RE = [(re.compile(p), r) for p, r in GENERIC]


def normalize(text):
    """بازگشت (متن نرمال‌شده، شمارش جایگزینی‌ها)"""
    hits = Counter()
    t = text
    for rx, rep in GENERIC_RE:
        def _sub(m, rep=rep, rx=rx):
            hits[rx.pattern] += 1
            return m.expand(rep)
        t = rx.sub(_sub, t)
    return t, hits


def main():
    reg = json.load(open(os.path.join(WORK, "source_registry.json")))
    log = {}
    for rec in reg:
        sid = rec["source_id"]
        path = os.path.join(WORK, "flows", sid + ".json")
        if not os.path.exists(path):
            continue
        data = json.load(open(path))
        clean = rec["quality"]["common_ratio"] >= 0.13 and "Guyton" not in rec["rel_path"]
        total = Counter()
        if clean:
            for p in data["paragraphs"]:
                p["text"], hits = normalize(p["text"])
                total.update(hits)
                if "text_raw" not in p:
                    p["text_raw"] = None
            log[sid] = {"normalized": True, "changes": {k: v for k, v in total.items() if v}}
        else:
            log[sid] = {"normalized": False,
                        "reason": "سنجه سلامت متن پایین؛ اجتناب از اصلاح حدسی (تصویر صفحه ارائه می‌شود)"}
        data["normalized"] = clean
        json.dump(data, open(os.path.join(OUT, sid + ".json"), "w"), ensure_ascii=False)
    json.dump(log, open(os.path.join(WORK, "normalization_log.json"), "w"),
              ensure_ascii=False, indent=1)
    n = sum(sum(v.get("changes", {}).values()) for v in log.values())
    print(f"{sum(1 for v in log.values() if v['normalized'])} منبع نرمال‌سازی شد؛ {n} اصلاح")


if __name__ == "__main__":
    main()

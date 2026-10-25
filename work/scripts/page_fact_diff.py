#!/usr/bin/env python3
"""FINAL AUDIT — page-level fact diff.

For every source page that the coverage matrix marks as *uncited* (and, on
demand, for any page range), this tool extracts the page's **checkable facts** —
Latin terms, numbers/percentages, and drug/proper names — and looks for each of
them inside the delivered session document.

Why this is a stronger test than "I read the page": the delivered documents are
Persian, so a page can be covered in substance while sharing almost no wording
with the source.  A missing *number*, *drug name* or *English term* is a much
better signal of a real gap than a text similarity score.

Numbers are matched after normalising Persian/Arabic digits; Latin terms are
matched case-insensitively.

Output: work/audit/fact_diff.json  +  a printed summary.

Run:  python work/scripts/page_fact_diff.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "فیزیولوژی اعصاب حواس ویژه"
SESS = REPO / "content" / "sessions"
OUT = REPO / "work" / "audit" / "fact_diff.json"

FA = "۰۱۲۳۴۵۶۷۸۹"
AR = "٠١٢٣٤٥٦٧٨٩"


def norm(text: str) -> str:
    out = []
    for ch in text:
        if ch in FA:
            out.append(str(FA.index(ch)))
        elif ch in AR:
            out.append(str(AR.index(ch)))
        elif ch in "\u200c\u200f\u202b\u202c":
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def doc_text(session: str) -> str:
    chunks: list[str] = []
    for path in sorted(SESS.glob(f"{session}_*.json")):
        raw = path.read_text(encoding="utf-8")

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str) and k in {
                            "text", "title", "fa", "note", "footer", "kicker",
                            "label", "caption", "sub", "detail"}:
                        chunks.append(v)
                    elif isinstance(v, (dict, list)):
                        walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    if isinstance(v, str):
                        chunks.append(v)
                    else:
                        walk(v)
        walk(json.loads(raw))
    return norm(" ".join(chunks))


NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:[.,]\d+)?)(?![\w])")
LAT = re.compile(r"[A-Za-z][A-Za-z\-]{2,}")


def facts(page_text: str) -> tuple[list[str], list[str]]:
    nums = sorted({m.group(1) for m in NUM.finditer(norm(page_text))})
    lats = sorted({m.group(0).lower() for m in LAT.finditer(page_text)})
    return nums, lats


# source id → (path, session, pages to test)
PLAN = [
    ("s01-1402", "جلسه 1/نوروفیزیولوژی 01 نهایی بهمن 1402.pdf", "s01", [9, 10, 11]),
    ("s02-1402", "جلسه 2/نوروفیزیولوژی 02 نهایی بهمن 1402.pdf", "s02", [17]),
    ("s03-1402", "جلسه 3/نوروفیزیولوژی 03 نهایی بهمن 1402.pdf", "s03", [10, 11]),
    ("s01-1404", "جلسه 1/جلسه 1 نوروفیزیولوژی مهر 1404.pdf", "s01", [31]),
    ("s04-1402", "جلسه 4/نوروفیزیولوژی 04 نهایی بهمن 1402.pdf", "s04",
     [4, 5, 6, 7, 8, 11, 12, 14, 15, 16]),
    ("s05-1402", "جلسه 5/نوروفیزیولوژی 05 نهایی بهمن 1402.pdf", "s04",
     [4, 5, 6, 7, 8, 11, 12]),
    ("s07-p2", "جلسه 7/جزوه جلسه 8 پارت 2 بهمن 1402.pdf", "s07", [4, 19]),
    ("s09-bg", "تکمیلی - جزوات دکتر قدیری/فیزیولوژی - جلسه دوم دکتر قدیری.pdf", "s09", [10]),
    ("supp-eravan-motor", "تکمیلی - جزوات دکتر قدیری/فیزیولوژی_جلسه_دوم_دکتر_ایروان_پور.pdf",
     "s07", [4, 20, 23]),
]


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    report = []
    for sid, rel, session, pages in PLAN:
        path = SRC / rel
        if not path.exists():
            report.append(dict(source=sid, page=None, error="missing"))
            continue
        have = doc_text(session)
        with pymupdf.open(path) as doc:
            for p in pages:
                if p > len(doc):
                    continue
                text = doc[p - 1].get_text()
                nums, lats = facts(text)
                miss_n = [n for n in nums if n not in have]
                miss_l = [t for t in lats if t not in have.lower()]
                report.append(dict(source=sid, page=p, chars=len(text.strip()),
                                   numbers_total=len(nums), numbers_missing=miss_n,
                                   latin_total=len(lats), latin_missing=miss_l))
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for row in report:
        if row.get("error"):
            print(f"{row['source']}: {row['error']}")
            continue
        print(f"{row['source']:18s} p{row['page']:<3d} chars={row['chars']:<5d} "
              f"missing numbers={row['numbers_missing'][:8]} "
              f"| missing latin={row['latin_missing'][:8]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

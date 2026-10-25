#!/usr/bin/env python3
"""FINAL AUDIT — source-coverage engine.

Builds a page-level coverage matrix between every source PDF in the repository
and the delivered session documents.

How coverage is measured
------------------------
Every teaching block in ``content/sessions/sNN_*.json`` carries a ``src`` string
that names its source and page(s), e.g. ``«جزوهٔ مهر ۱۴۰۴، ص ۱۲–۱۳»``.  This
script parses those strings, resolves each one to a *specific* source file (the
mapping is explicit below, per session, because the same label — «جزوهٔ بهمن
۱۴۰۲» — means a different file in different session folders), and then reports,
for every page of every source:

    cited      → at least one block in the delivered document points at it
    uncited    → no block points at it  (must be adjudicated one by one)

Outputs
-------
``work/audit/coverage.json``      machine table
``reports/SOURCE_COVERAGE.md``    human table (per source + page lists)

Run:  python work/scripts/final_audit.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "فیزیولوژی اعصاب حواس ویژه"
SESS = REPO / "content" / "sessions"
OUT_DIR = REPO / "work" / "audit"
OUT_MD = REPO / "reports" / "SOURCE_COVERAGE.md"

FA = "۰۱۲۳۴۵۶۷۸۹"


def fa2int(text: str) -> int:
    return int("".join(str(FA.index(c)) if c in FA else c for c in text))


def pages(text: str) -> list[int]:
    """All page numbers mentioned right after a «ص» marker."""
    out: list[int] = []
    for chunk in re.findall(r"ص(?:ص|فحه)?\s*([۰-۹0-9][۰-۹0-9\s،,و–\-]*)", text):
        chunk = chunk.split("·")[0]
        nums = re.findall(r"[۰-۹0-9]+", chunk)
        # drop year-like tokens
        nums = [n for n in nums if len(n) <= 2]
        for i, n in enumerate(nums):
            try:
                v = fa2int(n)
            except ValueError:
                continue
            out.append(v)
    return sorted({p for p in out if 1 <= p <= 400})


# ---------------------------------------------------------------- source list
def page_count(path: Path) -> int:
    with pymupdf.open(path) as doc:
        return len(doc)


SOURCES = [
    # id, path, session(s), regex that identifies the label, note
    ("s01-1404", SRC / "جلسه 1/جلسه 1 نوروفیزیولوژی مهر 1404.pdf", ["s01"], r"مهر\s*۱۴۰۴", ""),
    ("s01-1402", SRC / "جلسه 1/نوروفیزیولوژی 01 نهایی بهمن 1402.pdf", ["s01"], r"بهمن\s*۱۴۰۲", ""),
    ("s02-1404", SRC / "جلسه 2/جلسه ۲ نوروفیزیولوژی مهر 1404.pdf", ["s02"], r"مهر\s*۱۴۰۴", ""),
    ("s02-1402", SRC / "جلسه 2/نوروفیزیولوژی 02 نهایی بهمن 1402.pdf", ["s02"], r"بهمن\s*۱۴۰۲", ""),
    ("s03-1404", SRC / "جلسه 3/3 نوروفیزیولوژی مهر1404.pdf", ["s03"], r"مهر\s*۱۴۰۴", ""),
    ("s03-1402", SRC / "جلسه 3/نوروفیزیولوژی 03 نهایی بهمن 1402.pdf", ["s03"], r"بهمن\s*۱۴۰۲", ""),
    ("s04-1404", SRC / "جلسه 4/جلسه ۴ نورو فیزیولوژی مهر1404.pdf", ["s04"], r"مهر\s*۱۴۰۴", ""),
    # NOTE: in s04 the label «جزوهٔ بهمن ۱۴۰۲» is used for two different files
    # (جلسهٔ ۴ = 16 ص and جلسهٔ ۵ = 13 ص).  A generic citation is therefore
    # counted for both files; the ambiguity is recorded in the audit report.
    ("s04-1402", SRC / "جلسه 4/نوروفیزیولوژی 04 نهایی بهمن 1402.pdf", ["s04"], r"بهمن\s*۱۴۰۲", ""),
    ("s05-1404", SRC / "جلسه 5/نورو۵ تالیفی مهر1404.pdf", ["s05"], r"مهر\s*۱۴۰۴", ""),
    ("s05-1402", SRC / "جلسه 5/نوروفیزیولوژی 05 نهایی بهمن 1402.pdf", ["s04", "s05"],
     r"بهمن\s*۱۴۰۲|جلسهٔ\s*۵|درد و سردرد", ""),
    ("s05-alt", SRC / "جلسه 5/فیزیو آفلاین بینایی.pdf", ["s05"], r"آفلاین\s*بینایی", "نسخهٔ موازی درس بینایی"),
    ("s06-1404", SRC / "جلسه 6/نورو فیزیولوژی جلسه ۶ مهر1404.pdf", ["s06"], r"مهر\s*۱۴۰۴", ""),
    ("s06-1402", SRC / "جلسه 6/نوروفیزیولوژی 06 نهایی بهمن 1402.pdf", ["s06"], r"بهمن\s*۱۴۰۲", ""),
    ("s07-p1", SRC / "جلسه 7/نوروفیزیولوژی_8_نهایی_پارت_1_بهمن_1402.pdf", ["s07"],
     r"پارت\s*[۱1](?!\s*و)", ""),
    ("s07-p2", SRC / "جلسه 7/جزوه جلسه 8 پارت 2 بهمن 1402.pdf", ["s07"], r"پارت\s*[۲2]", ""),
    ("s08-1402", SRC / "جلسه 9 - اعمال حرکتی ساقه مغز و کورتکس/نوروفیزیولوژی 09 نهایی بهمن 1402.pdf",
     ["s08"], r"بهمن\s*۱۴۰۲|جلسهٔ\s*۹", ""),
    ("s09-cereb", SRC / "جلسه 10 - مخچه/نوروفیزیولوژی 10 نهایی بهمن 1402.pdf", ["s09"], r"جزوهٔ\s*مخچه", ""),
    ("s09-bg", SRC / "جلسه 11 - عقده های قاعده ای/نوروفیزیولوژی 11 نهایی بهمن 1402.pdf",
     ["s09"], r"عقده", ""),
    ("s10-1402", SRC / "جلسه 12 - حافظه و یادگیری/نوروفیزیولوژی 12 نهایی بهمن 1402.pdf",
     ["s10"], r"بهمن\s*۱۴۰۲", ""),
    ("s11-1402", SRC / "جلسه 13 - لیمبیک/نوروفیزیولوژی 13و14 نهایی بهمن 1402.pdf",
     ["s11", "s12"], r"بهمن\s*۱۴۰۲|جلسهٔ\s*۱۳", ""),
    # s13 labels its only source as «جزوهٔ بهمن ۱۴۰۲» although the file is the
    # autonomic booklet; the label — not the file name — is what the docs use.
    ("s13-1402", SRC / "جلسه 15 - سیستم اتونوم/فیزیو آفلاین اتونوم.pdf", ["s13"], r"بهمن\s*۱۴۰۲", ""),
    ("s14-deck", SRC / "جلسه 16 -پری لب/جزوه پری لب نورو فیزیولوژی عملی.pdf", ["s14"],
     r"معاینات\s*نورولوژیک|پری\s*لب", ""),
    # --- supplementary booklets
    ("supp-ghadiri-last", SRC / "تکمیلی - جزوات دکتر قدیری/دکتر قدیری - جلسه آخر.pdf",
     ["s10"], r"جلسهٔ\s*آخر", ""),
    ("supp-ghadiri-cereb", SRC / "تکمیلی - جزوات دکتر قدیری/فیزیولوژی - جلسه اول دکتر قدیری.pdf",
     ["s09"], r"قدیری\s*—\s*مخچه", ""),
    ("supp-ghadiri-bg", SRC / "تکمیلی - جزوات دکتر قدیری/فیزیولوژی - جلسه دوم دکتر قدیری.pdf",
     ["s09"], r"قدیری\s*—\s*عقده", ""),
    ("supp-ghadiri-eeg", SRC / "تکمیلی - جزوات دکتر قدیری/فیزیولوژی - جلسه سوم دکتر قدیری.pdf",
     ["s12"], r"فعالیت‌های\s*مغزی|قدیری\s*—\s*EEG", ""),
    ("supp-ghadiri-limbic", SRC / "تکمیلی - جزوات دکتر قدیری/فیزیولوژی - جلسه چهارم دکتر قدیری.pdf",
     ["s11"], r"لیمبیک\s*\(مهر|قدیری\s*—\s*سیستم\s*لیمبیک", ""),
    ("supp-eravan-reflex", SRC / "تکمیلی - جزوات دکتر قدیری/فیزیولوژی_جلسه_اول_دکتر_ایروان_پور.pdf",
     ["s07"], r"ایروان‌پور\s*—\s*رفلکس", ""),
    ("supp-eravan-motor", SRC / "تکمیلی - جزوات دکتر قدیری/فیزیولوژی_جلسه_دوم_دکتر_ایروان_پور.pdf",
     ["s07"], r"ایروان‌پور\s*—\s*کنترل\s*حرکات", ""),
]


def session_srcs(session: str) -> list[str]:
    out: list[str] = []
    for path in sorted(SESS.glob(f"{session}_*.json")):
        for topic in json.loads(path.read_text(encoding="utf-8")):
            def walk(obj):
                if isinstance(obj, dict):
                    s = obj.get("src")
                    if isinstance(s, str):
                        out.append(s)
                    for v in obj.values():
                        walk(v)
                elif isinstance(obj, list):
                    for v in obj:
                        walk(v)
            walk(topic)
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    total_pages = total_cited = 0
    table = []
    for sid, path, sessions, pattern, note in SOURCES:
        if not path.exists():
            table.append(dict(id=sid, path=str(path.relative_to(REPO)), pages=None,
                              cited=[], uncited=[], note="فایل موجود نیست"))
            continue
        n = page_count(path)
        rx = re.compile(pattern)
        cited: set[int] = set()
        for sess in sessions:
            for s in session_srcs(sess):
                if rx.search(s):
                    cited.update(p for p in pages(s) if p <= n)
        # page 1 of a booklet is its cover/title page in nearly every file
        uncited = [p for p in range(1, n + 1) if p not in cited]
        total_pages += n
        total_cited += len(cited)
        table.append(dict(id=sid, path=str(path.relative_to(REPO)), pages=n,
                          cited=sorted(cited), uncited=uncited, note=note))

    (OUT_DIR / "coverage.json").write_text(
        json.dumps(table, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    lines = [
        "# ماتریس پوشش منابع (صفحه‌به‌مبحث)",
        "",
        "> تولید خودکار با `work/scripts/final_audit.py`. مبنا: رشتهٔ `src` هر بلوک",
        "> آموزشی در `content/sessions/*.json`. «پوشش» یعنی دست‌کم یک بلوک در سند",
        "> تحویل‌شده به آن صفحه ارجاع می‌دهد؛ صفحات پوشش‌داده‌نشده باید یک‌به‌یک",
        "> تعیین تکلیف شوند و در `reports/FINAL_AUDIT_ISSUES.md` ردیف دارند.",
        "",
        f"- منابع بررسی‌شده: **{len(SOURCES)} فایل** — **{total_pages} صفحه**",
        f"- صفحات دارای ارجاع (پوشش‌داده‌شده): **{total_cited}**",
        f"- صفحات بدون ارجاع: **{total_pages - total_cited}**",
        "",
        "| شناسه | فایل | ص | ارجاع‌دار | بی‌ارجاع | صفحات بی‌ارجاع | یادداشت |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in table:
        if row["pages"] is None:
            lines.append(f"| `{row['id']}` | `{row['path']}` | — | — | — | — | {row['note']} |")
            continue
        unc = row["uncited"]
        unc_txt = "، ".join(str(p) for p in unc) if unc else "—"
        if len(unc_txt) > 90:
            unc_txt = unc_txt[:87] + "…"
        lines.append(
            f"| `{row['id']}` | `{Path(row['path']).name}` | {row['pages']} | "
            f"{len(row['cited'])} | {len(unc)} | {unc_txt} | {row['note']} |")
    # --- per-page adjudication of the pages that carry no `src` citation
    adj_path = Path("work/audit/uncited_adjudication.json")
    if adj_path.exists():
        import json as _json
        adj = _json.loads(adj_path.read_text(encoding="utf-8"))
        cat_name = {
            "A": "جلد/سرصفحه",
            "B": "نسخهٔ موازی تکراری",
            "C": "محتوا در سند پوشش دارد",
            "D": "صفحهٔ سفید",
        }
        lines += ["", "## تعیین تکلیف صفحه‌به‌صفحهٔ صفحات بی‌ارجاع", "",
                  "هر صفحهٔ بدون `src` در `work/audit/uncited_adjudication.json` یک ردیف دارد:",
                  "دسته، دلیل، و فهرست واژه‌های لاتین/اعدادی که در سند پیدا نشد", "",
                  "| منبع | ص | دسته | دلیل | واژه/عدد پیدانشده |",
                  "| --- | --- | --- | --- | --- |"]
        for row in adj:
            miss = (row.get("latin_missing") or []) + (row.get("numbers_missing") or [])
            miss_txt = "، ".join(miss[:8]) + ("…" if len(miss) > 8 else "") if miss else "—"
            lines.append(f"| `{row['source']}` | {row['page']} | "
                         f"{row['category']} — {cat_name.get(row['category'], '')} | "
                         f"{row['reason']} | {miss_txt} |")
        from collections import Counter as _C
        cnt = _C(r["category"] for r in adj)
        lines += ["", f"**جمع:** {len(adj)} صفحه — "
                      f"جلد/سرصفحه {cnt.get('A',0)} · نسخهٔ موازی {cnt.get('B',0)} · "
                      f"پوشش مفهومی {cnt.get('C',0)} · سفید {cnt.get('D',0)}", ""]
    # اعداد فارسی، ولی شناسه‌های داخل بک‌تیک دست‌نخورده بمانند
    _fa = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    _parts = ("\n".join(lines)).split("`")
    _txt = "`".join(seg if i % 2 else seg.translate(_fa) for i, seg in enumerate(_parts))
    OUT_MD.write_text(_txt + "\n", encoding="utf-8")

    print(f"sources: {len(SOURCES)} | pages: {total_pages} | cited: {total_cited} "
          f"| uncited: {total_pages - total_cited}")
    for row in table:
        if row["pages"] and row["uncited"]:
            print(f"  {row['id']:22s} {len(row['uncited']):3d}/{row['pages']:3d} uncited "
                  f"→ {row['uncited'][:14]}{'…' if len(row['uncited'])>14 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

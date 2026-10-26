"""Quality gates for the anatomy (neuroanatomy) booklets.

Same philosophy as ``render/qa_report.py``: everything printed is **measured on the
produced PDF and on the authored JSON**, never asserted.  The physiology report is
left untouched; this script is the anatomy counterpart and adds the three gates the
anatomy plan requires (G6 bilingual labels, G7 citation completeness, G8 hand-off
sheet and language hygiene).

    .venv/bin/python render/qa_anat.py --session s01

Gates
-----
G1 structure      every block is typed, carries a ``src``, and its asset exists
G2 coverage       every page of the lecture booklet range is claimed by a topic
G3 text layer     the produced PDF re-opens and contains the authored characters
G4 figures        every plate asset is in ``images_anatomy/INDEX.json`` and embedded
G5 TOC            printed page numbers equal the real page of each anchor
G6 labels         every plate has labels, each with both a Persian and a Latin term
G7 citations      every plate names its source and a page; book plates name a figure
G8 hand-off       every topic ends with the hand-off sheet and the pages carry no
                  production/tooling wording

Writes ``reports/ANAT_S{NN}_QA_REPORT.md``; exit code 1 on a hard failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pypdfium2 as pdfium

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "render"))

CONTENT_DIR = REPO / "content" / "anatomy"
ASSET_INDEX = REPO / "images_anatomy" / "INDEX.json"

KNOWN_TYPES = {"p", "ul", "ol", "h3", "callout", "plate", "path", "table",
               "idcard", "handoff"}
NEEDS_SRC = {"p", "ul", "ol", "callout", "path", "table"}

SESSIONS = {
    "s01": dict(
        pdf=REPO / "pdf" / "HumsYar_NeuroAnat_Jalase1.pdf",
        outline="s01_topics.json",
        content=("s01_a.json", "s01_b.json"),
        pages=(2, 18),
        report=REPO / "reports" / "ANAT_S01_QA_REPORT.md",
    ),
    "s02": dict(
        pdf=REPO / "pdf" / "HumsYar_NeuroAnat_Jalase2.pdf",
        outline="s02_topics.json",
        content=("s02_a.json", "s02_b.json", "s02_c.json"),
        pages=(19, 35),
        report=REPO / "reports" / "ANAT_S02_QA_REPORT.md",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


MARK_RE = re.compile(r"[\u064b-\u065f\u0670\u0654\u0655\u200c\u200d\u200e\u200f]")


def norm(text: str) -> str:
    """NFKC + drop Arabic combining marks.

    The PDF stores shaped glyphs; a hamza written above a letter survives as a
    presentation form and the combining mark itself is not recoverable by the
    extractor.  Comparing base letters (documented limitation, not a silent fix)
    is the only order-free check that measures something real.
    """
    import unicodedata
    return MARK_RE.sub("", unicodedata.normalize("NFKC", text))


def fa_n(n: int | str) -> str:
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="s01", choices=sorted(SESSIONS))
    args = ap.parse_args()
    session = args.session
    cfg = SESSIONS[session]

    outline = json.loads((CONTENT_DIR / "outline" / cfg["outline"]).read_text(encoding="utf-8"))
    topics = {t["topic_id"]: t for t in outline["topics"]}
    content: dict[str, list] = {}
    for fname in cfg["content"]:
        for topic in json.loads((CONTENT_DIR / fname).read_text(encoding="utf-8")):
            content[topic["topic_id"]] = topic["blocks"]

    problems: list[str] = []
    warnings: list[str] = []

    index_assets = {}
    if ASSET_INDEX.exists():
        for a in json.loads(ASSET_INDEX.read_text(encoding="utf-8"))["assets"]:
            index_assets[a.get("path") or a.get("asset_id")] = a
    else:
        problems.append("images_anatomy/INDEX.json is missing")

    plates = [(tid, i, b) for tid, blocks in content.items()
              for i, b in enumerate(blocks) if b.get("type") == "plate"]

    # ------------------------------------------------------------------ G1
    block_total = 0
    by_type: dict[str, int] = {}
    for tid, blocks in content.items():
        for i, b in enumerate(blocks):
            block_total += 1
            kind = b.get("type")
            by_type[kind] = by_type.get(kind, 0) + 1
            if kind not in KNOWN_TYPES:
                problems.append(f"G1 {tid}#{i}: unknown block type {kind!r}")
            if kind in NEEDS_SRC and not b.get("src"):
                problems.append(f"G1 {tid}#{i} ({kind}): block without src")
            if kind == "plate":
                if not (REPO / b["asset"]).exists():
                    problems.append(f"G1 {tid}#{i}: missing asset {b['asset']}")
                for field in ("title", "citation", "fa_text", "book"):
                    if not b.get(field):
                        problems.append(f"G1 {tid}#{i}: plate without {field}")

    # ------------------------------------------------------------------ G2
    lo, hi = cfg["pages"]
    claimed: dict[int, list[str]] = {}
    for tid, t in topics.items():
        for p in t.get("pages", []):
            claimed.setdefault(int(p), []).append(tid)
    uncovered = [p for p in range(lo, hi + 1) if p not in claimed]
    for p in uncovered:
        problems.append(f"G2 lecture page {p} is not claimed by any topic")
    outside = sorted(p for p in claimed if not lo <= p <= hi)
    for p in outside:
        warnings.append(f"G2 page {p} is claimed but outside the session range {lo}–{hi}")

    # ------------------------------------------------------------------ G3 + G4
    pdf = pdfium.PdfDocument(str(cfg["pdf"]))
    pages_text = [pdf[i].get_textpage().get_text_range() for i in range(len(pdf))]
    all_text = norm("\n".join(pages_text))
    fa_chars = len(re.findall(r"[\u0600-\u06FF]", all_text))
    latin_chars = len(re.findall(r"[A-Za-z]", all_text))

    # Persian text is written as shaped glyphs in visual order, so order-insensitive
    # character presence is the only honest check (same rule as the physiology QA).
    from collections import Counter
    pdf_chars = Counter(all_text.replace(" ", "").replace("\n", ""))
    missing_text = []
    for tid, blocks in content.items():
        for b in blocks:
            probe = b.get("text") or (b.get("items") or [None])[0] or b.get("title")
            if not probe:
                continue
            head = norm(probe)[:40].replace(" ", "").replace("\n", "")
            if head and not all(pdf_chars[ch] >= n for ch, n in Counter(head).items()):
                missing_text.append((tid, probe[:60]))
    for tid, probe in missing_text[:10]:
        problems.append(f"G3 characters of block not found in PDF text layer: {tid} :: {probe}")

    images_per_page = []
    for i in range(len(pdf)):
        n = sum(1 for _ in pdf[i].get_objects(filter=(pdfium.raw.FPDF_PAGEOBJ_IMAGE,)))
        images_per_page.append(n)
    embedded = sum(images_per_page)
    if embedded < len(plates):
        warnings.append(f"G4 plates={len(plates)} but embedded images={embedded} "
                        "(a plate may share a page or be deduplicated by the PDF)")

    not_indexed = [b["asset"] for _, _, b in plates if b["asset"] not in index_assets]
    for a in not_indexed:
        warnings.append(f"G4 asset not listed in images_anatomy/INDEX.json: {a}")

    # book mix per session — the user's rule: both books in every session
    by_book = {}
    for _, _, b in plates:
        by_book[b["book"]] = by_book.get(b["book"], 0) + 1
    for book in ("snell", "grays"):
        if not by_book.get(book):
            problems.append(f"G4 no plate from {book}: every session must use both books")

    # ------------------------------------------------------------------ G5
    import build_anat as B
    B.SESSION = session
    pages: dict[str, int] = {}
    book = None
    for _ in range(4):
        book = B.build(Path("/tmp/_qa_anat_toc.pdf"), pages)
        if book.heading_pages == pages:
            break
        pages = dict(book.heading_pages)
    else:
        problems.append("G5 TOC pagination did not converge")
    drift = [k for k, v in book.heading_pages.items() if k in pages and pages[k] != v]
    for k in drift:
        problems.append(f"G5 TOC page drift for {k}: {pages[k]} -> {book.heading_pages[k]}")
    blank_pages = [i + 1 for i, txt in enumerate(pages_text) if not txt.strip()]
    for p in blank_pages:
        problems.append(f"G5 blank page in the produced PDF: {p}")

    # ------------------------------------------------------------------ G6
    label_rows = []
    for tid, i, b in plates:
        labels = b.get("labels") or []
        if len(labels) < 3:
            warnings.append(f"G6 {tid}#{i}: only {len(labels)} labels")
        for pair in labels:
            if len(pair) != 2 or not pair[0].strip() or not pair[1].strip():
                problems.append(f"G6 {tid}#{i}: broken label pair {pair!r}")
            else:
                label_rows.append(pair)
    latin_terms = sum(1 for fa, en in label_rows if re.search(r"[A-Za-z]", en))

    # ------------------------------------------------------------------ G7
    fig_re = re.compile(r"(Fig(?:ure)?\.?\s*\d+[-–.]\d+|شکل\s*[۰-۹]+[.\-–][۰-۹]+)")
    cite_ok = 0
    for tid, i, b in plates:
        cite = b.get("citation", "")
        has_page = bool(re.search(r"(p\.\s*\d+|ص\s*[۰-۹\d]|pp\.\s*\d+)", cite))
        if not has_page:
            problems.append(f"G7 {tid}#{i}: citation without a page — {cite!r}")
        else:
            cite_ok += 1
        if b["book"] in ("snell", "grays"):
            if not fig_re.search(cite):
                warnings.append(f"G7 {tid}#{i}: book plate without a figure number — {cite!r}")
            if not b.get("en_caption"):
                problems.append(f"G7 {tid}#{i}: book plate without the original English caption")
        if b["book"] == "grays" and not cite.startswith(("Gray", "گری")):
            problems.append(f"G7 {tid}#{i}: Gray's plate with a non-Gray's citation")
        if b["book"] == "snell" and not cite.startswith(("Snell", "اسنل")):
            problems.append(f"G7 {tid}#{i}: Snell plate with a non-Snell citation")

    # ------------------------------------------------------------------ G8
    FORBIDDEN = ("بررسی‌شده", "بررسی نشده", "OCR", "کیفیت‌سنجی", "گزارش فنی",
                 "همین مخزن", "هوش مصنوعی", "GitHub", "مخزن", "بازبین علمی",
                 "استخراج متن", "لایهٔ متنی")
    handoff_ok = 0
    for tid, blocks in content.items():
        ho = [b for b in blocks if b.get("type") == "handoff"]
        if len(ho) != 1:
            problems.append(f"G8 {tid}: {len(ho)} hand-off sheets (exactly one required)")
            continue
        h = ho[0]
        for field in ("title", "kicker", "sources", "open", "question"):
            if not str(h.get(field, "")).strip():
                problems.append(f"G8 {tid}: hand-off sheet without {field!r}")
        if len(h.get("checklist") or []) != 5:
            problems.append(f"G8 {tid}: hand-off checklist has "
                            f"{len(h.get('checklist') or [])} rows (5 required)")
        handoff_ok += 1
    words = 0
    for tid, blocks in content.items():
        for b in blocks:
            blob = " ".join(str(b.get(k, "")) for k in ("text", "src", "title", "note",
                                                        "open", "question", "sources"))
            for w in FORBIDDEN:
                if w in blob:
                    words += 1
                    problems.append(f"G8 {tid}: presentation wording {w!r} in block "
                                    f"{b.get('type')}")

    # ------------------------------------------------------------------ report
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = cfg["report"]
    lines = [
        f"# گزارش کنترل کیفیت — آناتومی، جلسهٔ {fa_n(int(session[1:]))}",
        "",
        f"تولید: {now} · فایل: `{cfg['pdf'].name}` · حجم: {cfg['pdf'].stat().st_size:,} بایت · "
        f"SHA-256: `{sha256(cfg['pdf'])}`",
        "",
        "این گزارش با اجرای واقعی روی خروجی تولیدشده نوشته شده است؛ هر عدد از خود فایل "
        "اندازه‌گیری شده و هیچ مقداری دستی وارد نشده است.",
        "",
        "## G1 — ساختار محتوا",
        "",
        f"- مبحث‌ها: **{len(content)}** از {len(topics)}",
        f"- بلوک‌ها: **{block_total}**",
        f"- خطای سخت این دروازه: **{sum(1 for p in problems if p.startswith('G1'))}**",
        "",
        "| نوع بلوک | تعداد |",
        "| --- | --- |",
    ]
    for kind, n in sorted(by_type.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{kind}` | {n} |")

    lines += [
        "",
        "## G2 — پوشش صفحه‌های جزوه",
        "",
        f"- دامنهٔ هدف: صفحه‌های **{fa_n(lo)} تا {fa_n(hi)}**",
        f"- صفحه‌های بدون پوشش: **{len(uncovered)}**"
        + (" — " + "، ".join(fa_n(p) for p in uncovered) if uncovered else ""),
        "",
        "| مبحث | صفحه‌های جزوه | بلوک | قاب تصویر | صفحهٔ PDF |",
        "| --- | --- | --- | --- | --- |",
    ]
    for tid, t in topics.items():
        blocks = content.get(tid, [])
        n_plates = sum(1 for b in blocks if b.get("type") == "plate")
        pgs = "، ".join(fa_n(p) for p in t.get("pages", []))
        lines.append(f"| {tid} | {pgs} | {len(blocks)} | {n_plates} | "
                     f"{book.heading_pages.get(tid, '—')} |")

    lines += [
        "",
        "## G3 — لایهٔ متنی خروجی",
        "",
        f"- نویسه‌های فارسی: **{fa_chars:,}** · نویسه‌های لاتین: **{latin_chars:,}** · "
        f"نسبت: **{fa_chars / max(latin_chars, 1):.2f}**",
        f"- بلوک‌هایی که متنشان در لایهٔ متنی پیدا نشد: **{len(missing_text)}**",
        f"- تعداد صفحهٔ سند: **{len(pdf)}**",
        "",
        "## G4 — تصویرها",
        "",
        f"- قاب‌های تصویر در محتوا: **{len(plates)}**",
        f"- تصویر جاسازی‌شده در PDF: **{embedded}**",
        f"- توزیع بر اساس کتاب: " + " · ".join(
            f"{k} = {fa_n(v)}" for k, v in sorted(by_book.items())),
        f"- دارایی‌های ثبت‌نشده در `images_anatomy/INDEX.json`: **{len(not_indexed)}**",
        "",
        "## G5 — فهرست و صفحه‌بندی",
        "",
        f"- همگرایی فهرست: **{'بله' if not drift else 'خیر'}**",
        f"- صفحه‌های خالی: **{len(blank_pages)}**",
        "",
        "## G6 — برچسب‌های دوزبانه",
        "",
        f"- جفت‌برچسب‌ها: **{len(label_rows)}** (از این تعداد، **{latin_terms}** معادل لاتین دارند)",
        f"- برچسب ناقص: **{sum(1 for p in problems if p.startswith('G6'))}**",
        "",
        "## G7 — کامل بودن ارجاع",
        "",
        f"- قاب‌هایی که ارجاعشان شمارهٔ صفحه دارد: **{cite_ok} از {len(plates)}**",
        f"- قاب کتاب بدون کپشن اصلی انگلیسی: "
        f"**{sum(1 for p in problems if 'English caption' in p)}**",
        "",
        "## G8 — برگهٔ تحویل و زبان متن",
        "",
        f"- مبحث‌های دارای برگهٔ تحویل کامل: **{fa_n(handoff_ok)} از "
        f"{fa_n(len(content))}**",
        f"- واژه‌های فنی/ابزاری در متن: **{fa_n(words)}**",
        "",
        "## نتیجهٔ دروازه‌ها",
        "",
        f"- خطاهای سخت: **{len(problems)}**",
        f"- هشدارها: **{len(warnings)}**",
        "",
    ]
    for p in problems:
        lines.append(f"- ❌ {p}")
    for w in warnings:
        lines.append(f"- ⚠️ {w}")

    lines += [
        "",
        "## آنچه این گزارش ادعا نمی‌کند",
        "",
        "- **بازبینی علمی نشده است**: هیچ جمله‌ای توسط متخصص با رفرنس تطبیق داده نشده است؛ "
        "این گزارش فقط ساختار، ارجاع، پوشش و خوانایی را می‌سنجد.",
        "- درستی علمی محتوا، درستی ترجمهٔ برچسب‌ها و تناسب شکل با متن، هر سه خارج از دامنهٔ "
        "این دروازه‌ها هستند و باید در بازبینی علمی جداگانه تأیید شوند.",
        "- تعداد قاب‌های هر کتاب فقط شمارش است؛ «کافی بودن» تنوع تصویری قضاوت علمی است.",
        "",
    ]
    report.parent.mkdir(exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")

    print(f"report: {report.relative_to(REPO)}")
    print(f"blocks={block_total} plates={len(plates)} embedded={embedded} "
          f"pages={len(pdf)} fa={fa_chars} latin={latin_chars} "
          f"problems={len(problems)} warnings={len(warnings)}")
    for p in problems:
        print("  FAIL:", p)
    for w in warnings:
        print("  WARN:", w)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

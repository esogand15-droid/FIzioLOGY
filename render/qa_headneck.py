"""Quality gates for the anatomy (neuroanatomy) booklets.

Same philosophy as ``render/qa_report.py``: everything printed is **measured on the
produced PDF and on the authored JSON**, never asserted.  The physiology report is
left untouched; this script is the anatomy counterpart and adds the three gates the
anatomy plan requires (G6 bilingual labels, G7 citation completeness, G8 hand-off
sheet and language hygiene).

    .venv/bin/python render/qa_headneck.py --session hn01

Gates
-----
G1 structure      every block is typed, carries a ``src``, and its asset exists
G2 coverage       every page of the lecture booklet range is claimed by a topic
G3 text layer     the produced PDF re-opens and contains the authored characters
G4 figures        every plate asset is in ``headneck/images/INDEX.json`` and embedded
G5 TOC            printed page numbers equal the real page of each anchor
G6 labels         every plate has labels, each with both a Persian and a Latin term
G7 citations      every plate names its source and a page; book plates name a figure
G8 hand-off       every topic ends with the hand-off sheet and the pages carry no
                  production/tooling wording

Writes ``headneck/reports/HN_S{NN}_QA_REPORT.md``; exit code 1 on a hard failure.
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
from hn_updates import apply_update

CONTENT_DIR = REPO / "headneck" / "content"
ASSET_INDEX = REPO / "headneck" / "images" / "INDEX.json"

KNOWN_TYPES = {"p", "ul", "ol", "h3", "callout", "plate", "path", "table",
               "idcard", "handoff", "note"}
NEEDS_SRC = {"p", "ul", "ol", "callout", "path", "table"}

SESSIONS = {
    "hn01": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase1.pdf",
        outline="hn01_topics.json",
        content=("hn01_a.json", "hn01_b.json"),
        page_ranges=[(1, 22)],
        report=REPO / "headneck" / "reports" / f"HN_S01_QA_REPORT.md",
    ),
    "hn02": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase2.pdf",
        outline="hn02_topics.json",
        content=("hn02_a.json", "hn02_b.json"),
        page_ranges=[(1, 33)],
        report=REPO / "headneck" / "reports" / f"HN_S02_QA_REPORT.md",
    ),
    "hn03": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase3.pdf",
        outline="hn03_topics.json",
        content=("hn03_a.json", "hn03_b.json"),
        page_ranges=[(1, 20)],
        report=REPO / "headneck" / "reports" / f"HN_S03_QA_REPORT.md",
    ),
    "hn04": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase4_FINAL.pdf",
        outline="hn04_topics.json",
        content=("hn04_a.json", "hn04_b.json"),
        # Two source PDFs: part 1 pages 1–25, part 2 encoded as 100+page.
        page_ranges=[(1, 25), (101, 114)],
        report=REPO / "headneck" / "reports" / f"HN_S04_FINAL_TECHNICAL_QA_REPORT.md",
    ),
    "hn05": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase5.pdf",
        outline="hn05_topics.json",
        content=("hn05_a.json", "hn05_b.json"),
        page_ranges=[(1, 45)],
        report=REPO / "headneck" / "reports" / f"HN_S05_QA_REPORT.md",
    ),
    "hn06": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase6.pdf",
        outline="hn06_topics.json",
        content=("hn06_a.json", "hn06_b.json"),
        page_ranges=[(1, 20)],
        report=REPO / "headneck" / "reports" / f"HN_S06_QA_REPORT.md",
    ),
    "hn07": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase7.pdf",
        outline="hn07_topics.json",
        content=("hn07_a.json", "hn07_b.json"),
        page_ranges=[(1, 20)],
        report=REPO / "headneck" / "reports" / f"HN_S07_QA_REPORT.md",
    ),
    "hn08": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase8.pdf",
        outline="hn08_topics.json",
        content=("hn08_a.json", "hn08_b.json"),
        page_ranges=[(1, 13)],
        report=REPO / "headneck" / "reports" / f"HN_S08_QA_REPORT.md",
    ),
    "hn09": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase9.pdf",
        outline="hn09_topics.json",
        content=("hn09_a.json", "hn09_b.json"),
        page_ranges=[(1, 15)],
        report=REPO / "headneck" / "reports" / f"HN_S09_QA_REPORT.md",
    ),
    "hn10": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase10.pdf",
        outline="hn10_topics.json",
        content=("hn10_a.json", "hn10_b.json"),
        page_ranges=[(1, 8)],
        report=REPO / "headneck" / "reports" / f"HN_S10_QA_REPORT.md",
    ),
    "hn11": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase11.pdf",
        outline="hn11_topics.json",
        content=("hn11_a.json", "hn11_b.json"),
        page_ranges=[(1, 20)],
        report=REPO / "headneck" / "reports" / f"HN_S11_QA_REPORT.md",
    ),
    "hn12": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase12.pdf",
        outline="hn12_topics.json",
        content=("hn12_a.json", "hn12_b.json"),
        page_ranges=[(1, 15)],
        report=REPO / "headneck" / "reports" / f"HN_S12_QA_REPORT.md",
    ),
    "hn13": dict(
        pdf=REPO / "pdf" / "HumsYar_HeadNeck_Jalase13.pdf",
        outline="hn13_topics.json",
        content=("hn13_a.json", "hn13_b.json"),
        page_ranges=[(1, 56)],
        report=REPO / "headneck" / "reports" / f"HN_S13_QA_REPORT.md",
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
    return MARK_RE.sub("", unicodedata.normalize("NFKC", text)).replace("⁄", "/")


def fa_n(n: int | str) -> str:
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="s01", choices=sorted(SESSIONS))
    ap.add_argument("--pdf", help="PDF to check instead of the published session PDF")
    ap.add_argument("--report", help="report output path")
    args = ap.parse_args()
    session = args.session
    cfg = dict(SESSIONS[session])
    if args.pdf:
        cfg["pdf"] = Path(args.pdf).resolve()
    if args.report:
        cfg["report"] = Path(args.report).resolve()
    outline = json.loads((CONTENT_DIR / "outline" / cfg["outline"]).read_text(encoding="utf-8"))
    topics = {t["topic_id"]: t for t in outline["topics"]}
    content: dict[str, list] = {}
    for fname in cfg["content"]:
        for topic in json.loads((CONTENT_DIR / fname).read_text(encoding="utf-8")):
            content[topic["topic_id"]] = topic["blocks"]
    content = apply_update(session, content)

    problems: list[str] = []
    warnings: list[str] = []

    index_assets = {}
    if ASSET_INDEX.exists():
        for a in json.loads(ASSET_INDEX.read_text(encoding="utf-8"))["assets"]:
            index_assets[a.get("path") or a.get("asset_id")] = a
    else:
        problems.append("headneck/images/INDEX.json is missing")

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
    # A session may print from more than one lecture file (session 8 is part 1
    # plus part 2), so the target is a list of ranges, not one interval. Pages
    # of the second file are stored as 100 + page number so both fit in one int.
    ranges = cfg.get("page_ranges") or [cfg["pages"]]
    wanted = {p for lo_, hi_ in ranges for p in range(lo_, hi_ + 1)}
    claimed: dict[int, list[str]] = {}
    for tid, t in topics.items():
        for p in t.get("pages", []):
            claimed.setdefault(int(p), []).append(tid)
    uncovered = [p for p in sorted(wanted) if p not in claimed]
    for p in uncovered:
        problems.append(f"G2 lecture page {p} is not claimed by any topic")
    outside = sorted(p for p in claimed if p not in wanted)
    for p in outside:
        warnings.append(f"G2 page {p} is claimed but outside the session ranges")

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
        warnings.append(f"G4 asset not listed in headneck/images/INDEX.json: {a}")

    # book mix per session — the user's rule: both books in every session
    by_book = {}
    for _, _, b in plates:
        by_book[b["book"]] = by_book.get(b["book"], 0) + 1
    for book in ("netter", "grays"):
        if not by_book.get(book):
            problems.append(f"G4 no plate from {book}: every session must use both books")

    # ------------------------------------------------------------------ G5
    import build_headneck as B
    B.SESSION = session
    pages: dict[str, int] = {}
    book = None
    for _ in range(4):
        book = B.build(Path("/tmp/_qa_hn_toc.pdf"), pages)
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
    # Netter numbers its figures as plates (``Plate 25``); a Netter citation may
    # quote that number instead of a Fig. 8.x-style figure number.
    plate_re = re.compile(r"(?:Plate|پلیت)\s*(?:BP\s*)?[۰-۹\d]+", re.IGNORECASE)
    cite_ok = 0
    for tid, i, b in plates:
        cite = b.get("citation", "")
        has_page = bool(re.search(r"(?:p\.\s*\d+|ص\s*[۰-۹\d]+|pp\.\s*\d+|صفحه[ٔ]?(?:\s+واقعی)?\s+(?:PDF\s+)?[۰-۹\d]+)", cite))
        if not has_page:
            problems.append(f"G7 {tid}#{i}: citation without a page — {cite!r}")
        else:
            cite_ok += 1
        if b["book"] in ("netter", "grays"):
            if not fig_re.search(cite) and not (b["book"] == "netter"
                                                and plate_re.search(cite)):
                warnings.append(f"G7 {tid}#{i}: book plate without a figure number — {cite!r}")
            if not b.get("en_caption"):
                problems.append(f"G7 {tid}#{i}: book plate without the original English caption")
        if b["book"] == "grays" and not cite.startswith(("Gray", "گری")):
            problems.append(f"G7 {tid}#{i}: Gray's plate with a non-Gray's citation")
        if b["book"] == "netter" and not cite.startswith(("Netter", "نتر")):
            problems.append(f"G7 {tid}#{i}: Netter plate with a non-Netter citation")

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
        f"# گزارش کنترل کیفیت — آناتومی سر و گردن، جلسهٔ {fa_n(int(session[2:]))}",
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
        "- دامنهٔ هدف: " + " · ".join(
            (f"صفحه‌های **{fa_n(a)} تا {fa_n(b)}**" if (a, b) == ranges[0]
             else f"بخش ۲: صفحه‌های **{fa_n(a - 100)} تا {fa_n(b - 100)}**")
            for a, b in ranges),
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
        if session == 'hn04':
            from build_headneck import page_range
            pgs = page_range(t.get('pages', []), part_labels=True)
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
        f"- دارایی‌های ثبت‌نشده در `headneck/images/INDEX.json`: **{len(not_indexed)}**",
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
        "- **این گزارش تأیید علمی نیست**: وضعیت بازبینی محتوایی باید از گزارش مستقلِ همراه خوانده شود؛ "
        "این گزارش فقط ساختار، ارجاع، پوشش و خوانایی را می‌سنجد.",
        "- درستی علمی محتوا، درستی ترجمهٔ برچسب‌ها و تناسب شکل با متن، هر سه خارج از دامنهٔ "
        "این دروازه‌ها هستند و باید در بازبینی علمی جداگانه تأیید شوند.",
        "- تعداد قاب‌های هر کتاب فقط شمارش است؛ «کافی بودن» تنوع تصویری قضاوت علمی است.",
        "",
    ]
    report.parent.mkdir(exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")

    try:
        display_report = report.relative_to(REPO)
    except ValueError:
        display_report = report
    print(f"report: {display_report}")
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

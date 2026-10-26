"""Build the neuroanatomy session PDFs (HumsYar · آناتومی دستگاه اعصاب).

One session = one PDF in ``pdf/``.  The physiology builder
(``render/build_master.py``) is never touched: anatomy has its own content root
(``content/anatomy/``), its own session table and a few block types that only
exist here (``plate`` = a book figure with its own citation, ``path`` = a
numbered conduction chain, ``status`` = the evidence tag for one claim).

    .venv/bin/python render/build_anat.py --session s01 [--out PATH] [--force]

Two-pass layout: pass 1 records the page of every anchor, pass 2 prints the TOC
with those numbers.  The TOC always has the same number of rows, so pagination
is stable between passes; the script asserts that instead of shipping a wrong
TOC.

Nothing is invented here.  A plate block carries the book, page and figure
number of the picture; a missing file is reported on the page (never skipped).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pdf_kit as K
from pdf_kit import MM, PDFBook, TextStyle

REPO = Path(__file__).resolve().parents[1]
CONTENT = REPO / "content" / "anatomy"

FOOTER = "HumsYar · جزوهٔ مادر آناتومی دستگاه اعصاب"

# --------------------------------------------------------------- session table
# ``of`` is always ۱۳: the official list the user supplied has 13 sessions.
ANAT_SESSIONS = {
    "s01": dict(
        num="۱", n=1, of="۱۳",
        title="بافت‌شناسی سیستم عصبی",
        cover_title=["آناتومی دستگاه اعصاب", "جلسهٔ ۱ — بافت‌شناسی"],
        cover_topic="نورون، نوروگلیا و غلاف میلین",
        divider_title="بافت‌شناسی\nسیستم عصبی:\nاز نورون تا میلین",
        divider_sub="جزوهٔ درس · Snell فصل‌های ۱ و ۲ · Gray's فصل ۱",
        lecture="جزوهٔ درس (جلسهٔ ۱ و ۲) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۲–۱۸",
        outline="s01_topics.json",
        content=("s01_a.json", "s01_b.json"),
        anchor="anat-s01",
        pdf_name="HumsYar_NeuroAnat_Jalase1.pdf",
        next_topics=["نخاع (جلسهٔ ۳)", "ساقهٔ مغز (جلسهٔ ۵)", "مخچه (جلسهٔ ۷)"],
    ),
}


# --------------------------------------------------------------------- helpers
def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fa(n) -> str:
    return str(n).translate(K.FA_DIGITS)


def page_range(pages) -> str:
    pages = sorted(int(p) for p in pages or [])
    if not pages:
        return "—"
    if len(pages) == 1:
        return fa(pages[0])
    if pages == list(range(pages[0], pages[-1] + 1)):
        return f"{fa(pages[0])}–{fa(pages[-1])}"
    return "، ".join(fa(p) for p in pages)


def tno(tid: str) -> str:
    return fa(int(tid.split("-T")[-1]))


# ----------------------------------------------------------------------- pages
def cover_page(book: PDFBook, cfg: dict) -> None:
    c = book.c
    c.setFillColor(K.TEAL_L)
    c.setFont("VazirM", 11)
    c.drawCentredString(K.A4W / 2, K.A4H * 0.86, K.shape("HumsYar · جزوهٔ مادر آناتومی"))
    c.setFillColor(K.HexColor("#ffffff"))
    c.setFont("VazirB", 29)
    c.drawCentredString(K.A4W / 2, K.A4H * 0.615, K.shape(cfg["cover_title"][0]))
    c.drawCentredString(K.A4W / 2, K.A4H * 0.552, K.shape(cfg["cover_title"][1]))
    c.setFillColor(K.TEAL_L)
    c.setFont("Vazir", 13.5)
    c.drawCentredString(K.A4W / 2, K.A4H * 0.475, K.shape(cfg["cover_topic"]))
    c.setStrokeColor(K.HexColor("#0d9488"))
    c.setLineWidth(1.4)
    c.line(K.A4W * 0.30, K.A4H * 0.44, K.A4W * 0.70, K.A4H * 0.44)
    c.setFillColor(K.HexColor("#94a3b8"))
    c.setFont("Vazir", 9.8)
    lines = [
        f"جلسهٔ {cfg['num']} از {cfg['of']} — {cfg['lecture']}",
        "متن: جزوهٔ درس + Snell's Clinical Neuroanatomy, 9th ed.",
        "تصویر: Snell و Gray's Anatomy for Students, 3rd ed. — هر دو کتاب در هر جلسه",
        f"نسخهٔ ۰٫۱ — فقط جلسهٔ {cfg['num']} تألیف شده است",
    ]
    yy = K.A4H * 0.375
    for t in lines:
        c.drawCentredString(K.A4W / 2, yy, K.shape(t))
        yy -= 18
    c.setFont("VazirL", 8.4)
    c.setFillColor(K.HexColor("#64748b"))
    c.drawCentredString(K.A4W / 2, K.A4H * 0.12,
                        K.shape("سند کاری درس آناتومی — پیش‌نویس ویرایشی، بازبینی علمی در جریان"))


def divider(book: PDFBook, kicker: str, title: str, subtitle: str, bullets=()) -> None:
    def painter(b: PDFBook) -> None:
        c = b.c
        c.setFillColor(K.TEAL)
        c.setFont("VazirM", 11)
        c.drawRightString(K.A4W - K.M_RIGHT - 4, K.A4H * 0.74, K.shape(kicker))
        c.setFillColor(K.HexColor("#ffffff"))
        c.setFont("VazirB", 27)
        yy = K.A4H * 0.66
        for line in title.split("\n"):
            c.drawRightString(K.A4W - K.M_RIGHT - 4, yy, K.shape(line))
            yy -= 38
        c.setFillColor(K.TEAL_L)
        c.setFont("Vazir", 11.5)
        c.drawRightString(K.A4W - K.M_RIGHT - 4, yy - 6, K.shape(subtitle))
        c.setFillColor(K.HexColor("#94a3b8"))
        c.setFont("Vazir", 9.4)
        yy -= 42
        for b_ in bullets:
            c.drawRightString(K.A4W - K.M_RIGHT - 4, yy, K.shape("• " + b_))
            yy -= 17
    book.dark_page(painter)


def front_matter(book: PDFBook, cfg: dict, stats: dict) -> None:
    """Colophon + reading rules + the citation/tag law of this booklet."""
    book.h1("شناسنامهٔ سند و قاعدهٔ خواندن آن", anchor="front-colophon",
            kicker="قبل از شروع بخوانید")

    book.label_card(
        "این سند چیست و چه چیزی نیست",
        [
            {"label": "این سند چیست",
             "text": "جزوهٔ مادر جلسهٔ نخست درس آناتومی دستگاه اعصاب؛ بازنویسی ساخت‌یافتهٔ جزوهٔ "
                     "درس، همراه با تصویرهای دو کتاب مرجع و متن توضیحی فارسی زیر هر تصویر."},
            {"label": "این سند چه چیزی نیست",
             "text": "جایگزین کتاب مرجع نیست و به‌جای متن کتاب نوشته نشده است؛ هر جا عدد، صفحه "
                     "یا جمله‌ای از کتاب آمده، ارجاع همان صفحه کنارِ آن نوشته شده است."},
            {"label": "منابع متن",
             "text": f"{cfg['lecture']} · Snell's Clinical Neuroanatomy, 9th ed. (متن قابل انتخاب) · "
                     "Gray's Anatomy for Students, 3rd ed. (فقط تصویر و رابطهٔ فضایی)"},
            {"label": "منابع تصویر",
             "text": f"{fa(stats['lec'])} تصویر از جزوهٔ درس · {fa(stats['snell'])} تصویر از Snell · "
                     f"{fa(stats['grays'])} تصویر از Gray's. هر جلسه از هر دو کتاب تصویر دارد؛ "
                     "اولویت‌بندی بین دو کتاب وجود ندارد."},
            {"label": "پرسش‌های تعیین‌کننده",
             "text": "۱) این تصویر از کدام کتاب و کدام صفحه است؟ ۲) هر برچسب فارسی معادل کدام "
                     "واژهٔ انگلیسی روی تصویر است؟ ۳) چه بخشی از متن، ادعای بررسی‌شده دارد و چه "
                     "بخشی فقط شناسایی شده است؟"},
        ],
        accent=K.TEAL, tint=K.TEAL_LL, kicker="شناسنامه",
        footer="وضعیت: پیش‌نویس ویرایشی — بازبینی علمی در جریان",
    )

    book.h2("سه برچسب وضعیت شواهد", anchor="front-tags")
    book.paragraph(
        "در تمام این جزوه، هر ادعا یکی از این سه برچسب را دارد. برچسب کنارِ خودِ ادعا نوشته "
        "می‌شود، نه در یک پیوست جدا؛ چون خواننده باید در همان خط بداند چه چیزی سند دارد و چه "
        "چیزی ندارد.")
    book.table(
        ["برچسب", "معنی دقیق", "چطور تشخیصش بدهم"],
        [
            ["بررسی‌شده",
             "متن یا تصویرِ منبع دیده شده و ادعا مستقیماً از آن گرفته شده است.",
             "کنار ادعا، صفحهٔ جزوه یا شمارهٔ شکل کتاب نوشته شده است."],
            ["شناسایی‌شده ولی بررسی‌نشده",
             "منبع در دسترس است و جای ادعا معلوم است، اما متن/تصویر آن صفحه هنوز خوانده و "
             "تطبیق داده نشده است.",
             "عبارت «بررسی‌نشده» یا «نیازمند تطبیق» کنار ادعا می‌آید."],
            ["غیرقابل‌دسترسی",
             "منبع اصلی (مثلاً اسلاید استاد یا نمونه‌سؤال) وجود ندارد یا در اختیار ما نیست.",
             "جای ادعا یک کادر هشدار می‌آید، نه یک جملهٔ حدسی."],
        ],
        widths=[K.CONTENT_W * 0.22, K.CONTENT_W * 0.44, K.CONTENT_W * 0.34],
        caption="جدول ۰-۱ — برچسب‌های وضعیت شواهد در این جزوه",
        src="قاعدهٔ داخلی تیم تألیف",
    )

    book.h2("قاعدهٔ ارجاع به تصویر و متن", anchor="front-cite")
    book.numbered([
        "هر تصویر در یک قاب می‌آید: عنوان فارسی، ارجاع (کتاب، شمارهٔ شکل، صفحهٔ pdf)، "
        "کپشن اصلی انگلیسی، توضیح فارسی، برچسب‌های دوزبانه و ارجاع متن.",
        "شمارهٔ صفحه بر اساس فایل pdf کتاب است، نه شمارهٔ چاپی؛ چون هیچ‌کدام از دو کتاب شمارهٔ "
        "صفحهٔ چاپی خوانا در پانوشت ندارند.",
        "کپشن انگلیسی عیناً از کتاب نقل می‌شود و هرگز به فارسی بازنویسی نمی‌شود؛ ترجمه و "
        "توضیح فارسی در سطر جداگانه می‌آید.",
        "برای جزوهٔ درس، ارجاع با شمارهٔ صفحهٔ همان جزوه است؛ صفحه‌شماری جزوه از جلد شروع "
        "می‌شود، پس «ص ۳» یعنی سومین صفحهٔ فایل جزوه.",
        "هیچ شکل، عدد یا جمله‌ای ساخته نمی‌شود. اگر تصویری در دسترس نبود، جای آن کادر هشدار "
        "می‌آید و در گزارش QA ثبت می‌شود.",
    ])
    book.source_line("قاعدهٔ ارجاع — همین جزوه، بخش QA")


def toc_page(book: PDFBook, cfg: dict, outline: dict, toc_pages: dict) -> None:
    book.h1("فهرست مطالب", anchor="toc", kicker="راهنمای سند")
    book.paragraph("شمارهٔ روبه‌روی هر سطر، شمارهٔ صفحهٔ همین سند است.",
                   TextStyle(size=9, color=K.MUTED))
    rows = [
        ("۰", "شناسنامهٔ سند و قاعدهٔ خواندن آن", "front-colophon", 0),
        ("۰", "سه برچسب وضعیت شواهد", "front-tags", 1),
        ("۰", "قاعدهٔ ارجاع به تصویر و متن", "front-cite", 1),
        (cfg["num"], f"فصل {cfg['num']} — جلسهٔ {cfg['num']}: {cfg['cover_topic']}",
         cfg["anchor"], 0),
    ]
    for i, t in enumerate(outline["topics"], start=1):
        rows.append((f"{i:02d}", t["title"], t["topic_id"], 1))
    rows += [("پ", "جمع‌بندی، چک‌لیست و برگهٔ تحویل", "anat-summary", 0),
             ("پ", "قدم بعدی: چه چیزی در جلسهٔ بعد می‌آید", "anat-next", 1)]
    step = 20 if len(rows) <= 26 else 17
    for num, title, anchor, indent in rows:
        pg = toc_pages.get(anchor)
        book.toc_row(num, title, fa(pg) if pg else "—",
                     indent=indent * 18, accent=K.TEAL if indent == 0 else K.BLUE,
                     step=step)


def session_intro(book: PDFBook, cfg: dict, outline: dict, stats: dict) -> None:
    book.h1(f"جلسهٔ {cfg['num']} در یک نگاه", anchor="anat-glance", kicker="نقشهٔ جلسه")
    book.label_card(
        "این جلسه چه چیزی را می‌سازد",
        [
            {"label": "موضوع جلسه", "text": cfg["title"]},
            {"label": "دامنهٔ صفحه‌های جزوه", "text": f"{cfg['pages_label']} — همهٔ صفحه‌های این "
                                                    "دامنه بررسی و در مبحث‌ها توزیع شده‌اند."},
            {"label": "تعداد مبحث", "text": f"{fa(len(outline['topics']))} مبحث"},
            {"label": "تعداد تصویر",
             "text": f"{fa(stats['plates'])} قاب تصویر: {fa(stats['lec'])} از جزوه، "
                     f"{fa(stats['snell'])} از Snell، {fa(stats['grays'])} از Gray's."},
            {"label": "خروجی این جلسه",
             "text": "شناخت نورون و زوائدش، انتقال آکسونی، سیناپس، شش نوع سلول گلیال، و تفاوت "
                     "میلین‌سازی در CNS و PNS."},
        ],
        accent=K.TEAL, tint=K.TEAL_LL, kicker="شناسنامهٔ جلسه",
        footer=f"منابع: {cfg['lecture']} · Snell فصل ۱–۲ · Gray's فصل ۱",
    )
    book.h2("نقشهٔ مبحث‌های این جلسه", anchor="anat-map")
    rows = []
    for i, t in enumerate(outline["topics"], start=1):
        rows.append([f"{i:02d}", t["title"], page_range(t.get("pages", [])),
                     t.get("gist", "")])
    book.table(["#", "مبحث", "صفحه‌های جزوه", "در یک جمله"],
               rows, widths=[K.CONTENT_W * 0.07, K.CONTENT_W * 0.30,
                             K.CONTENT_W * 0.15, K.CONTENT_W * 0.48],
               caption="جدول ۱-۰ — نقشهٔ مبحث‌ها",
               src="نقشهٔ محتوایی همین جزوه")


def topic_head(book: PDFBook, t: dict, idx: int, total: int) -> None:
    book.ensure(120)
    book.h2(t["title"], anchor=t["topic_id"])
    meta = (f"مبحث {fa(idx)} از {fa(total)} · صفحه‌های جزوه: {page_range(t.get('pages', []))}")
    if t.get("prereq"):
        meta += " · پیش‌نیاز: " + t["prereq"]
    book.paragraph(meta, TextStyle(size=8.3, color=K.MUTED, justify=False))
    book.spacer(2)


# ----------------------------------------------------------------- block render
def render_blocks(book: PDFBook, blocks) -> None:
    for b in blocks:
        kind = b.get("type")
        if kind == "p":
            book.paragraph(b["text"], TextStyle(space_after=2))
            if b.get("src"):
                book.source_line(b["src"])
        elif kind == "ul":
            book.bullets(b["items"])
            book.source_line(b.get("src", ""))
            book.spacer(3)
        elif kind == "ol":
            book.numbered(b["items"])
            book.source_line(b.get("src", ""))
            book.spacer(3)
        elif kind == "h3":
            book.h3(b["text"])
        elif kind == "callout":
            book.callout(b["text"], kind=b.get("kind", "key"), title=b.get("title"))
            if b.get("src"):
                book.source_line(b["src"])
            book.spacer(2)
        elif kind == "plate":
            book.anat_plate(
                REPO / b["asset"],
                b["title"], b["citation"], b.get("en_caption", ""),
                b.get("fa_text", ""), labels=[tuple(x) for x in b.get("labels", [])],
                view=b.get("view", ""), src=b.get("src", ""),
                max_h=(b.get("max_h", 132)) * MM,
            )
        elif kind == "path":
            book.path_steps(b["steps"], title=b.get("title", "مسیر گام‌به‌گام"))
            if b.get("src"):
                book.source_line(b["src"])
            book.spacer(2)
        elif kind == "table":
            book.table(b["head"], b["rows"], caption=b.get("caption", ""),
                       src=b.get("src", ""), widths=b.get("widths"))
            book.spacer(3)
        elif kind == "idcard":
            book.label_card(b.get("title", "شناسنامهٔ مبحث"), b.get("rows", []),
                            accent=K.TEAL, tint=K.TEAL_LL, kicker=b.get("kicker", ""),
                            footer=b.get("footer", ""))
        elif kind == "handoff":
            book.ensure(185)
            book.label_card(b.get("title", "برگهٔ تحویل مبحث"), b.get("rows", []),
                            accent=K.AMBER, tint=K.AMBER_BG, kicker=b.get("kicker", ""),
                            tick=True, footer=b.get("footer", ""))
        elif kind == "status":
            book.callout(b["text"], kind=b.get("kind", "info"),
                         title=b.get("title", "وضعیت این بخش از شواهد"))
            if b.get("src"):
                book.source_line(b["src"])
            book.spacer(2)
        else:
            raise ValueError(f"unknown block type: {kind}")


def summary(book: PDFBook, content: dict) -> None:
    """Closing checklist built from the session's own blocks."""
    book.h1("جمع‌بندی، چک‌لیست و برگهٔ تحویل", anchor="anat-summary", kicker="پایان جلسه")
    book.paragraph(
        "این بخش سه کار می‌کند: اول ساختارهای کلیدی جلسه را در یک جدول جمع می‌کند، بعد یک "
        "چک‌لیست خودآزمایی می‌دهد که با آن می‌شود فهمید کدام بخش را باید دوباره خواند، و آخر "
        "برگهٔ تحویل تیم را می‌بندد. هیچ‌کدام از این سه، ادعای تازه‌ای به جزوه اضافه نمی‌کنند؛ "
        "همه از متن مبحث‌های بالا ساخته شده‌اند.")
    struct = []
    for tid, blocks in content.items():
        for b in blocks:
            if b.get("type") != "plate":
                continue
            src_book = {"lecture": "جزوهٔ درس", "snell": "Snell", "grays": "Gray's"}.get(
                b.get("book"), "—")
            m = re.search(r"(Fig(?:ure)?\.?\s*\d+[.\-–]\d+)", b.get("citation", ""))
            fig = m.group(1).replace("Figure", "Fig.") if m else ""
            struct.append([b["title"], src_book, fig or "—", b.get("src", "")])
    if struct:
        book.table(["ساختار", "کتاب", "شکل", "جای متن"],
                   struct, widths=[K.CONTENT_W * 0.36, K.CONTENT_W * 0.16,
                                   K.CONTENT_W * 0.20, K.CONTENT_W * 0.28],
                   caption="جدول ۷-۱ — همهٔ قاب‌های تصویر این جلسه و جای متنیشان",
                   src="فهرست خودکار از قاب‌های همین سند")
    book.table(
        ["چک‌لیست خودآزمایی", "می‌توانم؟"],
        [
            ["سه جزء نورون و تفاوت دندریت با آکسون را از حفظ بگویم.", "☐"],
            ["بگویم چرا اجسام نیسل در آکسون نیستند و این چه پیامدی دارد.", "☐"],
            ["مسیر آنتروگراد و رتروگراد را با پروتئین ناقل هرکدام بنویسم.", "☐"],
            ["چهار نوع نورون از نظر مورفولوژی را با یک مثال برای هرکدام بگویم.", "☐"],
            ["شش نوع سیناپس بر اساس ساختارهای درگیر را نام ببرم.", "☐"],
            ["شش سلول گلیال و منشأ جنینی هرکدام را در جدول بازسازی کنم.", "☐"],
            ["تفاوت میلین‌سازی الیگودندروسیت و سلول شوان را توضیح دهم.", "☐"],
        ],
        widths=[K.CONTENT_W * 0.86, K.CONTENT_W * 0.14],
        caption="جدول ۷-۲ — چک‌لیست خودآزمایی جلسهٔ ۱",
        src="ساخته‌شده از مبحث‌های همین سند",
    )


def next_steps(book: PDFBook, cfg: dict) -> None:
    book.h1("قدم بعدی: چه چیزی در جلسهٔ بعد می‌آید", anchor="anat-next", kicker="ادامهٔ کار")
    book.paragraph(
        f"این سند جلسهٔ {cfg['num']} از {cfg['of']} است و هر جلسه سند جداگانهٔ خودش را می‌گیرد؛ "
        "سند جلسه‌های پیشین دست‌نخورده بایگانی می‌شود. برای هر جلسهٔ بعدی همان مسیر تکرار "
        "می‌شود: شناسنامه، مبحث‌ها، قاب‌های تصویر از هر دو کتاب، و چک‌لیست.")
    book.bullets([
        "مبحث‌هایی که در این جلسه باز شد و در جلسه‌های بعد بسته می‌شود: شامه‌های مغز و نخاع، "
        "سد خونی‌مغزی، سازمان‌دهی عصبی محیطی و بازسازی عصبی (همه در صفحه‌های ۱۹–۳۵ همین جزوه، "
        "جلسهٔ ۲).",
        "مباحث ساختاری بعدی: " + " · ".join(cfg.get("next_topics", [])) + ".",
        "همهٔ برچسب‌های «بررسی‌نشده» این سند در گزارش QA جلسه فهرست شده‌اند و باید قبل از "
        "تأیید نهایی جلسه بسته شوند.",
    ])
    book.callout(
        "این جلسه فقط زمانی «تکمیل» شمرده می‌شود که گزارش QA آن، پوشش کامل صفحه‌های ۲–۱۸ و "
        "بازبینی علمی همهٔ قاب‌ها را نشان بدهد. تا آن زمان وضعیت این سند پیش‌نویس است.",
        kind="warn", title="شرط اعلام تکمیل")


def back_page(book: PDFBook, cfg: dict) -> None:
    def painter(b: PDFBook) -> None:
        c = b.c
        c.setFillColor(K.HexColor("#ffffff"))
        c.setFont("VazirB", 20)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.62, K.shape("HumsYar"))
        c.setFillColor(K.TEAL_L)
        c.setFont("Vazir", 11)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.56,
                            K.shape("جزوهٔ مادر آناتومی دستگاه اعصاب"))
        c.setFillColor(K.HexColor("#94a3b8"))
        c.setFont("Vazir", 9.5)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.50,
                            K.shape(f"جلسهٔ {cfg['num']} از {cfg['of']} — {cfg['title']}"))
        c.setFont("VazirL", 8.4)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.44,
                            K.shape("تصویرها از Snell و Gray's · متن از جزوهٔ درس"))
    book.dark_page(painter)


# ---------------------------------------------------------------------- build
def build(out_path: Path, toc_pages: dict | None = None) -> PDFBook:
    cfg = ANAT_SESSIONS[SESSION]
    outline = load_json(CONTENT / "outline" / cfg["outline"])

    content: dict[str, list] = {}
    for fname in cfg["content"]:
        for topic in load_json(CONTENT / fname):
            content[topic["topic_id"]] = topic["blocks"]

    plates = [b for blocks in content.values() for b in blocks if b.get("type") == "plate"]
    stats = {
        "plates": len(plates),
        "lec": sum(1 for b in plates if b.get("book") == "lecture"),
        "snell": sum(1 for b in plates if b.get("book") == "snell"),
        "grays": sum(1 for b in plates if b.get("book") == "grays"),
    }

    book = PDFBook(out_path, f"جزوهٔ مادر آناتومی دستگاه اعصاب — جلسهٔ {cfg['num']}",
                   footer=FOOTER, subject="جزوهٔ مادر — آناتومی دستگاه اعصاب")
    book.dark_page(lambda b: cover_page(b, cfg), reuse_blank_page=True)
    front_matter(book, cfg, stats)
    toc_page(book, cfg, outline, toc_pages or {})

    n_tables = sum(1 for blocks in content.values() for b in blocks if b.get("type") == "table")
    n_paths = sum(1 for blocks in content.values() for b in blocks if b.get("type") == "path")
    divider(book, f"فصل {cfg['num']} · جلسهٔ {cfg['num']}", cfg["divider_title"],
            cfg["divider_sub"],
            [f"{fa(len(outline['topics']))} مبحث · {fa(stats['plates'])} قاب تصویر "
             f"({fa(stats['snell'])} Snell · {fa(stats['grays'])} Gray's · {fa(stats['lec'])} جزوه)",
             f"{fa(n_tables)} جدول · {fa(n_paths)} مسیر گام‌به‌گام",
             "هر ادعا برچسب بررسی‌شده / بررسی‌نشده / غیرقابل‌دسترسی دارد",
             "پیش‌نویس ویرایشی — بازبینی علمی در جریان"])
    session_intro(book, cfg, outline, stats)

    for i, t in enumerate(outline["topics"], start=1):
        topic_head(book, t, i, len(outline["topics"]))
        render_blocks(book, content.get(t["topic_id"], []))

    summary(book, content)
    next_steps(book, cfg)
    back_page(book, cfg)
    book._furniture()
    book.c.save()
    return book


def drop_trailing_blank_page(path: Path) -> int | None:
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(path))
    if not reader.pages:
        return None
    last = reader.pages[-1]
    has_text = bool((last.extract_text() or "").strip())
    try:
        has_images = bool(last.images)
    except Exception:
        has_images = False
    if has_text or has_images:
        return len(reader.pages)
    writer = PdfWriter()
    for page in reader.pages[:-1]:
        writer.add_page(page)
    writer.add_metadata(reader.metadata or {})
    with path.open("wb") as fh:
        writer.write(fh)
    return len(writer.pages)


def main() -> None:
    global SESSION
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="s01", choices=sorted(ANAT_SESSIONS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--force", action="store_true",
                    help="allow overwriting an already published session PDF")
    args = ap.parse_args()

    SESSION = args.session
    cfg = ANAT_SESSIONS[SESSION]
    out = Path(args.out) if args.out else REPO / "pdf" / cfg["pdf_name"]
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not args.force:
        raise SystemExit(
            f"{out} already exists — a published session PDF is never replaced by "
            "another session. Pass --force only to re-render this same session.")

    pages: dict[str, int] = {}
    book = None
    for attempt in range(4):
        book = build(out, pages)
        if book.heading_pages == pages:
            print(f"stable after {attempt + 1} pass(es): {book.page} pages")
            break
        pages = dict(book.heading_pages)
    else:
        raise SystemExit("TOC pagination did not converge")

    after = drop_trailing_blank_page(out)
    if after is not None and after != book.page:
        print(f"dropped empty trailing page: {book.page} -> {after} pages")
    if book.missing_assets:
        print("MISSING ASSETS:", *book.missing_assets, sep="\n  ")
    print(f"written: {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()

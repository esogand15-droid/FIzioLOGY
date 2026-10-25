"""Build HumsYar_Neuro_Special_Senses_Master.pdf from the authored JSON content.

Usage
-----
    /home/user/.venv/bin/python render/build_master.py [--out PATH] [--only-front]

The build is a two-pass layout: pass 1 discovers the page of every anchor, pass 2
writes the table of contents with those numbers.  Because the TOC always emits
the same number of rows, pagination is stable between passes; the script asserts
that and fails loudly instead of shipping a wrong TOC.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pdf_kit as K
from pdf_kit import CONTENT_W, MM, PDFBook, TextStyle

REPO = Path(__file__).resolve().parents[1]
CONTENT = REPO / "content" / "sessions"
OUTLINE = REPO / "content" / "outline" / "s01_topics.json"
GUYTON = REPO / "work" / "references" / "guyton_ch45_excerpts.json"

GUYTON_ED = "Guyton & Hall, Textbook of Medical Physiology, 12th ed. (2011)"

SOURCE_1404 = "جزوهٔ مهر ۱۴۰۴ (دکتر خوارزمی)"
SOURCE_1402 = "جزوهٔ ورودی بهمن ۱۴۰۲"

# --------------------------------------------------------------------- helpers
def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def guyton_chunks(gsections: dict, keys, max_chunks: int = 4, per_chunk: int = 3):
    """Group verbatim Guyton sentences into display chunks.

    Sentences come from ``guyton_ch45_excerpts.json`` (line wrapping undone, page
    of every sentence recorded).  Nothing is rewritten here: sentences are only
    grouped, so each chunk can carry the printed page of its first sentence.
    """
    sents: list[dict] = []
    for key in keys:
        sec = gsections.get(key)
        if not sec or not sec.get("found"):
            continue
        sents.extend(sec.get("sentences", []))
    chunks = []
    for i in range(0, len(sents), per_chunk):
        group = sents[i:i + per_chunk]
        if not group:
            continue
        chunks.append({"page": group[0]["page"],
                       "text": " ".join(x["text"] for x in group),
                       "page_end": group[-1]["page"]})
    return chunks[:max_chunks]


def fa(n) -> str:
    return str(n).translate(K.FA_DIGITS)


def tno(tid: str) -> str:
    """``s01-T06`` -> Persian topic number, so no internal code reaches the page."""
    return fa(int(str(tid).split("-")[-1].lstrip("T")))


def page_range(pages) -> str:
    return "، ".join(fa(p) for p in pages)


def cover_page(book: PDFBook) -> None:
    c = book.c
    c.setFillColor(K.TEAL_L)
    c.setFont("VazirM", 11)
    c.drawCentredString(K.A4W / 2, K.A4H * 0.86, K.shape("HumsYar · جزوهٔ مادر"))
    c.setFillColor(K.HexColor("#ffffff"))
    c.setFont("VazirB", 30)
    c.drawCentredString(K.A4W / 2, K.A4H * 0.60, K.shape("فیزیولوژی اعصاب"))
    c.drawCentredString(K.A4W / 2, K.A4H * 0.535, K.shape("و حواس ویژه"))
    c.setFillColor(K.TEAL_L)
    c.setFont("Vazir", 14)
    c.drawCentredString(K.A4W / 2, K.A4H * 0.455, K.shape("جزوهٔ مادر — نسخهٔ کاری تیم یادداشت‌نویسی"))
    c.setStrokeColor(K.Color(37 / 255, 99 / 255, 235 / 255))
    c.setLineWidth(1.4)
    c.line(K.A4W * 0.30, K.A4H * 0.42, K.A4W * 0.70, K.A4H * 0.42)
    c.setFillColor(K.HexColor("#94a3b8"))
    c.setFont("Vazir", 10)
    lines = [
        "دکتر خوارزمی — دانشکدهٔ پزشکی",
        "جلسهٔ ۱ (از ۱۶): سازمان‌دهی سیستم عصبی، نورون، نوروترانسمیترها",
        "نسخهٔ ۰٫۱ — فقط جلسهٔ ۱ تألیف شده است",
    ]
    yy = K.A4H * 0.355
    for t in lines:
        c.drawCentredString(K.A4W / 2, yy, K.shape(t))
        yy -= 18
    c.setFont("VazirL", 8.5)
    c.setFillColor(K.HexColor("#64748b"))
    c.drawCentredString(K.A4W / 2, K.A4H * 0.12,
                        K.shape("سند کاری برای تیم هشت‌نفرهٔ یادداشت‌نویسی — انتشار عمومی نیست"))


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
        c.setFont("Vazir", 12)
        c.drawRightString(K.A4W - K.M_RIGHT - 4, yy - 6, K.shape(subtitle))
        c.setFillColor(K.HexColor("#94a3b8"))
        c.setFont("Vazir", 9.5)
        yy -= 40
        for b_ in bullets:
            c.drawRightString(K.A4W - K.M_RIGHT - 4, yy, K.shape("• " + b_))
            yy -= 17
    book.dark_page(painter)


# --------------------------------------------------------------------- sections
def front_matter(book: PDFBook, outline: dict) -> None:
    book.h1("این سند چیست و چطور از آن استفاده کنیم", anchor="front-colophon",
            kicker="شناسنامه")
    book.paragraph(
        "این «جزوهٔ مادر» سند مرجع تیم یادداشت‌نویسی درس فیزیولوژی اعصاب و حواس ویژه است؛ "
        "نه جزوهٔ نهایی دانشجویی و نه جایگزین کتاب. هدفش سه چیز است: (۱) نگه‌داشتن تمام "
        "محتوای منابع (جزوه‌های ۱۴۰۲ و ۱۴۰۴، اسلایدها، شکل‌ها، جداول و متن گایتون) در یک "
        "ساختار واحد؛ (۲) دادن نقشهٔ دقیق مباحث و پیش‌نیازها به تیم، تا کار نوشتن قابل تقسیم "
        "و قابل بازبینی باشد؛ (۳) روشن نگه‌داشتن این نکته که هر جمله از کجا آمده است.")
    book.h3("این جزوه برای چه کسی نوشته شده")
    book.bullets([
        "برای هشت نفر نویسندهٔ یادداشت که هر کدام یک یا چند مبحث را می‌نویسند و باید بدانند "
        "مبحثش از کجا شروع می‌شود، به چه چیزی تکیه می‌کند و کجا تمام می‌شود.",
        "برای بازبین علمی، که باید بتواند با یک نگاه ببیند کدام جمله از استاد است، کدام از "
        "جزوهٔ دانشجویی و کدام ترجمهٔ تحریریهٔ ما.",
        "برای دانشجوی سال‌بالاتر که این متن را در جلسهٔ درس می‌خواند و باید جای نوشتن، جای "
        "شکل و جای مرور را روی کاغذ پیدا کند.",
    ])

    book.h2("منابعی که این جزوه بر آن‌ها بنا شده", anchor="front-sources")
    book.table(
        ["منبع", "چه چیزی از آن در این جزوه آمده", "شکل ارجاع در متن"],
        [
            ["جزوهٔ مهر ۱۴۰۴ — دکتر خوارزمی",
             "متن پایهٔ همهٔ مباحث؛ ترتیب و دسته‌بندی مطالب هم از آن گرفته شده است.",
             "«جزوهٔ مهر ۱۴۰۴، ص …»"],
            ["جزوهٔ بهمن ۱۴۰۲ (نوشتهٔ دانشجوی سال‌بالاتر)",
             "توضیح‌های ساده‌تر، مثال‌های سر کلاس و شکل‌های دست‌ساز.",
             "«جزوهٔ بهمن ۱۴۰۲، ص …»"],
            ["اسلایدهای انگلیسی کلاس",
             "جدول‌ها، فهرست‌ها و شکل‌های اصلی درس (منبع اولویت‌دار برای شکل‌ها).",
             "«اسلاید کلاس، ص …»"],
            [GUYTON_ED,
             "متن اصلی انگلیسی فصل ۴۵، همراه با ترجمهٔ روان تحریریه در همان کادر.",
             "«گایتون، فصل ۴۵، ص …»"],
            ["جزوات تکمیلی دکتر قدیری",
             "منبع کمکی برای جلسات بعد؛ در این نسخه استفاده نشده است.",
             "—"],
        ],
        widths=[CONTENT_W * 0.34, CONTENT_W * 0.40, CONTENT_W * 0.26],
        size=8.3,
        caption="جدول ۰-۱ — منابع این جلسه و شکل ارجاع به آن‌ها در متن.",
        src="فهرست منابع درس و نسخهٔ چاپی گایتون")

    book.h2("چطور از این جزوه استفاده کنیم", anchor="front-how")
    book.numbered([
        "شناسنامهٔ آموزشی هر مبحث را بخوانید (چرا مهم است، اهداف یادگیری، پیش‌نیاز، اصطلاحات "
        "کلیدی). اگر پیش‌نیاز ضروری را نمی‌دانید، اول همان مبحث را بخوانید.",
        "متن مبحث را بخوانید؛ در پایان هر پاراگراف، منبع و صفحهٔ همان جمله نوشته شده است. "
        "توضیح آموزشی ما با جملهٔ منبع یکی نیست و همیشه جدا نوشته می‌شود.",
        "شکل‌ها را ببینید؛ زیر هر شکل، منبع و یک توضیح فارسی آمده تا بدانید شکل چه چیزی را "
        "نشان می‌دهد و به کدام بخش درس مربوط است.",
        "جمع‌بندی مبحث را مرور کنید، سپس در کادرهای خالی همان مبحث یادداشت خودتان را بنویسید.",
        "برگهٔ تحویل پایان مبحث را پر کنید؛ بی آن، مبحث تحویل‌شده حساب نمی‌شود.",
    ])
    book.callout(
        "این نسخه پیش‌نویس ویرایشی است: جمله‌ها به منبع و صفحه گره خورده‌اند، اما درستی علمی "
        "آن‌ها هنوز جمله‌به‌جمله تأیید نشده است. هر جا جمله‌ای با منبع اصلی نمی‌خواند یا "
        "اصطلاحی مشکوک بود، همان را در برگهٔ تحویل علامت بزنید؛ ما عمداً چیزی را پاک نمی‌کنیم "
        "تا اختلاف دیده شود.", kind="warn", title="وضعیت این نسخه")
    book.h3("دو نکتهٔ ویرایشی که در خواندن به آن برمی‌خورید")
    book.bullets([
        "املای چند واژه در جزوهٔ ۱۴۰۴ اشتباه تایپ شده است (مثلاً «اطالعات» به‌جای «اطلاعات» یا "
        "«عضالت» به‌جای «عضلات»). در این جزوه املای درست نوشته شده؛ اگر جایی از منبع عیناً "
        "نقل شده و املا نادرست است، در همان جمله اصلاح شده است.",
        "صفحه‌های جزوهٔ ۱۴۰۲ با خواندن تصویر همان صفحه به متن فارسی برگردانده شده‌اند. اگر "
        "عبارتی روی صفحه ناخوانا یا بریده بوده، به‌جای حدس زدن، در متن «…» گذاشته شده و در "
        "همان مبحث یادداشت شده است.",
    ])


def work_division(book: PDFBook, outline: dict) -> None:
    book.h1("نقشهٔ مباحث و پیش‌نیازها", anchor="front-workplan",
            kicker="راهنمای تیم")
    book.paragraph(
        "هر مبحث یک واحد تحویل است: متن، شکل‌ها، جمع‌بندی، کادرهای یادداشت و یک برگهٔ تحویل. "
        "ترتیب کار باید ترتیب پیش‌نیازها را رعایت کند؛ مبحثی که پیش‌نیاز «ضروری» آن نوشته "
        "نشده، نباید بسته شود.")
    rows = []
    for t in outline["topics"]:
        pre = "، ".join(f"مبحث {tno(p['topic_id'])} ({p.get('level', '')})"
                        for p in t["prerequisites"]) or "—"
        rows.append([tno(t["topic_id"]), t["title"],
                     page_range(t["notes1402"]), pre, "⋯"])
    book.table(["#", "مبحث", "ص ۱۴۰۲", "پیش‌نیاز", "نویسنده"],
               rows, widths=[CONTENT_W * 0.07, CONTENT_W * 0.55, CONTENT_W * 0.14,
                             CONTENT_W * 0.15, CONTENT_W * 0.09],
               size=8.0,
               caption="جدول ۰-۲ — ستون «نویسنده» عمداً خالی است و در جلسهٔ کاری تیم پر می‌شود.",
               src="نقشهٔ مباحث همین جزوه")
    book.h3("قواعد نوشتن و تحویل")
    book.numbered([
        "جمله‌ها تا حد امکان با همان واژگان منبع نوشته می‌شوند؛ بازنویسی فقط برای روان‌خوانی است "
        "و نباید معنا را عوض کند.",
        "توضیح آموزشی ما باید از نقل منبع جدا و قابل تشخیص باشد: جملهٔ استاد، جملهٔ جزوهٔ "
        "دانشجویی، متن گایتون و ترجمهٔ تحریریه هر کدام جای خودشان را دارند.",
        "هیچ عدد، صفحه، آمار یا نقل‌قولی از خودمان ساخته نمی‌شود؛ ارجاع هر جمله در پایان "
        "همان پاراگراف می‌آید.",
        "شکل‌ها فقط از منابع همین درس می‌آیند، با نام و شمارهٔ صفحهٔ همان منبع، و زیر هر شکل "
        "یک توضیح فارسی می‌نویسیم که بگوید شکل چه چیزی را نشان می‌دهد.",
        "اختلاف منابع پنهان نمی‌شود؛ در همان مبحث، در کادر «نیازمند بررسی علمی» ثبت می‌شود.",
        "کادرهای یادداشت خالی می‌مانند؛ محتوای آن‌ها را نویسندهٔ مبحث یا دانشجو پر می‌کند.",
        "پیش از تحویل، مبحث یک‌بار در نسخهٔ چاپی خوانده می‌شود: تیترها، ارجاع‌ها، شکل‌ها و "
        "برگهٔ تحویل. بعد از آن مبحث تحویل‌شده است.",
    ])
    book.callout("تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر برای مباحث ساختاری (۱ تا ۵)، "
                 "سه نفر برای نوروترانسمیترها (۶ تا ۱۰)، دو نفر برای گیرنده‌ها و سم‌شناسی "
                 "(۱۱ تا ۱۳)، یک نفر برای هم‌انتقالی و جمع‌بندی (۱۴) به‌همراه گردآوری. "
                 "این تقسیم پیشنهاد است، نه تصمیم نهایی تیم.", kind="info")


def chapter_opener(book: PDFBook, outline: dict, guyton: dict) -> None:
    book.h1(outline["title"], anchor="ch-s01", kicker="فصل ۱ · جلسهٔ ۱")
    book.paragraph(
        f"استاد: {outline['professor']} · ترم: {outline['term']} · "
        "منبع اصلی متن: جزوهٔ مهر ۱۴۰۴ (۴۲ صفحه، صفحات ۲ تا ۴۲) · "
        "منبع دوم: جزوهٔ ورودی بهمن ۱۴۰۲ (۱۳ صفحه).")
    book.h2("نقشهٔ درخت مباحث", anchor="ch-s01-tree")
    rows = []
    for t in outline["topics"]:
        sub = t["title"]
        rows.append([tno(t["topic_id"]), sub, page_range(t["notes1402"]), t["notes_size"]])
    book.table(["#", "مبحث", "ص ۱۴۰۲", "اندازه"], rows,
               widths=[CONTENT_W * 0.08, CONTENT_W * 0.68, CONTENT_W * 0.16, CONTENT_W * 0.08],
               size=8.2, caption="جدول ۱-۰ — چهارده مبحث جلسهٔ ۱. زیرمبحث‌ها در ابتدای هر مبحث فهرست شده‌اند.",
               src="نقشهٔ مباحث همین جزوه")
    book.h3("پیش‌نیازهای بین‌مبحثی (نقشهٔ وابستگی دوطرفه)")
    dep_rows = []
    for t in outline["topics"]:
        for p in t["prerequisites"]:
            dep_rows.append([tno(t["topic_id"]), tno(p["topic_id"]),
                             p.get("level", ""), p.get("reason", "")])
    book.table(["مبحث", "پیش‌نیاز", "سطح", "دلیل"], dep_rows,
               widths=[CONTENT_W * 0.10, CONTENT_W * 0.12, CONTENT_W * 0.16, CONTENT_W * 0.62],
               size=7.9,
               caption="جدول ۱-۰۲ — رابطهٔ پیش‌نیاز دوطرفه است: اگر مبحث ۱۱ به مبحث ۶ نیاز دارد، مبحث ۶ پس‌نیاز مبحث ۱۱ است.",
               src="نقشهٔ پیش‌نیازهای همین جزوه")
    book.callout(
        "هر مبحث در ابتدای خود یک شناسنامه دارد که پیش‌نیاز ضروری و پیش‌نیاز پیشنهادی‌اش را "
        "جدا نشان می‌دهد. اگر پیش‌نیاز ضروری نوشته نشده باشد، آن مبحث بسته نمی‌شود.",
        kind="info")


def topic_head(book: PDFBook, t: dict, idx: int, total: int, outline: dict) -> None:
    anchor = t["topic_id"]
    book.h2(t["title"], anchor=anchor)
    pre = "؛ ".join(f"مبحث {tno(p['topic_id'])} — {p.get('level','')}" for p in t["prerequisites"])
    meta = f"مبحث {fa(idx)} از {fa(total)} · صفحه‌های جزوهٔ ۱۴۰۴: {page_range(t.get('p1404', []))}"
    if pre:
        meta += " · پیش‌نیاز: " + pre
    book.paragraph(meta, TextStyle(size=8.3, color=K.MUTED, justify=False))
    book.spacer(2)


def render_blocks(book: PDFBook, blocks, gsections: dict) -> None:
    for b in blocks:
        kind = b.get("type")
        if kind == "p":
            book.paragraph(b["text"], TextStyle(space_after=2))
            book.source_line(b.get("src", ""))
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
            book.source_line(b.get("src", ""))
            book.spacer(2)
        elif kind == "figure":
            book.figure(REPO / b["asset"], b.get("caption", ""), b.get("src", ""))
        elif kind == "facsimile":
            book.facsimile(REPO / b["asset"], b.get("caption", ""), b.get("src", ""))
        elif kind == "note":
            sizes = {"small": 32, "medium": 48, "large": 68}
            book.note_box(sizes.get(b.get("size", "medium"), 48), b.get("title", "یادداشت عضو تیم"),
                          tag=b.get("tag", ""))
        elif kind == "idcard":
            book.label_card(b.get("title", "شناسنامهٔ آموزشی"), b.get("rows", []),
                            accent=K.TEAL, tint=K.TEAL_LL,
                            kicker=b.get("kicker", ""), footer=b.get("footer", ""))
        elif kind == "handoff":
            book.label_card(b.get("title", "برگهٔ تحویل مبحث"), b.get("rows", []),
                            accent=K.AMBER, tint=K.AMBER_BG,
                            kicker=b.get("kicker", ""), tick=True,
                            footer=b.get("footer", ""))
        elif kind == "guytonpair":
            prange = b.get("pages", "")
            cite = f"{GUYTON_ED}, Ch. {b.get('chapter', '45')}"
            if prange:
                cite += f", {prange}"
            book.guyton_pair(b.get("title", ""), cite, b["english"], b["fa"],
                             note=b.get("note", ""))
            book.spacer(4)
        elif kind == "guyton":
            keys = b.get("sections", [])
            paras = guyton_chunks(gsections, keys, max_chunks=b.get("max_chunks", 4), per_chunk=b.get("per_chunk", 3))
            if not paras:
                book.callout("بخش گایتون برای این مبحث یافت نشد.", kind="warn")
                continue
            pages = [p["page"] for p in paras if p.get("page")]
            if not pages:
                prange = ""
            elif min(pages) == max(pages):
                prange = f"p. {min(pages)}"
            else:
                prange = f"pp. {min(pages)}–{max(pages)}"
            book.guyton_block(b.get("title", ""), f"{GUYTON_ED}, Ch. 45, {prange}",
                              paras, note=b.get("note", ""),
                              max_paras=len(paras))
        else:
            raise ValueError(f"unknown block type: {kind}")


def roadmap(book: PDFBook, outline: dict, content: dict) -> None:
    book.h1("نقشهٔ جلسات آینده", anchor="roadmap", kicker="ادامهٔ کار")
    book.paragraph(
        "این نسخه فقط جلسهٔ ۱ را دارد. جلسه‌های زیر شناسایی شده‌اند و جزوه/اسلایدشان در "
        "اختیار تیم است؛ برای هر جلسه همان مسیر جلسهٔ ۱ تکرار می‌شود: شناسنامه، متن با ارجاع، "
        "شکل‌ها، جمع‌بندی، کادرهای یادداشت و برگهٔ تحویل.")
    book.h2("پوشش صفحه‌های جزوهٔ ۱۴۰۴ در این نسخه", anchor="roadmap-cover")
    per_page = {}
    for t in outline["topics"]:
        for p in t.get("p1404", []):
            per_page.setdefault(p, []).append(tno(t["topic_id"]))
    rows = []
    run_start = None
    run_topics = None
    for p in range(2, 44):
        topics_here = tuple(per_page.get(p, []))
        if p == 43 or topics_here != run_topics:
            if run_start is not None:
                span = fa(run_start) if run_start == p - 1 else f"{fa(run_start)}–{fa(p - 1)}"
                rows.append([span, "، ".join(run_topics) or "— بدون مبحث —"])
            run_start, run_topics = p, topics_here
        if p == 43:
            break
    book.table(["صفحهٔ جزوهٔ ۱۴۰۴", "مبحث این جزوه"], rows,
               widths=[CONTENT_W * 0.22, CONTENT_W * 0.78], size=7.6,
               caption="جدول ۲-۱ — همهٔ صفحه‌های ۲ تا ۴۲ جزوهٔ ۱۴۰۴ در دست‌کم یک مبحث پوشش داده شده‌اند.",
               src="مقایسهٔ صفحه‌به‌صفحهٔ جزوه و مباحث این سند")

    book.h2("جلسه‌های باقی‌مانده", anchor="roadmap-sessions")
    rows = [
        ["۲", "سیناپس، پتانسیل عمل و هدایت عصبی", "دارد", "دارد"],
        ["۳", "گیرنده‌های حسی و انتقال حس", "دارد", "دارد"],
        ["۴", "درد، رفلکس‌ها و مسیرهای صعودی", "دارد", "دارد"],
        ["۵", "حرکت، مخچه و عقده‌های قاعده‌ای", "دارد", "دارد"],
        ["۶", "سیستم اتونوم", "دارد", "دارد"],
        ["۷", "نخاع و مسیرهای نزولی", "دارد", "—"],
        ["۸–۱۲", "بینایی، شنوایی، تعادل، چشایی، بویایی", "دارد", "دارد"],
        ["۱۳–۱۴", "سیستم لیمبیک و حافظه", "دارد", "دارد"],
        ["۱۵", "اتونوم تکمیلی (جزوهٔ مستقل)", "دارد", "جزئی"],
        ["۱۶", "پری لب", "دارد", "—"],
    ]
    book.table(["جلسه", "موضوع", "جزوهٔ ۱۴۰۴", "جزوهٔ ۱۴۰۲"], rows,
               widths=[CONTENT_W * 0.10, CONTENT_W * 0.50, CONTENT_W * 0.20,
                       CONTENT_W * 0.20],
               size=8.0,
               caption="جدول ۲-۲ — ستون‌های «جزوهٔ ۱۴۰۴» و «جزوهٔ ۱۴۰۲» می‌گویند منبع آن جلسه در اختیار تیم هست یا نه.",
               src="فهرست منابع درس")


def back_page(book: PDFBook) -> None:
    def painter(b: PDFBook) -> None:
        c = b.c
        c.setFillColor(K.HexColor("#ffffff"))
        c.setFont("VazirB", 18)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.60, K.shape("پایان نسخهٔ ۰٫۱"))
        c.setFillColor(K.TEAL_L)
        c.setFont("Vazir", 11)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.55,
                            K.shape("جلسهٔ ۱ تألیف شد؛ اجرای جلسهٔ ۲ منوط به دستور تیم است"))
        c.setFillColor(K.HexColor("#64748b"))
        c.setFont("VazirL", 9)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.22,
                            K.shape("HumsYar · سند کاری — بدون بازبینی علمی نهایی"))
    book.dark_page(painter)


# --------------------------------------------------------------------- assembly
def build(out_path: Path, toc_pages: dict[str, int] | None = None) -> PDFBook:
    outline = load_json(OUTLINE)
    guyton = load_json(GUYTON)["sections"]

    content: dict[str, list] = {}
    for fname in ("s01_a.json", "s01_b.json", "s01_c.json"):
        for topic in load_json(CONTENT / fname):
            content[topic["topic_id"]] = topic["blocks"]
    # page map for the topic header line
    page_map = {
        "s01-T01": [2, 3], "s01-T02": [3, 4, 5, 6], "s01-T03": [6, 7, 8, 9],
        "s01-T04": [9, 10, 11, 12, 13, 14], "s01-T05": [14, 15, 16, 17, 18],
        "s01-T06": [18, 19, 20, 21, 22, 23], "s01-T07": [23, 24, 25],
        "s01-T08": [25, 26, 27], "s01-T09": [27, 28], "s01-T10": [28, 29],
        "s01-T11": [29, 30, 31, 32], "s01-T12": [32, 33, 34, 35, 36],
        "s01-T13": [36, 37, 38], "s01-T14": [38, 39, 40, 41, 42],
    }
    for t in outline["topics"]:
        t["p1404"] = page_map.get(t["topic_id"], [])

    book = PDFBook(out_path, "جزوهٔ مادر فیزیولوژی اعصاب و حواس ویژه — نسخهٔ ۰٫۱")
    book.dark_page(cover_page, reuse_blank_page=True)

    front_matter(book, outline)
    work_division(book, outline)

    # ---------------- TOC (numbers come from the previous pass)
    toc_pages = toc_pages or {}
    book.new_page()
    book.h1("فهرست مطالب", anchor="toc", kicker="راهنمای سند")
    book.paragraph("شمارهٔ روبه‌روی هر سطر، شمارهٔ صفحهٔ همین سند است.",
                   TextStyle(size=9, color=K.MUTED))
    toc_rows = [
        ("۰", "شناسنامه و راهنمای استفاده", "front-colophon", 0),
        ("۰", "نقشهٔ مباحث و پیش‌نیازها", "front-workplan", 0),
        ("۱", "فصل ۱ — جلسهٔ ۱: سازمان‌دهی تا نوروترانسمیترها", "ch-s01", 0),
    ]
    for i, t in enumerate(outline["topics"], start=1):
        toc_rows.append((f"{i:02d}", t["title"], t["topic_id"], 1))
    toc_rows += [
        ("۲", "نقشهٔ جلسات آینده", "roadmap", 0),
        ("۲", "پوشش صفحه‌های جزوهٔ ۱۴۰۴", "roadmap-cover", 1),
        ("۲", "جلسه‌های باقی‌مانده", "roadmap-sessions", 1),
    ]
    for num, title, anchor, indent in toc_rows:
        pg = toc_pages.get(anchor)
        book.toc_row(num, title, fa(pg) if pg else "—",
                     indent=indent * 18, accent=K.TEAL if indent == 0 else K.BLUE)

    # ---------------- chapter
    n_figs = sum(1 for blocks in content.values() for b in blocks
                 if b.get("type") == "figure")
    n_guy = sum(1 for blocks in content.values() for b in blocks
                if b.get("type") in ("guyton", "guytonpair"))
    divider(book, "فصل ۱ · جلسهٔ ۱", "نوروفیزیولوژی:\nاز سازمان‌دهی تا\nنوروترانسمیترها",
            "دکتر خوارزمی · مهر ۱۴۰۴ + بهمن ۱۴۰۲",
            [f"{fa(len(outline['topics']))} مبحث · {fa(n_figs)} شکل و جدول از منابع درس · "
             f"{fa(n_guy)} کادر گایتون با ترجمه",
             "صفحه‌های ۲ تا ۴۲ جزوهٔ ۱۴۰۴ و ۱۳ صفحهٔ ۱۴۰۲",
             "پیش‌نویس ویرایشی — بازبینی علمی در جریان"])
    chapter_opener(book, outline, {"sections": guyton})

    for i, t in enumerate(outline["topics"], start=1):
        topic_head(book, t, i, len(outline["topics"]), outline)
        render_blocks(book, content.get(t["topic_id"], []), guyton)

    roadmap(book, outline, content)
    back_page(book)
    book._furniture()
    book.c.save()
    return book


def drop_trailing_blank_page(path: Path) -> int | None:
    """Remove a completely empty page at the end of the PDF (if any).

    ``dark_page()`` always opens a fresh page after it finishes so that the
    following content has a clean frame; when the back cover is the last element
    of the book that leaves one empty page.  Removing it keeps the page count
    honest (and the TOC numbers match the printed numbers).
    """
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(path))
    if not reader.pages:
        return None
    last = reader.pages[-1]
    has_text = bool((last.extract_text() or "").strip())
    has_images = False
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
    if reader.outline:
        try:
            writer.add_outline_item_destination if False else None
        except Exception:
            pass
    with path.open("wb") as fh:
        writer.write(fh)
    return len(writer.pages)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "HumsYar_Neuro_Special_Senses_Master.pdf"))
    args = ap.parse_args()
    out = Path(args.out)

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

    pages_after = drop_trailing_blank_page(out)
    if pages_after is not None and pages_after != book.page:
        print(f"dropped empty trailing page: {book.page} -> {pages_after} pages")

    if book.missing_assets:
        print("MISSING ASSETS:", *book.missing_assets, sep="\n  ")
    print("written:", out, out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()

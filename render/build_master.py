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

STATUS_ROWS = [
    ["طراحی‌شده", "ساختار، فهرست و نقشهٔ مباحث نوشته شده؛ محتوای علمی هنوز تولید نشده.",
     "همهٔ جلسات ۱ تا ۱۶"],
    ["پیاده‌سازی‌شده", "متن/شکل از منبع استخراج شده و در ساختار نشسته، اما هنوز روی خروجی نهایی بازبینی نشده.",
     "جلسهٔ ۱"],
    ["آزمون دودی (smoke test)", "کد ساخت PDF با محتوای واقعی یک‌بار اجرا و صفحه‌به‌صفحه دیده شده.",
     "همین سند"],
    ["اجرا روی فایل واقعی", "کل زنجیره روی فایل‌های اصلی منبع (نه نمونه) اجرا شده و خروجی متن/تصویر بررسی شده.",
     "جلسهٔ ۱"],
    ["بازبینی علمی", "یک عضو تیم با رفرنس، درستی هر جمله را تأیید کرده است.", "هنوز آغاز نشده"],
    ["آمادهٔ ادغام", "چهار شرط بالا + بازبینی علمی + رفع تعارض‌ها.", "هنوز آغاز نشده"],
]


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
        "محتوای منابع (جزوه‌های ۱۴۰۲ و ۱۴۰۴، اسلایدها، شکل‌ها، جداول و رفرنس گایتون) در یک "
        "ساختار واحد؛ (۲) دادن نقشهٔ دقیق مباحث و پیش‌نیازها به تیم، تا کار نوشتن قابل تقسیم "
        "و قابل بازبینی باشد؛ (۳) ثبت شفاف آنچه هنوز بررسی علمی نشده است.")
    book.h3("دامنهٔ این نسخه (نسخهٔ ۰٫۱)")
    book.bullets([
        "تألیف‌شده: جلسهٔ ۱ — سازمان‌دهی سیستم عصبی، اجزای سلولی و نورون، نوروترانسمیترها و هم‌انتقال‌دهنده‌ها (۱۴ مبحث).",
        "طراحی‌شده اما تألیف‌نشده: جلسات ۲ تا ۱۶ (فقط در فهرست و نقشهٔ کلی سند آمده‌اند).",
        "دادهٔ خام استخراج‌شده (متن، شکل، بازبینی) برای جلسات دیگر موجود است، اما هیچ متنی از آن‌ها وارد این سند نشده است.",
    ])
    book.callout(
        "هیچ بخشی از این سند «بازبینی علمی» نشده است. همهٔ بخش‌ها در سطح «پیاده‌سازی‌شده» و "
        "«اجرا روی فایل واقعی» هستند؛ یعنی متن به منبع خود گره خورده و صفحه‌اش ثبت است، اما "
        "درستی علمی جمله‌به‌جمله هنوز تأیید نشده است.", kind="warn", title="وضعیت فعلی سند")

    book.h2("منابع و نسخه‌ها", anchor="front-sources")
    book.table(
        ["منبع", "نقش در این سند", "حجم / وضعیت"],
        [
            ["جزوهٔ مهر ۱۴۰۴ — دکتر خوارزمی", "منبع اصلی متن جلسهٔ ۱", "۴۲ صفحه؛ لایهٔ متنی پس از اصلاح فنی قابل استناد"],
            ["جزوهٔ ورودی بهمن ۱۴۰۲", "منبع دوم (ادغام جزئیات و شکل‌ها)", "۱۳ صفحه؛ لایهٔ متنی/OCR غیرقابل استناد ← از تصویر صفحه استفاده شده"],
            [GUYTON_ED, "جای‌گذاری متن اصلی در مبحث متناظر", "بخش‌های فصل ۴۵ استخراج و صفحه‌گذاری شده"],
            ["ترجمهٔ فارسی گایتون (جلد اول)", "ارجاع فارسی — در این مرحله در دسترس نیست", "فایل فقط LFS pointer بود؛ دانلود نشده"],
            ["جزوات تکمیلی دکتر قدیری", "منبع کمکی (برای جلسات بعد)", "خارج از دامنهٔ این نسخه"],
        ],
        widths=[CONTENT_W * 0.36, CONTENT_W * 0.34, CONTENT_W * 0.30],
        size=8.3,
        caption="جدول ۰-۱ — منابع فعال این نسخه. نسخهٔ فارسی گایتون عمداً دانلود نشده است تا حجم غیرلازم منتقل نشود.",
        src="INVENTORY.md و work/source_manifest.json")

    book.h2("سطوح وضعیت کار", anchor="front-status")
    book.paragraph("در این سند ادعای «انجام شد» فقط با یکی از این شش برچسب بیان می‌شود. "
                   "برچسب هر بخش در جدول پوشش (پیوست پ) قابل ردیابی است.")
    book.table(["برچسب", "معنای دقیق", "در این نسخه"],
               STATUS_ROWS, widths=[CONTENT_W * 0.20, CONTENT_W * 0.58, CONTENT_W * 0.22],
               size=8.2, caption="جدول ۰-۲ — تعریف سطوح وضعیت (QA levels).")

    book.h2("اصول ویرایش که تیم ملزم به رعایت آن است", anchor="front-rules")
    book.bullets([
        "جمله‌ها تا حد امکان با همان واژگان منبع نوشته می‌شوند؛ بازنویسی فقط برای روان‌خوانی است و نباید معنا را تغییر دهد.",
        "هر جملهٔ محتوایی یک ارجاع صفحه دارد؛ جملهٔ بدون ارجاع باید حذف یا با «[نیازمند منبع]» علامت‌گذاری شود.",
        "هیچ عدد، صفحه، هش، آمار یا نقل‌قولی از خودمان ساخته نمی‌شود.",
        "متن گایتون هرگز به استاد نسبت داده نمی‌شود و همیشه در کادر جداگانهٔ ارجاع‌دار می‌آید.",
        "اختلاف بین نسخهٔ ۱۴۰۲ و ۱۴۰۴ حل نمی‌شود؛ ثبت می‌شود (پیوست ث).",
        "کادر «یادداشت عضو تیم» دست‌نخورده و خالی می‌ماند؛ محتوای آن را نویسندهٔ مبحث پر می‌کند.",
    ])


def work_division(book: PDFBook, outline: dict) -> None:
    book.h1("نقشهٔ تقسیم کار و پیش‌نیازها", anchor="front-workplan",
            kicker="راهنمای تیم")
    book.paragraph(
        "هر مبحث یک واحد تحویل (deliverable) است: یک فایل JSON کوچک با شناسهٔ ثابت، که "
        "ساخت PDF را می‌سازد. ترتیب کار باید ترتیب پیش‌نیازها را رعایت کند؛ مبحثی که "
        "پیش‌نیاز «ضروری» آن نوشته نشده، نباید بسته شود.")
    rows = []
    for t in outline["topics"]:
        pre = "، ".join(f"{p['topic_id'].split('-')[-1]} ({p.get('level', '')})"
                        for p in t["prerequisites"]) or "—"
        rows.append([t["topic_id"].split("-")[-1], t["title"],
                     page_range(t["notes1402"]), pre, t["notes_size"], "⋯"])
    book.table(["#", "مبحث", "ص ۱۴۰۲", "پیش‌نیاز", "اندازه", "نویسنده"],
               rows, widths=[CONTENT_W * 0.06, CONTENT_W * 0.46, CONTENT_W * 0.13,
                             CONTENT_W * 0.19, CONTENT_W * 0.08, CONTENT_W * 0.08],
               size=8.0,
               caption="جدول ۰-۳ — ستون «نویسنده» عمداً خالی است و در جلسهٔ کاری تیم پر می‌شود.",
               src="content/outline/s01_topics.json")
    book.h3("قواعد چرخهٔ کار (برای هر جلسه، یک چرخه)")
    book.numbered([
        "مبحث را از فایل JSON بردارید؛ فقط همان فایل را ویرایش کنید تا تعارض git پیش نیاید.",
        "هر بلوک متن باید فیلد src (منبع + صفحه) داشته باشد؛ بلوک بدون src در ساخت PDF رد می‌شود.",
        "شکل‌ها فقط از images/INDEX.json و با نام فایل دقیق ارجاع داده شوند.",
        "پیش از تحویل: ساخت PDF را اجرا کنید و همان مبحث را در خروجی ببینید (چک‌لیست چهار موردی).",
        "در پایان جلسه: PROJECT_STATUS.md به‌روزرسانی، کامیت، و توقف تا دستور بعدی.",
    ])
    book.callout("تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر برای مباحث ساختاری (۱ تا ۵)، "
                 "سه نفر برای نوروترانسمیترها (۶ تا ۱۰)، دو نفر برای گیرنده‌ها و سم‌شناسی "
                 "(۱۱ تا ۱۳)، یک نفر برای هم‌انتقالی و جمع‌بندی (۱۴) + گردآوری. "
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
        rows.append([t["topic_id"].split("-")[-1], sub, page_range(t["notes1402"]), t["notes_size"]])
    book.table(["#", "مبحث (سطح ۲)", "ص ۱۴۰۲", "اندازه"], rows,
               widths=[CONTENT_W * 0.08, CONTENT_W * 0.68, CONTENT_W * 0.16, CONTENT_W * 0.08],
               size=8.2, caption="جدول ۱-۰ — مباحث جلسهٔ ۱. زیرمبحث‌ها (سطح ۳) در ابتدای هر مبحث فهرست شده‌اند.")
    book.h3("پیش‌نیازهای بین‌مبحثی (نقشهٔ وابستگی دوطرفه)")
    dep_rows = []
    for t in outline["topics"]:
        for p in t["prerequisites"]:
            dep_rows.append([t["topic_id"].split("-")[-1], p["topic_id"].split("-")[-1],
                             p.get("level", ""), p.get("reason", "")])
    book.table(["مبحث", "پیش‌نیاز", "سطح", "دلیل"], dep_rows,
               widths=[CONTENT_W * 0.10, CONTENT_W * 0.12, CONTENT_W * 0.16, CONTENT_W * 0.62],
               size=7.9,
               caption="جدول ۱-۰۲ — هر ردیف در نقشهٔ دوطرفه هم دیده می‌شود: اگر T11 به T06 نیاز دارد، T06 «پس‌نیاز» T11 است.",
               src="content/outline/s01_topics.json")
    book.callout(
        "هر مبحث در متن، پیش‌نیازهایش را در جعبهٔ بالای خود نشان می‌دهد؛ همین اطلاعات در "
        "پیوست پ برای کنترل پوشش استفاده می‌شود.", kind="info")


def topic_head(book: PDFBook, t: dict, idx: int, total: int, outline: dict) -> None:
    anchor = t["topic_id"]
    book.h2(t["title"], anchor=anchor)
    pre = "؛ ".join(f"{p['topic_id'].split('-')[-1]} — {p.get('level','')}" for p in t["prerequisites"])
    meta = f"مبحث {fa(idx)} از {fa(total)} · صفحات ۱۴۰۴: {page_range(t.get('p1404', []))}"
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


def appendices(book: PDFBook, outline: dict, guyton: dict, content: dict) -> None:
    book.h1("پیوستها", anchor="apx", kicker="مرجع و کنترل کیفیت")

    book.h2("پیوست الف — نقشهٔ ارجاع گایتون", anchor="apx-A")
    book.paragraph("هر بخش گایتون که در متن استفاده شده، با همان شناسه و همان محدودهٔ صفحه در "
                   "این جدول آمده است. صفحه‌ها «صفحهٔ چاپی» نسخهٔ انگلیسی (چاپ دوازدهم، ۲۰۱۱) "
                   "هستند و از نشانگرهای صفحهٔ لایهٔ متنی همان چاپ گرفته شده‌اند. نگاشت «شمارهٔ "
                   "صفحهٔ فایل PDF» هنوز تولید نشده و عمداً خالی است؛ نسخهٔ فارسی گایتون هم "
                   "(فایل LFS) در دسترس نبوده و ارجاع فارسی افزوده نشده است.")
    rows = []
    for key, sec in guyton["sections"].items():
        if not sec.get("found"):
            rows.append([key, sec.get("heading", ""), "—", "—", "۰"])
            continue
        used = sorted({t["topic_id"].split("-")[-1] for t in outline["topics"]
                       if key in (t.get("guyton") or [])})
        rows.append([key, sec["heading"],
                     f"{sec['page_start']}–{sec['page_end']}",
                     "، ".join(used) or "—", fa(len(sec["sentences"]))])
    book.table(["شناسه", "عنوان بخش", "ص چاپی", "استفاده در", "تعداد پاراگراف"], rows,
               widths=[CONTENT_W * 0.16, CONTENT_W * 0.42, CONTENT_W * 0.12,
                       CONTENT_W * 0.16, CONTENT_W * 0.14],
               size=8.0,
               caption="جدول پ-الف — نگاشت بخش‌های گایتون. ستون آخر تعداد جمله‌های نقل‌شده/موجود در هر بخش است.",
               src="work/references/guyton_ch45_excerpts.json")

    book.h2("پیوست ب — پوشش صفحات جزوهٔ مهر ۱۴۰۴", anchor="apx-B")
    book.paragraph("هر صفحهٔ ۲ تا ۴۲ جزوهٔ ۱۴۰۴ باید در دست‌کم یک مبحث پوشش داده شود. "
                   "این جدول از فایل ساخت تولید می‌شود؛ صفحهٔ بدون پوشش یعنی کار ناقص است.")
    per_page = {}
    for t in outline["topics"]:
        for p in t.get("p1404", []):
            per_page.setdefault(p, []).append(t["topic_id"].split("-")[-1])
    rows = []
    run_start = None
    run_topics = None
    for p in range(2, 44):
        topics_here = tuple(per_page.get(p, []))
        if p == 43 or topics_here != run_topics:
            if run_start is not None:
                span = fa(run_start) if run_start == p - 1 else f"{fa(run_start)}–{fa(p - 1)}"
                rows.append([span, "، ".join(run_topics) or "— پوشش ندارد —"])
            run_start, run_topics = p, topics_here
        if p == 43:
            break
    book.table(["صفحهٔ ۱۴۰۴", "مبحث"], rows, widths=[CONTENT_W * 0.20, CONTENT_W * 0.80],
               size=7.6, caption="جدول پ-ب — نقشهٔ پوشش صفحه‌به‌مبحث (صفحات پیاپی با پوشش یکسان در یک ردیف ادغام شده‌اند؛ همهٔ ۲ تا ۴۲ پوشش دارند).")

    book.h2("پیوست پ — وضعیت هر مبحث (سطح QA)", anchor="apx-C")
    book.paragraph("وضعیت همهٔ مباحث این نسخه: «پیاده‌سازی‌شده» + «اجرا روی فایل واقعی». "
                   "هیچ مبحثی هنوز «بازبینی علمی» یا «آمادهٔ ادغام» نیست.")
    rows = []
    for t in outline["topics"]:
        blocks = content.get(t["topic_id"], [])
        figs = sum(1 for b in blocks if b.get("type") in ("figure", "facsimile"))
        notes = sum(1 for b in blocks if b.get("type") == "note")
        guy = sum(1 for b in blocks if b.get("type") == "guyton")
        rows.append([t["topic_id"].split("-")[-1], fa(len(blocks)), fa(figs),
                     fa(guy), fa(notes), "پیاده‌سازی‌شده"])
    book.table(["#", "بلوک", "شکل/تصویر", "گایتون", "کادر یادداشت", "وضعیت"], rows,
               widths=[CONTENT_W * 0.08, CONTENT_W * 0.13, CONTENT_W * 0.18,
                       CONTENT_W * 0.14, CONTENT_W * 0.24, CONTENT_W * 0.23],
               size=8.0, caption="جدول پ-پ — شمارش ساختاری هر مبحث.", src="content/sessions/*.json")

    book.h2("پیوست ث — تعارض‌ها و اختلاف‌های ثبت‌شده", anchor="apx-D")
    book.paragraph("اختلاف منابع حل نشده و پنهان نمی‌شود؛ در اینجا ثبت می‌شود تا در بازبینی "
                   "علمی تصمیم بگیرد.")
    for c in outline["conflicts"]:
        book.callout(c["detail"], kind="warn", title=f"{c['issue']} — {c['label']}")
    book.paragraph("موارد باز: (۱) نگاشت صفحهٔ PDF به صفحهٔ چاپی گایتون؛ (۲) نسخهٔ فارسی "
                   "گایتون (فایل LFS در دسترس نیست)؛ (۳) بازبینی علمی همهٔ مباحث.")

    book.h2("پیوست ج — جلسات باقی‌مانده", anchor="apx-E")
    book.paragraph("جلسات زیر شناسایی و در فهرست کلی سند ثبت شده‌اند، اما محتوای آن‌ها در این "
                   "نسخه تألیف نشده است. برای هر جلسه، همان چرخهٔ کاری جلسهٔ ۱ اجرا می‌شود.")
    rows = [
        ["۲", "سیناپس، پتانسیل عمل و هدایت عصبی", "دارد", "دارد", "طراحی‌شده"],
        ["۳", "گیرنده‌های حسی و انتقال حس", "دارد", "دارد", "طراحی‌شده"],
        ["۴", "درد، رفلکس‌ها و مسیرهای صعودی", "دارد", "دارد", "طراحی‌شده"],
        ["۵", "حرکت، مخچه و عقده‌های قاعده‌ای", "دارد", "دارد", "طراحی‌شده"],
        ["۶", "سیستم اتونوم", "دارد", "دارد", "طراحی‌شده"],
        ["۷", "نخاع و مسیرهای نزولی", "دارد", "—", "طراحی‌شده (جزوهٔ ۱۴۰۴ موجود نیست)"],
        ["۸–۱۲", "بینایی، شنوایی، تعادل، چشایی، بویایی", "دارد", "دارد", "طراحی‌شده"],
        ["۱۳–۱۴", "سیستم لیمبیک و حافظه", "دارد", "دارد", "طراحی‌شده (دو جلسه ادغام شده)"],
        ["۱۵", "اتونوم تکمیلی (جزوهٔ مستقل)", "دارد", "جزئی", "طراحی‌شده"],
        ["۱۶", "پری لب", "دارد", "—", "طراحی‌شده"],
    ]
    book.table(["جلسه", "موضوع", "جزوهٔ ۱۴۰۴", "جزوهٔ ۱۴۰۲", "وضعیت"], rows,
               widths=[CONTENT_W * 0.10, CONTENT_W * 0.44, CONTENT_W * 0.14,
                       CONTENT_W * 0.14, CONTENT_W * 0.18],
               size=7.9, caption="جدول پ-ج — دامنهٔ کل پروژه و آنچه هنوز نوشته نشده است.")


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
    book.paragraph("شماره‌ها صفحهٔ همین PDF هستند. فهرست در دو مرحله ساخته می‌شود تا شماره‌ها "
                   "با چیدمان نهایی بخوانند.", TextStyle(size=9, color=K.MUTED))
    toc_rows = [
        ("۰", "شناسنامه و راهنمای استفاده", "front-colophon", 0),
        ("۰", "نقشهٔ تقسیم کار و پیش‌نیازها", "front-workplan", 0),
        ("۱", "فصل ۱ — جلسهٔ ۱: سازمان‌دهی تا نوروترانسمیترها", "ch-s01", 0),
    ]
    for i, t in enumerate(outline["topics"], start=1):
        toc_rows.append((f"{i:02d}", t["title"], t["topic_id"], 1))
    toc_rows += [
        ("۱", "پیوست الف — نقشهٔ ارجاع گایتون", "apx-A", 1),
        ("۲", "پیوست ب — پوشش صفحات جزوهٔ ۱۴۰۴", "apx-B", 1),
        ("۳", "پیوست پ — وضعیت هر مبحث (سطح QA)", "apx-C", 1),
        ("۴", "پیوست ث — تعارض‌ها و اختلاف‌های ثبت‌شده", "apx-D", 1),
        ("۵", "پیوست ج — جلسات باقی‌مانده", "apx-E", 1),
    ]
    for num, title, anchor, indent in toc_rows:
        pg = toc_pages.get(anchor)
        book.toc_row(num, title, fa(pg) if pg else "—",
                     indent=indent * 18, accent=K.TEAL if indent == 0 else K.BLUE)

    # ---------------- chapter
    divider(book, "فصل ۱ · جلسهٔ ۱", "نوروفیزیولوژی:\nاز سازمان‌دهی تا\nنوروترانسمیترها",
            "دکتر خوارزمی · مهر ۱۴۰۴ + بهمن ۱۴۰۲",
            ["۱۴ مبحث · ۵ شکل اسکن‌شده · ۵ کادر گایتون",
             "صفحات ۲ تا ۴۲ جزوهٔ ۱۴۰۴", "هیچ بخشی هنوز بازبینی علمی نشده است"])
    chapter_opener(book, outline, {"sections": guyton})

    for i, t in enumerate(outline["topics"], start=1):
        topic_head(book, t, i, len(outline["topics"]), outline)
        render_blocks(book, content.get(t["topic_id"], []), guyton)

    appendices(book, outline, {"sections": guyton}, content)
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

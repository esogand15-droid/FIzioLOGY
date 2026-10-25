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

# Every session is a separate document and a separate file in ``pdf/``; nothing
# is ever overwritten.  A session entry only says *where* its data lives and how
# the cover should read -- the layout code is shared.
SESSIONS = {
    "s01": dict(
        num="۱", n=1, of="۱۶",
        guyton_ch="فصل ۴۵",
        split="تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر برای مباحث ساختاری (۱ تا ۵)، "
              "سه نفر برای نوروترانسمیترها (۶ تا ۱۰)، دو نفر برای گیرنده‌ها و سم‌شناسی "
              "(۱۱ تا ۱۳)، یک نفر برای هم‌انتقالی و جمع‌بندی (۱۴) به‌همراه گردآوری. "
              "این تقسیم پیشنهاد است، نه تصمیم نهایی تیم.",
        outline="s01_topics.json",
        content=("s01_a.json", "s01_b.json", "s01_c.json"),
        guyton="guyton_ch45_excerpts.json",
        chapter_anchor="ch-s01",
        cover_title=["فیزیولوژی اعصاب", "و حواس ویژه"],
        cover_topic="سازمان‌دهی سیستم عصبی، نورون، نوروترانسمیترها",
        divider_title="نوروفیزیولوژی:\nاز سازمان‌دهی تا\nنوروترانسمیترها",
        pdf_name="HumsYar_Neuro_Jalase1.pdf",
    ),
    "s02": dict(
        num="۲", n=2, of="۱۶",
        guyton_ch="فصل‌های ۴۵ و ۴۶",
        split="تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر برای مباحث پایه و طبقه‌بندی "
              "(۱ تا ۴)، دو نفر برای سیناپس شیمیایی و گیرنده‌ها (۵ تا ۷)، دو نفر برای "
              "پتانسیل پس‌سیناپسی و هدایت عصبی (۸ تا ۱۱)، دو نفر برای کنترل پیش‌سیناپسی، "
              "مدارها و پایداری (۱۲ تا ۱۶) به‌همراه گردآوری. این تقسیم پیشنهاد است، نه "
              "تصمیم نهایی تیم.",
        outline="s02_topics.json",
        content=("s02_a.json", "s02_b.json", "s02_c.json"),
        guyton="guyton_s02_excerpts.json",
        chapter_anchor="ch-s02",
        cover_title=["فیزیولوژی اعصاب", "و حواس ویژه"],
        cover_topic="سیناپس، پتانسیل پس‌سیناپسی و مدارهای نورونی",
        divider_title="نوروفیزیولوژی:\nاز سیناپس تا\nمدارهای نورونی",
        pdf_name="HumsYar_Neuro_Jalase2.pdf",
    ),
    "s03": dict(
        num="۳", n=3, of="۱۶",
        guyton_ch="فصل‌های ۴۶ و ۴۷",
        split="تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر برای تعریف و طبقه‌بندی گیرنده‌ها "
              "(۱ تا ۷)، دو نفر برای ترانسداکشن و کدگذاری شدت (۸ تا ۱۴)، دو نفر برای "
              "سازش‌پذیری و حس‌های تماسی (۱۵ تا ۱۷)، دو نفر برای مسیرهای صعودی و "
              "درماتوم‌ها (۱۸ تا ۲۰) به‌همراه گردآوری. این تقسیم پیشنهاد است، نه "
              "تصمیم نهایی تیم.",
        outline="s03_topics.json",
        content=("s03_a.json", "s03_b.json", "s03_c.json"),
        guyton="guyton_s03_excerpts.json",
        chapter_anchor="ch-s03",
        cover_title=["فیزیولوژی اعصاب", "و حواس ویژه"],
        cover_topic="گیرنده‌های حسی، ترانسداکشن و مسیرهای صعودی",
        divider_title="نوروفیزیولوژی:\nاز گیرندهٔ حسی\nتا قشر",
        pdf_name="HumsYar_Neuro_Jalase3.pdf",
    ),
    "s04": dict(
        num="۴", n=4, of="۱۶",
        guyton_ch="فصل‌های ۴۷ و ۴۸",
        split="تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر برای قشر حسی پیکری و نواحی آن "
              "(۱ تا ۳)، دو نفر برای لایه‌ها، ستون‌ها و کنترل تالاموسی (۴ تا ۷)، دو نفر برای "
              "کدگذاری شدت، میدان گیرنده و مهار جانبی (۸ تا ۱۰)، دو نفر برای درد و حرارت "
              "(۱۱ تا ۱۹) به‌همراه گردآوری. این تقسیم پیشنهاد است، نه تصمیم نهایی تیم.",
        outline="s04_topics.json",
        content=("s04_a.json", "s04_b.json", "s04_c.json"),
        guyton="guyton_s04_excerpts.json",
        chapter_anchor="ch-s04",
        cover_title=["فیزیولوژی اعصاب", "و حواس ویژه"],
        cover_topic="قشر حسی پیکری، درد و حرارت",
        divider_title="نوروفیزیولوژی:\nاز قشر حسی پیکری\nتا درد و حرارت",
        pdf_name="HumsYar_Neuro_Jalase4.pdf",
    ),
    "s05": dict(
        num="۵", n=5, of="۱۶",
        guyton_ch="فصل‌های ۵۰ و ۵۱",
        split="تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر برای ساختار شبکیه و فتورسپتورها "
              "(۱ تا ۵)، دو نفر برای ترانسداکسیون، تطابق و دید رنگ (۶ تا ۱۰)، دو نفر برای مدارهای "
              "شبکیه و مسیر بینایی (۱۱ تا ۱۷)، دو نفر برای قشر، حرکات چشم و رفلکس‌ها (۱۸ تا ۲۴) "
              "به‌همراه گردآوری. این تقسیم پیشنهاد است، نه تصمیم نهایی تیم.",
        outline="s05_topics.json",
        content=("s05_a.json", "s05_b.json", "s05_c.json"),
        guyton="guyton_s05_excerpts.json",
        chapter_anchor="ch-s05",
        cover_title=["فیزیولوژی اعصاب", "و حواس ویژه"],
        cover_topic="بینایی: شبکیه، مسیر بینایی و حرکات چشم",
        divider_title="نوروفیزیولوژی:\nاز شبکیه\nتا حرکات چشم",
        pdf_name="HumsYar_Neuro_Jalase5.pdf",
    ),
    "s06": dict(
        num="۶", n=6, of="۱۶",
        guyton_ch="فصل ۵۲",
        split="تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر برای گوش خارجی و میانی و تطبیق "
              "امپدانس (۱ تا ۵)، دو نفر برای حلزون، پتانسیل داخل حلزونی و سلول مویی (۶ تا ۱۲)، "
              "دو نفر برای غشای قاعده‌ای، فرکانس و بلندی صدا (۱۳ تا ۱۸)، دو نفر برای مسیرها، قشر، "
              "جهت‌یابی و اختلالات شنوایی (۱۹ تا ۲۳) به‌همراه گردآوری. این تقسیم پیشنهاد است، نه "
              "تصمیم نهایی تیم.",
        outline="s06_topics.json",
        content=("s06_a.json", "s06_b.json", "s06_c.json"),
        guyton="guyton_s06_excerpts.json",
        chapter_anchor="ch-s06",
        cover_title=["فیزیولوژی اعصاب", "و حواس ویژه"],
        cover_topic="شنوایی: از گوش خارجی تا قشر شنوایی",
        divider_title="نوروفیزیولوژی:\nاز صدا\nتا فهم صدا",
        pdf_name="HumsYar_Neuro_Jalase6.pdf",
    ),
    "s07": dict(
        num="۷", n=7, of="۱۶",
        guyton_ch="فصل‌های ۵۴ و ۵۵",
        no1404=True,
        split="تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر برای آناتومی نخاع، نورون حرکتی و "
              "واحد حرکتی (۱ تا ۶)، دو نفر برای دوک عضلانی و رفلکس کشش (۷ تا ۱۲)، دو نفر "
              "برای مهار متقابل، اندام وتری و رفلکس‌های نخاعی (۱۳ تا ۲۲)، دو نفر برای قشر "
              "حرکتی و مسیرهای نزولی و ضایعات (۲۳ تا ۲۸) به‌همراه گردآوری. این تقسیم "
              "پیشنهاد است، نه تصمیم نهایی تیم.",
        outline="s07_topics.json",
        content=("s07_a.json", "s07_b.json", "s07_c.json"),
        guyton="guyton_s07_excerpts.json",
        chapter_anchor="ch-s07",
        cover_title=["فیزیولوژی اعصاب", "و حواس ویژه"],
        cover_topic="نخاع، رفلکس‌های نخاعی و مسیرهای نزولی",
        divider_title="نوروفیزیولوژی:\nاز قوس رفلکس\nتا مسیر نزولی",
        pdf_name="HumsYar_Neuro_Jalase7.pdf",
    ),
    "s08": dict(
        num="۸", n=8, of="۱۶",
        guyton_ch="فصل ۵۵ (بخش ساقهٔ مغز و تعادل)",
        no1404=True,
        single_part=True,
        split="تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر برای دستگاه شبکه‌ای، "
              "مسیرهای رتیکول‌واسپاینال و سفتی دِسِبره (۱ تا ۷)، دو نفر برای لابیرنت، "
              "ماکولا و ترارسانی سلول مویی (۸ تا ۱۲)، دو نفر برای رفتار ماکولا، مجاری "
              "نیم‌دایره و سازش (۱۳ تا ۱۶)، دو نفر برای مسیر مرکزی، بازتاب "
              "دهلیزی-چشمی و عوامل دیگر تعادل (۱۷ تا ۲۱) به‌همراه گردآوری. این تقسیم "
              "پیشنهاد است، نه تصمیم نهایی تیم.",
        outline="s08_topics.json",
        content=("s08_a.json", "s08_b.json", "s08_c.json"),
        guyton="guyton_s08_excerpts.json",
        chapter_anchor="ch-s08",
        cover_title=["فیزیولوژی اعصاب", "و حواس ویژه"],
        cover_topic="ساقهٔ مغز، حس تعادل و کنترل وضعیت",
        divider_title="نوروفیزیولوژی:\nاز ساقهٔ مغز\nتا تعادل بدن",
        pdf_name="HumsYar_Neuro_Jalase8.pdf",
    ),
    "s09": dict(
        num="۹", n=9, of="۱۶",
        guyton_ch="فصل ۵۶ (مخچه و عقده‌های قاعده‌ای)",
        no1404=True,
        part_labels=("جزوهٔ مخچه", "جزوهٔ عقده‌های قاعده‌ای"),
        split="تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر پایهٔ مخچه (۱ تا ۴)، دو نفر "
              "سلول‌ها و ورودی و خروجی مخچه (۵ تا ۱۰)، دو نفر بخش‌های سه‌گانه و ضایعات "
              "(۱۱ تا ۱۷)، دو نفر عقده‌های قاعده‌ای و پارکینسون (۱۸ تا ۳۰) به‌همراه گردآوری. "
              "این تقسیم پیشنهاد است، نه تصمیم نهایی تیم.",
        outline="s09_topics.json",
        content=("s09_a.json", "s09_b.json", "s09_c.json"),
        guyton="guyton_s09_excerpts.json",
        chapter_anchor="ch-s09",
        cover_title=["فیزیولوژی اعصاب", "و حواس ویژه"],
        cover_topic="مخچه، عقده‌های قاعده‌ای و کنترل حرکت",
        divider_title="نوروفیزیولوژی:\nاز مخچه\nتا عقده‌های قاعده‌ای",
        pdf_name="HumsYar_Neuro_Jalase9.pdf",
    ),
    "s10": dict(
        num="۱۰", n=10, of="۱۶",
        guyton_ch="فصل ۵۷ (قشر مغز و کارکردهای عالی)",
        no1404=True,
        single_part=True,
        split="تقسیم کار پیشنهادی برای تیم هشت‌نفره: دو نفر مرور عقده‌های قاعده‌ای و دو "
              "بیماری آن (۱ تا ۳)، دو نفر دروازهٔ خروجی و ساختار قشر و ارتباط "
              "تالاموکورتیکال (۴ تا ۷)، دو نفر نواحی ارتباطی و نگریست و ورنیکه و شکنج "
              "زاویه‌ای (۸ تا ۱۲)، دو نفر نامیدن، بروکا، قشر پیشانی، لیمبیک، غالب بودن و "
              "آفازی‌ها (۱۳ تا ۱۸) به‌همراه گردآوری. این تقسیم پیشنهاد است، نه تصمیم "
              "نهایی تیم.",
        outline="s10_topics.json",
        content=("s10_a.json", "s10_b.json", "s10_c.json"),
        guyton="guyton_s10_excerpts.json",
        chapter_anchor="ch-s10",
        cover_title=["فیزیولوژی اعصاب", "و حواس ویژه"],
        cover_topic="کارکردهای عالی قشر مغز، زبان و آفازی‌ها",
        divider_title="نوروفیزیولوژی:\nاز قشر مغز\nتا زبان و آفازی",
        pdf_name="HumsYar_Neuro_Jalase10.pdf",
    ),
}

SESSION = "s01"
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
    """Printed list of 1402 pages; an empty list means the deck has none for that topic."""
    return "، ".join(fa(p) for p in pages) if pages else "—"


def part_label(cfg: dict, idx: int) -> str:
    """Name of part 1/2 of the 1402 notes (generic unless the session names them)."""
    labels = cfg.get("part_labels")
    if labels and 1 <= idx <= len(labels):
        return labels[idx - 1]
    return "پارت " + ("۱" if idx == 1 else "۲")


def pages_1402(t: dict) -> str:
    """1402 pages of a topic; sessions with two decks show the part of each page."""
    if t.get("notes1402_p2"):
        return (f"پارت ۱: {page_range(t.get('notes1402', []))} · "
                f"پارت ۲: {page_range(t['notes1402_p2'])}")
    return page_range(t.get("notes1402", []))


def cover_page(book: PDFBook, cfg: dict, outline: dict) -> None:
    c = book.c
    c.setFillColor(K.TEAL_L)
    c.setFont("VazirM", 11)
    c.drawCentredString(K.A4W / 2, K.A4H * 0.86, K.shape("HumsYar · جزوهٔ مادر"))
    c.setFillColor(K.HexColor("#ffffff"))
    c.setFont("VazirB", 30)
    c.drawCentredString(K.A4W / 2, K.A4H * 0.60, K.shape(cfg["cover_title"][0]))
    c.drawCentredString(K.A4W / 2, K.A4H * 0.535, K.shape(cfg["cover_title"][1]))
    c.setFillColor(K.TEAL_L)
    c.setFont("Vazir", 14)
    c.drawCentredString(K.A4W / 2, K.A4H * 0.455,
                        K.shape("جزوهٔ مادر — نسخهٔ کاری تیم یادداشت‌نویسی"))
    c.setStrokeColor(K.Color(37 / 255, 99 / 255, 235 / 255))
    c.setLineWidth(1.4)
    c.line(K.A4W * 0.30, K.A4H * 0.42, K.A4W * 0.70, K.A4H * 0.42)
    c.setFillColor(K.HexColor("#94a3b8"))
    c.setFont("Vazir", 10)
    lines = [
        f"{outline.get('professor', 'دکتر خوارزمی')} — دانشکدهٔ پزشکی",
        f"جلسهٔ {cfg['num']} (از {cfg['of']}): {cfg['cover_topic']}",
        f"نسخهٔ ۰٫۱ — فقط جلسهٔ {cfg['num']} تألیف شده است",
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
def front_matter(book: PDFBook, outline: dict, cfg: dict) -> None:
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
    if cfg.get("no1404") and cfg.get("single_part"):
        source_rows = [
            ["جزوهٔ بهمن ۱۴۰۲ (نوشتهٔ دانشجوی سال‌بالاتر)",
             "متن پایه و ترتیب مباحث این جلسه: ساقهٔ مغز، دستگاه شبکه‌ای و مسیرهای "
             "رتیکول‌واسپاینال، سپس دستگاه دهلیزی و تعادل و در پایان ارتباط‌های مرکزی آن.",
             "«جزوهٔ بهمن ۱۴۰۲، ص …»"],
            ["اسلایدهای انگلیسی کلاس",
             "جدول‌ها، فهرست‌ها و شکل‌های اصلی درس (منبع اولویت‌دار برای شکل‌ها).",
             "«اسلاید کلاس، ص …»"],
            [GUYTON_ED,
             f"متن اصلی انگلیسی {cfg['guyton_ch']}، همراه با ترجمهٔ روان تحریریه در همان کادر.",
             "«گایتون، فصل ۵۵، ص …»"],
            ["جزوات تکمیلی دکتر قدیری",
             "منبع کمکی برای جلسات بعد؛ در این نسخه استفاده نشده است.",
             "—"],
        ]
    elif cfg.get("no1404"):
        source_rows = [
            [f"{part_label(cfg, 1)} (نوشتهٔ دانشجوی سال‌بالاتر)",
             ("متن پایهٔ نیمهٔ نخست این جلسه: آناتومی نخاع، واحد حرکتی، دوک عضلانی، "
              "رفلکس‌های کشش و خم‌کننده، رفلکس‌های نخاعی و شوک نخاعی."
              if cfg["n"] == 7 else
              "متن پایهٔ نیمهٔ نخست این جلسه: بازتاب‌های دهلیزی و اختلالات تعادل، "
              "ساختار و مدارهای مخچه، بخش‌های سه‌گانه و نشانه‌های ضایعهٔ آن."),
             f"«{part_label(cfg, 1)}، ص …»"],
            [f"{part_label(cfg, 2)} (نوشتهٔ دانشجوی سال‌بالاتر)",
             ("تکرار رفلکس‌های نخاعی با شکل‌های تازه، سپس قشر حرکتی، مسیرهای نزولی و ضایعات."
              if cfg["n"] == 7 else
              "ادامهٔ نشانه‌های ضایعهٔ مخچه، سپس اجزای عقده‌های قاعده‌ای، مدارهای "
              "مستقیم و غیرمستقیم، دوپامین و بیماری پارکینسون."),
             f"«{part_label(cfg, 2)}، ص …»"],
            ["اسلایدهای انگلیسی کلاس",
             "جدول‌ها، فهرست‌ها و شکل‌های اصلی درس (منبع اولویت‌دار برای شکل‌ها).",
             "«اسلاید کلاس، ص …»"],
            [GUYTON_ED,
             f"متن اصلی انگلیسی {cfg['guyton_ch']}، همراه با ترجمهٔ روان تحریریه در همان کادر.",
             "«گایتون، فصل …، ص …»"],
            ["جزوات تکمیلی دکتر قدیری",
             "منبع کمکی برای جلسات بعد؛ در این نسخه استفاده نشده است.",
             "—"],
        ]
    else:
        source_rows = [
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
             f"متن اصلی انگلیسی {cfg['guyton_ch']}، همراه با ترجمهٔ روان تحریریه در همان کادر.",
             "«گایتون، فصل …، ص …»"],
            ["جزوات تکمیلی دکتر قدیری",
             "منبع کمکی برای جلسات بعد؛ در این نسخه استفاده نشده است.",
             "—"],
        ]
    book.table(
        ["منبع", "چه چیزی از آن در این جزوه آمده", "شکل ارجاع در متن"],
        source_rows,
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
        ("صفحه‌های جزوهٔ بهمن ۱۴۰۲ در این جلسه بدون لایهٔ متن قابل استفاده بوده‌اند؛ متن آن‌ها "
         "با خواندن تصویر همان صفحه به فارسی برگردانده شده است. اگر عبارتی روی صفحه ناخوانا یا "
         "بریده بوده، به‌جای حدس زدن، در متن «…» گذاشته شده و در همان مبحث یادداشت شده است."
         if cfg.get("no1404") else
         "املای چند واژه در جزوهٔ ۱۴۰۴ اشتباه تایپ شده است (مثلاً «اطالعات» به‌جای «اطلاعات» یا "
         "«عضالت» به‌جای «عضلات»). در این جزوه املای درست نوشته شده؛ اگر جایی از منبع عیناً "
         "نقل شده و املا نادرست است، در همان جمله اصلاح شده است."),
        ("این جلسه جزوهٔ مهر ۱۴۰۴ ندارد؛ بنابراین در تمام سند هیچ ارجاعی به ۱۴۰۴ نیامده و متن "
         "فقط بر جزوهٔ بهمن ۱۴۰۲ و گایتون فصل ۵۵ استوار است. جزوهٔ ۱۴۰۲ این جلسه یک پارت "
         "۱۵ صفحه‌ای است، پس در ارجاع‌ها فقط شمارهٔ صفحه آمده است."
         if cfg.get("single_part") else
         "این جلسه جزوهٔ مهر ۱۴۰۴ ندارد؛ بنابراین در تمام سند هیچ ارجاعی به ۱۴۰۴ نیامده و متن "
         "فقط بر دو پارت جزوهٔ بهمن ۱۴۰۲ و گایتون فصل‌های ۵۴ و ۵۵ استوار است. دو پارت هر دو از "
         "صفحهٔ ۱ شروع می‌شوند، پس شمارهٔ پارت همیشه در ارجاع نوشته شده است."
         if cfg.get("no1404") else
         "صفحه‌های جزوهٔ ۱۴۰۲ با خواندن تصویر همان صفحه به متن فارسی برگردانده شده‌اند. اگر "
         "عبارتی روی صفحه ناخوانا یا بریده بوده، به‌جای حدس زدن، در متن «…» گذاشته شده و در "
         "همان مبحث یادداشت شده است."),
    ])


def work_division(book: PDFBook, outline: dict, cfg: dict) -> None:
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
                     pages_1402(t), pre, "⋯"])
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
    book.callout(cfg["split"], kind="info")


def chapter_opener(book: PDFBook, outline: dict, guyton: dict, cfg: dict | None = None) -> None:
    cfg = cfg or SESSIONS["s01"]
    book.h1(outline["title"], anchor=cfg["chapter_anchor"],
            kicker=f"فصل {cfg['num']} · جلسهٔ {cfg['num']}")
    p1404 = [p for t in outline["topics"] for p in t.get("p1404", [])]
    p1402 = [p for t in outline["topics"] for p in t.get("notes1402", [])]
    rng04 = (f"صفحه‌های {fa(min(p1404))} تا {fa(max(p1404))}") if p1404 else "—"
    rng02 = (f"{fa(max(p1402))} صفحه") if p1402 else "—"
    if cfg.get("no1404"):
        parts = []
        if p1402 and cfg.get("single_part"):
            parts.append(f"{fa(max(p1402))} صفحه")
        elif p1402:
            parts.append(f"پارت ۱ در {fa(max(p1402))} صفحه")
        p2 = [p for t in outline["topics"] for p in t.get("notes1402_p2", [])]
        if p2:
            parts.append(f"پارت ۲ در {fa(max(p2))} صفحه")
        if cfg.get("single_part"):
            src_line = (f"استاد: {outline['professor']} · ترم: {outline['term']} · "
                        f"منبع اصلی متن: جزوهٔ بهمن ۱۴۰۲ ({' و '.join(parts)}). "
                        "این جلسه جزوهٔ مهر ۱۴۰۴ ندارد و جزوهٔ ۱۴۰۲ آن یک پارت است.")
        else:
            if cfg.get("part_labels"):
                parts = []
                if p1402:
                    parts.append(f"{part_label(cfg, 1)} در {fa(max(p1402))} صفحه")
                if p2:
                    parts.append(f"{part_label(cfg, 2)} در {fa(max(p2))} صفحه")
                src_line = (f"استاد: {outline['professor']} · ترم: {outline['term']} · "
                            f"منبع اصلی متن: {' و '.join(parts)}؛ چون هر جزوه شمارهٔ صفحهٔ خودش "
                            "را دارد، در همهٔ ارجاع‌ها نام جزوه هم نوشته شده است. "
                            "این جلسه جزوهٔ مهر ۱۴۰۴ ندارد.")
            else:
                src_line = (f"استاد: {outline['professor']} · ترم: {outline['term']} · "
                            f"منبع اصلی متن: جزوهٔ بهمن ۱۴۰۲ ({' و '.join(parts)})؛ چون هر پارت "
                            "شمارهٔ صفحهٔ خودش را دارد، در همهٔ ارجاع‌ها شمارهٔ پارت هم نوشته شده است. "
                            "این جلسه جزوهٔ مهر ۱۴۰۴ ندارد.")
    else:
        src_line = (f"استاد: {outline['professor']} · ترم: {outline['term']} · "
                    f"منبع اصلی متن: جزوهٔ مهر ۱۴۰۴ ({rng04})")
        if p1402:
            src_line += f" · منبع دوم: جزوهٔ ورودی بهمن ۱۴۰۲ ({rng02})."
        else:
            src_line += " · این جلسه جزوهٔ متناظر ۱۴۰۲ ندارد."
    book.paragraph(src_line + ".")
    book.h2("نقشهٔ درخت مباحث", anchor=f"{cfg['chapter_anchor']}-tree")
    rows = []
    for t in outline["topics"]:
        sub = t["title"]
        rows.append([tno(t["topic_id"]), sub, pages_1402(t),
                     {"small": "کوچک", "medium": "متوسط", "large": "بزرگ"}
                     .get(t.get("notes_size"), "متوسط")])
    book.table(["#", "مبحث", "ص ۱۴۰۲", "حجم"], rows,
               widths=[CONTENT_W * 0.08, CONTENT_W * 0.68, CONTENT_W * 0.16, CONTENT_W * 0.08],
               size=8.2,
               caption=f"جدول {cfg['num']}-۰ — {fa(len(outline['topics']))} مبحث جلسهٔ {cfg['num']}. "
                       "زیرمبحث‌ها در ابتدای هر مبحث فهرست شده‌اند.",
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
               caption=f"جدول {cfg['num']}-۳ — رابطهٔ پیش‌نیاز دوطرفه است: اگر مبحثی به مبحث دیگری "
                       "نیاز دارد، آن مبحث پس‌نیاز این یکی است.",
               src="نقشهٔ پیش‌نیازهای همین جزوه")
    book.callout(
        "هر مبحث در ابتدای خود یک شناسنامه دارد که پیش‌نیاز ضروری و پیش‌نیاز پیشنهادی‌اش را "
        "جدا نشان می‌دهد. اگر پیش‌نیاز ضروری نوشته نشده باشد، آن مبحث بسته نمی‌شود.",
        kind="info")


def topic_head(book: PDFBook, t: dict, idx: int, total: int, outline: dict) -> None:
    anchor = t["topic_id"]
    book.h2(t["title"], anchor=anchor)
    pre = "؛ ".join(f"مبحث {tno(p['topic_id'])} — {p.get('level','')}" for p in t["prerequisites"])
    if t.get("notes1402_p2") and t.get("notes1402"):
        src_pages = (f"صفحه‌های جزوهٔ ۱۴۰۲: پارت ۱ ص {page_range(t.get('notes1402', []))} · "
                     f"پارت ۲ ص {page_range(t['notes1402_p2'])}")
    elif t.get("notes1402_p2"):
        src_pages = f"صفحه‌های جزوهٔ ۱۴۰۲ (پارت ۲): {page_range(t['notes1402_p2'])}"
    elif outline.get("single_part"):
        src_pages = f"صفحه‌های جزوهٔ ۱۴۰۲: {page_range(t.get('notes1402', []))}"
    elif outline.get("no1404") or not t.get("p1404"):
        src_pages = f"صفحه‌های جزوهٔ ۱۴۰۲ (پارت {t.get('notes_part', '۱')}): {page_range(t.get('notes1402', []))}"
    else:
        src_pages = f"صفحه‌های جزوهٔ ۱۴۰۴: {page_range(t.get('p1404', []))}"
    meta = f"مبحث {fa(idx)} از {fa(total)} · {src_pages}"
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
    cfg = SESSIONS[SESSION]
    book.paragraph(
        f"این سند جلسهٔ {cfg['num']} را دارد و هر جلسهٔ تازه، سند جداگانهٔ خودش را می‌گیرد؛ "
        "سند جلسه‌های پیشین دست‌نخورده بایگانی می‌شود. جلسه‌های زیر شناسایی شده‌اند و "
        "جزوه/اسلایدشان در اختیار تیم است؛ برای هر جلسه همان مسیر تکرار می‌شود: شناسنامه، "
        "متن با ارجاع، شکل‌ها، جمع‌بندی، کادرهای یادداشت و برگهٔ تحویل.")
    if cfg.get("no1404"):
        book.h2("پوشش صفحه‌های جزوهٔ ۱۴۰۲ در این نسخه", anchor="roadmap-cover")
        _coverage_1402(book, outline, cfg)
        _remaining_sessions(book, cfg)
        return
    book.h2("پوشش صفحه‌های جزوهٔ ۱۴۰۴ در این نسخه", anchor="roadmap-cover")
    per_page = {}
    for t in outline["topics"]:
        for p in t.get("p1404", []):
            per_page.setdefault(p, []).append(tno(t["topic_id"]))
    rows = []
    run_start = None
    run_topics = None
    lo_pg = min(per_page) if per_page else 2
    hi_pg = max(per_page) if per_page else 2
    uncovered = 0
    for p in range(lo_pg, hi_pg + 2):
        topics_here = tuple(per_page.get(p, []))
        if not topics_here and p <= hi_pg:
            uncovered += 1
        if p == hi_pg + 1 or topics_here != run_topics:
            if run_start is not None:
                span = fa(run_start) if run_start == p - 1 else f"{fa(run_start)}–{fa(p - 1)}"
                rows.append([span, "، ".join(run_topics) or "— بدون مبحث —"])
            run_start, run_topics = p, topics_here
        if p == hi_pg + 1:
            break
    book.table(["صفحهٔ جزوهٔ ۱۴۰۴", "مبحث این جزوه"], rows,
               widths=[CONTENT_W * 0.22, CONTENT_W * 0.78], size=7.6,
               caption=f"جدول {cfg['num']}-۱ — صفحه‌های {fa(lo_pg)} تا {fa(hi_pg)} جزوهٔ ۱۴۰۴ و مبحثی که "
                       "آن‌ها را پوشش می‌دهد." + (" همهٔ صفحه‌ها پوشش دارند."
                                                   if uncovered == 0 else ""),
               src="مقایسهٔ صفحه‌به‌صفحهٔ جزوه و مباحث این سند")

    _remaining_sessions(book, cfg)


def _coverage_1402(book: PDFBook, outline: dict, cfg: dict) -> None:
    """Page coverage of a session whose source is two 1402 decks, each from page 1."""
    if cfg.get("single_part"):
        book.paragraph("منبع متنی این جلسه یک جزوهٔ ۱۵ صفحه‌ای بهمن ۱۴۰۲ است. جدول زیر می‌گوید "
                       "هر صفحهٔ آن جزوه در کدام مبحث این سند آمده است.")
    else:
        book.paragraph("منبع این جلسه دو جزوهٔ بهمن ۱۴۰۲ است و هر جزوه شمارهٔ صفحهٔ خودش را "
                       "دارد؛ بنابراین پوشش را برای هر جزوه جدا می‌آوریم.")
    single = cfg.get("single_part")
    for part, key in (("۱", "notes1402"), ("۲", "notes1402_p2")):
        per_page = {}
        for t in outline["topics"]:
            for pg in t.get(key, []):
                per_page.setdefault(pg, []).append(tno(t["topic_id"]))
        if not per_page:
            continue
        lo_pg, hi_pg = min(per_page), max(per_page)
        rows = []
        for pg in range(lo_pg, hi_pg + 1):
            rows.append([fa(pg), "، ".join(per_page.get(pg, [])) or "— بدون مبحث —"])
        gaps = sum(1 for pg in range(lo_pg, hi_pg + 1) if pg not in per_page)
        head = ("صفحهٔ جزوهٔ ۱۴۰۲" if single else "صفحهٔ " + part_label(cfg, int(
            part.translate(str.maketrans("۱۲", "12")))))
        where = ("" if single else " " + part_label(cfg, int(
            part.translate(str.maketrans("۱۲", "12")))))
        book.table([head, "مبحث این جزوه"], rows,
                   widths=[CONTENT_W * 0.22, CONTENT_W * 0.78], size=7.6,
                   caption=f"جدول {cfg['num']}-۱ — صفحه‌های {fa(lo_pg)} تا {fa(hi_pg)}{where} "
                           "جزوهٔ بهمن ۱۴۰۲ و مبحثی که آن‌ها را پوشش می‌دهد."
                           + ("" if gaps else " در این بازه صفحهٔ بدون مبحث نمانده است."),
                   src="مقایسهٔ صفحه‌به‌صفحهٔ جزوه و مباحث این سند")
        book.spacer(4)


def _remaining_sessions(book: PDFBook, cfg: dict) -> None:
    # keep the heading with its (sometimes very short) table
    book.ensure(190)
    book.h2("جلسه‌های باقی‌مانده", anchor="roadmap-sessions")
    remaining = [
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
    # for the 1402-only sessions the deck numbers run ahead of the session order
    # (this session = session 10, deck 12), so filter on the deck number
    horizon = 12 if cfg.get("no1404") else cfg["n"]
    rows = [r for r in remaining if int(r[0].translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).split("–")[0]) > horizon]
    book.table(["جلسهٔ جزوه", "موضوع", "جزوهٔ ۱۴۰۴", "جزوهٔ ۱۴۰۲"], rows,
               widths=[CONTENT_W * 0.10, CONTENT_W * 0.50, CONTENT_W * 0.20,
                       CONTENT_W * 0.20],
               size=8.0,
               caption=f"جدول {cfg['num']}-۲ — شماره‌ها شمارهٔ جلسه در جزوهٔ درس است. این سند جلسهٔ "
                       f"{cfg['num']} از {cfg['of']} است و جزوهٔ جلسهٔ ۱۲ را پوشش می‌دهد؛ به همین دلیل "
                       "شمارش جلسه‌های باقی‌مانده از ۱۳ ادامه می‌یابد. ستون‌های «جزوهٔ ۱۴۰۴» و "
                       "«جزوهٔ ۱۴۰۲» می‌گویند منبع آن جلسه در اختیار تیم هست یا نه.",
               src="فهرست منابع درس")


def back_page(book: PDFBook, cfg: dict) -> None:
    def painter(b: PDFBook) -> None:
        c = b.c
        c.setFillColor(K.HexColor("#ffffff"))
        c.setFont("VazirB", 18)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.60, K.shape("پایان نسخهٔ ۰٫۱"))
        c.setFillColor(K.TEAL_L)
        c.setFont("Vazir", 11)
        nxt = str(cfg["n"] + 1).translate(K.FA_DIGITS)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.55,
                            K.shape(f"جلسهٔ {cfg['num']} تألیف شد؛ آغاز جلسهٔ {nxt} "
                                    "منوط به دستور تیم است"))
        c.setFillColor(K.HexColor("#64748b"))
        c.setFont("VazirL", 9)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.22,
                            K.shape("HumsYar · سند کاری — بدون بازبینی علمی نهایی"))
    book.dark_page(painter)


# --------------------------------------------------------------------- assembly
def build(out_path: Path, toc_pages: dict[str, int] | None = None) -> PDFBook:
    cfg = SESSIONS[SESSION]
    outline = load_json(REPO / "content" / "outline" / cfg["outline"])
    guyton = load_json(REPO / "work" / "references" / cfg["guyton"])["sections"]

    content: dict[str, list] = {}
    for fname in cfg["content"]:
        for topic in load_json(CONTENT / fname):
            content[topic["topic_id"]] = topic["blocks"]
    # page map for the topic header line (the outline is the single source)
    for t in outline["topics"]:
        t["p1404"] = t.get("p1404", [])

    book = PDFBook(out_path, "جزوهٔ مادر فیزیولوژی اعصاب و حواس ویژه — نسخهٔ ۰٫۱")
    book.dark_page(lambda b: cover_page(b, cfg, outline), reuse_blank_page=True)

    front_matter(book, outline, cfg)
    work_division(book, outline, cfg)

    # ---------------- TOC (numbers come from the previous pass)
    toc_pages = toc_pages or {}
    book.new_page()
    book.h1("فهرست مطالب", anchor="toc", kicker="راهنمای سند")
    book.paragraph("شمارهٔ روبه‌روی هر سطر، شمارهٔ صفحهٔ همین سند است.",
                   TextStyle(size=9, color=K.MUTED))
    toc_rows = [
        ("۰", "شناسنامه و راهنمای استفاده", "front-colophon", 0),
        ("۰", "نقشهٔ مباحث و پیش‌نیازها", "front-workplan", 0),
        (cfg["num"], f"فصل {cfg['num']} — جلسهٔ {cfg['num']}: {cfg['cover_topic']}",
         cfg["chapter_anchor"], 0),
    ]
    for i, t in enumerate(outline["topics"], start=1):
        toc_rows.append((f"{i:02d}", t["title"], t["topic_id"], 1))
    toc_rows += [
        ("ر", "نقشهٔ جلسات آینده", "roadmap", 0),
        ("ر", ("پوشش صفحه‌های جزوهٔ ۱۴۰۲" if cfg.get("no1404")
               else "پوشش صفحه‌های جزوهٔ ۱۴۰۴"), "roadmap-cover", 1),
        ("ر", "جلسه‌های باقی‌مانده", "roadmap-sessions", 1),
    ]
    toc_step = 19 if len(toc_rows) <= 28 else 16.5
    for num, title, anchor, indent in toc_rows:
        pg = toc_pages.get(anchor)
        book.toc_row(num, title, fa(pg) if pg else "—",
                     indent=indent * 18, accent=K.TEAL if indent == 0 else K.BLUE,
                     step=toc_step)

    # ---------------- chapter
    n_figs = sum(1 for blocks in content.values() for b in blocks
                 if b.get("type") == "figure")
    n_guy = sum(1 for blocks in content.values() for b in blocks
                if b.get("type") in ("guyton", "guytonpair"))
    divider(book, f"فصل {cfg['num']} · جلسهٔ {cfg['num']}", cfg["divider_title"],
            outline.get("subtitle", "دکتر خوارزمی · مهر ۱۴۰۴ + بهمن ۱۴۰۲"),
            [f"{fa(len(outline['topics']))} مبحث · {fa(n_figs)} شکل و جدول از منابع درس · "
             f"{fa(n_guy)} کادر گایتون با ترجمه",
             outline.get("divider_note", "جزوهٔ مهر ۱۴۰۴ و جزوهٔ بهمن ۱۴۰۲"),
             "پیش‌نویس ویرایشی — بازبینی علمی در جریان"])
    chapter_opener(book, outline, {"sections": guyton}, cfg)

    for i, t in enumerate(outline["topics"], start=1):
        topic_head(book, t, i, len(outline["topics"]), outline)
        render_blocks(book, content.get(t["topic_id"], []), guyton)

    roadmap(book, outline, content)
    back_page(book, cfg)
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
    global SESSION, OUTLINE, GUYTON
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="s01", choices=sorted(SESSIONS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--force", action="store_true",
                    help="allow overwriting an already published session PDF")
    args = ap.parse_args()

    SESSION = args.session
    cfg = SESSIONS[SESSION]
    OUTLINE = REPO / "content" / "outline" / cfg["outline"]
    GUYTON = REPO / "work" / "references" / cfg["guyton"]

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

    pages_after = drop_trailing_blank_page(out)
    if pages_after is not None and pages_after != book.page:
        print(f"dropped empty trailing page: {book.page} -> {pages_after} pages")

    if book.missing_assets:
        print("MISSING ASSETS:", *book.missing_assets, sep="\n  ")
    print("written:", out, out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()

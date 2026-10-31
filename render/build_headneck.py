"""Build the head-and-neck session PDFs (HumsYar · آناتومی سر و گردن).

One session = one PDF in ``pdf/``.  The physiology builder
(``render/build_master.py``) is never touched: anatomy has its own content root
(``headneck/content/``), its own session table and a few block types that only
exist here (``plate`` = a book figure with its own citation, ``path`` = a
numbered conduction chain, ``status`` = the evidence tag for one claim).

    .venv/bin/python render/build_headneck.py --session hn01 [--out PATH] [--force]

Two-pass layout: pass 1 records the page of every anchor, pass 2 prints the TOC
with those numbers.  The TOC always has the same number of rows, so pagination
is stable between passes; the script asserts that instead of shipping a wrong
TOC.

Nothing is invented here.  A plate block carries the book, page and figure
number of the picture; a missing file is reported on the page (never skipped).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hn_kit as K
from hn_kit import MM, PDFBook, TextStyle
from hn_updates import apply_update

REPO = Path(__file__).resolve().parents[1]
CONTENT = REPO / "headneck" / "content"
IMAGES = "headneck/images/"

FOOTER = "HumsYar · جزوهٔ مادر آناتومی سر و گردن"

# --------------------------------------------------------------- session table
# ``of`` is always ۱۳: the official list the user supplied has 13 sessions.
HN_SESSIONS = {
    "hn01": dict(
        num="۱", n=1, of="۱۳",
        title="جمجمه: جایگاه، دسته‌بندی، نماها، پیشانی، بینی و فک فوقانی",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۱ — نسخهٔ بازبینی‌شده"],
        cover_topic="اسکلت محوری · سه تقسیم‌بندی · پنج نما · استخوان پیشانی · بینی و ماگزیلا",
        divider_title="از نما تا استخوان",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۱) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۲۲",
        outline="hn01_topics.json",
        content=("hn01_a.json", "hn01_b.json"),
        measure_idcard=True,
        anchor="hn-01",
        pdf_name="HumsYar_HeadNeck_Jalase1.pdf",
        outcome="جمجمه را از پنج نما ببینید، ۸ استخوان کاسهٔ سر و ۱۴ استخوان صورت "
                "را دسته‌بندی کنید، و بخش‌های استخوان پیشانی، استخوان بینی و فک "
                "فوقانی را با سینوس آن بشناسید.",
        intro_sources="نتر، پلیت‌های ۸، ۲۵–۲۷، ۳۰–۳۲، ۳۵–۳۷، ۵۹، ۶۲–۶۳، ۶۷–۶۸، ۸۵، ۱۱۱ و ۱۲۷ · گری، شکل‌های ۸.۱۸، ۸.۱۹، ۸.۲۱ و ۸.۷۳",
        next_topics=["استخوان‌های گونه‌ای و اشکی", "شکل کامل فک فوقانی و کام",
                     "استخوان آهیانه و گیجگاهی", "نما‌های قاعدهٔ جمجمه"],
    ),
    "hn02": dict(
        num="۲", n=2, of="۱۳",
        title="استخوان‌های صورت و طرفی جمجمه: گونه، فک تحتانی، گیجگاهی و آهیانه‌ای",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۲ — نسخهٔ بازبینی‌شده"],
        cover_topic="استخوان گونه و قوس گونه‌ای · فک تحتانی · گیجگاهی · آهیانه‌ای و ملاج‌ها",
        divider_title="از گونه تا آهیانه",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۲) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۳۳",
        outline="hn02_topics.json",
        content=("hn02_a.json", "hn02_b.json"),
        measure_idcard=True,
        anchor="hn-02",
        pdf_name="HumsYar_HeadNeck_Jalase2.pdf",
        outcome="استخوان گونه با سه سطح و سه سوراخش، فک تحتانی با شاخ و لندمارک‌هایش، "
                "شکستگی‌های شایع صورت، چهار بخش استخوان گیجگاهی با شکاف‌ها و زوائدش، و "
                "استخوان آهیانه‌ای با درزها و چهار ملاج را بشناسید.",
        intro_sources="نتر، سر و گردن (از جمله پلیت‌های ۲۴، ۲۵، ۲۷ تا ۳۱، ۳۳، ۳۵، ۳۸ تا ۴۰، ۴۲، ۷۲، ۷۵، ۸۱، ۱۲۹، BP ۱۶ و BP ۲۵) · گری، فصل ۸ "
                      "(شکل‌های ۸.۱۸، ۸.۱۹، ۸.۲۱ و ۸.۲۴)",
        next_topics=["استخوان اسفنوئید و بال بزرگ و کوچک", "استخوان پالاتین و صفحهٔ عمودی آن",
                     "استخوان پس‌سری و بخش‌های قاعده‌ای", "سوراخ‌ها و مجاری قاعدهٔ جمجمه"],
    ),
    "hn03": dict(
        num="۳", n=3, of="۱۳",
        title="اسفنوئید، پالاتین و اکسیپیتال",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۳ — استخوان‌های عمقی جمجمه"],
        cover_topic="بال بزرگ و کوچک، زوائد پتریگوئید، صفحهٔ پالاتین و بخش‌های اکسیپیتال",
        divider_title="سه استخوان، یک قاعده",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۳) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۲۰",
        outline="hn03_topics.json",
        content=("hn03_a.json", "hn03_b.json"),
        anchor="hn-03",
        pdf_name="HumsYar_HeadNeck_Jalase3.pdf",
        measure_idcard=True,
        outcome="اجزای اسفنوئید، کامی و پس‌سری، سوراخ‌های اصلی، پتریون و مسیرهای وریدی را در نماهای مختلف تشخیص دهید.",
        intro_sources="جزوهٔ جلسهٔ ۳ · نتر، پلیت‌های ۲۷، ۲۹، ۳۳ و ۳۴ · گری، شکل‌های ۸.۱۹، ۸.۲۰، ۸.۲۳، ۸.۲۶ و ۸.۲۷",
        next_topics=["حفره‌های قاعدهٔ جمجمه", "سوراخ‌ها و مجاری قاعدهٔ جمجمه", "ارتباط فضاهای جمجمه"],
    ),
    "hn04": dict(
        num="۴", n=4, of="۱۳",
        title="قاعدهٔ جمجمه و سوراخ‌های آن",
        measure_idcard=True,
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۴ — قاعدهٔ جمجمه"],
        cover_topic="اتموئید و پتروس، حفره‌ها و سوراخ‌های قاعده، ناهنجاری‌ها و شکستگی‌ها",
        divider_title="قاعدهٔ جمجمه",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۴) — مهر ۱۴۰۴",
        pages_label="بخش ۱، صفحات PDF ۱–۲۵؛ بخش ۲، صفحات PDF ۱–۱۴",
        outline="hn04_topics.json",
        content=("hn04_a.json", "hn04_b.json"),
        anchor="hn-04",
        pdf_name="HumsYar_HeadNeck_Jalase4_FINAL.pdf",
        outcome="نمای درونی و تحتانی قاعده، پتروس، گذرگاه‌ها و مباحث بالینی جزوه را بشناسید.",
        intro_sources="جزوهٔ جلسهٔ ۴، دو بخش · نتر، پلیت‌های ۲۹–۳۴، ۶۱، ۶۳ و ۱۲۵ · گری، شکل‌های ۸.۲۱، ۸.۲۳ و ۸.۲۵–۸.۲۷",
        next_topics=["مهره‌های گردنی", "مفاصل و رباط‌های گردن", "فاسیاها و فضاهای گردنی"],
    ),
    "hn05": dict(
        num="۵", n=5, of="۱۳",
        title="گردن: مهره‌ها، فاسیاها و فضاها",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۵ — گردن"],
        cover_topic="مهره‌های گردنی، مفاصل، فاسیاها، فضاها و استخوان لامی",
        divider_title="از مهره تا فاسیا",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۵) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۴۵",
        outline="hn05_topics.json",
        content=("hn05_a.json", "hn05_b.json"),
        anchor="hn-05",
        measure_idcard=True,
        pdf_name="HumsYar_HeadNeck_Jalase5_FINAL.pdf",
        outcome="مهره‌های گردنی، مفاصل و رباط‌ها، فاسیاها و فضاهای گردن و استخوان لامی را بشناسید.",
        intro_sources="جزوهٔ جلسهٔ ۵ · نتر، پلیت‌های ۴۳، ۴۴، ۴۶، ۴۷، ۵۱، ۵۶ و ۵۷ · گری، شکل‌های ۸.۱۵۸–۸.۱۶۰",
        next_topics=[],
    ),
    "hn06": dict(
        num="۶", n=6, of="۱۳",
        title="عضلات گردن: لامی، پیش‌مهره‌ای و خلفی",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۶ — عضلات گردن"],
        cover_topic="عضلات بالا و زیر لامی، پیش‌مهره‌ای، اسکالن و خلف گردن",
        divider_title="لایه‌های عضلانی گردن",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۶) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۲۰",
        outline="hn06_topics.json",
        content=("hn06_a.json", "hn06_b.json"),
        anchor="hn-06",
        measure_idcard=True,
        pdf_name="HumsYar_HeadNeck_Jalase6.pdf",
        outcome="عضلات لامی، پیش‌مهره‌ای و اسکالن، لایه‌های عضلات خلف گردن و مثلث زیرپس‌سری را بشناسید.",
        intro_sources="جزوهٔ جلسهٔ ۶ · نتر، پلیت‌های ۵۳ تا ۵۵، ۱۹۵ و ۱۹۷ · گری، شکل‌های ۸.۱۶۳، ۸.۱۶۴ و ۸.۱۸۵",
        next_topics=[],
    ),
    "hn07": dict(
        num="۷", n=7, of="۱۳",
        title="مثلث‌های گردن و فاسیای گردنی",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۷ — مثلث‌های گردن"],
        cover_topic="مثلث‌های قدامی و خلفی، لایه‌های فاسیا و فضاهای گردنی",
        divider_title="نقشهٔ مثلث‌ها",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۷) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۲۰",
        outline="hn07_topics.json",
        content=("hn07_a.json", "hn07_b.json"),
        anchor="hn-07",
        pdf_name="HumsYar_HeadNeck_Jalase7.pdf",
        outcome="",
        intro_sources="نتر، سر و گردن (پلیت ۲۲–۱۷۷) · گری، فصل ۸",
        next_topics=[],
    ),
    "hn08": dict(
        num="۸", n=8, of="۱۳",
        title="عروق گردنی",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۸ — عروق گردنی"],
        cover_topic="کاروتید مشترک و شاخه‌ها، ژوگولار داخلی و خارجی، سابکلاوین و مهره‌ای",
        divider_title="شریان‌ها و وریدهای گردن",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۸) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۱۳",
        outline="hn08_topics.json",
        content=("hn08_a.json", "hn08_b.json"),
        anchor="hn-08",
        pdf_name="HumsYar_HeadNeck_Jalase8.pdf",
        outcome="",
        intro_sources="نتر، سر و گردن (پلیت ۲۲–۱۷۷) · گری، فصل ۸",
        next_topics=[],
    ),
    "hn09": dict(
        num="۹", n=9, of="۱۳",
        title="اعصاب گردن و غدهٔ تیروئید",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۹ — اعصاب گردن و تیروئید"],
        cover_topic="شبکهٔ گردنی، اعصاب جمجمه‌ای در گردن، تیروئید و پارا تیروئید",
        divider_title="اعصاب و تیروئید",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۹) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۱۵",
        outline="hn09_topics.json",
        content=("hn09_a.json", "hn09_b.json"),
        anchor="hn-09",
        pdf_name="HumsYar_HeadNeck_Jalase9.pdf",
        outcome="",
        intro_sources="نتر، سر و گردن (پلیت ۲۲–۱۷۷) · گری، فصل ۸",
        next_topics=[],
    ),
    "hn10": dict(
        num="۱۰", n=10, of="۱۳",
        title="اسکالپ و ناحیهٔ تمپورال",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۱۰ — اسکالپ و ناحیهٔ تمپورال"],
        cover_topic="لایه‌های اسکالپ، عروق و اعصاب، فاسیای تمپورال و عضلهٔ تمپورالیس",
        divider_title="پوست سر و ناحیهٔ گیجگاهی",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۱۰) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۸",
        outline="hn10_topics.json",
        content=("hn10_a.json", "hn10_b.json"),
        anchor="hn-10",
        pdf_name="HumsYar_HeadNeck_Jalase10.pdf",
        outcome="",
        intro_sources="نتر، سر و گردن (پلیت ۲۲–۱۷۷) · گری، فصل ۸",
        next_topics=[],
    ),
    "hn11": dict(
        num="۱۱", n=11, of="۱۳",
        title="صورت: عضلات، عصب صورت و غدد بزاقی",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۱۱ — صورت"],
        cover_topic="عضلات صورت، عصب هفتم و شاخه‌ها، شریان صورت، پاروتید و غدد بزاقی",
        divider_title="صورت",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۱۱) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۲۰",
        outline="hn11_topics.json",
        content=("hn11_a.json", "hn11_b.json"),
        anchor="hn-11",
        pdf_name="HumsYar_HeadNeck_Jalase11.pdf",
        outcome="",
        intro_sources="نتر، سر و گردن (پلیت ۲۲–۱۷۷) · گری، فصل ۸",
        next_topics=[],
    ),
    "hn12": dict(
        num="۱۲", n=12, of="۱۳",
        title="جنین‌شناسی جمجمه",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۱۲ — جنین‌شناسی جمجمه"],
        cover_topic="قوس‌های حلقی، مشتقات آن‌ها، رشد نوروکرانیوم و ملاحظات بالینی",
        divider_title="از قوس تا جمجمه",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۱۲) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۱۵",
        outline="hn12_topics.json",
        content=("hn12_a.json", "hn12_b.json"),
        anchor="hn-12",
        pdf_name="HumsYar_HeadNeck_Jalase12.pdf",
        outcome="",
        intro_sources="نتر، سر و گردن (پلیت ۲۲–۱۷۷) · گری، فصل ۸",
        next_topics=[],
    ),
    "hn13": dict(
        num="۱۳", n=13, of="۱۳",
        title="آناتومی عملی: جدول برچسب‌ها و جمع‌بندی",
        cover_title=["آناتومی سر و گردن", "جلسهٔ ۱۳ — آناتومی عملی"],
        cover_topic="نماهای کلیدی جمجمه و گردن، برچسب‌های عملی و مرور نهایی",
        divider_title="جمع‌بندی عملی",
        divider_sub="جزوهٔ درس · نتر · گری",
        lecture="جزوهٔ درس (جلسهٔ ۱۳) — مهر ۱۴۰۴",
        pages_label="صفحه‌های ۱–۵۶",
        outline="hn13_topics.json",
        content=("hn13_a.json", "hn13_b.json"),
        anchor="hn-13",
        pdf_name="HumsYar_HeadNeck_Jalase13.pdf",
        outcome="",
        intro_sources="نتر، سر و گردن (پلیت ۲۲–۱۷۷) · گری، فصل ۸",
        next_topics=[],
    ),
}


# --------------------------------------------------------------------- helpers
def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fa(n) -> str:
    return str(n).translate(K.FA_DIGITS)


def _compress(nums: list[int]) -> str:
    nums = sorted(nums)
    if len(nums) == 1:
        return fa(nums[0])
    if nums == list(range(nums[0], nums[-1] + 1)):
        return f"{fa(nums[0])}–{fa(nums[-1])}"
    return "، ".join(fa(p) for p in nums)


def page_range(pages, part_labels: bool = False) -> str:
    """`pages` holds lecture page numbers; 100+n is page n of the second file.

    Session 8 is printed from two lecture files, so a topic has to be able to
    say «بخش ۲: ۱–۳» instead of pretending the second file continues the first.
    """
    pages = sorted(int(p) for p in pages or [])
    if not pages:
        return "—"
    first = [p for p in pages if p < 100]
    second = [p - 100 for p in pages if p >= 100]
    chunks = []
    if first:
        chunks.append(("بخش ۱: " if part_labels else "") + _compress(first))
    if second:
        chunks.append("بخش ۲: " + _compress(second))
    return " · ".join(chunks)


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
        ("متن اصلی: جزوهٔ درس · توضیح تکمیلی با ارجاع جداگانه" if cfg['n'] in (1, 2, 4, 5) else
         "متن: جزوهٔ درس + گری، آناتومی برای دانشجویان، ویراست ۳"),
        "تصویر: نتر، اطلس آناتومی انسان، ویراست ۸ · گری، آناتومی برای دانشجویان، ویراست ۳",
        ("نسخهٔ نهایی ویرایشی و آموزشی — ۳۱ اکتبر ۲۰۲۶" if cfg['n'] in (4,5) else "نسخهٔ آموزشی به‌روزشده برای جزوه‌نویسان" if cfg['n'] == 1 else "نسخهٔ ۰٫۱ — پیش‌نویس ویرایشی"),
    ]
    yy = K.A4H * 0.375
    for t in lines:
        c.drawCentredString(K.A4W / 2, yy, K.shape(t))
        yy -= 18
    c.setFont("VazirL", 8.4)
    c.setFillColor(K.HexColor("#64748b"))
    c.drawCentredString(K.A4W / 2, K.A4H * 0.12,
                        K.shape("سند کاری درس آناتومی سر و گردن — نسخهٔ آموزشی" if cfg['n'] in (1, 4, 5) else "سند کاری درس آناتومی سر و گردن — پیش‌نویس ویرایشی"))


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
    """How this booklet is built: structure, citation law, figure placement."""
    book.h1("ساختار این جزوه و قاعدهٔ خواندن آن", anchor="front-colophon",
            kicker="قبل از شروع بخوانید")

    book.label_card(
        "این جزوه چگونه ساخته شده است",
        [
            {"label": "قاعدهٔ ساخت",
             "text": ("متن رونویسی‌شدهٔ جزوه با برچسب منبع، جدا از توضیحات تکمیلی در مبحث‌ها درج شده است؛ تطبیق نهایی واژه‌به‌واژه در حال انجام است. هر مبحث شناسنامه، متن، شکل و برگهٔ تحویل دارد." if cfg["n"] == 3 and os.environ.get("HUMSYAR_HN03_WIP") == "1" else
                      "محتوای درس بازنویسی و در مبحث‌های مستقل تنظیم شده است؛ این نسخه نقل کامل و واژه‌به‌واژهٔ منبع نیست. هر مبحث شناسنامه، متن، شکل و برگهٔ تحویل دارد." if cfg["n"] == 3 else
                     "جلسهٔ ۵ بر پایهٔ نسخهٔ قبلی بازبینی و به‌روز شده است. متن جزوه با اصل منبع مقابله شد؛ جدول‌ها و کادرهای آموزشی از نقل جدا هستند. اختلاف‌های علمی و محدودیت تصاویر در گزارش همراه ثبت‌اند. این ویرایش تأیید مستقل متخصص بالینی یا راهنمای درمان نیست." if cfg["n"] == 5 else
                     "متن هر دو بخش با تصاویر منبع مقابله شده است؛ سه اصلاح لفظیِ تیترها در گزارش ثبت شده‌اند. جدول‌ها و کادرهای آموزشی از نقل منبع جدا هستند. بازبینی تمام صفحات خروجی و شکل‌های مرتبط در گزارش همراه مستند است. این بازبینی ویرایشی، تأیید مستقل متخصص بالینی یا راهنمای درمان نیست." if cfg["n"] == 4 else
                     "متن و مرور جزوه رونویسی و صفحه‌های منبع و خروجی به‌صورت تصویری بررسی شده‌اند. این نسخه برای کار جزوه‌نویسان آماده شده؛ مقابلهٔ مستقل نهایی واژه‌به‌واژه هنوز انجام نشده است. شناسنامه‌ها و شرح شکل‌ها توضیح تکمیلی‌اند." if cfg["n"] in (1, 2) else
                     "پیش‌نویس: متن صفحه‌های محتوایی و مرور جزوه رونویسی اولیه شده است؛ مقابلهٔ مستقل واژه‌به‌واژه و بررسی جامع جای تصاویر هنوز کامل نشده است. شناسنامه‌ها و شرح شکل‌ها توضیح تکمیلی‌اند.")},
            {"label": "جای شکل‌ها",
             "text": ("قاب‌های قبلی در موضوع خود حفظ شده‌اند و نماهای مرجع به همان مباحث افزوده شده‌اند. برخی قاب‌های بزرگ به صفحهٔ بعد منتقل می‌شوند؛ توضیحِ راهنما درون همان قاب است. کیفیت ریزنوشته‌های تصاویر جزوه یکسان نیست." if cfg["n"] == 5 else
                      "شکل‌های آموزشی هر دو بخش به‌صورت قاب مستقل نزدیک موضوع مربوط جای‌گذاری شده‌اند؛ برخی قاب‌ها به صفحهٔ بعد منتقل می‌شوند." if cfg["n"] == 4 else
                      "قاب‌های مرتبط در همان مبحث یا نزدیک متن آمده‌اند؛ بعضی قاب‌های بزرگ به صفحهٔ بعد منتقل می‌شوند. برش‌ها و شرح‌ها بازبینی تصویری شده‌اند." if cfg["n"] in (1, 2) else
                      "شکل‌ها نزدیک متن مرتبط قرار گرفته‌اند؛ بررسی کامل جای همهٔ آن‌ها در این پیش‌نویس هنوز تمام نشده است." if cfg["n"] == 2 else
                      "قاب‌ها در مبحث مرتبط قرار گرفته‌اند؛ ممکن است به صفحهٔ بعد منتقل شوند و فاصلهٔ هر شکل تا توضیح آن نیازمند بررسی دیداری است." if cfg["n"] == 3 and os.environ.get("HUMSYAR_HN03_WIP") == "1" else
                      "هر شکل دقیقاً پس از پاراگرافی می‌آید که آن را توضیح می‌دهد؛ هیچ شکلی از متن خودش دور نمی‌افتد و شکل‌ها یک‌جا جمع نمی‌شوند.")},
            {"label": "منابع متن",
             "text": (f"{cfg['lecture']}؛ رونویسی منبع و توضیحات افزوده با ارجاع مجزا درج شده‌اند. نتر و گری برای شکل‌ها و روابط تصویری استفاده شده‌اند." if cfg["n"] == 3 and os.environ.get("HUMSYAR_HN03_WIP") == "1" else
                      f"{cfg['lecture']}؛ متن بازنویسی‌شده از جزوه است. نتر و گری برای شکل‌ها و مقایسهٔ روابط تصویری استفاده شده‌اند." if cfg["n"] == 3 else
                      f"{cfg['lecture']} · نتر، اطلس آناتومی انسان (نگرش منطقه‌ای) · گری، آناتومی برای دانشجویان")},
            {"label": "منابع تصویر",
             "text": f"{fa(stats['lec'])} تصویر از جزوهٔ درس · {fa(stats['netter'])} از نتر · "
                     f"{fa(stats['grays'])} از گری. هر جلسه از هر دو کتاب تصویر دارد؛ "
                     "اولویت‌بندی بین دو کتاب وجود ندارد."},
            {"label": "واحد شمارش",
             "text": "واحد این جزوه «مبحث» است: هر مبحث یک شماره، یک عنوان و یک سطر در فهرست "
                     "دارد، و ارجاع‌دهی و ویرایش روی همین شماره انجام می‌شود."},
        ],
        accent=K.TEAL, tint=K.TEAL_LL, kicker="شناسنامه",
        footer=("جزوهٔ مادر برای کار جزوه‌نویسان" if cfg["n"] in (1, 2, 4, 5) else "پیش‌نویس ویرایشی — بازبینی علمی در جریان"),
    )

    book.h2("قاعدهٔ ارجاع و علامت‌گذاری", anchor="front-cite")
    book.numbered([
        (("شمارهٔ صفحهٔ جزوه شمارهٔ صفحهٔ فایل PDF است؛ شمارهٔ چاپی پایین جزوه در جلسهٔ ۳ یک عدد کمتر است. " if cfg["n"] == 3 else
          "شمارهٔ صفحهٔ جزوه، شمارهٔ صفحهٔ فایل PDF منبع است. ") +
         "هر بلوک متنی ارجاع دارد؛ ارجاع نتر شمارهٔ پلیت و صفحهٔ PDF و ارجاع گری شمارهٔ شکل و صفحهٔ چاپی را نشان می‌دهد."),
        "هر قاب تصویر چهار بخش دارد: عنوان فارسی، ارجاع کامل، کپشن اصلی انگلیسی (برای "
        "نتر و گری) و توضیح فارسی که همان تصویر را به متن مبحث وصل می‌کند.",
        ("برچسب‌های دوزبانه نام ساختارهای تصویرند؛ در شکل‌های بدون برچسب، موارد راهنمای جهت‌یابی‌اند و در توضیح قاب ذکر شده‌اند." if cfg["n"] == 3 else "برچسب‌های دوزبانه نام ساختارهای تصویرند؛ در شکل‌های بدون برچسب، موارد راهنمای جهت‌یابی‌اند و الزاماً برچسب چاپ‌شدهٔ خود تصویر نیستند."),
        ("عنوان انگلیسی هر شکل برای شناسایی منبع آمده است؛ شرح فارسی و جدول‌های آموزشی، افزودهٔ مستقل‌اند." if cfg["n"] == 4 else "جمله‌های انگلیسی داخل کادر با خط کنار، عیناً از کتاب نقل شده‌اند و ترجمه نشده‌اند."),
        "کادر «یادداشت عضو تیم» در پایان هر مبحث، جای نوشتن حاشیه و پرسش ویراستار است.",
    ])


def toc_page(book: PDFBook, cfg: dict, outline: dict, toc_pages: dict) -> None:
    book.new_page()
    book.h1("فهرست مطالب", anchor="toc", kicker="راهنمای سند")
    book.paragraph("شمارهٔ روبه‌روی هر سطر، شمارهٔ صفحهٔ همین سند است.",
                   TextStyle(size=9, color=K.MUTED))
    rows = [
        ("۰", "شناسنامهٔ سند و قاعدهٔ خواندن آن", "front-colophon", 0),
        ("۰", "قاعدهٔ ارجاع به تصویر و متن", "front-cite", 1),
        (cfg["num"], f"فصل {cfg['num']} — جلسهٔ {cfg['num']}: {cfg['cover_topic']}",
         cfg["anchor"], 0),
    ]
    for i, t in enumerate(outline["topics"], start=1):
        rows.append((fa(f"{i:02d}"), t["title"], t["topic_id"], 1))
    rows += [("پ", "جمع‌بندی، چک‌لیست و برگهٔ تحویل", "hn-summary", 0),
             ("پ", "قدم بعدی: چه چیزی در جلسهٔ بعد می‌آید", "hn-next", 1)]
    step = 20 if len(rows) <= 26 else 17
    for num, title, anchor, indent in rows:
        pg = toc_pages.get(anchor)
        book.toc_row(num, title, fa(pg) if pg else "—",
                     indent=indent * 18, accent=K.TEAL if indent == 0 else K.BLUE,
                     step=step)


def session_intro(book: PDFBook, cfg: dict, outline: dict, stats: dict) -> None:
    book.h1(f"جلسهٔ {cfg['num']} در یک نگاه", anchor="hn-glance", kicker="نقشهٔ جلسه")
    book.label_card(
        "این جلسه چه چیزی را می‌سازد",
        [
            {"label": "موضوع جلسه", "text": cfg["title"]},
            {"label": "دامنهٔ صفحه‌های جزوه", "text": (f"{cfg['pages_label']} — شماره‌ها مربوط به دو فایل مستقل‌اند." if cfg["n"] == 4 else
                                                    f"{cfg['pages_label']} — صفحه‌های منبع و خروجی بازبینی تصویری شده‌اند؛ مقابلهٔ مستقل نهایی لفظی باقی است." if cfg["n"] in (1, 2) else
                                                    f"{cfg['pages_label']} — مقابلهٔ لفظی و بررسی جامع شکل‌ها ناتمام است." if cfg["n"] == 2 else
                                                    f"{cfg['pages_label']} — همهٔ صفحه‌های این دامنه بررسی و در مبحث‌ها توزیع شده‌اند.")},
            {"label": "تعداد مبحث", "text": f"{fa(len(outline['topics']))} مبحث"},
            {"label": "تعداد تصویر",
             "text": f"{fa(stats['plates'])} قاب تصویر: {fa(stats['lec'])} از جزوه، "
                     f"{fa(stats['netter'])} از نتر، {fa(stats['grays'])} از گری."},
            {"label": "خروجی این جلسه",
             "text": cfg.get("outcome", "شناخت نورون و زوائدش، انتقال آکسونی، سیناپس، شش نوع "
                                       "سلول گلیال، و تفاوت میلین‌سازی در CNS و PNS.")},
        ],
        accent=K.TEAL, tint=K.TEAL_LL, kicker="شناسنامهٔ جلسه",
        footer=f"منابع: {cfg['lecture']} · {cfg.get('intro_sources', 'نتر، سر و گردن · گری، فصل ۸')}",
    )
    # how to read this session: three short rules that keep the reader oriented
    # and fill the page the intro card leaves half empty
    book.h3("راهنمای خواندن این جلسه")
    book.bullets([
        "هر مبحث با یک شناسنامه باز می‌شود: جای این مبحث در جزوه، و چیزی که باید از آن "
        "یاد گرفته شود.",
        ("متن و قاب‌های شکل در مبحث مربوط قرار دارند؛ قاب‌های بزرگ ممکن است به صفحهٔ بعد منتقل شوند." if cfg["n"] == 4 or (cfg["n"] == 3 and os.environ.get("HUMSYAR_HN03_WIP") == "1") else
         "بعد متن ساخت‌یافته می‌آید و شکل‌ها همان‌جا کنار متن خودشان می‌نشینند؛ هیچ شکلی از متنش جدا نمی‌شود."),
        "پایان هر مبحث یک کادر یادداشت دارد؛ همان‌جا بنویسید چه چیزی را باید دوباره "
        "بخوانید.",
        "آخرین برگهٔ هر مبحث برگهٔ تحویل است: منابع خوانده‌شده، پنج کار پیش از تحویل، و "
        "پرسش باز. جدول نقشه و چک‌لیست پایان جلسه برای مرور سریع‌اند."])
    rows = []
    for i, t in enumerate(outline["topics"], start=1):
        rows.append([fa(f"{i:02d}"), t["title"], page_range(t.get("pages", []), part_labels=cfg["n"] == 4),
                     t.get("gist", "")])
    # the map table is 17 rows tall: it gets a page of its own, under its own
    # title, instead of being pushed down and leaving the title behind
    need = book.table_needs(["#", "مبحث", "صفحه‌های جزوه", "در یک جمله"], rows,
                            [K.CONTENT_W * 0.06, K.CONTENT_W * 0.44,
                             K.CONTENT_W * 0.14, K.CONTENT_W * 0.36],
                            "جدول ۱-۰ — نقشهٔ مبحث‌ها", "نقشهٔ محتوایی این جزوه", 8.0)[3]
    if book.bottom_limit() - book.y < need + 90:
        book.new_page()
    book.h2("بازگشت به متن درس: هر مبحث و صفحه‌هایش", anchor="hn-map")
    emit_table(book, ["#", "مبحث", "صفحه‌های جزوه", "در یک جمله"],
               rows, widths=[K.CONTENT_W * 0.06, K.CONTENT_W * 0.44,
                             K.CONTENT_W * 0.14, K.CONTENT_W * 0.36],
               size=8.0, caption="جدول ۱-۰ — نقشهٔ مبحث‌ها",
               src="نقشهٔ محتوایی این جزوه")


def topic_head(book: PDFBook, t: dict, idx: int, total: int,
               after: float = 0.0, part_labels: bool = False) -> None:
    # the topic title keeps the identity card that opens the topic with it
    book.ensure(120)
    book.h2(t["title"], anchor=t["topic_id"],
            keep_with=min(after, book.usable_height() - 140))
    meta = (f"مبحث {fa(idx)} از {fa(total)} · صفحه‌های جزوه: {page_range(t.get('pages', []), part_labels=part_labels)}")
    if t.get("prereq"):
        meta += " · پیش‌نیاز: " + t["prereq"]
    book.paragraph(meta, TextStyle(size=8.3, color=K.MUTED, justify=False))
    book.spacer(2)


# --------------------------------------------------------------- team notes
NOTE_TITLE = "یادداشت عضو تیم — چرا این مبحث اهمیت دارد؟"


def with_notes(blocks: list, idx: int) -> list:
    """Every topic gets one lined note box for the reader's own writing.

    The box sits right after the topic's identity card, i.e. exactly where the
    reader has just read what the topic is about and before the first figure;
    it is added here rather than in the content files so that all sessions get
    the same box in the same place and no content file has to be rewritten.
    """
    out = list(blocks)
    if any(b.get("type") == "note" for b in out):      # a hand-placed box wins
        return out
    note = {"type": "note", "size": "medium", "title": NOTE_TITLE,
            "tag": f"مبحث {fa(idx)}"}
    # the box closes the topic and sits right before its delivery sheet, the
    # same place the note pages have in the physiology notebook: the reader
    # writes there after finishing the topic and before signing it off.
    pos = next((i for i, b in enumerate(out) if b.get("type") == "handoff"), None)
    out.insert(pos if pos is not None else len(out), note)
    return out


def emit_table(book: PDFBook, head, rows, widths=None, caption: str = "",
               src: str = "", size: float = 8.5) -> None:
    """Draw a table so that no table is ever torn between two pages.

    The table first tries to fit, whole, into the room left on the current page
    (shrinking a fraction of a point if that is what it takes). Only a table
    taller than a whole page is handed over in parts, and then every part is a
    complete table with its own header and its own caption.
    """
    rows = list(rows)
    page_room = book.usable_height() - 14

    def measure(sz):
        return book.table_needs(head, rows, widths, caption, src, sz)

    avail = book.bottom_limit() - book.y - 6
    for sz in (size, size - 0.4, size - 0.8, size - 1.2, 6.8):
        _, _, _, total = measure(sz)
        if total <= avail:
            book.table(head, rows, widths=widths, caption=caption, src=src, size=sz)
            return
    # it cannot fit under what is left: start a fresh page, unless almost the
    # whole page is still free (then splitting is better than a blank page)
    if avail < page_room * 0.55:
        book.new_page()
        avail = page_room
    head_h, row_hs, cap_reserve, _ = measure(size)
    groups, cur, cur_h, room = [], [], head_h + cap_reserve, avail
    for row, h in zip(rows, row_hs):
        if cur and cur_h + h > room:
            groups.append((cur, room))
            cur, cur_h, room = [row], head_h + cap_reserve, page_room
        else:
            cur.append(row)
            cur_h += h
    if cur:
        groups.append((cur, room))
    total = len(groups)
    for n, (group, _room) in enumerate(groups, start=1):
        cap = caption
        if total > 1:
            cap = f"{caption} — بخش {fa(n)} از {fa(total)}"
        book.table(head, group, widths=widths, caption=cap, src=src, size=size)


# ------------------------------------------------------- heading orphan control
def _block_height(book: PDFBook, b: dict | None) -> float:
    """Rough height in points of the block that follows a heading.

    A heading may only be placed if this much room is left under it, so a
    heading can never sit alone at the foot of a page.
    """
    if not b:
        return 0.0
    kind = b.get("type")
    if kind == "p":
        lines = book.wrap(b.get("text", ""), "Vazir", 10.4, K.CONTENT_W)
        return min(len(lines), 4) * 17.6 + 16
    if kind in ("ul", "ol"):
        items = b.get("items", [])[:2]
        return sum(max(1, len(book.wrap(x, "Vazir", 10.4, K.CONTENT_W - 22))) * 17.6
                   for x in items) + 18
    if kind == "plate":
        return (b.get("max_h", 132)) * MM + 96
    if kind == "table":
        return 60 + sum(20 for _ in b.get("rows", [])[:3])
    if kind == "callout":
        return 70
    if kind == "path":
        return 90
    if kind == "idcard":
        # a session that opts in measures its own cards, so a tall identity card
        # is never left behind at the foot of a page; session 1 keeps its
        # approved pagination
        if getattr(book, "measure_idcard", False):
            return book.card_height(b.get("rows", []), footer=b.get("footer", "")) + 4
        return 150
    if kind == "handoff":
        return 170
    if kind == "note":
        return 90
    return 60.0


# ----------------------------------------------------------------- block render
def render_blocks(book: PDFBook, blocks, cfg: dict) -> None:
    for pos, b in enumerate(blocks):
        trace_before = book.page
        kind = b.get("type")
        after = _block_height(book, blocks[pos + 1] if pos + 1 < len(blocks) else None)
        # the citation line belongs to its own block: the paragraph or list
        # reserves room for it, so the two never land on different pages
        cite_room = 14
        if kind == "p":
            book.paragraph(b["text"], TextStyle(space_after=2),
                           keep_with=cite_room if b.get("src") else 0)
            if b.get("src"):
                book.source_line(b["src"])
        elif kind == "ul":
            book.bullets(b["items"], keep_with=cite_room if b.get("src") else 0)
            book.source_line(b.get("src", ""))
            book.spacer(3)
        elif kind == "ol":
            book.numbered(b.get("display_items", b["items"]),
                          start=b.get("display_start", 1),
                          keep_with=cite_room if b.get("src") else 0)
            book.source_line(b.get("src", ""))
            book.spacer(3)
        elif kind == "h3":
            # Session 3 may have a page label followed by one or more headings.
            # Reserve the whole chain plus the first content block: reserving
            # just the next heading leaves the page label orphaned when that
            # heading moves with its paragraph. Other sessions keep their layout.
            extra = cite_room if b.get("src") else 0
            if cfg["n"] in (3, 4):
                idx = pos + 1
                after = 0.0
                while idx < len(blocks) and blocks[idx].get("type") == "h3":
                    following = blocks[idx]
                    lines = book.wrap(following.get("text", ""), "VazirB", 11.4, K.CONTENT_W - 18)
                    after += 16 + len(lines) * 11.4 * 1.6 + 12
                    after += cite_room if following.get("src") else 0
                    idx += 1
                if idx < len(blocks):
                    nxt = blocks[idx]
                    if nxt.get("type") == "p":
                        lines = book.wrap(nxt.get("text", ""), "Vazir", 10.4, K.CONTENT_W)
                        after += len(lines) * 17.6 + 16
                    else:
                        after += _block_height(book, nxt)
            book.h3(b["text"], keep_with=min(after + 12 + extra, book.usable_height() - 90))
            if b.get("src"):
                book.source_line(b["src"])
        elif kind == "callout":
            book.callout(b["text"], kind=b.get("kind", "key"), title=b.get("title"))
            if b.get("src"):
                book.source_line(b["src"])
            book.spacer(2)
        elif kind == "plate":
            # Optional minimum preserves readable figures instead of shrinking
            # them into the last available space on a nearly full page.
            if b.get("min_img_h"):
                book.ensure(b["min_img_h"] * MM + 130)
            # In session 2, reference plates contain many small labels.  Do not
            # squeeze them into the remaining space below another large figure.
            elif cfg["n"] == 2 and b.get("asset", "").endswith(
                ("hn02_netter_p35.jpeg", "hn02_netter_p38.jpeg", "hn02_netter_p39.jpeg", "hn02_netter_p42.jpeg")
            ):
                book.ensure(120 * MM + 220)
            elif cfg["n"] == 2 and b.get("book") == "netter" and b.get("max_h", 132) >= 100:
                book.ensure(85 * MM + 210)
            # a tall, narrow figure would be shrunk into whatever room is left
            # and become unreadable; such plates declare ``fresh`` and start a
            # page of their own so the figure keeps its full size.
            if b.get("fresh"):
                # A short preceding paragraph must not create an almost empty
                # page just to honour a fresh-plate hint.  Only session 3 opts
                # into this threshold; the plate still has at least ~80% of a
                # page for its image and caption, and other sessions are stable.
                enough_room = (cfg["n"] == 3 and
                               book.bottom_limit() - book.y >= book.usable_height() - 140)
                if not enough_room:
                    book.new_page()
            book.anat_plate(
                REPO / b["asset"],
                b["title"], b["citation"], b.get("en_caption", ""),
                b.get("fa_text", ""), labels=[tuple(x) for x in b.get("labels", [])],
                view=b.get("view", ""), src=b.get("src", ""),
                max_h=(132 if cfg["n"] == 2 and b.get("asset", "").endswith(
                    ("hn02_netter_p35.jpeg", "hn02_netter_p38.jpeg", "hn02_netter_p39.jpeg", "hn02_netter_p42.jpeg")
                ) else b.get("max_h", 132)) * MM, en_body=b.get("en_body", ""),
            )
        elif kind == "path":
            book.path_steps(b["steps"], title=b.get("title", "مسیر گام‌به‌گام"))
            if b.get("src"):
                book.source_line(b["src"])
            book.spacer(2)
        elif kind == "table":
            emit_table(book, b["head"], b["rows"], caption=b.get("caption", ""),
                       src=b.get("src", ""), widths=b.get("widths"))
            book.spacer(3)
        elif kind == "note":
            sizes = {"small": 32, "medium": 48, "large": 68}
            want = sizes.get(b.get("size", "medium"), 48)
            # the box closes its topic and must stay with the delivery sheet that
            # follows it, so a delivery sheet's worth of room is reserved first.
            reserve = 70 if b.get("keep_with_next") else 0
            if reserve:
                book.ensure((want + reserve) * MM)
            # it is a blank ruled area, so it can shrink into what is left
            # instead of jumping to the next page and leaving a hole; and when
            # the delivery sheet after it has to move over anyway, the box grows
            # into the room that would otherwise stay empty.
            room = (book.bottom_limit() - book.y) / MM - 6 - reserve
            if room < want:
                # a box that would end up tiny also has to jump to the next
                # page, and then it would sit at the top of an almost empty
                # page; start that page first so the area keeps its height.
                if room < 34:
                    book.new_page()
                    room = (book.bottom_limit() - book.y) / MM - 6 - reserve
                if room < want:
                    want = max(24, room)
            book.spacer(4)
            book.note_box(want, b.get("title", "یادداشت عضو تیم"), tag=b.get("tag", ""))
        elif kind == "idcard":
            book.label_card(b.get("title", "شناسنامهٔ مبحث"), b.get("rows", []),
                            accent=K.TEAL, tint=K.TEAL_LL, kicker=b.get("kicker", ""),
                            footer=b.get("footer", ""))
        elif kind == "handoff":
            q = str(b.get("question", "")).strip()
            for _prefix in ("پرسش باز:", "پرسش باز :"):
                if q.startswith(_prefix):
                    q = q[len(_prefix):].strip()
            srcs = b.get("sources", "")
            if isinstance(srcs, (list, tuple)):
                srcs = " · ".join(str(x).strip() for x in srcs if str(x).strip())
            book.handoff_sheet(b.get("title", "برگهٔ تحویل مبحث"),
                               srcs, b.get("checklist", []),
                               b.get("open", ""),
                               kicker=b.get("kicker", ""),
                               note=(f"پرسش باز: {q}" if q else ""))
        else:
            raise ValueError(f"unknown block type: {kind}")
        if hasattr(book, 'block_trace'):
            book.block_trace.append(dict(topic_id=book.trace_topic, position=pos,
                type=kind, text=b.get('text',''), source=b.get('src',''),
                asset=b.get('asset'), page_before=trace_before, page_end=book.page,
                block_sha256=hashlib.sha256(json.dumps(b,ensure_ascii=False,sort_keys=True).encode()).hexdigest()))



def summary(book: PDFBook, content: dict, outline: dict, cfg: dict) -> None:
    """Closing checklist built from the session's own blocks."""
    # the closing section always opens on a fresh page: a section title that
    # lands on the last line of a topic page reads as a mistake.
    book.new_page()
    book.h1("جمع‌بندی، چک‌لیست و برگهٔ تحویل", anchor="hn-summary", kicker="پایان جلسه")
    book.paragraph(
        "این چک‌لیست از پرسش‌های خودِ مبحث‌های بالا ساخته شده است: هر ردیف یک مبحث، و ستون "
        "دوم همان چیزی است که باید بتوانید بی‌آنکه به متن نگاه کنید توضیح دهید. هر ردیف را "
        "که نتوانستید، همان مبحث را دوباره بخوانید و بعد برگهٔ تحویل آن را پر کنید.")
    rows = []
    for i, t in enumerate(outline["topics"], start=1):
        gist = (t.get("gist") or t["title"]).rstrip(".")
        rows.append([f"مبحث {fa(i)} — {t['title']}", gist + "؟", "☐"])
    emit_table(
        book, ["چک‌لیست خودآزمایی", "می‌توانم این را توضیح دهم؟", "☐"],
        rows, widths=[K.CONTENT_W * 0.30, K.CONTENT_W * 0.58, K.CONTENT_W * 0.12],
        caption=f"جدول {cfg['num']}-۷ — چک‌لیست خودآزمایی جلسهٔ {cfg['num']}",
        src="ساخته‌شده از مبحث‌های این جزوه",
    )
    book.callout(
        "پایان هر مبحث یک برگهٔ تحویل دارد: منابعی که برای آن مبحث خوانده شده، پنج کار پیش از "
        "تحویل، و هر ابهام یا اختلافی که باید در بازبینی روشن شود. جزوه وقتی تمام است که همهٔ "
        "این برگه‌ها امضا شده باشند.",
        kind="key", title="برگهٔ تحویل هر مبحث")


def next_steps(book: PDFBook, cfg: dict) -> None:
    book.h1("قدم بعدی: چه چیزی در جلسهٔ بعد می‌آید", anchor="hn-next", kicker="ادامهٔ کار")
    book.paragraph(
        ("جلسهٔ چهارم، قاعدهٔ جمجمه را تکمیل می‌کند؛ موضوع جلسهٔ پنجم گردن است و منبع مستقل دارد." if cfg["n"] == 4 else
         f"این سند جلسهٔ {cfg['num']} از {cfg['of']} است و جلسهٔ بعد از همان نقطهٔ صفحه‌ای "
         f"ادامه می‌دهد که این جلسه در آن ایستاده است."))
    book.bullets(
        ["ساختارهای بعدی: " + " · ".join(cfg.get("next_topics", [])) + "."] +
        [f"{t['title']} با همین نظم ادامه می‌یابد." for t in cfg.get("next_notes", [])]
    )
    # the whole 13-session plan, straight from the session table, so the reader
    # sees where this booklet sits and what the next twelve sessions carry
    plan = []
    for key, s_cfg in HN_SESSIONS.items():
        if not s_cfg.get("title"):
            continue
        state = "همین جلسه" if s_cfg.get("n") == cfg.get("n") else "پیشِ‌رو"
        plan.append([s_cfg["num"], s_cfg["title"], state])
    emit_table(book, ["جلسه", "عنوان جلسه", "وضعیت"], plan,
               widths=[K.CONTENT_W * 0.10, K.CONTENT_W * 0.66, K.CONTENT_W * 0.24],
               size=8.0, caption=f"جدول {cfg['num']}-۸ — نقشهٔ سیزده جلسهٔ جزوهٔ مادر",
               src="برنامهٔ مصوب جلسه‌های سر و گردن")
    book.callout(
        ("این جزوه برای کار جزوه‌نویسان آماده شده است؛ داوری تخصصی علمی انجام نشده است." if cfg["n"] in (4, 5) else "این جزوه پیش‌نویس ویرایشی است: هر مبحث با امضای برگهٔ تحویل خودش نهایی می‌شود."),
        kind="warn", title="وضعیت این جزوه")


def back_page(book: PDFBook, cfg: dict) -> None:
    def painter(b: PDFBook) -> None:
        c = b.c
        c.setFillColor(K.HexColor("#ffffff"))
        c.setFont("VazirB", 20)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.62, K.shape("HumsYar"))
        c.setFillColor(K.TEAL_L)
        c.setFont("Vazir", 11)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.56,
                            K.shape("جزوهٔ مادر آناتومی سر و گردن"))
        c.setFillColor(K.HexColor("#94a3b8"))
        c.setFont("Vazir", 9.5)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.50,
                            K.shape(f"جلسهٔ {cfg['num']} از {cfg['of']} — {cfg['title']}"))
        c.setFont("VazirL", 8.4)
        c.drawCentredString(K.A4W / 2, K.A4H * 0.44,
                            K.shape("تصویرها از نتر و گری · متن از جزوهٔ درس"))
    book.dark_page(painter)


# ---------------------------------------------------------------------- build
def build(out_path: Path, toc_pages: dict | None = None) -> PDFBook:
    cfg = HN_SESSIONS[SESSION]
    outline = load_json(CONTENT / "outline" / cfg["outline"])

    content: dict[str, list] = {}
    for fname in cfg["content"]:
        for topic in load_json(CONTENT / fname):
            content[topic["topic_id"]] = topic["blocks"]

    content = apply_update(SESSION, content)
    plates = [b for blocks in content.values() for b in blocks if b.get("type") == "plate"]
    stats = {
        "plates": len(plates),
        "lec": sum(1 for b in plates if b.get("book") == "lecture"),
        "netter": sum(1 for b in plates if b.get("book") == "netter"),
        "grays": sum(1 for b in plates if b.get("book") == "grays"),
    }

    book = PDFBook(out_path, f"جزوهٔ مادر آناتومی سر و گردن — جلسهٔ {cfg['num']}",
                   footer=FOOTER, subject="جزوهٔ مادر — آناتومی سر و گردن")
    book.block_trace = []
    book.trace_topic = ''
    book.measure_idcard = cfg.get("measure_idcard", False)
    book.keep_parenthesized_latin = cfg['n'] == 3
    book.dark_page(lambda b: cover_page(b, cfg), reuse_blank_page=True)
    front_matter(book, cfg, stats)
    toc_page(book, cfg, outline, toc_pages or {})

    n_tables = sum(1 for blocks in content.values() for b in blocks if b.get("type") == "table")
    n_paths = sum(1 for blocks in content.values() for b in blocks if b.get("type") == "path")
    divider(book, f"فصل {cfg['num']} · جلسهٔ {cfg['num']}", cfg["divider_title"],
            cfg["divider_sub"],
            [f"{fa(len(outline['topics']))} مبحث · {fa(stats['plates'])} قاب تصویر "
             f"({fa(stats['netter'])} نتر · {fa(stats['grays'])} گری · {fa(stats['lec'])} جزوه)",
             f"{fa(n_tables)} جدول · {fa(n_paths)} مسیر گام‌به‌گام",
             "متن هر مبحث با ارجاع صفحه، و هر تصویر با مشخصات منبع",
             "نسخهٔ کاری برای جزوه‌نویسان" if cfg["n"] in (1, 2, 4, 5) else "پیش‌نویس ویرایشی — بازبینی علمی در جریان"])
    # dark_page advances to the page *after* the divider; the chapter's TOC
    # entry must point to the divider itself, not the following intro page.
    book.heading_pages[cfg["anchor"]] = book.page - 1 if cfg["n"] in (3, 4) else book.page
    session_intro(book, cfg, outline, stats)

    for i, t in enumerate(outline["topics"], start=1):
        blocks = with_notes(content.get(t["topic_id"], []), i)
        topic_head(book, t, i, len(outline["topics"]),
                   after=_block_height(book, blocks[0] if blocks else None), part_labels=cfg["n"] == 4)
        book.trace_topic = t['topic_id']
        render_blocks(book, blocks, cfg)

    summary(book, content, outline, cfg)
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
    # Keep a NUL in an early PDF comment as well as the standard binary marker.
    # Some patch/snapshot systems otherwise mistake ASCII85-heavy PDFs for text
    # and transcode bytes, corrupting font streams and xref offsets. The comment
    # is harmless to PDF readers; pypdf writes correct offsets after the header.
    for page in reader.pages[:-1]:
        writer.add_page(page)
    writer.add_metadata(reader.metadata or {})
    # add_page may adopt the source header, so set this only after adding pages.
    writer.pdf_header = "%PDF-1.4\n%binary\x00"
    with path.open("wb") as fh:
        writer.write(fh)
    return len(writer.pages)


def main() -> None:
    global SESSION
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="s01", choices=sorted(HN_SESSIONS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--trace", help="write block-to-output-page layout evidence as JSON")
    ap.add_argument("--force", action="store_true",
                    help="allow overwriting an already published session PDF")
    args = ap.parse_args()

    SESSION = args.session
    cfg = HN_SESSIONS[SESSION]
    out = Path(args.out).resolve() if args.out else REPO / "pdf" / cfg["pdf_name"]
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
    if args.trace:
        trace_path=Path(args.trace)
        trace_path.parent.mkdir(parents=True,exist_ok=True)
        trace_path.write_text(json.dumps(dict(pdf=str(out.relative_to(REPO)),
            sha256=hashlib.sha256(out.read_bytes()).hexdigest(),blocks=book.block_trace),ensure_ascii=False,indent=2)+'\n')
    if book.missing_assets:
        print("MISSING ASSETS:", *book.missing_assets, sep="\n  ")
    try:
        display_path = out.relative_to(REPO)
    except ValueError:
        display_path = out
    print(f"written: {display_path}")


if __name__ == "__main__":
    main()

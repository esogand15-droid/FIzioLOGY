# -*- coding: utf-8 -*-
"""فهرست مجموعهٔ شش‌جلدی حواس ویژه — دو صفحه.

خروجی: pdf/HumsYar_NeuroHawas_Fehrest_Majmue.pdf
آمار از neuro_booklet/build/series_stats.json و series_sources.json خوانده می‌شود
(هر دو با اسکن ماژول‌های محتوا و فایل‌های PDF ساخته شده‌اند).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "neuro_booklet", "render"))

from rtl_kit import Kit, fa, C, PAGE_W, PAGE_H, M_SIDE  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.lib.colors import HexColor  # noqa: E402

OUT = os.path.join(ROOT, "pdf", "HumsYar_NeuroHawas_Fehrest_Majmue.pdf")
STATS = json.load(open(os.path.join(ROOT, "neuro_booklet/build/series_stats.json"), encoding="utf-8"))
SRC = json.load(open(os.path.join(ROOT, "neuro_booklet/build/series_sources.json"), encoding="utf-8"))
FONTS = os.path.join(ROOT, "assets", "fonts")

FA_D = "۰۱۲۳۴۵۶۷۸۹"


def fnum(n, sep="٬"):
    s = "".join(FA_D[int(ch)] if ch.isdigit() else ch for ch in str(n))
    if sep and len(s) > 3:
        out, grp = "", []
        for ch in reversed(s):
            grp.append(ch)
            if len(grp) == 3:
                out = "".join(reversed(grp)) + (sep + out if out else "")
                grp = []
        if grp:
            out = "".join(reversed(grp)) + sep + out
        return out
    return s


def short_title(t, limit=44):
    t = t.strip()
    return t if len(t) <= limit else t[:limit].rstrip() + "…"


def mb(b):
    return fa("%.1f" % (b / 1048576.0)).replace(".", "٫")


def main():
    k = Kit(OUT, FONTS, meta=dict(
        pdf_title="فهرست مجموعهٔ شش‌جلدی حواس ویژه — هم‌یار",
        author="HumsYar",
        subject="فهرست و شناسنامهٔ شش جلد جزوهٔ نوروفیزیولوژی حواس ویژه",
        header_right="فهرست مجموعه حواس ویژه",
        header_left="HumsYar",
        footer_left="گروه جزوه‌نویسی پزشکی · هم‌یار",
        footer_right="فهرست مجموعه · شش جلد",
    ))

    tot_pages = sum(v["pages"] for v in STATS)
    tot_mab = sum(v["mab"] for v in STATS)
    tot_tab = sum(v["tab"] for v in STATS)
    tot_fig = sum(v["fig"] for v in STATS)
    tot_box = sum(v["box"] for v in STATS)

    # ------------------------------------------------------------ صفحهٔ ۱
    k.new_page("body")
    k.h_section_band(
        "فهرست مجموعه",
        "شش جلد، %s صفحه: یک درس کامل" % fnum(tot_pages),
        sub="نوروفیزیولوژی اعصاب و حواس ویژه",
        key="band",
    )

    k.para(
        "این شش جلد حاصل بازخوانی کامل جزوه‌های کلاس نوروفیزیولوژی (مهر ۱۴۰۴) و مقابلهٔ بند‌به‌بند آن‌ها با "
        "جزوه‌های امتحانی بهمن ۱۴۰۲ و دو مرجع گایتون و گانگون است. هر جلد یک ساختار یکسان دارد: جلد، راهنمای "
        "خواندن، فهرست یک‌صفحه‌ای، نقشهٔ راه جلسه و منابع، مباحث شناسنامه‌دار، جدول‌ها و شکل‌های خود جزوه، "
        "یادداشت و برگهٔ تحویل، پیوست مقابله، و چک‌لیست پذیرش با خودآزمایی پاسخ‌دار. شماره‌گذاری صفحه‌ها، "
        "بوکمارک‌ها و رنگ‌ها در هر شش جلد یکی است تا رفت‌وبرگشت بین جلدها بی‌دردسر باشد.",
        size=9.3, lead=1.95,
    )

    k.h2("جلدهای مجموعه")
    headers = ["جلد", "عنوان جلسه", "صفحه", "مبحث", "جدول", "شکل", "کادر"]
    rows = []
    for v in STATS:
        rows.append([
            "جلد " + v["no"],
            v["title"],
            fnum(v["pages"]),
            fnum(v["mab"]),
            fnum(v["tab"]),
            fnum(v["fig"]),
            fnum(v["box"]),
        ])
    rows.append(["جمع", "شش جلد", fnum(tot_pages), fnum(tot_mab), fnum(tot_tab), fnum(tot_fig), fnum(tot_box)])
    k.table(headers, rows, widths=[0.085, 0.465, 0.10, 0.10, 0.085, 0.085, 0.08],
            size=8.1, header_size=8.1, align_cols={2: "c", 3: "c", 4: "c", 5: "c", 6: "c"},
            caption="جدول ۱ — شناسنامهٔ شش جلد",
            source="آمار از خود فایل‌های PDF و ماژول‌های محتوا استخراج شده است (بازبینی ماشینی، آبان ۱۴۰۴).")

    k.box(
        "ترتیب خواندن پیشنهادی",
        "این شش جلد یک زنجیره‌اند، نه شش جزوهٔ جدا: جلد ۱ زبان سلول عصبی را می‌سازد (پتانسیل غشا، "
        "ناقل‌ها)، جلد ۲ همان زبان را به سیناپس و مدار می‌برد، جلد ۳ از گیرنده تا قشر حسی می‌آید، "
        "جلد ۴ مسیرها و درد را کامل می‌کند، و جلدهای ۵ و ۶ دو حس ویژهٔ بینایی و شنوایی‌اند. "
        "اگر وقت کم است، جفت‌های ۱+۲ و ۵+۶ را پیوسته بخوانید.",
        kind="note",
        bullet_items=[
            "پیش از هر جلد، «راهنمای خواندن» و «نقشهٔ راه جلسه» را ببینید؛ شناسنامهٔ هر مبحث پیش‌نیازش را می‌گوید.",
            "جدول‌های جمع‌بندی (آخرین جدول هر جلد) برای مرور شب امتحان کافی‌اند.",
            "پیوست مقابله نشان می‌دهد چه چیزی از جزوهٔ ۱۴۰۲ به متن اضافه شده و از کجا.",
        ],
    )

    k.box(
        "آنچه در این مجموعه نیست",
        "جلسهٔ ۷ به بعد درس، جزوهٔ ۱۴۰۴ ندارد؛ در مخزن فقط خلاصه‌های امتحانی بهمن ۱۴۰۲ (نخاع و "
        "رفلکس‌ها، ساقه مغز، مخچه، عقده‌های قاعده‌ای، حافظه، لیمبیک، اتونوم و پری‌لب) هست و پوشهٔ "
        "«جلسه ۷» هم تکرار پوشهٔ ۸ است. بنابراین این مجموعه با جلد ۶ بسته می‌شود و مدعی پوشش آن بخش‌ها نیست.",
        kind="amber",
    )

    k.gap(4 * mm)
    k.source_line("شش جلد · %s صفحه · %s مبحث · %s جدول · %s شکل — همهٔ فایل‌ها در پوشهٔ pdf همین مخزن."
                  % (fnum(tot_pages), fnum(tot_mab), fnum(tot_tab), fnum(tot_fig)))

    # ------------------------------------------------------------ صفحهٔ ۲
    k.new_page("body")
    k.h_section_band(
        "نگاشت و شناسه",
        "هر جلد کجای منابع می‌نشیند",
        sub="Guyton ویراست ۱۲ · Ganong ویراست ۲۶",
        key="band2",
    )

    k.h2("نگاشت به مراجع")
    rows = []
    for v in STATS:
        s = SRC.get(v["no"], {})
        g = "، ".join(fa(x) for x in s.get("guyton", [])[:3]) or "—"
        gn = "، ".join(fa(x) for x in s.get("ganong", [])[:2]) or "—"
        rows.append(["جلد " + v["no"], short_title(v["title"], 40), "فصل " + g, "فصل " + gn])
    k.table(["جلد", "عنوان", "گایتون", "گانگون"], rows, widths=[0.10, 0.50, 0.21, 0.19],
            size=8.1, header_size=8.1,
            caption="جدول ۲ — فصل‌هایی که بیشترین ارجاع در هر جلد را دارند",
            source="فصل‌ها از خطوط «منبع:» همان جلد شمرده شده‌اند؛ پرتکرارترین فصل‌ها آمده است.")

    k.h2("شناسهٔ فایل‌ها")
    rows = []
    for v in STATS:
        rows.append(["جلد " + v["no"], fnum(v["pages"]), mb(v["bytes"]), v["sha"]])
    k.table(["جلد", "صفحه", "حجم (مگابایت)", "کد SHA-256 (۱۰ نویسه)"], rows,
            widths=[0.10, 0.10, 0.185, 0.615], size=8.1, header_size=8.1, ltr_cols=(3,),
            align_cols={1: "c", 2: "c"},
            caption="جدول ۳ — شناسهٔ تحویل",
            source="کد، ده نویسهٔ نخست SHA-256 فایل است؛ برای بررسی سلامت فایل پس از دانلود." )

    k.box(
        "قاعدهٔ استناد و بازبینی",
        "هر جملهٔ متن درس در این شش جلد یک خط «منبع:» دارد؛ برای نقل قول در ارائه یا جزوهٔ خودتان همان "
        "خط را بیاورید. سه نکتهٔ عملی:",
        kind="note",
        bullet_items=[
            "برای اطمینان از سلامت فایل، کد جدول ۳ را با SHA-256 فایل دانلودشده بسنجید؛ حتی یک صفحهٔ جابه‌جا این کد را عوض می‌کند.",
            "برای چاپ، A4 دورو با مقیاس ۱۰۰ درصد بزنید؛ مقیاس ۹۰ درصد شمارهٔ صفحه‌ها را از بوکمارک جدا نمی‌کند اما جدول‌های ریز را کم‌خوان می‌کند.",
            "اگر جایی از متن با جزوهٔ کلاس ناسازگار بود، کادر کهربایی همان مبحث را ببینید؛ اختلاف‌ها ثبت شده‌اند، نه پاک.",
        ],
    )

    k.gap(3 * mm)
    k.source_line("نسخهٔ ۱٫۰ — آبان ۱۴۰۴ · گروه جزوه‌نویسی پزشکی، هم‌یار · ساخت با build_series_index.py")

    k.save()
    print("OUT:", OUT)
    import pymupdf
    d = pymupdf.open(OUT)
    print("pages:", d.page_count, "bytes:", os.path.getsize(OUT))
    print("bookmarks:", [t for _, t, _ in d.get_toc()])


if __name__ == "__main__":
    main()

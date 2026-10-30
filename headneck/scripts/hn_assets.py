"""برش و ثبت تصویرهای جلسه‌های آناتومی سر و گردن.

هر جلسه فقط تصویرهای خودش را می‌نویسد؛ مخزن با صدها مگابایت تصویر پر نمی‌شود.
سه نوع منبع داریم و هر سه از همان صفحه رندر می‌شوند، چون برچسب‌ها و زیرنویس
انگلیسی به تصویر چسبیده‌اند و بریدن تصویر خام آن‌ها را از دست می‌دهد:

* ``lecture`` — جزوهٔ درس هر جلسه (رضا‌سنگ برای هر شکل، حاشیهٔ ۶ نقطه).
* ``netter``  — اطلس نتر ۸ چاپ ۲۰۲۳؛ کل صفحهٔ پلیت، چون عنوان و شمارهٔ پلیت
  و برچسب‌ها روی همان صفحه نوشته شده‌اند. نگاشت: صفحهٔ PDF = پلیت + ۵۱.
* ``grays``   — گری، آناتومی برای دانشجویان، ویراست ۳؛ جعبهٔ شکل از صفحهٔ چاپی.
  نگاشت فایل ۸۰۱–۱۰۰۰: صفحهٔ PDF = صفحهٔ چاپی − ۷۷۲.

اجرا
----
    .venv/bin/python headneck/scripts/hn_assets.py --session hn01
    .venv/bin/python headneck/scripts/hn_assets.py --session hn01 --only hn01_netter_p25

فایل‌های خروجی در ``headneck/images/`` و فهرستشان در ``headneck/images/INDEX.json``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "headneck" / "images"
INDEX = OUT / "INDEX.json"
SRC = Path("/tmp/hn")

LEC1 = SRC / "جلسه 1 - سر و گردن 1__جلسه_اول_علوم_تشریح_سر_و_گردن_مهر_1404.pdf"
NETTER = SRC / "جلسه 1 - سر و گردن 1__Netter Atlas of Human Anatomy Classic Regional Approach.pdf"
GRAYS = SRC / ("علوم تشریح دستگاه اعصاب__user - Gray's Anatomy For Students, "
               "3rd Edition-801-1000.pdf")

NETTER_OFFSET = 52      # شمارهٔ صفحهٔ PDF (یک‌پایه) = شمارهٔ پلیت + ۵۲
GRAYS_OFFSET = 772      # شمارهٔ صفحهٔ PDF (یک‌پایه) = صفحهٔ چاپی − ۷۷۲

DPI = 200

# چند قاب، متن ستون کنارِ صفحهٔ جزوه را هم گرفته است؛ این نوارها اندکی از
# لبهٔ تصویر را سفید می‌کنند تا حرف‌های نیمهٔ ستون همسایه در قاب نماند.
# asset_id: [ (x0, y0, x1, y1) در پیکسل تصویر خروجی ]
TRIM: dict[str, list[tuple[int, int, int, int]]] = {
    "hn02_lec_p26_parietal": [(0, 0, 22, 393), (818, 0, 900, 393)],
}

# asset_id: (book, source, page, bbox, view_note)
# bbox = جعبه در نقطه‌های صفحهٔ PDF؛ None یعنی کل صفحه (با حاشیهٔ کوچک).
SPECS: dict[str, tuple] = {
    # ── جلسهٔ ۱ ────────────────────────────────────────────────────────────────
    "hn01_lec_p13_nasal": ("lecture", LEC1, 13, (66, 92, 350, 320),
                           "جزوهٔ درس، ص ۱۳ — استخوان بینی: نمای قدامی و خلفی"),
    "hn01_lec_p15_maxilla": ("lecture", LEC1, 15, (18, 122, 248, 360),
                             "جزوهٔ درس، ص ۱۵ — سطح خارجی فک فوقانی و زائدهٔ پیشانی"),
    "hn01_lec_p16_palate": ("lecture", LEC1, 16, (28, 64, 214, 218),
                            "جزوهٔ درس، ص ۱۶ — زوائد کامی و کام سخت"),
    "hn01_lec_p17_sinus": ("lecture", LEC1, 17, (212, 62, 550, 278),
                           "جزوهٔ درس، ص ۱۷ — سینوس فک فوقانی در جسم ماگزیلا"),
    "hn01_lec_p20_split": ("lecture", LEC1, 20, (204, 232, 601, 424),
                           "جزوهٔ درس، ص ۲۰ — کارت تقسیم‌بندی استخوان‌های جمجمه"),
    "hn01_netter_p25": ("netter", NETTER, 25 + NETTER_OFFSET, None,
                        "نمای قدامی جمجمه با برچسب‌های نتر"),
    "hn01_netter_p27": ("netter", NETTER, 27 + NETTER_OFFSET, None,
                        "نمای طرفی جمجمه؛ خطوط گیجگاهی و زائدهٔ گونه‌ای"),
    "hn01_netter_p30": ("netter", NETTER, 30 + NETTER_OFFSET, None,
                        "کالواریا: نمای فوقانی و سطح داخلی"),
    "hn01_netter_p32": ("netter", NETTER, 32 + NETTER_OFFSET, None,
                        "قاعدهٔ جمجمه از بالا: سه حفرهٔ کرانیال"),
    "hn01_netter_p37": ("netter", NETTER, 37 + NETTER_OFFSET, None,
                        "اسکلت بینی و سینوس‌های اطراف بینی"),
    "hn01_netter_p26": ("netter", NETTER, 26 + NETTER_OFFSET, None,
                        "رادیوگرافی جمجمه: کاسهٔ چشم و سینوس‌ها"),
    "hn01_grays_p855": ("grays", GRAYS, 855 - GRAYS_OFFSET, (54, 316, 570, 756),
                        "نمای قدامی جمجمه"),
    "hn01_grays_p857": ("grays", GRAYS, 857 - GRAYS_OFFSET, (32, 214, 594, 716),
                        "نمای طرفی جمجمه"),
    "hn01_grays_p860": ("grays", GRAYS, 860 - GRAYS_OFFSET, (112, 360, 548, 728),
                        "نمای فوقانی جمجمه: کالواریا و درزها"),
    "hn01_grays_p927": ("grays", GRAYS, 927 - GRAYS_OFFSET, (306, 54, 560, 344),
                        "استخوان‌های کاسهٔ چشم؛ صفحهٔ کاسه‌چشمی پیشانی و سوراخ‌های پرویزنی"),
}

# figure lists of each lecture page, measured by reading the pages themselves
from hn_figures import FIGURES  # noqa: E402
SPECS.update({k: v for k, v in FIGURES.items() if k not in SPECS})
try:                                        # session 2 (may not exist yet)
    from hn02_figures import FIGURES as FIGURES_HN02  # noqa: E402
    from hn02_figures import SPECS_HN02  # noqa: E402
except ImportError:
    FIGURES_HN02, SPECS_HN02 = {}, {}
SPECS.update({k: v for k, v in FIGURES_HN02.items() if k not in SPECS})
SPECS.update({k: v for k, v in SPECS_HN02.items() if k not in SPECS})

PLATE_OF = {  # only for book plates, so a reader can find the figure again
    "hn01_netter_p25": 25, "hn01_netter_p27": 27, "hn01_netter_p30": 30,
    "hn01_netter_p32": 32, "hn01_netter_p37": 37, "hn01_netter_p26": 26,
}


def _open(path: Path) -> pymupdf.Document:
    return pymupdf.open(path)


def _netter_box(page: pymupdf.Page) -> pymupdf.Rect:
    """The plate's ink: illustration plus its printed labels and plate title."""
    rect = None
    for x in page.get_image_info():
        r = pymupdf.Rect(x["bbox"])
        rect = r if rect is None else rect | r
    for b in page.get_text("blocks"):
        if not b[4].strip():
            continue
        r = pymupdf.Rect(b[:4])
        rect = r if rect is None else rect | r
    if rect is None:
        return page.rect
    r = rect + (-4, -4, 4, 4)
    return r & page.rect


def export(only: set[str] | None = None, session: str | None = None) -> list[dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    index = {"assets": []}
    if INDEX.exists():
        index = json.loads(INDEX.read_text(encoding="utf-8"))
    have = {a["asset_id"]: a for a in index["assets"]}
    cache: dict[str, pymupdf.Document] = {}
    written = []
    for asset_id, (book, source, page_no, bbox, note) in SPECS.items():
        if only and asset_id not in only:
            continue
        if session and not asset_id.startswith(session + "_"):
            continue
        key = str(source)
        if key not in cache:
            cache[key] = _open(source)
        doc = cache[key]
        page = doc[page_no - 1]
        box = _netter_box(page) if bbox is None else pymupdf.Rect(bbox)
        name = f"{asset_id}.jpeg"
        if asset_id == "hn02_lec_p08_outer":
            # Page rendering also captures the adjacent paragraph and border.
            # Preserve the complete original figure using its PDF soft mask.
            from PIL import Image
            images = [im for im in page.get_images(full=True)
                      if im[2:4] == (646, 551) and im[1]]
            if len(images) != 1:
                raise ValueError(f"Expected one masked page-8 figure, got {len(images)}")
            xref, mask = images[0][:2]
            base = pymupdf.Pixmap(doc, xref)
            mask_pix = pymupdf.Pixmap(doc, mask)
            im = Image.frombytes("RGBA" if base.alpha else "RGB",
                                 (base.width, base.height), base.samples).convert("RGB")
            alpha = Image.frombytes("L", (mask_pix.width, mask_pix.height), mask_pix.samples)
            bg = Image.new("RGB", im.size, "white")
            bg.paste(im, mask=alpha)
            # The source mask includes a dark page-edge fragment, not the figure.
            bg = bg.crop((34, 0, bg.width, bg.height))
            bg.save(OUT / name, quality=95)
            pix = pymupdf.Pixmap(OUT / name)
            box = page.get_image_rects(xref)[0]
        else:
            pix = page.get_pixmap(dpi=DPI, clip=box)
        if asset_id == "hn02_lec_p08_outer":
            pass  # already saved with its soft mask composited on white
        elif asset_id in TRIM:
            from PIL import Image, ImageDraw
            import io as _io
            im = Image.open(_io.BytesIO(pix.tobytes("png"))).convert("RGB")
            dr = ImageDraw.Draw(im)
            for r in TRIM[asset_id]:
                dr.rectangle(r, fill=(255, 255, 255))
            im.save(OUT / name, quality=88)
            pix = pymupdf.Pixmap(OUT / name)
        else:
            pix.save(OUT / name, jpg_quality=88)
        row = dict(
            asset_id=asset_id, book=book, session=asset_id.split("_")[0],
            source_file=source.name, page=page_no, note=note,
            bbox=[round(v, 1) for v in box], w=pix.width, h=pix.height,
            px=pix.width * pix.height, bytes=(OUT / name).stat().st_size,
            path=f"headneck/images/{name}",
        )
        if asset_id in PLATE_OF:
            row["plate"] = PLATE_OF[asset_id]
        have[asset_id] = row
        written.append(row)
    for doc in cache.values():
        doc.close()
    index["assets"] = sorted(have.values(), key=lambda a: a["asset_id"])
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="hn01", choices=["hn01", "hn02"])
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args()
    rows = export(set(a.only) if a.only else None, session=a.session)
    for r in rows:
        print(f"{r['asset_id']:24s} {r['w']}x{r['h']}  {r['bytes']:>7,} B  {r['note']}")
    print(f"\n{len(rows)} assets written · index: {INDEX.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
# یادداشت مهم (رفع اشکال ۱۴۰۴/۰۸/۱۸):
# متن فارسی پس از bidi.get_display() در «ترتیب بصری» است. اگر این رشته روی فاصله
# شکسته و تکه‌ها از راست به چپ رسم شوند، ترتیب کلمه‌ها برعکس می‌شود. پس در
# هم‌ترازی دوطرفه، کلمه‌های «منطقی» (خروجی wrap_words) از راست به چپ چیده می‌شوند
# و عبارت‌های لاتین چندکلمه‌ای با _visual_chunks() یک‌جا می‌مانند.
"""
rtl_kit — موتور صفحه‌آرایی فارسی (راست‌به‌چپ) برای جزوهٔ مادر
ساخته‌شده با ReportLab + arabic_reshaper + python-bidi
"""
import os
import re
import math
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase.pdfmetrics import stringWidth

# ---------------------------------------------------------------- اعداد فارسی
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def fa(n):
    s = str(n)
    return "".join(FA_DIGITS[int(ch)] if ch.isdigit() else ch for ch in s)


# قطعه‌های لاتین/عددی که باید در قالب LTR جدا شوند
_LTR_RUN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"[A-Za-z0-9][A-Za-z0-9\-+./%:°'&]*(?:\s[A-Za-z0-9][A-Za-z0-9\-+./%:°'&]*)*"
)


# ---------------------------------------------------------------- پالت رنگی
C = dict(
    ink="#0a0f1e",
    ink2="#0d1524",
    ink3="#0a1a26",
    blue="#2563eb",
    teal="#0d9488",
    sky="#f0f6ff",
    line="#e2e8f0",
    paper="#ffffff",
    gray="#5b6472",
    gray2="#7c8798",
)
C["gold"] = "#b45309"
C["soft_teal"] = "#ecfdf8"
C["soft_blue"] = "#eef4ff"
C["soft_amber"] = "#fff7ed"
C["soft_rose"] = "#fff1f2"

PAGE_W, PAGE_H = A4
M_TOP = 21 * mm
M_BOT = 19 * mm
M_SIDE = 15 * mm

ZWNJ = "\u200c"
PH = "\uE000"  # جانگهدار نیم‌فاصله

def _needs_greek(ch):
    o = ord(ch)
    return 0x0370 <= o <= 0x03FF or 0x1F00 <= o <= 0x1FFF or 0x2190 <= o <= 0x21FF


def _split_greek(s):
    """رشته را به تکه‌های (متن، یونانی‌بودن) می‌شکند."""
    runs, cur, flag = [], "", None
    for ch in s:
        f = _needs_greek(ch)
        if flag is None or f == flag:
            cur += ch
            flag = f
        else:
            runs.append((cur, flag))
            cur, flag = ch, f
    if cur:
        runs.append((cur, flag))
    return runs



_LATIN_WORD = re.compile(r"^[0-9A-Za-z\u00C0-\u024F\u0370-\u03FF][0-9A-Za-z\u00C0-\u024F\u0370-\u03FF\.,\-\u2013\u2014/()'\u2019:\;%+&*\[\]]*$")


def _is_latin_word(w):
    return bool(_LATIN_WORD.match(w))


def _visual_chunks(words):
    """کلمه‌های منطقی را به «تکه‌های دوجهته» تبدیل می‌کند.

    تکه‌های لاتین پشت‌سرهم (مثل Guyton and Hall) در یک تکه می‌مانند تا
    هنگام رسم از راست به چپ، ترتیب درونی خودشان برگردانده نشود.
    """
    chunks = []
    for w in words:
        if chunks and _is_latin_word(w) and _is_latin_word(chunks[-1].split(" ")[-1]):
            chunks[-1] = chunks[-1] + " " + w
        else:
            chunks.append(w)
    return chunks


class Kit:
    def __init__(self, path, fonts_dir, meta=None):
        self.path = path
        self.fonts = {
            "r": ("Vazirmatn-Regular.ttf", "Vazir"),
            "m": ("Vazirmatn-Medium.ttf", "VazirM"),
            "sb": ("Vazirmatn-SemiBold.ttf", "VazirSB"),
            "b": ("Vazirmatn-Bold.ttf", "VazirB"),
            "l": ("Vazirmatn-Light.ttf", "VazirL"),
            # پشتیبان برای حروف یونانی (β، δ، Δ، γ) و فلش‌ها که Vazirmatn ندارد
            "gk": ("DejaVuSans.ttf", "DejaVu"),
            "gkb": ("DejaVuSans-Bold.ttf", "DejaVuB"),
        }
        for key, (fname, alias) in self.fonts.items():
            ttf = os.path.join(fonts_dir, fname)
            if alias not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(alias, ttf))
        self.F = {k: v[1] for k, v in self.fonts.items()}
        self.meta = meta or {}
        self.c = canvas.Canvas(path, pagesize=A4, pageCompression=1)
        self._install_greek_fallback()
        self.c.setTitle(self.meta.get("pdf_title", ""))
        self.c.setAuthor(self.meta.get("author", "HumsYar"))
        self.c.setSubject(self.meta.get("subject", ""))
        self.c.setCreator("HumsYar booklet builder")

        self.page_no = 0
        self.y = PAGE_H - M_TOP
        self.toc = []            # [(level, title, page, key)]
        self.bookmarks = []      # [(key, title, level)]
        self._bm = 0
        self.fig_no = 0
        self.tab_no = 0
        self.cur_kind = "body"
        self.section_label = ""
        self.running_titles = {}
        self.anchors = {}
        self.defer_new_page = False
        self.right = PAGE_W - M_SIDE
        self.left = M_SIDE
        self.maxw = self.right - self.left

    # ------------------------------------------------------------ پایه متن
    def shape(self, s):
        """تبدیل متن منطقی فارسی به رشتهٔ بصری آمادهٔ رسم.

        قطعه‌های لاتین/عددی (مثل 5-HT3 یا Guyton and Hall) داخل LRE…PDF
        گذاشته می‌شوند تا الگوریتم دوجهته ترتیب نویسه‌هایشان را برنگرداند.
        """
        if s is None:
            return ""
        s = str(s).replace(ZWNJ, PH)
        s = _LTR_RUN.sub(lambda m: "\u202a" + m.group(0) + "\u202c", s)
        s = arabic_reshaper.reshape(s)
        s = get_display(s, base_dir="R")
        s = s.replace("\u202a", "").replace("\u202c", "")
        return s.replace(PH, ZWNJ)

    def shape_ltr(self, s):
        return str(s)

    def tw(self, s, font="r", size=10, rtl=True):
        vis = self.shape(s) if rtl else self.shape_ltr(s)
        return stringWidth(vis, self.F[font], size)

    # ------------------------------------------------------------ صفحه
    def new_page(self, kind="body", keep_frame=True):
        if self.page_no > 0:
            self._footer()
            self.c.showPage()
        self.page_no += 1
        self.cur_kind = kind
        if keep_frame and kind in ("body", "opener", "mabhas"):
            self._frame()
        self.y = PAGE_H - M_TOP

    def _footer(self):
        c = self.c
        if self.cur_kind in ("cover", "back", "plain"):
            return
        y = 11 * mm
        c.setStrokeColor(HexColor(C["line"]))
        c.setLineWidth(0.6)
        c.line(self.left, y + 6.5 * mm, self.right, y + 6.5 * mm)
        c.setFont(self.F["r"], 7.6)
        c.setFillColor(HexColor(C["gray"]))
        c.drawString(self.left, y, self.shape(self.meta.get("footer_left", "")))
        c.drawRightString(self.right, y, self.shape(self.meta.get("footer_right", "")))
        # شمارهٔ صفحه در قرص
        w, h = 15 * mm, 6 * mm
        cx = PAGE_W / 2
        c.setFillColor(HexColor(C["ink"]))
        c.roundRect(cx - w / 2, y - 1.2 * mm, w, h, 2.6 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor("#ffffff"))
        c.setFont(self.F["m"], 8)
        c.drawCentredString(cx, y + 0.7 * mm, fa(self.page_no))

    def _frame(self):
        """سرصفحهٔ باریک + نوار تزئینی بالای صفحه."""
        c = self.c
        c.setFillColor(HexColor(C["sky"]))
        c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        c.setFillColor(HexColor("#ffffff"))
        c.rect(0, 0, PAGE_W, PAGE_H - 9 * mm, stroke=0, fill=1)
        # نوار بالا
        c.setFillColor(HexColor(C["ink"]))
        c.rect(0, PAGE_H - 9 * mm, PAGE_W, 9 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor(C["teal"]))
        c.rect(0, PAGE_H - 9.6 * mm, PAGE_W * 0.34, 0.6 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor(C["blue"]))
        c.rect(PAGE_W * 0.34, PAGE_H - 9.6 * mm, PAGE_W * 0.2, 0.6 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor("#e8eefc"))
        c.setFont(self.F["sb"], 8.2)
        c.drawRightString(self.right, PAGE_H - 6.4 * mm, self.shape(self.meta.get("header_right", "")))
        c.setFont(self.F["r"], 7.4)
        c.setFillColor(HexColor("#9fb0cc"))
        c.drawString(self.left, PAGE_H - 6.4 * mm, self.shape(self.meta.get("header_left", "")))

    def glow(self, path, cx, cy, size):
        """هالهٔ نرم از تصویر PNG با کانال آلفا."""
        self.c.drawImage(path, cx - size / 2, cy - size / 2, width=size, height=size, mask="auto")

    # -------------------------------------------------- فالبک حروف یونانی
    def _install_greek_fallback(self):
        """هر حرف یونانی/فلش را با فونت پشتیبان می‌کشد؛ بقیهٔ متن با Vazirmatn می‌ماند."""
        c = self.c
        self._cur_font = self.F["r"]
        self._cur_size = 10
        _orig_set_font = c.setFont
        _orig_right = c.drawRightString
        _orig_left = c.drawString
        _orig_center = c.drawCentredString

        def set_font(psname, size, leading=None):
            self._cur_font = psname
            self._cur_size = size
            try:
                return _orig_set_font(psname, size, leading)
            except TypeError:
                return _orig_set_font(psname, size)

        def gk_font():
            return self.F["gkb"] if self._cur_font in (self.F["b"], self.F["sb"]) else self.F["gk"]

        def draw_mixed(x, y, text, mode):
            txt = text if isinstance(text, str) else str(text)
            if not any(_needs_greek(ch) for ch in txt):
                if mode == "right":
                    return _orig_right(x, y, txt)
                if mode == "center":
                    return _orig_center(x, y, txt)
                return _orig_left(x, y, txt)
            size = self._cur_size
            main, alt = self._cur_font, gk_font()
            runs = _split_greek(txt)
            widths = [stringWidth(t, alt if g else main, size) for t, g in runs]
            total = sum(widths)
            xx = x - total if mode == "right" else (x - total / 2 if mode == "center" else x)
            for (t, g), w in zip(runs, widths):
                _orig_set_font(alt if g else main, size)
                _orig_left(xx, y, t)
                xx += w
            _orig_set_font(main, size)

        c.setFont = set_font
        c.drawRightString = lambda x, y, text, *a, **k: draw_mixed(x, y, text, "right")
        c.drawString = lambda x, y, text, *a, **k: draw_mixed(x, y, text, "left")
        c.drawCentredString = lambda x, y, text, *a, **k: draw_mixed(x, y, text, "center")

    # ------------------------------------------------------------ فضای صفحه
    def space(self, need):
        return (self.y - need) >= (M_BOT + 4 * mm)

    def ensure(self, need, kind=None):
        if not self.space(need):
            self.new_page(kind or (self.cur_kind if self.cur_kind != "body" else "body"))

    def gap(self, h=3 * mm):
        self.y -= h

    # ------------------------------------------------------------ پاراگراف
    def wrap_words(self, text, font="r", size=10, width=None, rtl=True):
        """شکست خط با حفظ «کلمه‌های منطقی» (ترتیب خواندن)، نه رشتهٔ بصری."""
        width = width or self.maxw
        words = str(text).split(" ")
        lines, cur = [], []
        for w in words:
            cand = " ".join(cur + [w])
            if not cur or self.tw(cand, font, size, rtl) <= width:
                cur.append(w)
            else:
                lines.append(cur)
                cur = [w]
        if cur:
            lines.append(cur)
        return lines

    def wrap(self, text, font="r", size=10, width=None, rtl=True):
        out = []
        for ln in self.wrap_words(text, font, size, width, rtl):
            txt = " ".join(ln)
            vis = self.shape(txt) if rtl else txt
            out.append((txt, vis, stringWidth(vis, self.F[font], size)))
        return out

    def para(self, text, size=9.8, font="r", lead=1.85, align="justify",
             color=None, indent=0, first_indent=0, width=None, rtl=True,
             space_after=2.0 * mm, x_left=None):
        """پاراگراف فارسی با شکست خط و هم‌ترازی راست/دوطرفه."""
        width = (width or self.maxw) - indent - first_indent
        xr = self.right - indent
        word_lines = self.wrap_words(text, font, size, width, rtl)
        lines = []
        for _ln in word_lines:
            _t = " ".join(_ln)
            _v = self.shape(_t) if rtl else _t
            lines.append((_t, _v, stringWidth(_v, self.F[font], size), _ln))
        lh = size * lead
        color = color or C["ink"]
        self.c.setFillColor(HexColor(color))
        first = True
        for i, (txt, vis, w, words) in enumerate(lines):
            self.ensure(lh, self.cur_kind)
            if not first:
                pass
            yy = self.y - size * 0.92
            wl = width if (i < len(lines) - 1 or align == "justify") else w
            if align == "justify" and i < len(lines) - 1 and rtl and len(words) > 1:
                # هم‌ترازی دوطرفه: کلمه‌ها به ترتیب منطقی (خواندن) از راست به چپ رسم می‌شوند
                chunks = _visual_chunks(words)
                chunks = [c for c in chunks if c.strip()]
                sp = stringWidth(" ", self.F[font], size)
                shapes = [self.shape(c) for c in chunks]
                widths = [stringWidth(sv, self.F[font], size) for sv in shapes]
                gaps = max(1, len(chunks) - 1)
                slack = max(0.0, width - (sum(widths) + gaps * sp)) / gaps
                self.c.setFont(self.F[font], size)
                x = xr
                for sv, sw in zip(shapes, widths):
                    x -= sw
                    self.c.drawString(x, yy, sv)
                    x -= (sp + slack)
            elif align == "justify" and i < len(lines) - 1:
                self.c.setFont(self.F[font], size)
                self.c.drawRightString(xr, yy, vis)
            elif align == "center":
                self.c.setFont(self.F[font], size)
                self.c.drawCentredString(xr - width / 2, yy, vis)
            else:
                self.c.setFont(self.F[font], size)
                self.c.drawRightString(xr, yy, vis)
            self.y -= lh
            first = False
        self.y -= space_after

    def rich(self, parts, size=9.8, lead=1.85, align="justify", space_after=2 * mm, bullet=None):
        """پاراگراف با بخش‌های پررنگ: parts = [(متن, 'r'|'b'|'sb'|'m', رنگ)]"""
        # ساده‌سازی: هر بخش در ادامهٔ هم، با شکست خط در مرز بخش‌ها
        for i, (txt, fnt, col) in enumerate(parts):
            self.para(txt, size=size, font=fnt or "r", lead=lead, align=align,
                      color=col or C["ink"], space_after=0, indent=0)
        self.y -= space_after

    # ------------------------------------------------------------ عنوان‌ها
    def h_section_band(self, kicker, title, key=None, sub=""):
        """نوار آغاز مبحث."""
        self.ensure(34 * mm)
        c = self.c
        top = self.y
        c.setFillColor(HexColor(C["ink"]))
        c.roundRect(self.left, top - 17 * mm, self.maxw, 17 * mm, 3.2 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor(C["teal"]))
        c.roundRect(self.left, top - 17 * mm, 2.6 * mm, 17 * mm, 1.3 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor("#7dd3c8"))
        c.setFont(self.F["sb"], 8.2)
        c.drawRightString(self.right - 5 * mm, top - 6.2 * mm, self.shape(kicker))
        c.setFillColor(HexColor("#ffffff"))
        c.setFont(self.F["b"], 15.4)
        c.drawRightString(self.right - 5 * mm, top - 13.2 * mm, self.shape(title))
        if sub:
            c.setFillColor(HexColor("#9fb0cc"))
            c.setFont(self.F["r"], 7.8)
            c.drawString(self.left + 5 * mm, top - 13 * mm, self.shape(sub))
        self.y = top - 17 * mm - 4.5 * mm
        if key:
            self.bookmark(key, title, 1)

    def h1(self, title, key=None, num=None):
        self.ensure(20 * mm)
        c = self.c
        self.y -= 1 * mm
        c.setFillColor(HexColor(C["ink"]))
        c.setFont(self.F["b"], 13.2)
        label = title if num is None else f"{fa(num)}. {title}"
        c.drawRightString(self.right, self.y - 5 * mm, self.shape(label))
        c.setStrokeColor(HexColor(C["teal"]))
        c.setLineWidth(1.4)
        c.line(self.right, self.y - 7.4 * mm, self.right - 16 * mm, self.y - 7.4 * mm)
        c.setStrokeColor(HexColor(C["line"]))
        c.setLineWidth(0.8)
        c.line(self.right - 16 * mm, self.y - 7.4 * mm, self.left, self.y - 7.4 * mm)
        self.y -= 11.5 * mm
        if key:
            self.bookmark(key, title, 2)
            self.toc.append((2, label, self.page_no, key))

    def h2(self, title, size=11.2):
        self.ensure(14 * mm)
        c = self.c
        c.setFillColor(HexColor(C["blue"]))
        c.circle(self.right - 1.6 * mm, self.y - 2.9 * mm, 1.15 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor(C["ink2"]))
        c.setFont(self.F["sb"], size)
        c.drawRightString(self.right - 5.5 * mm, self.y - 4.2 * mm, self.shape(title))
        self.y -= 8.5 * mm

    def h3(self, title, size=10.2, color=None):
        self.ensure(11 * mm)
        c = self.c
        c.setFillColor(HexColor(color or C["teal"]))
        c.setFont(self.F["sb"], size)
        c.drawRightString(self.right, self.y - 4 * mm, self.shape(title))
        self.y -= 7 * mm

    # ------------------------------------------------------------ فهرست‌ها
    def bullets(self, items, size=9.6, lead=1.72, bullet="•", indent=4 * mm,
                color=None, font="r", space_after=1.2 * mm):
        for it in items:
            lines = self.wrap(it, font, size, self.maxw - indent - 3 * mm)
            lh = size * lead
            self.ensure(lh * min(2, len(lines)) + 1 * mm, self.cur_kind)
            yy = self.y - size * 0.92
            self.c.setFillColor(HexColor(color or C["ink"]))
            self.c.setFont(self.F["r"], size)
            self.c.drawRightString(self.right - indent + 0.6 * mm, yy, self.shape(bullet))
            for i, (txt, vis, w) in enumerate(lines):
                if i > 0:
                    yy -= lh
                self.c.setFont(self.F[font], size)
                self.c.setFillColor(HexColor(color or C["ink"]))
                self.c.drawRightString(self.right - indent - 3.2 * mm, yy, vis)
            self.y = yy - lh * 0.92
        self.y -= space_after

    def numbered(self, items, size=9.6, lead=1.72, start=1, indent=5.5 * mm, space_after=1.2 * mm):
        n = start
        for it in items:
            lines = self.wrap(it, "r", size, self.maxw - indent - 4 * mm)
            lh = size * lead
            self.ensure(lh * min(2, len(lines)) + 1 * mm, self.cur_kind)
            yy = self.y - size * 0.92
            self.c.setFillColor(HexColor(C["teal"]))
            self.c.setFont(self.F["sb"], size)
            self.c.drawRightString(self.right - indent + 1.2 * mm, yy, fa(n) + ".")
            for i, (txt, vis, w) in enumerate(lines):
                if i > 0:
                    yy -= lh
                self.c.setFont(self.F["r"], size)
                self.c.setFillColor(HexColor(C["ink"]))
                self.c.drawRightString(self.right - indent - 4.4 * mm, yy, vis)
            self.y = yy - lh * 0.92
            n += 1
        self.y -= space_after

    # ------------------------------------------------------------ جداول
    def table(self, headers, rows, widths=None, size=8.2, header_size=8.2,
              caption=None, source=None, ltr_cols=(), align_cols=None, cls=None):
        """
        جدول راست‌به‌چپ. headers از راست به چپ مرتب‌اند.
        widths: نسبت‌ها (جمع=۱) از راست به چپ
        ltr_cols: ایندکس ستون‌های لاتین
        """
        n = len(headers)
        widths = widths or [1 / n] * n
        ws = [self.maxw * w for w in widths]
        pad = 1.7 * mm
        lh = size * 1.55

        def _rtl_text(t):
            return any("\u0621" <= ch <= "\u064a" or "\u066e" <= ch <= "\u06d3" for ch in t)

        def cell_lines(txt, i, w):
            t = str(txt)
            if i in ltr_cols and not _rtl_text(t):
                return self.wrap_ltr_cell(t, w - 2 * pad, size)
            return [v for (_, v, _) in self.wrap(str(txt), "r", size, w - 2 * pad)]

        def hdr_lines(txt, i, w):
            """سرصفحهٔ فارسی همیشه راست‌به‌چپ؛ فقط سرصفحهٔ تمام‌لاتین چپ‌به‌راست."""
            t = str(txt)
            if i in ltr_cols and not _rtl_text(t):
                return self.wrap_ltr_cell(t, w - 2 * pad, size)
            return [v for (_, v, _) in self.wrap(t, "r", size, w - 2 * pad)]

        # ارتفاع سرصفحه
        hh = max(len(hdr_lines(h, i, ws[i])) for i, h in enumerate(headers)) * lh + 2 * pad
        # برای هر ردیف ارتفاع
        body_rows = []
        for r in rows:
            hs = [len(cell_lines(cell, i, ws[i])) for i, cell in enumerate(r)]
            h = max(hs) * lh + 2 * pad
            body_rows.append((r, h))

        # تصمیم یک‌باره برای شکستن جدول (بدون سرصفحهٔ یتیم)
        cap_extra = 7 * mm if caption else 0
        avail_now = self.y - (M_BOT + 4 * mm) - cap_extra
        fit_h, n_fit = hh, 0
        for _, rh in body_rows:
            if fit_h + rh + 2 * mm > avail_now:
                break
            fit_h += rh
            n_fit += 1
        if n_fit < len(body_rows):
            if n_fit < 4 or (len(body_rows) - n_fit) < 3:
                self.new_page(self.cur_kind)

        def draw_header(top):
            x = self.right
            self.c.setFillColor(HexColor(C["ink"]))
            self.c.rect(self.left, top - hh, self.maxw, hh, stroke=0, fill=1)
            for i, htxt in enumerate(headers):
                w = ws[i]
                lines = hdr_lines(htxt, i, w)
                yy = top - pad - size * 0.95
                self.c.setFillColor(HexColor("#ffffff"))
                self.c.setFont(self.F["sb"], header_size)
                for ln in lines:
                    self.c.drawRightString(x - pad, yy, ln)
                    yy -= lh
                x -= w
            return top - hh

        if caption:
            self.ensure(12 * mm)
            self.c.setFillColor(HexColor(C["ink2"]))
            self.c.setFont(self.F["sb"], 9)
            self.c.drawRightString(self.right, self.y - 3.4 * mm, self.shape(caption))
            self.y -= 6.2 * mm

        top = self.y
        y = draw_header(top)
        alt = False
        for r, h in body_rows:
            if y - h < M_BOT + 4 * mm:
                # ادامهٔ جدول در صفحهٔ بعد
                self.set_y(y - 1 * mm)
                self.new_page(self.cur_kind)
                y = draw_header(self.y)
                alt = False
            if alt:
                self.c.setFillColor(HexColor(C["sky"]))
                self.c.rect(self.left, y - h, self.maxw, h, stroke=0, fill=1)
            alt = not alt
            x = self.right
            for i, cell in enumerate(r):
                w = ws[i]
                lines = cell_lines(cell, i, w)
                yy = y - pad - size * 0.95
                for ln in lines:
                    self.c.setFillColor(HexColor(C["ink"]))
                    self.c.setFont(self.F["r"] if i not in ltr_cols else self.F["r"], size)
                    if align_cols and align_cols.get(i) == "c":
                        self.c.drawCentredString(x - w / 2, yy, ln)
                    else:
                        self.c.drawRightString(x - pad, yy, ln)
                    yy -= lh
                x -= w
            # خطوط
            self.c.setStrokeColor(HexColor(C["line"]))
            self.c.setLineWidth(0.55)
            x = self.right
            for i in range(n + 1):
                self.c.line(x, y, x, y - h)
                if i < n:
                    x -= ws[i]
            y -= h
        self.c.setStrokeColor(HexColor(C["line"]))
        self.c.setLineWidth(0.55)
        self.c.line(self.left, y, self.right, y)
        self.set_y(y - 2 * mm)
        if source:
            self.source_line(source)
        else:
            self.gap(1.5 * mm)

    def set_y(self, y):
        self.y = y

    def wrap_ltr_cell(self, txt, width, size):
        words = txt.split(" ")
        lines, cur = [], []
        for w in words:
            cand = " ".join(cur + [w])
            if not cur or stringWidth(cand, self.F["r"], size) <= width:
                cur.append(w)
            else:
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
        return lines

    # ------------------------------------------------------------ جعبه‌ها
    def box(self, title, body, source=None, kind="note", bullet_items=None,
            size=9.3, icon="◈"):
        """جعبهٔ حاشیه‌دار: note(فیروزه‌ای) / clinic(آبی) / wide(بنفش) / amber"""
        palette = {
            "note": (C["soft_teal"], C["teal"], "#0f766e"),
            "clinic": (C["soft_blue"], C["blue"], "#1d4ed8"),
            "amber": (C["soft_amber"], C["gold"], "#92400e"),
            "rose": (C["soft_rose"], "#be123c", "#9f1239"),
        }[kind]
        bg, bar, tcol = palette
        pad = 3.2 * mm
        inner = self.maxw - 2 * pad - 1.5 * mm
        # محاسبهٔ ارتفاع
        head_h = 6.4 * mm if title else 0
        bl = []
        if bullet_items:
            for it in bullet_items:
                bl.extend([v for (_, v, _) in self.wrap(it, "r", size, inner - 4 * mm)])
        body_lines = [v for (_, v, _) in self.wrap(body, "r", size, inner)] if body else []
        src_lines = [v for (_, v, _) in self.wrap(source, "r", 7.4, inner)] if source else []
        lh = size * 1.68
        slh = 7.4 * 1.6
        bh = len(body_lines) * lh
        blh = len(bl) * (size * 1.6)
        h = pad * 2 + head_h + bh + blh + (len(src_lines) * slh + 2 * mm if source else 0)

        if not self.space(min(h, 55 * mm)):
            self.new_page(self.cur_kind)
        # اگر خیلی بلند است، اجازهٔشکستن با ادامه در صفحهٔ بعد
        if h > PAGE_H - M_TOP - M_BOT - 20 * mm:
            h = PAGE_H - M_TOP - M_BOT - 20 * mm
        top = self.y
        self.c.setFillColor(HexColor(bg))
        self.c.roundRect(self.left, top - h, self.maxw, h, 2.4 * mm, stroke=0, fill=1)
        self.c.setFillColor(HexColor(bar))
        self.c.roundRect(self.right - 2.2 * mm, top - h, 2.2 * mm, h, 1.1 * mm, stroke=0, fill=1)
        xr = self.right - pad - 1.5 * mm
        yy = top - pad - size * 0.95
        if title:
            self.c.setFillColor(HexColor(tcol))
            self.c.setFont(self.F["sb"], 9.4)
            self.c.drawRightString(xr, top - pad - 3.2 * mm, self.shape(icon + " " + title))
            yy = top - pad - head_h - 1.6 * mm
        self.c.setFillColor(HexColor(C["ink"]))
        self.c.setFont(self.F["r"], size)
        for ln in body_lines:
            self.c.drawRightString(xr, yy, ln)
            yy -= lh
        if bl:
            for ln in bl:
                self.c.setFillColor(HexColor(C["ink"]))
                self.c.drawRightString(xr, yy, ln)
                yy -= size * 1.6
        if source:
            yy -= 1.2 * mm
            self.c.setFillColor(HexColor(C["gray"]))
            self.c.setFont(self.F["r"], 7.4)
            for ln in src_lines:
                self.c.drawRightString(xr, yy, ln)
                yy -= slh
        self.y = top - h - 3.4 * mm

    def source_line(self, text, size=7.3):
        self.ensure(6 * mm)
        self.c.setFillColor(HexColor(C["gray"]))
        self.c.setFont(self.F["r"], size)
        for ln in [v for (_, v, _) in self.wrap(text, "r", size, self.maxw - 1 * mm)]:
            self.c.drawRightString(self.right, self.y - size * 0.9, ln)
            self.y -= size * 1.55
        self.y -= 2 * mm

    # ------------------------------------------------------------ تصویر
    def figure(self, img, caption, source, max_h=None, width_ratio=1.0, frame=True):
        from PIL import Image
        iw, ih = Image.open(img).size
        boxw = self.maxw * width_ratio
        boxh = (max_h or 92 * mm)

        label = f"شکل {fa(self.fig_no + 1)} — "
        lab_w = self.tw(label, "sb", 8.4)

        limit = self.maxw - lab_w - 4 * mm
        words = str(caption).split()
        cur, taken = "", 0
        for wd in words:
            trial = (cur + " " + wd).strip()
            if self.tw(trial, "r", 8.4) <= limit:
                cur, taken = trial, taken + 1
            else:
                break
        first_line, rest = cur, " ".join(words[taken:])
        rest_lines = [v for (_, v, _) in self.wrap(rest, "r", 8.4, self.maxw - 4 * mm)] if rest else []
        cap_h = (1 + len(rest_lines)) * 8.4 * 1.62 + 2 * mm
        src_lines = [v for (_, v, _) in self.wrap(source, "r", 7.2, self.maxw - 4 * mm)]
        src_h = len(src_lines) * 7.2 * 1.55 + 1 * mm

        r = min(boxw / iw, boxh / ih)
        w, h = iw * r, ih * r
        total = h + cap_h + src_h + 6 * mm
        if not self.space(total):
            # اگر با کوچک‌کردن شکل در همین صفحه جا می‌شود، صفحه را نشکن
            avail = self.y - (M_BOT + 4 * mm)
            need_min = 46 * mm + cap_h + src_h + 6 * mm
            if avail >= need_min:
                boxh = avail - cap_h - src_h - 6 * mm
                r = min(boxw / iw, boxh / ih)
                w, h = iw * r, ih * r
                total = h + cap_h + src_h + 6 * mm
            else:
                self.new_page(self.cur_kind)

        self.fig_no += 1
        top = self.y
        x0 = self.right - self.maxw + (self.maxw - w) / 2
        if frame:
            self.c.setFillColor(HexColor("#ffffff"))
            self.c.roundRect(x0 - 2 * mm, top - h - 2 * mm, w + 4 * mm, h + 4 * mm, 2 * mm, stroke=0, fill=1)
            self.c.setStrokeColor(HexColor(C["line"]))
            self.c.setLineWidth(0.7)
            self.c.roundRect(x0 - 2 * mm, top - h - 2 * mm, w + 4 * mm, h + 4 * mm, 2 * mm, stroke=1, fill=0)
        self.c.drawImage(img, x0, top - h, width=w, height=h, mask="auto")
        yy = top - h - 2 * mm - 4.2 * mm
        self.c.setFillColor(HexColor(C["ink2"]))
        self.c.setFont(self.F["sb"], 8.4)
        self.c.drawRightString(self.right, yy, self.shape(label))
        if first_line:
            self.c.setFont(self.F["r"], 8.4)
            self.c.drawRightString(self.right - lab_w - 0.8 * mm, yy, self.shape(first_line))
        self.c.setFont(self.F["r"], 8.4)
        yy -= 8.4 * 1.62
        for ln in rest_lines:
            self.c.drawRightString(self.right, yy, ln)
            yy -= 8.4 * 1.62
        self.c.setFillColor(HexColor(C["gray"]))
        self.c.setFont(self.F["r"], 7.2)
        yy -= 0.6 * mm
        for ln in src_lines:
            self.c.drawRightString(self.right, yy, ln)
            yy -= 7.2 * 1.55
        self.y = yy - 3 * mm

    # ------------------------------------------------------------ جعبهٔ یادداشت
    def note_area(self, title="یادداشت", lines=7, height=None):
        h = height or (lines * 7.6 * mm + 9 * mm)
        if not self.space(h + 4 * mm):
            self.new_page(self.cur_kind)
        top = self.y
        self.c.setFillColor(HexColor("#ffffff"))
        self.c.setStrokeColor(HexColor(C["line"]))
        self.c.setLineWidth(0.8)
        self.c.roundRect(self.left, top - h, self.maxw, h, 2.2 * mm, stroke=1, fill=1)
        self.c.setFillColor(HexColor(C["ink2"]))
        self.c.setFont(self.F["sb"], 8.6)
        self.c.drawRightString(self.right - 3 * mm, top - 5.4 * mm, self.shape("✎ " + title))
        y = top - 11 * mm
        self.c.setStrokeColor(HexColor("#cbd6e6"))
        self.c.setLineWidth(0.6)
        n = lines
        for i in range(n):
            if y < top - h + 4 * mm:
                break
            self.c.line(self.left + 4 * mm, y, self.right - 4 * mm, y)
            y -= 7.6 * mm
        self.c.setDash()
        self.y = top - h - 3.4 * mm

    # ------------------------------------------------------------ برگهٔ تحویل
    def delivery_sheet(self, no, title, question, h=None):
        h = h or 90 * mm
        if not self.space(h):
            self.new_page(self.cur_kind)
        top = self.y
        c = self.c
        c.setFillColor(HexColor("#ffffff"))
        c.setStrokeColor(HexColor(C["teal"]))
        c.setLineWidth(1.1)
        c.roundRect(self.left, top - h, self.maxw, h, 2.6 * mm, stroke=1, fill=1)
        c.setFillColor(HexColor(C["ink"]))
        c.roundRect(self.left, top - 10 * mm, self.maxw, 10 * mm, 2.6 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor("#ffffff"))
        c.setFont(self.F["b"], 9.6)
        c.drawRightString(self.right - 3.4 * mm, top - 6.6 * mm,
                          self.shape(f"برگهٔ تحویل مبحث {fa(no)} — {title}"))
        c.setFillColor(HexColor("#7dd3c8"))
        c.setFont(self.F["r"], 7.6)
        c.drawString(self.left + 3.4 * mm, top - 6.6 * mm, self.shape("HumsYar · فیزیولوژی اعصاب و حواس ویژه"))

        # فیلدهای مشخصات
        y = top - 15.5 * mm
        c.setFillColor(HexColor(C["gray"]))
        for label, x0, w in [("نام و نام خانوادگی جزوه‌نویس", self.right - 4 * mm, 62 * mm),
                             ("تاریخ", self.right - 76 * mm, 34 * mm)]:
            c.setFont(self.F["r"], 7.4)
            c.drawRightString(x0, y, self.shape(label))
            c.setStrokeColor(HexColor("#cbd5e1"))
            c.setLineWidth(0.6)
            c.line(x0, y - 3.4 * mm, x0 - w, y - 3.4 * mm)

        # اقلام تحویل
        y -= 10.6 * mm
        c.setFillColor(HexColor(C["gray"]))
        c.setFont(self.F["r"], 7.4)
        c.drawRightString(self.right - 4 * mm, y, self.shape("اقلام تحویل‌شده (تیک بزنید):"))
        x = self.right - 4 * mm - self.tw("اقلام تحویل‌شده (تیک بزنید):", "r", 7.4) - 5 * mm
        for ch in ["رونویسی متن درس", "شکل و زیرنما", "جدول‌ها", "ارجاع موضعی", "بازخوانی املایی"]:
            c.setStrokeColor(HexColor(C["teal"]))
            c.setLineWidth(0.8)
            c.rect(x - 2.7 * mm, y - 0.8 * mm, 2.7 * mm, 2.7 * mm, stroke=1, fill=0)
            c.setFillColor(HexColor(C["ink"]))
            c.setFont(self.F["r"], 7.2)
            c.drawRightString(x - 4.4 * mm, y, self.shape(ch))
            x -= (2.7 * mm + 4.4 * mm + self.tw(ch, "r", 7.2) + 5.4 * mm)

        # پرسش مرتبط
        y -= 10.6 * mm
        c.setFillColor(HexColor(C["soft_blue"]))
        qh = max(27 * mm, h - 64 * mm)
        c.roundRect(self.left + 4 * mm, y - qh, self.maxw - 8 * mm, qh, 2 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor(C["ink2"]))
        c.setFont(self.F["sb"], 8)
        c.drawRightString(self.right - 6 * mm, y - 4.6 * mm, self.shape("پرسش مرتبط با این مبحث (پاسخ در همان جا نوشته شود)"))
        c.setFont(self.F["r"], 8)
        qlines = [v for (_, v, _) in self.wrap(question, "r", 8, self.maxw - 12 * mm)]
        yy = y - 9.4 * mm
        for ln in qlines[:4]:
            c.drawRightString(self.right - 6 * mm, yy, ln)
            yy -= 4.4 * mm
        c.setStrokeColor(HexColor("#c9d8ee"))
        c.setLineWidth(0.55)
        c.setDash(1.6, 2.0)
        ly = yy - 1.6 * mm
        bottom_lim = y - qh + 4 * mm
        while ly > bottom_lim:
            c.line(self.left + 8 * mm, ly, self.right - 8 * mm, ly)
            ly -= 7.4 * mm
        c.setDash()
        # امضا
        for label, x0 in [("امضای جزوه‌نویس", self.right - 4 * mm),
                          ("امضای تحویل‌گیرنده", self.right - 86 * mm)]:
            c.setStrokeColor(HexColor("#cbd5e1"))
            c.setLineWidth(0.6)
            c.line(x0, top - h + 12 * mm, x0 - 60 * mm, top - h + 12 * mm)
            c.setFillColor(HexColor(C["gray"]))
            c.setFont(self.F["r"], 7.2)
            c.drawRightString(x0, top - h + 7.6 * mm, self.shape(label))
        self.y = top - h - 4 * mm

    # ------------------------------------------------------------ نشانک
    def bookmark(self, key, title, level=1):
        self._bm += 1
        self.c.bookmarkPage(key)
        self.c.addOutlineEntry(title, key, level=level - 1, closed=False)

    def link_toc(self, key, rect):
        self.c.linkRect("", key, rect, relative=0, thickness=0)

    # ------------------------------------------------------------ ذخیره
    def save(self):
        self._footer()
        self.c.showPage()
        self.c.save()

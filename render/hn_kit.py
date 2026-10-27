"""HumsYar PDF kit v2 — a compact RTL layout engine on ReportLab.

Why not HTML/WeasyPrint: this sandbox has no Pango/Cairo, so the HumsYar visual
language (dark gradient covers, teal accents, note boxes, print-safe rules) is
rebuilt directly on the ReportLab canvas. Text is shaped with arabic_reshaper +
python-bidi and the Vazirmatn family is embedded, so Persian joining, ZWNJ,
bidi runs and embedded Latin terms render correctly.

Design notes
------------
* The vertical cursor ``self.y`` is measured **downward from the top margin**
  (top-down layout, like a web page).  ``py(y)`` converts a cursor value into a
  ReportLab PDF coordinate.
* Every block method advances ``self.y`` and never draws outside the frame; the
  page furniture (header rule, running title, page number) is absolute.
* Nothing here guesses: a missing image file is reported on the page instead of
  being silently skipped.
"""
from __future__ import annotations

import re
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------- brand tokens
INK = HexColor("#0f172a")
BODY = HexColor("#1e293b")
MUTED = HexColor("#64748b")
LINE = HexColor("#e2e8f0")
SOFT = HexColor("#f8fbff")
PAGE_BG = HexColor("#f0f6ff")
BLUE = HexColor("#2563eb")
BLUE_D = HexColor("#1d4ed8")
BLUE_BG = HexColor("#eff6ff")
TEAL = HexColor("#0d9488")
TEAL_D = HexColor("#0f766e")
TEAL_L = HexColor("#ccfbf1")
TEAL_LL = HexColor("#f0fdfa")
AMBER = HexColor("#b45309")
AMBER_BG = HexColor("#fffbeb")
AMBER_LINE = HexColor("#fcd34d")
ROSE = HexColor("#be123c")
ROSE_BG = HexColor("#fff1f2")
ROSE_LINE = HexColor("#fda4af")
CARD = HexColor("#ffffff")
DARK_1 = HexColor("#0a0f1e")
DARK_2 = HexColor("#0d1524")
DARK_3 = HexColor("#0a1a26")

FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"
FONT_FILES = {
    "Vazir": "Vazirmatn-Regular.ttf",
    "VazirB": "Vazirmatn-Bold.ttf",
    "VazirM": "Vazirmatn-Medium.ttf",
    "VazirL": "Vazirmatn-Light.ttf",
    # fallback family: Vazirmatn has no Greek letters and no arrows
    "DejaVu": "DejaVuSans.ttf",
    "DejaVuB": "DejaVuSans-Bold.ttf",
}
FALLBACK = {"Vazir": "DejaVu", "VazirL": "DejaVu", "VazirM": "DejaVu",
            "VazirB": "DejaVuB"}
REGISTERED = False
_VAZIR_CMAP: set[int] | None = None

A4W, A4H = A4
MM = 2.8346
M_TOP, M_BOTTOM, M_LEFT, M_RIGHT = 21 * MM, 19 * MM, 15 * MM, 15 * MM
CONTENT_W = A4W - M_LEFT - M_RIGHT

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
ZWNJ = "\u200c"


def register_fonts() -> None:
    global REGISTERED
    if REGISTERED:
        return
    for name, fname in FONT_FILES.items():
        pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / fname)))
    registerFontFamily("Vazir", normal="Vazir", bold="VazirB", italic="Vazir", boldItalic="VazirB")
    REGISTERED = True


def fa_digits(text: str) -> str:
    """Convert ASCII digits to Persian digits, leaving Latin/numeric tokens intact."""
    def repl(m: re.Match) -> str:
        return m.group(0).translate(FA_DIGITS)
    return re.sub(r"(?<![A-Za-z0-9\-_/.٫])\d+(?:[.,]\d+)?(?![A-Za-z0-9\-])", repl, text)


def vazir_cmap() -> set[int]:
    """Code points covered by the Vazirmatn family (used for per-char fallback)."""
    global _VAZIR_CMAP
    if _VAZIR_CMAP is None:
        from fontTools.ttLib import TTFont
        _VAZIR_CMAP = set(TTFont(str(FONT_DIR / FONT_FILES["Vazir"])).getBestCmap())
    return _VAZIR_CMAP


def runs(text: str, font: str) -> list[tuple[str, str]]:
    """Split an already-shaped string into (font, text) runs.

    Shaping happens before this call, so the string is in *visual* order and can
    be drawn strictly left to right.  Only characters missing from Vazirmatn
    (Greek letters, arrows, some symbols) switch to the fallback family.
    """
    cmap = vazir_cmap()
    fb = FALLBACK.get(font, "DejaVu")
    out: list[tuple[str, str]] = []
    for ch in text:
        f = font if (ord(ch) in cmap or ch.isspace()) else fb
        if out and out[-1][0] == f:
            out[-1] = (f, out[-1][1] + ch)
        else:
            out.append((f, ch))
    return out


def text_width(text: str, font: str, size: float) -> float:
    return sum(pdfmetrics.stringWidth(part, f, size) for f, part in runs(text, font))


def draw_shaped(c, x: float, y: float, shaped: str, font: str, size: float,
                color=None, align: str = "left") -> None:
    """Draw a shaped (visual-order) string with per-character font fallback."""
    if not shaped:
        return
    if color is not None:
        c.setFillColor(color)
    total = text_width(shaped, font, size)
    pen = x if align == "left" else (x - total if align == "right" else x - total / 2)
    for f, part in runs(shaped, font):
        c.setFont(f, size)
        c.drawString(pen, y, part)
        pen += pdfmetrics.stringWidth(part, f, size)


def shape(text: str) -> str:
    """Shape Arabic/Persian glyphs and resolve the bidi order for canvas drawing."""
    if not text:
        return ""
    return get_display(arabic_reshaper.reshape(text))


class TextStyle:
    def __init__(self, font="Vazir", size=10.6, leading=None, color=BODY,
                 justify=True, space_before=0, space_after=0, align="right"):
        self.font = font
        self.size = size
        self.leading = leading or size * 1.78
        self.color = color
        self.justify = justify
        self.space_before = space_before
        self.space_after = space_after
        self.align = align


class PDFBook:
    """Small flowing-document engine (RTL first)."""

    def __init__(self, path, title: str,
                 footer: str = "HumsYar · جزوهٔ مادر فیزیولوژی اعصاب و حواس ویژه",
                 subject: str = "جزوهٔ مادر — فیزیولوژی اعصاب و حواس ویژه"):
        register_fonts()
        self.path = Path(path)
        self.title = title
        self.footer = footer
        self.c = canvas.Canvas(str(self.path), pagesize=A4)
        self.c.setTitle(title)
        self.c.setAuthor("HumsYar")
        self.c.setSubject(subject)
        self.page = 1
        self.y = M_TOP
        self.heading_pages: dict[str, int] = {}
        self.outline: list[tuple[int, str, str]] = []
        self.running = ""
        self.dark_mode = False
        self.show_furniture = True
        self.missing_assets: list[str] = []
        self._dirty = False          # has anything been drawn on the current page?
        self._paint_bg()

    def _touch(self) -> None:
        """Mark the current page as non-empty (used to drop a trailing blank page)."""
        self._dirty = True

    # ------------------------------------------------------------- geometry
    def py(self, y: float) -> float:
        return A4H - y

    def bottom_limit(self) -> float:
        return A4H - M_BOTTOM

    def usable_height(self) -> float:
        return A4H - M_TOP - M_BOTTOM

    # ------------------------------------------------------------- pages
    def _paint_bg(self) -> None:
        self._dirty = False
        self.c.setFillColor(CARD)
        self.c.rect(0, 0, A4W, A4H, stroke=0, fill=1)

    def _furniture(self) -> None:
        if self.dark_mode or not self.show_furniture or not self._dirty:
            return
        c = self.c
        # header rule + running title
        top = A4H - M_TOP + 10
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(M_LEFT, top, A4W - M_LEFT, top)
        c.setFont("Vazir", 7.6)
        c.setFillColor(MUTED)
        if self.running:
            draw_shaped(c, A4W - M_RIGHT, top + 5, shape(self.running), "Vazir", 7.6,
                       MUTED, align="right")
        draw_shaped(c, M_LEFT, top + 5, "HumsYar · Master Notes", "Vazir", 7.6, MUTED)
        # footer rule + page number
        foot = M_BOTTOM - 10
        c.setStrokeColor(LINE)
        c.line(M_LEFT, foot, A4W - M_LEFT, foot)
        c.setFont("Vazir", 7.4)
        c.setFillColor(MUTED)
        draw_shaped(c, M_LEFT, foot - 11, shape(self.footer), "Vazir", 7.4, MUTED)
        c.setFont("VazirM", 9)
        c.setFillColor(TEAL_D)
        draw_shaped(c, A4W - M_RIGHT, foot - 11, fa_digits(str(self.page)), "VazirM", 9,
                    TEAL_D, align="right")

    def new_page(self) -> None:
        self._furniture()
        self.c.showPage()
        self.page += 1
        self.y = M_TOP
        self._paint_bg()

    def ensure(self, height: float) -> None:
        if self.y + height > self.bottom_limit():
            self.new_page()

    def spacer(self, h: float) -> None:
        self.y += h

    def save(self) -> None:
        self._furniture()
        self.c.save()

    # ------------------------------------------------------------- dark page
    def dark_page(self, painter, reuse_blank_page: bool = False) -> None:
        """Full-bleed dark page; ``painter(book)`` draws inside it."""
        if not reuse_blank_page:
            self._furniture()
            self.c.showPage()
            self.page += 1
        else:
            self.c.setFillColor(CARD)
            self.c.rect(0, 0, A4W, A4H, stroke=0, fill=1)
        self.dark_mode = True
        self.y = M_TOP
        c = self.c
        c.saveState()
        p = c.beginPath()
        p.rect(0, 0, A4W, A4H)
        c.clipPath(p, stroke=0, fill=0)
        c.setFillColor(DARK_1)
        c.rect(0, 0, A4W, A4H, stroke=0, fill=1)
        c.linearGradient(0, A4H, A4W, 0, (DARK_1, DARK_2, DARK_3), (0, 0.55, 1))
        c.restoreState()
        self._halo(A4W * 0.84, A4H * 0.88, 250, Color(37 / 255, 99 / 255, 235 / 255), 0.30)
        self._halo(A4W * 0.16, A4H * 0.10, 270, Color(20 / 255, 184 / 255, 166 / 255), 0.26)
        painter(self)
        c.showPage()
        self.page += 1
        self.dark_mode = False
        self.y = M_TOP
        self._paint_bg()

    def _halo(self, cx, cy, r, color, alpha) -> None:
        c = self.c
        for i in range(22, 0, -1):
            frac = i / 22
            c.saveState()
            c.setFillColor(color, alpha=alpha * (1 - frac) ** 1.7)
            c.circle(cx, cy, r * frac, stroke=0, fill=1)
            c.restoreState()

    def rule(self, y: float, x1: float, x2: float, colors=(BLUE, TEAL), width=2.0) -> None:
        self._touch()
        c = self.c
        steps = 64
        for i in range(steps):
            col = _mix(colors[0], colors[1], i / steps)
            c.setStrokeColor(col)
            c.setLineWidth(width)
            c.line(x1 + (x2 - x1) * i / steps, y, x1 + (x2 - x1) * (i + 1) / steps + 0.6, y)

    # ------------------------------------------------------------- text core
    def wrap(self, text: str, font: str, size: float, width: float) -> list[str]:
        words = str(text).split(" ")
        lines: list[str] = []
        cur = ""
        for w in words:
            trial = (cur + " " + w) if cur else w
            if text_width(shape(trial), font, size) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def draw_line(self, text: str, top: float, style: TextStyle, width: float,
                  x_right: float | None = None, justify: bool = False) -> None:
        """Draw one shaped line with its baseline inside a box starting at ``top``."""
        c = self.c
        c.setFont(style.font, style.size)
        c.setFillColor(style.color)
        shaped = shape(text)
        baseline = self.py(top + style.leading * 0.74)
        sw = text_width(shaped, style.font, style.size)
        x_right = A4W - M_RIGHT if x_right is None else x_right
        if justify and sw < width - 0.5 and all(ord(ch) in vazir_cmap() or ch.isspace()
                                               for ch in shaped):
            nsp = shaped.count(" ")
            if nsp:
                gap = (width - sw) / nsp
                if 0 < gap < style.size * 1.1:
                    c.setFont(style.font, style.size)
                    c.setFillColor(style.color)
                    c.drawString(x_right - width, baseline, shaped, wordSpace=gap)
                    return
        align = "center" if style.align == "center" else "right"
        draw_shaped(c, x_right if align != "center" else x_right - width / 2,
                    baseline, shaped, style.font, style.size, style.color, align=align)

    def paragraph(self, text: str, style: TextStyle | None = None, width: float = CONTENT_W,
                  x_right: float | None = None, indent: float = 0.0,
                  keep_with: float = 0.0) -> None:
        """One paragraph is one block: it moves to the next page instead of splitting.

        ``keep_with`` reserves room under the paragraph for whatever belongs to it
        (its source line, the first lines of the next block), so a paragraph never
        ends at the foot of a page with its citation or its continuation overleaf.
        """
        if not text:
            return
        self._touch()
        style = style or TextStyle()
        usable = width - indent
        x_right = (A4W - M_RIGHT if x_right is None else x_right) - indent
        lines = self.wrap(text, style.font, style.size, usable)
        need = len(lines) * style.leading + style.space_before + style.space_after + keep_with
        self.ensure(min(need, self.usable_height() - 8))
        self.y += style.space_before
        for i, line in enumerate(lines):
            just = style.justify and i < len(lines) - 1
            self.draw_line(line, self.y, style, usable, x_right, justify=just)
            self.y += style.leading
        self.y += style.space_after

    def source_line(self, text: str) -> None:
        if not text:
            return
        self._touch()
        self.ensure(13)
        c = self.c
        c.setFont("Vazir", 7.3)
        c.setFillColor(MUTED)
        draw_shaped(c, A4W - M_RIGHT, self.py(self.y + 8), shape(f"منبع: {text}"),
                    "Vazir", 7.3, MUTED, align="right")
        self.y += 12

    # ------------------------------------------------------------- headings
    def h1(self, text: str, anchor: str = "", kicker: str = "", outline: bool = True) -> None:
        self._touch()
        # the running title is set only after the page break decisions, otherwise
        # the page that is closed here would carry the *next* section's title
        self.ensure(78)
        self.y += 16
        c = self.c
        if kicker:
            c.setFont("VazirM", 8.6)
            c.setFillColor(TEAL)
            draw_shaped(c, A4W - M_RIGHT, self.py(self.y + 2), shape(kicker), "VazirM", 8.6,
                        TEAL, align="right")
            self.y += 16
        # A long section title must never run off the right-to-left margin:
        # first shrink a little, then (only if needed) break into two lines.
        shaped = shape(text)
        size = 18.5
        while size > 12.0 and text_width(shaped, "VazirB", size) > CONTENT_W:
            size -= 0.5
        lines = [shaped]
        if text_width(shaped, "VazirB", size) > CONTENT_W:
            size = 15.5
            lines = [shape(part) for part in self.wrap(text, "VazirB", size, CONTENT_W)]
            self.ensure(24 * len(lines) + 40)
        self.running = text
        c = self.c
        c.setFont("VazirB", size)
        c.setFillColor(INK)
        for i, line in enumerate(lines):
            draw_shaped(c, A4W - M_RIGHT, self.py(self.y + 16), line, "VazirB", size,
                        INK, align="right")
            if i < len(lines) - 1:
                self.y += size * 1.34
        self.y += 24
        self.rule(self.py(self.y), A4W - M_RIGHT, A4W - M_RIGHT - CONTENT_W * 0.36)
        self.y += 12
        if anchor:
            self.heading_pages[anchor] = self.page
            self.c.bookmarkPage(anchor)
            if outline:
                self.c.addOutlineEntry(text, anchor, level=0)

    def h2(self, text: str, anchor: str = "", keep_with: float = 46.0) -> None:
        self._touch()
        font, size = "VazirB", 13.2
        lines = self.wrap(text, font, size, CONTENT_W - 26)
        h = len(lines) * size * 1.62 + 13
        self.ensure(h + 18 + keep_with)
        c = self.c
        top = self.y
        c.setFillColor(TEAL_LL)
        c.roundRect(M_LEFT, self.py(top + h), CONTENT_W, h, 5, stroke=0, fill=1)
        c.setFillColor(TEAL)
        c.rect(A4W - M_RIGHT - 3.2, self.py(top + h), 3.2, h, stroke=0, fill=1)
        ty = top + 4
        for line in lines:
            c.setFont(font, size)
            c.setFillColor(TEAL_D)
            draw_shaped(c, A4W - M_RIGHT - 11, self.py(ty + size * 1.15), shape(line),
                        font, size, TEAL_D, align="right")
            ty += size * 1.62
        self.y = top + h + 7
        if anchor:
            self.heading_pages[anchor] = self.page
            self.c.bookmarkPage(anchor)
            self.c.addOutlineEntry(text, anchor, level=1)

    def h3(self, text: str, keep_with: float = 46.0) -> None:
        self._touch()
        font, size = "VazirB", 11.4
        lines = self.wrap(text, font, size, CONTENT_W - 18)
        self.ensure(16 + len(lines) * size * 1.6 + 12 + keep_with)
        self.y += 5
        c = self.c
        c.setFillColor(BLUE)
        c.circle(A4W - M_RIGHT - 4, self.py(self.y + 8), 2.1, stroke=0, fill=1)
        for line in lines:
            c.setFont(font, size)
            c.setFillColor(BLUE_D)
            draw_shaped(c, A4W - M_RIGHT - 13, self.py(self.y + size * 1.1), shape(line),
                        font, size, BLUE_D, align="right")
            self.y += size * 1.5
        self.y += 2

    # ------------------------------------------------------------- lists
    def bullets(self, items, style: TextStyle | None = None, level: int = 0,
                keep_with: float = 0.0) -> None:
        self._touch()
        style = style or TextStyle(size=10.4, leading=17.6, justify=False)
        # never leave a single bullet alone at the foot of a page
        self.ensure(min(len(items), 2) * style.leading + 8 + keep_with)
        for item in items:
            indent = 16 + level * 14
            lines = self.wrap(item, style.font, style.size, CONTENT_W - indent - 4)
            self.ensure(len(lines) * style.leading + 5)
            c = self.c
            c.setFillColor(TEAL if level == 0 else TEAL_L)
            c.setStrokeColor(TEAL)
            c.setLineWidth(1.0)
            my = self.py(self.y + 7.2)
            if level == 0:
                c.circle(A4W - M_RIGHT - 6.5, my, 2.2, stroke=0, fill=1)
            else:
                c.circle(A4W - M_RIGHT - 8, my, 1.8, stroke=1, fill=0)
            for line in lines:
                self.draw_line(line, self.y, style, CONTENT_W - indent,
                               A4W - M_RIGHT - indent)
                self.y += style.leading
            self.y += 2.6

    def numbered(self, items, style: TextStyle | None = None, start: int = 1,
                 keep_with: float = 0.0) -> None:
        self._touch()
        style = style or TextStyle(size=10.4, leading=17.6, justify=False)
        # never leave a single numbered item alone at the foot of a page
        self.ensure(min(len(items), 2) * style.leading + 8 + keep_with)
        for idx, item in enumerate(items, start=start):
            num = str(idx).translate(FA_DIGITS)
            lines = self.wrap(item, style.font, style.size, CONTENT_W - 30)
            self.ensure(len(lines) * style.leading + 6)
            c = self.c
            c.setFillColor(HexColor("#dbeafe"))
            c.roundRect(A4W - M_RIGHT - 16, self.py(self.y + 13), 15, 15, 4, stroke=0, fill=1)
            c.setFillColor(BLUE_D)
            c.setFont("VazirB", 8.4)
            draw_shaped(c, A4W - M_RIGHT - 8.5, self.py(self.y + 9), num, "VazirB", 8.4,
                        BLUE_D, align="center")
            for line in lines:
                self.draw_line(line, self.y, style, CONTENT_W - 24, A4W - M_RIGHT - 22)
                self.y += style.leading
            self.y += 3.0

    # ------------------------------------------------------------- boxes
    def callout(self, text: str, kind: str = "key", title: str | None = None) -> None:
        palette = {
            "key": (TEAL_LL, TEAL, TEAL_D),
            "exam": (AMBER_BG, AMBER_LINE, AMBER),
            "warn": (ROSE_BG, ROSE_LINE, ROSE),
            "info": (BLUE_BG, HexColor("#bfdbfe"), BLUE_D),
        }
        self._touch()
        fill, stroke, accent = palette.get(kind, palette["key"])
        labels = {"key": "نکتهٔ کلیدی", "exam": "نکتهٔ امتحانی", "warn": "هشدار",
                  "info": "توضیح"}
        title = title or labels.get(kind, "")
        style = TextStyle(size=10.2, leading=17.4, justify=True)
        pad = 9
        inner_w = CONTENT_W - 2 * pad - 6
        lines = self.wrap(text, style.font, style.size, inner_w)
        h = 20 + len(lines) * style.leading + pad
        self.ensure(h + 10)
        c = self.c
        top = self.y
        c.setFillColor(fill)
        c.setStrokeColor(stroke)
        c.setLineWidth(0.8)
        c.roundRect(M_LEFT, self.py(top + h), CONTENT_W, h, 6, stroke=1, fill=1)
        c.setFillColor(accent)
        c.roundRect(A4W - M_RIGHT - 3.4, self.py(top + h) + 3, 3.4, h - 6, 1.7, stroke=0, fill=1)
        c.setFont("VazirB", 8.8)
        c.setFillColor(accent)
        draw_shaped(c, A4W - M_RIGHT - pad, self.py(top + 13), shape(title), "VazirB", 8.8,
                    accent, align="right")
        yy = top + 17
        for line in lines:
            self.draw_line(line, yy, style, inner_w, A4W - M_RIGHT - pad, justify=False)
            yy += style.leading
        self.y = top + h + 9

    def guyton_block(self, title: str, citation: str, paragraphs, note: str = "",
                     max_paras: int = 4) -> None:
        """Verbatim English Guyton excerpt inside a clearly-cited framed block.

        The text is the source text (never re-written), so it is drawn LTR and
        each paragraph carries its printed page number.
        """
        self._touch()
        body = TextStyle(font="Vazir", size=8.9, leading=13.6, color=HexColor("#1f2937"),
                         justify=False, align="left")
        head_h = 34 if note else 24
        shown = paragraphs[:max_paras]
        measured = sum(len(self.wrap(p["text"], body.font, body.size, CONTENT_W - 34)) for p in shown)
        total = head_h + measured * body.leading + 26
        # a Guyton block may break across pages; draw it as a flow with a left bar
        c = self.c
        c.setStrokeColor(HexColor("#c7d2fe"))
        c.setLineWidth(2.2)
        start_y = self.y
        x_left = A4W - M_RIGHT - CONTENT_W + 10
        c.setFillColor(HexColor("#f8faff"))
        c.setFont("VazirB", 9.6)
        self.ensure(min(total, 120))
        # header
        self.y += 4
        c.setFillColor(HexColor("#312e81"))
        c.setFont("VazirB", 10)
        draw_shaped(c, A4W - M_RIGHT - 8, self.py(self.y + 12), shape("گایتون — " + title),
                    "VazirB", 10, HexColor("#312e81"), align="right")
        self.y += 17
        c.setFont("VazirL", 7.6)
        c.setFillColor(MUTED)
        draw_shaped(c, A4W - M_RIGHT - 8, self.py(self.y + 7), shape(citation), "VazirL", 7.6,
                    MUTED, align="right")
        self.y += 12
        for p in shown:
            for line in self.wrap(p["text"], body.font, body.size, CONTENT_W - 34):
                self.ensure(body.leading)
                c.setFont(body.font, body.size)
                c.setFillColor(body.color)
                draw_shaped(c, x_left, self.py(self.y + body.leading * 0.78), line,
                            body.font, body.size, body.color)
                self.y += body.leading
            c.setFont("Vazir", 7.0)
            c.setFillColor(MUTED)
            self.ensure(11)
            draw_shaped(c, x_left, self.py(self.y + 8), f"[p. {p.get('page', '?')}]",
                        "Vazir", 7.0, MUTED)
            self.y += 11
        if note:
            self.ensure(24)
            note_style = TextStyle(size=8.8, leading=14, color=HexColor("#4338ca"), justify=False)
            for line in self.wrap(note, note_style.font, note_style.size, CONTENT_W - 30):
                self.draw_line(line, self.y, note_style, CONTENT_W - 30, A4W - M_RIGHT - 8)
                self.y += note_style.leading
        # left guide bar
        c.setStrokeColor(HexColor("#c7d2fe"))
        c.setLineWidth(2.2)
        c.line(x_left - 8, self.py(self.y), x_left - 8, self.py(start_y + head_h - 14))
        self.y += 10

    def guyton_pair(self, title: str, citation: str, english, fa_text: str,
                    fa_label: str = "ترجمهٔ روان متن بالا (ترجمهٔ تحریریهٔ این جزوه — نقل‌قول از ترجمهٔ رسمی فارسی نیست)",
                    note: str = "") -> None:
        """English Guyton excerpt followed by an editorial Persian translation.

        ``english`` is a list of ``{"text": str, "page": int|None}`` items and is
        drawn LTR exactly as printed in the source.  ``fa_text`` is this team's
        fluent translation and is drawn RTL in a clearly separate band, so the
        two voices can never be confused on paper.
        """
        self._touch()
        c = self.c
        accent = HexColor("#312e81")
        soft = HexColor("#f7f8ff")
        en = TextStyle(size=8.9, leading=13.4, color=HexColor("#1f2937"), justify=False,
                       align="left")
        fa = TextStyle(size=10.0, leading=17.0, color=HexColor("#111827"), justify=True)
        lab = TextStyle(size=8.2, leading=14, color=HexColor("#4338ca"), justify=False)
        x_left = A4W - M_RIGHT - CONTENT_W + 10
        bar_x = x_left - 8

        def bar(y0: float, y1: float, color) -> None:
            c.setStrokeColor(color)
            c.setLineWidth(2.2)
            c.line(bar_x, self.py(y1), bar_x, self.py(y0))

        fa_paras = (fa_text if isinstance(fa_text, (list, tuple))
                    else [s.strip() for s in str(fa_text).split("\n\n") if s.strip()])
        # a Guyton pair that fits on one page is never split across two pages
        need = 30 + 17 + 12
        for para in english:
            need += len(self.wrap(para["text"], en.font, en.size, CONTENT_W - 34)) * en.leading
            if para.get("page"):
                need += 11
        for para in fa_paras:
            need += (len(self.wrap(para.replace("\n", " "), fa.font, fa.size, CONTENT_W - 34))
                     * fa.leading + 2)
        if note:
            need += len(self.wrap(note, "Vazir", 8.6, CONTENT_W - 30)) * 13.6
        # opt-in (cfg["guyton_atomic"]): earlier sessions keep their shipped layout
        if getattr(self, "guyton_atomic", False) and need <= self.usable_height() - 8:
            self.ensure(need)
        else:
            self.ensure(70)
        # ---- header
        top = self.y
        c.setFillColor(soft)
        c.rect(M_LEFT, self.py(top + 30), CONTENT_W, 30, stroke=0, fill=1)
        bar(top, top + 30, HexColor("#c7d2fe"))
        draw_shaped(c, A4W - M_RIGHT - 4, self.py(top + 13), shape("گایتون — " + title),
                    "VazirB", 10, accent, align="right")
        draw_shaped(c, A4W - M_RIGHT - 4, self.py(top + 25), shape(citation), "VazirL", 7.6,
                    MUTED, align="right")
        self.y = top + 30
        # ---- English source text (LTR, never re-flowed by hand)
        for para in english:
            for line in self.wrap(para["text"], en.font, en.size, CONTENT_W - 34):
                self.ensure(en.leading)
                bar(self.y, self.y + en.leading, HexColor("#c7d2fe"))
                draw_shaped(c, x_left, self.py(self.y + en.leading * 0.76), line,
                            en.font, en.size, en.color)
                self.y += en.leading
            pg = para.get("page")
            if pg:
                self.ensure(11)
                bar(self.y, self.y + 11, HexColor("#c7d2fe"))
                draw_shaped(c, x_left, self.py(self.y + 8), f"[p. {pg}]", "Vazir", 7.0, MUTED)
                self.y += 11
        # ---- Persian editorial translation band
        self.ensure(26)
        top = self.y
        c.setFillColor(HexColor("#eef2ff"))
        c.rect(M_LEFT, self.py(top + 17), CONTENT_W, 17, stroke=0, fill=1)
        draw_shaped(c, A4W - M_RIGHT - 6, self.py(top + 11), shape(fa_label), "VazirM", 8.2,
                    HexColor("#4338ca"), align="right")
        self.y = top + 17
        for pi, para in enumerate(fa_paras):
            fa_lines = self.wrap(para.replace("\n", " "), fa.font, fa.size, CONTENT_W - 34)
            for i, line in enumerate(fa_lines):
                self.ensure(fa.leading)
                c.setFillColor(CARD)
                c.rect(M_LEFT, self.py(self.y + fa.leading), CONTENT_W, fa.leading, stroke=0,
                       fill=1)
                bar(self.y, self.y + fa.leading, BLUE)
                self.draw_line(line, self.y, fa, CONTENT_W - 34, A4W - M_RIGHT - 6,
                               justify=i < len(fa_lines) - 1)
                self.y += fa.leading
            if pi < len(fa_paras) - 1:
                self.y += 2
        if note:
            self.ensure(18)
            n = TextStyle(size=8.6, leading=13.6, color=HexColor("#4338ca"), justify=False)
            for line in self.wrap(note, n.font, n.size, CONTENT_W - 30):
                self.draw_line(line, self.y, n, CONTENT_W - 30, A4W - M_RIGHT - 6)
                self.y += n.leading
        self.y += 9

    def label_card(self, title: str, rows, accent=TEAL, tint=TEAL_LL, kicker: str = "",
                   tick: bool = False, footer: str = "") -> None:
        """A ruled card of labelled rows (topic identity card / hand-off sheet).

        Each row is drawn with its own background so a long card can flow across
        a page break without cutting a row in half or losing its rules.
        """
        self._touch()
        c = self.c
        head_h = 24
        body = TextStyle(size=9.5, leading=15.4, color=BODY, justify=False)
        lab = TextStyle(size=8.2, leading=12, color=accent, justify=False)
        # measure the card first: the identity card is one block and must never
        # be cut in half between two pages
        plan: list[tuple[dict, list, float]] = []
        for row in rows:
            items = row.get("items")
            text = row.get("text", "")
            box_w = 15 if (row.get("tick", tick) and items is not None) else 0
            indent = 14 if (items is not None and bool(row.get("bullet", not row.get("tick", tick)))) else 0
            entries: list[tuple[str, bool]] = []
            if items is not None:
                for it in items:
                    for j, ln in enumerate(self.wrap(it, body.font, body.size,
                                                     CONTENT_W - 46 - box_w - indent)):
                        entries.append((ln, j == 0))
            elif text:
                entries = [(ln, False) for ln in
                           self.wrap(text, body.font, body.size, CONTENT_W - 46)]
            plan.append((row, entries, 15 + len(entries) * body.leading + 5))
        total = head_h + sum(h for _, _, h in plan) + 8
        if footer:
            total += len(self.wrap(footer, "Vazir", 8.2, CONTENT_W - 10)) * 13 + 4
        self.ensure(min(total, self.usable_height() - 10))
        top = self.y
        c.setFillColor(accent)
        c.roundRect(M_LEFT, self.py(top + head_h), CONTENT_W, head_h, 5, stroke=0, fill=1)
        draw_shaped(c, A4W - M_RIGHT - 9, self.py(top + 15), shape(title), "VazirB", 10.2,
                    CARD, align="right")
        if kicker:
            draw_shaped(c, M_LEFT + 9, self.py(top + 15), shape(kicker), "Vazir", 7.6,
                        CARD)
        self.y = top + head_h
        for row, entries, row_h in plan:
            label = row.get("label", "")
            items = row.get("items")
            row_tick = bool(row.get("tick", tick))
            row_bullet = bool(row.get("bullet", not row_tick))
            box_w = 15 if (row_tick and items is not None) else 0
            indent = 14 if (items is not None and row_bullet) else 0
            top = self.y
            c.setFillColor(tint)
            c.rect(M_LEFT, self.py(top + row_h), CONTENT_W, row_h, stroke=0, fill=1)
            c.setFillColor(accent)
            c.rect(A4W - M_RIGHT - 2.6, self.py(top + row_h), 2.6, row_h, stroke=0, fill=1)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.5)
            c.line(M_LEFT, self.py(top + row_h), A4W - M_RIGHT, self.py(top + row_h))
            draw_shaped(c, A4W - M_RIGHT - 9, self.py(top + 11), shape(label), "VazirB", 8.2,
                        accent, align="right")
            yy = top + 15
            for line, starts in entries:
                if row_tick and items is not None and starts:
                    c.setStrokeColor(accent)
                    c.setLineWidth(0.9)
                    c.rect(M_LEFT + 8, self.py(yy + 12.5), 8.4, 8.4, stroke=1, fill=0)
                if items is not None and row_bullet and starts:
                    c.setFillColor(accent)
                    c.circle(A4W - M_RIGHT - 13, self.py(yy + 8.6), 1.6, stroke=0, fill=1)
                self.draw_line(line, yy, body, CONTENT_W - 46 - box_w - indent,
                               A4W - M_RIGHT - 9 - indent, justify=False)
                yy += body.leading
            self.y = top + row_h
        if footer:
            self.ensure(18)
            f = TextStyle(size=8.2, leading=13, color=MUTED, justify=False)
            for line in self.wrap(footer, f.font, f.size, CONTENT_W - 10):
                self.draw_line(line, self.y + 3, f, CONTENT_W - 10, A4W - M_RIGHT - 4)
                self.y += f.leading
        self.y += 8

    def handoff_sheet(self, title: str, sources: str, checklist, question: str,
                      kicker: str = "این برگه را نویسندهٔ مبحث پر می‌کند",
                      note: str = "", accent=AMBER, tint=AMBER_BG) -> None:
        """The team's hand-off form: sources read, pre-delivery checks, one open point.

        It is one sheet (never split): the header, the source line, the tick list,
        the open question and the signature line stay on the same page.
        """
        self._touch()
        head_h = 24
        body = TextStyle(size=9.4, leading=15.2, color=BODY, justify=False)
        lab = TextStyle(size=8.4, leading=12.6, color=accent, justify=False)
        rows: list[tuple[str, list[str], bool]] = []
        rows.append(("منابعی که برای این مبحث خوانده شد",
                     self.wrap(sources, body.font, body.size, CONTENT_W - 46), False))
        for item in checklist:
            rows.append(("", self.wrap(item, body.font, body.size, CONTENT_W - 63), True))
        lab_hidden = True
        q_lines = self.wrap(question, body.font, body.size, CONTENT_W - 46) if question else []
        note_lines = self.wrap(note, lab.font, lab.size, CONTENT_W - 46) if note else []
        total = head_h + 8
        for label, lines, _ in rows:
            total += (15 if label else 0) + len(lines) * body.leading + 7
        total += 20 + len(q_lines) * body.leading + len(note_lines) * lab.leading + 34
        self.ensure(min(total, self.usable_height() - 12))
        c = self.c
        top = self.y
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.setFillColor(CARD)
        c.roundRect(M_LEFT, self.py(top + total), CONTENT_W, total, 6, stroke=1, fill=1)
        c.setFillColor(accent)
        c.roundRect(M_LEFT, self.py(top + head_h), CONTENT_W, head_h, 6, stroke=0, fill=1)
        c.rect(M_LEFT, self.py(top + head_h), CONTENT_W, 3, stroke=0, fill=1)
        draw_shaped(c, A4W - M_RIGHT - 9, self.py(top + 15.5), shape(title), "VazirB", 10.2,
                    CARD, align="right")
        if kicker:
            draw_shaped(c, M_LEFT + 9, self.py(top + 15.5), shape(kicker), "Vazir", 7.6, CARD)
        y = top + head_h + 6
        for label, lines, is_tick in rows:
            if label:
                draw_shaped(c, A4W - M_RIGHT - 9, self.py(y + 10), shape(label), "VazirB",
                            8.4, accent, align="right")
                y += 14
            for line in lines:
                if is_tick:
                    c.setStrokeColor(accent)
                    c.setLineWidth(0.9)
                    c.rect(M_LEFT + 9, self.py(y + 11.5), 8, 8, stroke=1, fill=0)
                self.draw_line(line, y, body, CONTENT_W - 63 if is_tick else CONTENT_W - 46,
                               A4W - M_RIGHT - 9, justify=False)
                y += body.leading
            y += 6
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(M_LEFT + 9, self.py(y + 2), A4W - M_RIGHT - 9, self.py(y + 2))
        y += 6
        draw_shaped(c, A4W - M_RIGHT - 9, self.py(y + 10), shape("اختلاف یا ابهام علمی برای بازبین"),
                    "VazirB", 8.4, accent, align="right")
        y += 14
        for line in q_lines:
            self.draw_line(line, y, body, CONTENT_W - 46, A4W - M_RIGHT - 9, justify=False)
            y += body.leading
        if note:
            for line in self.wrap(note, lab.font, lab.size, CONTENT_W - 46):
                self.draw_line(line, y + 2, lab, CONTENT_W - 46, A4W - M_RIGHT - 9, justify=False)
                y += lab.leading
        y += 8
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(M_LEFT + 9, self.py(y), A4W - M_RIGHT - 9, self.py(y))
        sig = TextStyle(size=8.0, leading=12, color=MUTED, justify=False)
        y += 5
        self.draw_line("امضای نویسنده: …………………………    تاریخ: …………………………    شمارهٔ نسخه: ………………",
                       y, sig, CONTENT_W - 18, A4W - M_RIGHT - 9, justify=False)
        self.y = top + total + 8

    def note_box(self, height_mm: float, title: str = "یادداشت عضو تیم",
                 subtitle: str = "HumsYar · team workspace", tag: str = "") -> None:
        self._touch()
        h = height_mm * MM
        self.ensure(h + 16)
        c = self.c
        top = self.y
        c.setFillColor(HexColor("#fcfdff"))
        c.setStrokeColor(HexColor("#cbd5e1"))
        c.setLineWidth(0.7)
        c.setDash(2.4, 2.4)
        c.roundRect(M_LEFT, self.py(top + h), CONTENT_W, h, 5, stroke=1, fill=1)
        c.setDash()
        c.setFont("VazirM", 8.6)
        c.setFillColor(MUTED)
        draw_shaped(c, A4W - M_RIGHT - 8, self.py(top + 14), shape(title), "VazirM", 8.6,
                    MUTED, align="right")
        c.setFont("Vazir", 7.0)
        c.setFillColor(HexColor("#94a3b8"))
        draw_shaped(c, M_LEFT + 8, self.py(top + 14), subtitle, "Vazir", 7.0,
                    HexColor("#94a3b8"))
        if tag:
            c.setFont("VazirM", 7.4)
            c.setFillColor(TEAL)
            draw_shaped(c, A4W - M_RIGHT - 8, self.py(top + h - 9),
                        shape(f"{tag} · این کادر برای نوشتن شما"), "VazirM", 7.4, TEAL,
                        align="right")
        c.setStrokeColor(HexColor("#eef2f7"))
        c.setLineWidth(0.55)
        pitch = 14.0                      # 4.9 mm: comfortable for iPad stylus
        yy = top + 28
        while yy < top + h - 10:
            c.line(M_LEFT + 8, self.py(yy), A4W - M_RIGHT - 8, self.py(yy))
            yy += pitch
        self.y = top + h + 10

    # ------------------------------------------------------------- figures
    def figure(self, path, caption: str = "", src: str = "", max_h: float | None = None,
               width: float | None = None, frame: bool = True) -> None:
        self._touch()
        path = Path(path)
        if not path.exists():
            self.missing_assets.append(str(path))
            self.callout(f"تصویر یافت نشد: {path.name}", kind="warn")
            return
        img = ImageReader(str(path))
        iw, ih = img.getSize()
        width = width or CONTENT_W - 8
        limit = max_h or 150 * MM
        cap_lines = self.wrap(caption, "Vazir", 8.4, CONTENT_W - 22) if caption else []
        cap_h = len(cap_lines) * 12 + (10 if caption else 0)
        # Space left on this page (minus caption, padding and the frame).
        free = self.bottom_limit() - self.y - cap_h - 26
        min_h = 46 * MM                      # still readable on paper / iPad
        if free >= min_h:
            # do not push a figure to the next page (and leave a hole here) when
            # it can be scaled down to the space that is actually available
            limit = min(limit, free)
        scale = min(width / iw, limit / ih)
        w, h = iw * scale, ih * scale
        self.ensure(h + cap_h + 26)
        c = self.c
        top = self.y
        card_h = h + cap_h + 11
        if frame:
            c.setFillColor(CARD)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.7)
            c.roundRect(M_LEFT, self.py(top + card_h), CONTENT_W, card_h, 6, stroke=1, fill=1)
        c.drawImage(img, M_LEFT + (CONTENT_W - w) / 2, self.py(top + 6 + h), w, h,
                    preserveAspectRatio=True, mask="auto")
        yy = top + h + 12
        for line in cap_lines:
            c.setFont("Vazir", 8.4)
            c.setFillColor(BODY)
            draw_shaped(c, A4W / 2, self.py(yy + 3), shape(line), "Vazir", 8.4, BODY,
                        align="center")
            yy += 12
        if src:
            c.setFont("Vazir", 7.0)
            c.setFillColor(MUTED)
            draw_shaped(c, A4W / 2, self.py(yy + 3), shape(f"منبع: {src}"), "Vazir", 7.0,
                        MUTED, align="center")
            yy += 10
        self.y = top + card_h + 10

    def facsimile(self, path, caption: str = "", src: str = "", max_h: float | None = None) -> None:
        self.figure(path, caption, src, max_h=max_h or 120 * MM)

    # ------------------------------------------------------------- table
    # ------------------------------------------------- anatomy blocks (additive)
    def anat_plate(self, image, title: str, citation: str, en_caption: str,
                   fa_text: str, labels=None, view: str = "", src: str = "",
                   max_h: float | None = None, en_body: str = "") -> None:
        """A reference plate: the book's figure + its own caption + our Persian text.

        This is the anatomy counterpart of ``guyton_pair``: the picture is the
        quoted material, the Persian paragraph is our editorial explanation, and
        both stay visually separate so a reader can tell which is which.
        """
        self._touch()
        path = Path(image)
        if not path.exists():
            self.missing_assets.append(str(path))
            self.callout(f"تصویر یافت نشد: {path.name}", kind="warn")
            return
        img = ImageReader(str(path))
        iw, ih = img.getSize()
        box_w = CONTENT_W
        pad = 8
        # two header lines: the Persian title on top, the citation underneath, so
        # a long citation can never run into the title
        head_h = 32
        # ---- measure
        fa_style = TextStyle(size=9.9, leading=16.4, color=BODY, justify=True)
        fa_lines = self.wrap(fa_text, fa_style.font, fa_style.size, box_w - 2 * pad - 6) if fa_text else []
        en_style = TextStyle(size=8.3, leading=13.0, color=MUTED, justify=False)
        en_lines = self.wrap(en_caption, en_style.font, en_style.size, box_w - 2 * pad - 6) if en_caption else []
        lab_style = TextStyle(size=8.2, leading=13.0, color=BODY, justify=False)
        lab_lines = [self.wrap(f"{fa} · {en}" if fa else en, lab_style.font, lab_style.size,
                               box_w - 2 * pad - 22) for fa, en in (labels or [])]
        cap_h = (len(en_lines) * en_style.leading + 8) if en_lines else 0
        # a quoted passage of the book's own running text (only when it exists)
        bd_style = TextStyle(size=8.6, leading=13.6, color=INK, justify=False)
        bd_lines = self.wrap(en_body, bd_style.font, bd_style.size, box_w - 2 * pad - 14) \
            if en_body else []
        cap_h += (len(bd_lines) * bd_style.leading + 16) if bd_lines else 0
        lab_h = (sum(len(x) for x in lab_lines) * lab_style.leading + 14) if lab_lines else 0
        text_h = len(fa_lines) * fa_style.leading + (10 if fa_lines else 0)
        # ---- image: keep the aspect ratio, never upscale beyond the source
        lim_h = max_h or 132 * MM
        free = self.bottom_limit() - self.y - (head_h + cap_h + text_h + lab_h + 40)
        # a plate that would leave a big hole on this page is scaled down to the
        # room that is actually left, down to 42 mm; below that it moves over.
        if free > 42 * MM:
            lim_h = min(lim_h, free)
        scale = min((box_w - 2 * pad) / iw, lim_h / ih)
        w, h = iw * scale, ih * scale
        total = head_h + 10 + h + cap_h + text_h + lab_h + 14
        # a card is one block: if it is taller than a whole page the picture
        # shrinks until the card fits, instead of running off the page edge
        page_room = self.usable_height() - 12
        if total > page_room:
            h = max(38 * MM, h - (total - page_room))
            w = h * iw / ih          # keep the aspect ratio: never squash the plate
            total = head_h + 10 + h + cap_h + text_h + lab_h + 14
        self.ensure(total)
        c = self.c
        top = self.y
        c.setFillColor(CARD)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.8)
        c.roundRect(M_LEFT, self.py(top + total - 8), CONTENT_W, total - 8, 7, stroke=1, fill=1)
        c.setFillColor(TEAL_LL)
        c.roundRect(M_LEFT, self.py(top + head_h), CONTENT_W, head_h, 7, stroke=0, fill=1)
        c.rect(M_LEFT, self.py(top + head_h), CONTENT_W, 3, stroke=0, fill=1)
        draw_shaped(c, A4W - M_RIGHT - 8, self.py(top + 14), shape(title), "VazirB", 10.0,
                    TEAL_D, align="right")
        cite = citation + (f" · {view}" if view else "")
        draw_shaped(c, M_LEFT + 8, self.py(top + 25), shape(cite), "Vazir", 7.2, TEAL_D)
        y = top + head_h + 8
        c.drawImage(img, M_LEFT + (CONTENT_W - w) / 2, self.py(y + h), w, h,
                    preserveAspectRatio=True, mask="auto")
        y += h + 4
        if en_lines:
            c.setFillColor(MUTED)
            for ln in en_lines:
                draw_shaped(c, A4W - M_RIGHT - 6, self.py(y + 8), shape(ln), en_style.font,
                            en_style.size, MUTED, align="right")
                y += en_style.leading
            y += 6
        if bd_lines:
            c.setStrokeColor(LINE)
            c.setLineWidth(1.6)
            c.line(M_LEFT + 10, self.py(y + 2), M_LEFT + 10, self.py(y + len(bd_lines) * bd_style.leading + 2))
            for ln in bd_lines:
                self.draw_line(ln, y, bd_style, box_w - 2 * pad - 14, A4W - M_RIGHT - 20,
                               justify=False)
                y += bd_style.leading
            y += 10
        if fa_lines:
            c.setStrokeColor(TEAL_L)
            c.setLineWidth(0.7)
            c.line(M_LEFT + 8, self.py(y + 2), A4W - M_RIGHT - 8, self.py(y + 2))
            y += 8
            for ln in fa_lines:
                self.draw_line(ln, y, fa_style, box_w - 2 * pad - 2, A4W - M_RIGHT - 10)
                y += fa_style.leading
            y += 4
        if lab_lines:
            c.setFillColor(SOFT)
            lab_top = y
            lab_total = sum(len(x) for x in lab_lines) * lab_style.leading + 10
            c.rect(M_LEFT + 6, self.py(lab_top + lab_total), CONTENT_W - 12, lab_total,
                   stroke=0, fill=1)
            y += 3
            for wrapped in lab_lines:
                for j, ln in enumerate(wrapped):
                    if j == 0:
                        c.setFillColor(TEAL)
                        c.circle(A4W - M_RIGHT - 12, self.py(y + 8), 1.5, stroke=0, fill=1)
                    self.draw_line(ln, y, lab_style, box_w - 2 * pad - 22, A4W - M_RIGHT - 18,
                                   justify=False)
                    y += lab_style.leading
            y += 4
        if src:
            c.setFillColor(MUTED)
            draw_shaped(c, A4W - M_RIGHT - 8, self.py(y + 6), shape(f"ارجاع متن: {src}"),
                        "Vazir", 7.0, MUTED, align="right")
            y += 10
        self.y = top + total + 8

    def path_steps(self, steps, title: str = "مسیر گام‌به‌گام", merged=None) -> None:
        """Numbered chain of stations: مبدأ → مسیر → تقاطع → مقصد."""
        self._touch()
        if merged is not None:
            pass
        c = self.c
        head = 20
        self.ensure(head + 26)
        top = self.y
        c.setFillColor(BLUE_BG)
        c.roundRect(M_LEFT, self.py(top + head), CONTENT_W, head, 6, stroke=0, fill=1)
        draw_shaped(c, A4W - M_RIGHT - 8, self.py(top + 13), shape(title), "VazirB", 9.4,
                    BLUE_D, align="right")
        self.y = top + head + 4
        style = TextStyle(size=9.7, leading=15.4, color=BODY, justify=False)
        for i, st in enumerate(steps, start=1):
            lines = self.wrap(st, style.font, style.size, CONTENT_W - 42)
            h = len(lines) * style.leading + 8
            self.ensure(h)
            top = self.y
            c.setFillColor(HexColor("#f7f9ff"))
            c.rect(M_LEFT, self.py(top + h), CONTENT_W, h, stroke=0, fill=1)
            c.setFillColor(BLUE)
            c.circle(A4W - M_RIGHT - 13, self.py(top + 11), 7.2, stroke=0, fill=1)
            draw_shaped(c, A4W - M_RIGHT - 13, self.py(top + 14), fa_digits(str(i)),
                        "VazirB", 8.4, CARD, align="center")
            yy = top + 4
            for ln in lines:
                self.draw_line(ln, yy, style, CONTENT_W - 42, A4W - M_RIGHT - 26,
                               justify=False)
                yy += style.leading
            self.y = top + h
        self.spacer(6)

    def table_needs(self, head, rows, widths=None, caption: str = "", src: str = "",
                    size: float = 8.5):
        """Measured geometry of a table: header height, each row, caption reserve."""
        ncols = len(head)
        widths = widths or [CONTENT_W / ncols] * ncols
        cap_lines_n = len(self.wrap(caption, "Vazir", 8.2, CONTENT_W)) if caption else 0
        # paragraph() needs up to three leadings before it accepts a new block,
        # so the reserve must be at least that large or the caption is orphaned
        cap_reserve = max(cap_lines_n, 3) * 14 + (14 if src else 0)

        def cell_lines(text, i):
            return self.wrap(str(text), "Vazir", size, widths[i] - 9)

        head_lines = [cell_lines(h, i) for i, h in enumerate(head)]
        head_h = max(len(x) for x in head_lines) * (size + 3.6) + 9
        row_hs = [max(len(l) for l in [cell_lines(cell, i)
                                       for i, cell in enumerate(row)]) * (size + 3.2) + 8
                  for row in rows]
        return head_h, row_hs, cap_reserve, head_h + sum(row_hs) + 5 + cap_reserve

    def table(self, head, rows, widths=None, caption: str = "", src: str = "",
              size: float = 8.5, header_bg: str = "#e8f1ff") -> None:
        self._touch()
        ncols = len(head)
        widths = widths or [CONTENT_W / ncols] * ncols
        c = self.c

        def cell_lines(text, i):
            return self.wrap(str(text), "Vazir", size, widths[i] - 9)

        head_lines = [cell_lines(h, i) for i, h in enumerate(head)]
        head_h, row_hs, cap_reserve, whole = self.table_needs(
            head, rows, widths, caption, src, size)
        # a table that fits on one page is never split: measure it first, then
        # ask for the whole height.  A table taller than a page still never
        # leaves its header alone at the foot: the first row must fit with it.
        if whole <= self.usable_height() - 8:
            self.ensure(whole)
        else:
            self.ensure(head_h + (row_hs[0] if row_hs else 0) + 24 + cap_reserve)

        def draw_head(top_y: float) -> None:
            """Header row; drawn again on every continuation page."""
            c.setFillColor(HexColor(header_bg))
            c.rect(M_LEFT, self.py(top_y + head_h), sum(widths), head_h, stroke=0, fill=1)
            xx = A4W - M_RIGHT
            for i, lines in enumerate(head_lines):
                ty = top_y + 5
                for line in lines:
                    c.setFont("VazirB", size)
                    c.setFillColor(INK)
                    draw_shaped(c, xx - 5, self.py(ty + size + 1), shape(line), "VazirB", size,
                                INK, align="right")
                    ty += size + 3.4
                xx -= widths[i]

        draw_head(self.y)
        self.y += head_h
        alt = False
        last_idx = len(rows) - 1
        for r_idx, row in enumerate(rows):
            lpc = [cell_lines(cell, i) for i, cell in enumerate(row)]
            row_h = row_hs[r_idx]
            # the caption stays with the final row (no orphan page)
            reserve = cap_reserve if r_idx == last_idx else 0
            if self.y + row_h + reserve > self.bottom_limit():
                self.new_page()
                c = self.c
                c.setFont("VazirB", 8)
                c.setFillColor(MUTED)
                draw_shaped(c, A4W - M_RIGHT, self.py(self.y + 8),
                            shape("… ادامهٔ جدول"), "VazirB", 8, MUTED, align="right")
                self.y += 14
                draw_head(self.y)          # the reader never loses the column names
                self.y += head_h
            c.setFillColor(HexColor("#f7fafd") if alt else CARD)
            c.rect(M_LEFT, self.py(self.y + row_h), sum(widths), row_h, stroke=0, fill=1)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.5)
            c.line(M_LEFT, self.py(self.y + row_h), A4W - M_RIGHT, self.py(self.y + row_h))
            x = A4W - M_RIGHT
            for i, lines in enumerate(lpc):
                ty = self.y + 4
                for line in lines:
                    c.setFont("Vazir", size)
                    c.setFillColor(BODY)
                    draw_shaped(c, x - 5, self.py(ty + size + 1), shape(line), "Vazir", size,
                                BODY, align="right")
                    ty += size + 3.2
                x -= widths[i]
            self.y += row_h
            alt = not alt
        c.setStrokeColor(HexColor("#cbd5e1"))
        c.setLineWidth(0.7)
        c.line(M_LEFT, self.py(self.y), A4W - M_RIGHT, self.py(self.y))
        self.y += 5
        if caption:
            self.paragraph(caption, TextStyle(size=8.2, color=MUTED, justify=False))
        if src:
            self.source_line(src)

    # ------------------------------------------------------------- TOC
    def toc_row(self, num: str, title: str, page_no: str, indent: float = 0,
                accent=TEAL, dots: bool = True, step: float = 19) -> None:
        self._touch()
        self.ensure(20)
        c = self.c
        top = self.y
        c.setFillColor(accent)
        c.roundRect(A4W - M_RIGHT - 18 - indent, self.py(top + 14), 18, 14, 4, stroke=0, fill=1)
        c.setFont("VazirB", 8.0)
        c.setFillColor(CARD)
        draw_shaped(c, A4W - M_RIGHT - 9 - indent, self.py(top + 10), num, "VazirB", 8.0,
                    CARD, align="center")
        c.setFont("Vazir", 10.1)
        c.setFillColor(INK)
        tw = text_width(shape(title), "Vazir", 10.1)
        max_w = CONTENT_W - 78 - indent
        label = title
        while text_width(shape(label), "Vazir", 10.1) > max_w and len(label) > 6:
            label = label[:-2]
        if label != title:
            label = label.rstrip() + "…"
            tw = text_width(shape(label), "Vazir", 10.1)
        draw_shaped(c, A4W - M_RIGHT - 26 - indent, self.py(top + 10), shape(label),
                    "Vazir", 10.1, INK, align="right")
        c.setFont("Vazir", 9)
        c.setFillColor(MUTED)
        draw_shaped(c, M_LEFT + 2, self.py(top + 10), fa_digits(str(page_no)), "Vazir", 9,
                    MUTED)
        if dots:
            c.setStrokeColor(HexColor("#eef2f7"))
            c.setLineWidth(0.6)
            c.setDash(1, 3)
            x_start = M_LEFT + 24
            x_end = A4W - M_RIGHT - 26 - indent - tw - 6
            if x_end > x_start:
                c.line(x_start, self.py(top + 7), x_end, self.py(top + 7))
            c.setDash()
        self.y = top + step


def _mix(a: Color, b: Color, t: float) -> Color:
    return Color(a.red + (b.red - a.red) * t,
                 a.green + (b.green - a.green) * t,
                 a.blue + (b.blue - a.blue) * t)

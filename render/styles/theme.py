# -*- coding: utf-8 -*-
"""پالت رنگ، فونت‌ها و استایل‌های متنی HumsYar (جدا از منطق رندر)."""
import os

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONTS = os.path.join(ROOT, "render", "assets", "fonts")

# ── پالت HumsYar ───────────────────────────────────────────────
NAVY = colors.HexColor("#0a0f1e")
BLUE = colors.HexColor("#2563eb")
BLUE_L = colors.HexColor("#3b82f6")
TEAL = colors.HexColor("#14b8a6")
TEAL_L = colors.HexColor("#2dd4bf")
BG = colors.HexColor("#f0f6ff")
LINE = colors.HexColor("#e2e8f0")
TEXT = colors.HexColor("#1e293b")
MUTED = colors.HexColor("#64748b")
WARN = colors.HexColor("#b45309")
WARN_BG = colors.HexColor("#fffbeb")
CONF = colors.HexColor("#b91c1c")
CONF_BG = colors.HexColor("#fef2f2")


def fa(t):
    """آماده‌سازی متن فارسی برای ReportLab (شکل‌دهی حروف + ترتیب راست‌به‌چپ)."""
    if t is None:
        return ""
    t = str(t)
    try:
        return get_display(arabic_reshaper.reshape(t))
    except Exception:  # noqa: BLE001
        return t


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ── استایل‌ها ──────────────────────────────────────────────────
S = {}
S["body"] = ParagraphStyle("body", fontName="Vazir", fontSize=9.6, leading=16.5,
                           alignment=TA_JUSTIFY, textColor=TEXT, spaceAfter=1.6)
S["h1"] = ParagraphStyle("h1", fontName="VazirB", fontSize=17, leading=24, textColor=colors.white)
S["h2"] = ParagraphStyle("h2", fontName="VazirB", fontSize=13, leading=21, textColor=NAVY,
                         alignment=TA_RIGHT, spaceBefore=8, spaceAfter=4)
S["h3"] = ParagraphStyle("h3", fontName="VazirB", fontSize=10.5, leading=17, textColor=BLUE,
                         alignment=TA_RIGHT, spaceBefore=5, spaceAfter=2)
S["small"] = ParagraphStyle("small", fontName="Vazir", fontSize=8, leading=12.5, textColor=MUTED,
                            alignment=TA_RIGHT)
S["chip"] = ParagraphStyle("chip", fontName="VazirL", fontSize=7.4, leading=11, textColor=MUTED,
                           alignment=TA_RIGHT, spaceAfter=4)
S["cap"] = ParagraphStyle("cap", fontName="Vazir", fontSize=8, leading=12, textColor=MUTED,
                          alignment=TA_CENTER, spaceBefore=2)
S["cardT"] = ParagraphStyle("cardT", fontName="VazirB", fontSize=9.6, leading=15, textColor=NAVY,
                            alignment=TA_RIGHT)
S["card"] = ParagraphStyle("card", fontName="Vazir", fontSize=9, leading=15, textColor=TEXT,
                           alignment=TA_JUSTIFY)
S["toc1"] = ParagraphStyle("toc1", fontName="VazirB", fontSize=10.5, leading=17, textColor=NAVY,
                           alignment=TA_RIGHT)
S["toc2"] = ParagraphStyle("toc2", fontName="Vazir", fontSize=9, leading=15, textColor=TEXT,
                           alignment=TA_RIGHT)



def register_fonts():
    for name, fn in [("Vazir", "Vazirmatn-Regular.ttf"), ("VazirB", "Vazirmatn-Bold.ttf"),
                     ("VazirM", "Vazirmatn-Medium.ttf"), ("VazirL", "Vazirmatn-Light.ttf")]:
        pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, fn)))
    pdfmetrics.registerFontFamily("Vazir", normal="Vazir", bold="VazirB")

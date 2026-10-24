#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HumsYar — رندر PDF جزوه مادر فیزیولوژی اعصاب و حواس ویژه

روش: ReportLab + Vazirmatn (تعبیه‌شده) + بازچینش RTL با arabic_reshaper/python-bidi
ورودی: lock/chapters/*.json ، lock/manifest.json ، images/INDEX.json
خروجی: output/HumsYar_Neuro_SpecialSenses_Master.pdf
"""
import datetime
import json
import os
import re

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, Image,
                                KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "render", "assets", "fonts")
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

# ── تم و استایل‌ها (در فایل مستقل) ─────────────────────────────
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from styles.theme import (BG, BLUE, BLUE_L, CONF, CONF_BG, FONTS, LINE, MUTED, NAVY,  # noqa: E402
                          S, TEAL, TEAL_L, TEXT, WARN, WARN_BG, esc, fa,
                          register_fonts)

register_fonts()

# ── عناصر سفارشی ───────────────────────────────────────────────
class Postponable(Flowable):
    """Flowableهایی که ممکن است چند بار به صفحه بعد منتقل شوند.

    ReportLab پرچم _postponed را پس از انتقال پاک نمی‌کند؛ این کلاس آن را
    در هر ترسیم پاک می‌کند تا انتقال چندباره خطا ندهد.
    """

    def _clear_postponed(self):
        if hasattr(self, "_postponed"):
            del self._postponed

class HRule(Postponable):
    def __init__(self, width, color=LINE, thickness=0.7, space=3):
        Flowable.__init__(self)
        self.width, self.color, self.t, self.space = width, color, thickness, space

    def wrap(self, aw, ah):
        self._aw = aw
        return aw, self.t + 2 * self.space

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.t)
        self.canv.line(0, self.space, self._aw, self.space)


class SectionMarker(Flowable):
    """نشانگر مبحث: بوکمارک، ثبت شماره صفحه، لنگر برای لینک پیش‌نیازها."""

    def __init__(self, key, title, level=1):
        Flowable.__init__(self)
        self.key, self.title, self.level = key, title, level
        self.page_number = None

    def wrap(self, aw, ah):
        return aw, 0

    def draw(self):
        c = self.canv
        c.bookmarkPage(self.key)
        c.addOutlineEntry(self.title, self.key, level=self.level, closed=(self.level > 0))
        self.page_number = c.getPageNumber()
        PAGES[self.key] = self.page_number


PAGES = {}

IMG_CACHE = {}


def img_flowable(path, max_w, max_h):
    from PIL import Image as PILImage
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return None
    if full not in IMG_CACHE:
        im = PILImage.open(full)
        IMG_CACHE[full] = im.size
    w, h = IMG_CACHE[full]
    sc = min(max_w / w, max_h / h)
    return Image(full, width=w * sc, height=h * sc)


class Card(Postponable):
    """کارت اطلاعاتی با کادر رنگی و عنوان."""

    def __init__(self, title, body_flowables, accent=BLUE, bg=BG, width=None, icon=""):
        Flowable.__init__(self)
        self.title, self.body, self.accent, self.bg = title, body_flowables, accent, bg
        self.icon = icon
        self.pad = 5 * mm

    def wrap(self, aw, ah):
        self._aw = aw
        inner = aw - 2 * self.pad
        self._sizes = []
        h = 0
        for f in self.body:
            w, hh = f.wrap(inner, ah)
            self._sizes.append((w, hh))
            h += hh
        self._title_h = 5.2 * mm if self.title else 0
        self._h = h + self._title_h + 2 * self.pad
        return aw, self._h

    def draw(self):
        self._clear_postponed()
        c = self.canv
        c.saveState()
        c.setFillColor(self.bg)
        c.setStrokeColor(self.accent)
        c.setLineWidth(0.8)
        c.roundRect(0, 0, self._aw, self._h, 2.4 * mm, stroke=1, fill=1)
        c.setFillColor(self.accent)
        c.rect(self._aw - 1.6 * mm, 0, 1.6 * mm, self._h, stroke=0, fill=1)
        y = self._h - self.pad
        if self.title:
            c.setFont("VazirB", 9.4)
            c.setFillColor(self.accent)
            c.drawRightString(self._aw - self.pad, y - 3.2 * mm, fa(self.title))
            y -= self._title_h
        for f, (w, hh) in zip(self.body, self._sizes):
            f.canv = c
            c.saveState()
            c.translate(self._aw - self.pad - w, y - hh)
            f.draw()
            c.restoreState()
            y -= hh
        c.restoreState()


class NoteBox(Postponable):
    """باکس یادداشت عضو تیم — فضای نوشتن با خطوط کم‌رنگ."""

    SIZES = {"small": 38, "medium": 62, "large": 95}  # mm

    def __init__(self, size, width=None):
        Flowable.__init__(self)
        self.h = self.SIZES.get(size, 62) * mm
        self.size_name = size

    def wrap(self, aw, ah):
        self._aw = aw
        return aw, self.h

    def draw(self):
        self._clear_postponed()
        c = self.canv
        c.saveState()
        c.setFillColor(colors.HexColor("#fbfdff"))
        c.setStrokeColor(colors.HexColor("#cbd5e1"))
        c.setLineWidth(0.7)
        c.setDash(2.5, 2)
        c.roundRect(0, 0, self._aw, self.h, 2 * mm, stroke=1, fill=1)
        c.setDash()
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("VazirB", 9)
        c.drawRightString(self._aw - 4 * mm, self.h - 5.5 * mm,
                          fa("یادداشت و تکمیل عضو تیم جزوه‌نویسی"))
        c.setFont("Vazir", 7.6)
        c.setFillColor(MUTED)
        c.drawRightString(self._aw - 4 * mm, self.h - 10 * mm,
                          fa("نام / تاریخ / مبحث: .............................................."))
        # خطوط کم‌رنگ برای نوشتن
        y = self.h - 16 * mm
        c.setStrokeColor(colors.HexColor("#e8eef6"))
        c.setLineWidth(0.45)
        while y > 4 * mm:
            c.line(4 * mm, y, self._aw - 4 * mm, y)
            y -= 7.2 * mm
        c.restoreState()


class Divider(Postponable):
    def __init__(self, height=2 * mm):
        Flowable.__init__(self)
        self.height = height

    def wrap(self, aw, ah):
        return aw, self.height

    def draw(self):
        pass


# ── قالب صفحه ───────────────────────────────────────────────────
class Doc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(self, filename, pagesize=A4,
                                 leftMargin=17 * mm, rightMargin=17 * mm,
                                 topMargin=20 * mm, bottomMargin=17 * mm, **kw)
        W, H = A4
        frame = Frame(17 * mm, 17 * mm, W - 34 * mm, H - 37 * mm, id="body",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[Frame(0, 0, W, H, id="c",
                                                   leftPadding=0, rightPadding=0,
                                                   topPadding=0, bottomPadding=0)],
                         onPage=self.cover_bg),
            PageTemplate(id="body", frames=[frame], onPage=self.deco),
        ])
        self.chapter_title = ""

    def handle_flowable(self, flowables):
        """پاک‌سازی پرچم انتقال صفحه در ابتدای هر فریم تازه (رفع رفتار ReportLab)."""
        if flowables:
            f = flowables[0]
            try:
                at_top = self.frame._atTop
            except Exception:  # noqa: BLE001
                at_top = False
            if at_top and hasattr(f, "_postponed"):
                del f._postponed
        return BaseDocTemplate.handle_flowable(self, flowables)

    # جلد
    def cover_bg(self, canv, doc):
        pass

    def deco(self, canv, doc):
        W, H = A4
        canv.saveState()
        # نوار بالای صفحه
        canv.setFillColor(NAVY)
        canv.rect(0, H - 11 * mm, W, 11 * mm, stroke=0, fill=1)
        canv.setFillColor(TEAL)
        canv.rect(0, H - 11.9 * mm, W, 0.9 * mm, stroke=0, fill=1)
        canv.setFillColor(colors.white)
        canv.setFont("VazirM", 8.2)
        canv.drawRightString(W - 17 * mm, H - 7.6 * mm,
                             fa(doc.chapter_title or "جزوه مادر جامع فیزیولوژی اعصاب و حواس ویژه"))
        canv.setFont("Vazir", 7.6)
        canv.drawString(17 * mm, H - 7.6 * mm, "HumsYar · Neurophysiology Master Book")
        # پاورقی
        canv.setStrokeColor(LINE)
        canv.setLineWidth(0.5)
        canv.line(17 * mm, 12.5 * mm, W - 17 * mm, 12.5 * mm)
        canv.setFillColor(MUTED)
        canv.setFont("Vazir", 8)
        canv.drawCentredString(W / 2, 8.6 * mm, fa(f"صفحه {doc.page}"))
        canv.setFont("Vazir", 7)
        canv.drawString(17 * mm, 8.6 * mm, "HumsYar — نسخه ۲٫۱")
        canv.restoreState()


# ── بارگذاری داده ───────────────────────────────────────────────
def load():
    man = json.load(open(os.path.join(ROOT, "lock", "manifest.json")))
    chs = []
    for m in man:
        chs.append(json.load(open(os.path.join(ROOT, "lock", "chapters", m["chapter_id"] + ".json"))))
    reg = {r["source_id"]: r for r in json.load(open(os.path.join(ROOT, "work", "source_registry.json")))}
    figs = json.load(open(os.path.join(ROOT, "images", "INDEX.json")))
    return chs, reg, figs


def src_label(reg, sid, page=None):
    r = reg.get(sid)
    name = os.path.splitext(r["filename"])[0] if r else sid
    folder = os.path.dirname(r["rel_path"]).split("/")[-1] if r else ""
    p = f" — ص {page}" if page else ""
    return f"{sid} · {name} ({folder}){p}"


def build():
    """ساخت PDF و بازگرداندن نقشه شماره صفحه‌ها."""
    chapters, reg, figs = load()
    fig_by_id = {f["figure_id"]: f for f in figs}
    used_figs = []
    fig_no = {"n": 0}
    W, H = A4
    content_w = W - 34 * mm

    story = []

    # ── جلد ──
    story.append(NextPageTemplate("body"))
    story.append(CoverPage(chapters, reg, figs, content_w))
    story.append(PageBreak())

    # ── فهرست ──
    story.append(SectionMarker("toc", "فهرست مطالب", level=0))
    story.extend(PageTitle("فهرست مطالب", "راهنمای فصل‌ها و زیرمبحث‌ها"))
    toc_placeholder_idx = len(story)
    story.append(Divider(4 * mm))
    TOC_PLACEHOLDER = {"idx": toc_placeholder_idx}
    story.append(PageBreak())

    # ── راهنمای استفاده ──
    story.extend(guide_pages(reg, content_w))
    story.append(PageBreak())

    # ── فصل‌ها ──
    for ci, ch in enumerate(chapters, start=1):
        story.extend(chapter_opener(ci, ch, content_w, fig_by_id))
        story.append(PageBreak())
        doc_chapter = ch["chapter_title"]
        for si, sec in enumerate(ch["sections"], start=1):
            story.extend(render_section(ch, sec, reg, fig_by_id, content_w, used_figs, fig_no))
        # پیوست تصویری
        if ch.get("appendix"):
            story.append(PageBreak())
        for ap in ch.get("appendix", []):
            story.extend(render_appendix(ch, ap, reg, content_w))
        story.append(PageBreak())

    # ── پیوست پایانی: منابع، نمایه شکل‌ها، راهنمای علائم ──
    story.extend(back_matter(chapters, reg, figs, used_figs, content_w))

    # ── ساخت PDF (سه پاس برای شماره صفحات فهرست) ──
    final = os.path.join(OUT, "HumsYar_Neuro_SpecialSenses_Master.pdf")

    def make(toc_entries, out_path):
        PAGES.clear()
        st = list(story)
        st[TOC_PLACEHOLDER["idx"]:TOC_PLACEHOLDER["idx"] + 1] = (
            [Spacer(1, 1)] if toc_entries is None else toc_block(toc_entries, content_w))
        d = Doc(out_path)
        d.build(st)
        return dict(PAGES)

    pages1 = make(None, "/tmp/pass1.pdf")
    entries = [(k, v) for k, v in pages1.items() if k.startswith("CH")]
    pages2 = make(entries, "/tmp/pass2.pdf")
    entries2 = [(k, v) for k, v in pages2.items() if k.startswith("CH")]
    pages3 = make(entries2, final)
    entries3 = [(k, v) for k, v in pages3.items() if k.startswith("CH")]
    if entries3 != entries2:
        make(entries3, final)
    json.dump(figs, open(os.path.join(ROOT, "images", "INDEX.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(entries3, open(os.path.join(ROOT, "lock", "section_pages.json"), "w"),
              ensure_ascii=False, indent=1)
    return final, chapters, reg, used_figs, fig_no


def PageTitle(title, subtitle=""):
    t = Table([[Paragraph(fa(esc(title)), ParagraphStyle("pt", fontName="VazirB", fontSize=19,
                                                        leading=26, textColor=NAVY,
                                                        alignment=TA_RIGHT))]],
              colWidths=[A4[0] - 34 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BG),
                           ("LINEBELOW", (0, 0), (-1, 0), 1.6, TEAL),
                           ("TOPPADDING", (0, 0), (-1, -1), 7),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))
    out = [t]
    if subtitle:
        out.append(Spacer(1, 2 * mm))
        out.append(Paragraph(fa(esc(subtitle)), S["small"]))
    return out


class CoverPage(Postponable):
    def __init__(self, chapters, reg, figs, width):
        Flowable.__init__(self)
        self.ch = chapters
        self.reg = reg
        self.figs = figs
        self.width = width

    def wrap(self, aw, ah):
        self._aw, self._ah = A4
        return self._aw, self._ah

    def draw(self):
        self._clear_postponed()
        c = self.canv
        W, H = A4
        c.saveState()
        c.setFillColor(NAVY)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#0e1730"))
        c.rect(0, 0, W, H * 0.46, stroke=0, fill=1)
        c.setFillColor(TEAL)
        c.rect(0, H * 0.46, W, 1.4 * mm, stroke=0, fill=1)
        # لوگو
        logo = os.path.join(ROOT, "لوگو برند.jpg")
        if os.path.exists(logo):
            im = img_flowable("لوگو برند.jpg", 34 * mm, 34 * mm)
            if im:
                im.drawOn(c, W - 17 * mm - im._width, H - 30 * mm - im._height)
        c.setFillColor(colors.white)
        c.setFont("Vazir", 10)
        c.drawString(17 * mm, H - 22 * mm, "HumsYar")
        c.setFont("Vazir", 8)
        c.setFillColor(TEAL_L)
        c.drawString(17 * mm, H - 28 * mm, "Neuro & Special Senses · Master Source Book")
        # عنوان
        n_sec = sum(len(ch["sections"]) for ch in self.ch)
        n_fig = sum(1 for f in self.figs if f.get("used_in_pdf"))
        n_src = len(self.reg)
        y = H - 62 * mm
        c.setFillColor(colors.white)
        c.setFont("VazirB", 27)
        c.drawRightString(W - 17 * mm, y, fa("جزوه مادر جامع"))
        y -= 15 * mm
        c.setFont("VazirB", 24)
        c.drawRightString(W - 17 * mm, y, fa("فیزیولوژی اعصاب و حواس ویژه"))
        y -= 11 * mm
        c.setFont("Vazir", 11)
        c.setFillColor(TEAL_L)
        c.drawRightString(W - 17 * mm, y, fa("تجمیع و تطبیق جزوه‌ها، اسلایدها، ویدئوها و منابع مرجع"))
        y -= 7 * mm
        c.setFont("Vazir", 9)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawRightString(W - 17 * mm, y,
                          fa("دوره علوم پایه پزشکی — تیم جزوه‌نویسی (استادان فیروزجایی و خوارزمی؛ "
                             "منابع تکمیلی: دکتر قدیری)"))
        # آمار واقعی
        stats = [(fa("فصل"), len(self.ch)), (fa("زیرمبحث"), n_sec),
                 (fa("شکل"), n_fig if n_fig else len(self.figs)), (fa("منبع"), n_src)]
        bw = (W - 34 * mm - 3 * 5 * mm) / 4
        x = W - 17 * mm - bw
        y0 = H * 0.46 - 42 * mm
        for label, val in stats:
            c.setFillColor(colors.HexColor("#13203c"))
            c.roundRect(x, y0, bw, 26 * mm, 2.5 * mm, stroke=0, fill=1)
            c.setFillColor(TEAL_L)
            c.setFont("VazirB", 20)
            c.drawCentredString(x + bw / 2, y0 + 12.5 * mm, fa(f"{val:,}"))
            c.setFillColor(colors.HexColor("#94a3b8"))
            c.setFont("Vazir", 8.5)
            c.drawCentredString(x + bw / 2, y0 + 5 * mm, label)
            x -= bw + 5 * mm
        # پاورقی جلد
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.setFont("Vazir", 8.5)
        c.drawCentredString(W / 2, 26 * mm,
                            fa("نسخه سند ۲٫۱ — تولید " + datetime.date.today().isoformat() +
                               " — تهیه‌شده برای تیم جزوه‌نویسی"))
        c.setFont("Vazir", 7.5)
        c.drawCentredString(W / 2, 20 * mm,
                            fa("این نسخه، سند مبنای تیم است؛ نه جزوه نهایی دانشجویی."))
        c.restoreState()


class ChapterBand(Postponable):
    """نوار عنوان فصل (بدون محتوای متنی؛ متن‌ها به‌صورت Flowable می‌آیند)."""

    H = 46 * mm

    def __init__(self, number, title, width):
        Flowable.__init__(self)
        self.n, self.title, self.width = number, title, width

    def wrap(self, aw, ah):
        self._aw = aw
        return aw, self.H

    def draw(self):
        self._clear_postponed()
        c = self.canv
        w, h = self._aw, self.H
        c.saveState()
        c.setFillColor(NAVY)
        c.roundRect(0, 0, w, h, 3 * mm, stroke=0, fill=1)
        c.setFillColor(TEAL)
        c.rect(w - 2 * mm, 0, 2 * mm, h, stroke=0, fill=1)
        c.setFillColor(TEAL_L)
        c.setFont("VazirB", 40)
        c.drawRightString(w - 10 * mm, h / 2 - 14, fa(f"{self.n:02d}"))
        c.setFillColor(colors.white)
        c.setFont("VazirB", 15)
        c.drawRightString(w - 33 * mm, h / 2 + 8, fa("فصل"))
        title = self.title
        c.setFont("VazirB", 14.5)
        if len(title) > 44:
            cut = title.rfind(" ", 0, 44)
            c.drawRightString(w - 33 * mm, h / 2 + 6, fa(title[:cut]))
            c.drawRightString(w - 33 * mm, h / 2 - 8, fa(title[cut:]))
        else:
            c.drawRightString(w - 33 * mm, h / 2 + 2, fa(title))
        c.setFont("Vazir", 7.5)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawString(7 * mm, 7 * mm, f"Chapter {self.n:02d}")
        c.restoreState()


def chapter_opener(number, ch, content_w, fig_by_id):
    """نوار فصل + دامنه + هشدارها + فهرست زیرمبحث‌ها (به‌صورت Flowable)."""
    out = [ChapterBand(number, ch["chapter_title"], content_w), Spacer(1, 4 * mm)]
    if ch.get("scope"):
        out.append(Paragraph(fa(ch["scope"]), S["body"]))
        out.append(Spacer(1, 2 * mm))
    for note in ch.get("notes", []):
        out.append(Paragraph(fa("⚠ " + note),
                             ParagraphStyle("nt2", fontName="Vazir", fontSize=8.6, leading=14,
                                            textColor=WARN, alignment=TA_RIGHT)))
        out.append(Spacer(1, 1.5 * mm))
    out.append(Spacer(1, 3 * mm))
    rows = [[Paragraph(fa("زیرمبحث"), S["cardT"]), Paragraph(fa("شکل"), S["cardT"]),
             Paragraph(fa("متن"), S["cardT"])]]
    for sec in ch["sections"]:
        nfig = sum(1 for b in sec["blocks"] if b["type"] == "figure")
        npar = sum(1 for b in sec["blocks"] if b["type"] in ("paragraph", "supplement"))
        rows.append([Paragraph(fa(f"{sec['section_id'].split('-')[-1]} — {sec['title']}"), S["small"]),
                     Paragraph(fa(str(nfig)), S["small"]),
                     Paragraph(fa(str(npar)), S["small"])])
    t = Table(rows, colWidths=[content_w - 24 * mm, 12 * mm, 12 * mm], repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, LINE),
                           ("BACKGROUND", (0, 0), (-1, 0), BG),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    out += [Paragraph(fa("زیرمبحث‌های این فصل"), S["h3"]), t]
    # منابع این فصل
    src_rows = [[Paragraph(fa("منبع"), S["cardT"]), Paragraph(fa("نقش"), S["cardT"]),
                 Paragraph(fa("فایل"), S["cardT"])]]
    for sid in ch.get("sources", []):
        r = REG_CACHE.get(sid)
        if not r:
            continue
        role = "بدنه" if sid in [b["sid"] for b in ch.get("_bodies", [])] else "تکمیل"
        src_rows.append([Paragraph(fa(sid), S["small"]), Paragraph(fa(role), S["small"]),
                         Paragraph(fa(r["filename"]), S["small"])])
    for a in ch.get("appendix", []):
        src_rows.append([Paragraph(fa("پیوست"), S["small"]),
                         Paragraph(fa("تصویر صفحه"), S["small"]),
                         Paragraph(fa(a["filename"]), S["small"])])
    if len(src_rows) > 1:
        t2 = Table(src_rows, colWidths=[22 * mm, 22 * mm, content_w - 44 * mm], repeatRows=1)
        t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, LINE),
                                ("BACKGROUND", (0, 0), (-1, 0), BG),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
        out += [Spacer(1, 4 * mm), Paragraph(fa("منابع این فصل"), S["h3"]), t2]
    return out


def render_section(ch, sec, reg, fig_by_id, content_w, used_figs, fig_no):
    out = []
    out.append(CondPageBreak(60 * mm))
    out.append(SectionMarker(sec["section_id"], f"{ch['chapter_title']} / {sec['title']}", level=1))
    head = Table([[Paragraph(fa(esc(sec["title"])),
                            ParagraphStyle("sh", fontName="VazirB", fontSize=12.5, leading=19,
                                           textColor=NAVY, alignment=TA_RIGHT))]],
                 colWidths=[content_w])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BG),
                              ("LINEBEFORE", (0, 0), (0, -1), 2.6, BLUE),
                              ("TOPPADDING", (0, 0), (-1, -1), 5),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                              ("LEFTPADDING", (0, 0), (-1, -1), 7),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 7)]))
    sid_label = sec["section_id"].replace("-S", ".")
    out.append(Paragraph(fa(f"مبحث {sid_label}"), S["chip"]))
    out.append(head)
    out.append(Spacer(1, 2 * mm))
    # کارت پیش‌نیاز
    pre = sec.get("prerequisites") or []
    if pre:
        items = []
        for p in pre:
            ref = p["ref"]
            target = ref.replace("-S", ".")
            items.append(Paragraph(
                fa(f"• {p['level']}: مبحث {target} — {p['why']}") ,
                ParagraphStyle("pr", fontName="Vazir", fontSize=8.6, leading=13.5,
                               textColor=TEXT, alignment=TA_RIGHT)))
        out.append(Card("پیش از مطالعه این بخش", items, accent=TEAL, bg=colors.HexColor("#f0fdfa")))
        out.append(Spacer(1, 3 * mm))

    # بلوک‌های محتوا — گروه‌بندی پاراگراف‌های هم‌منبع
    group, group_src, group_pages = [], None, []

    def flush_group():
        nonlocal group, group_src, group_pages
        if not group:
            return
        flow = [Paragraph(fa(esc(t)), S["body"]) for t in group]
        if group_src:
            pages = sorted({p for p in group_pages if p})
            plabel = ""
            if pages:
                plabel = f" — ص {pages[0]}" + (f"–{pages[-1]}" if len(pages) > 1 else "")
            flow.append(Paragraph(fa("منبع: " + src_label(reg, group_src) + plabel), S["chip"]))
        out.extend(flow)
        group, group_src, group_pages = [], None, []

    for b in sec["blocks"]:
        t = b["type"]
        if t in ("paragraph", "supplement"):
            src = (b.get("sources") or [{}])[0]
            sid = src.get("sid")
            if t == "supplement" or (group_src and sid != group_src):
                flush_group()
            if t == "supplement":
                body = [Paragraph(fa(esc(b["text"])), S["card"]),
                        Paragraph(fa("منبع: " + src_label(reg, sid, src.get("page"))), S["chip"])]
                out.append(Card(b.get("source_type", "تکمیل از منبع دیگر"), body,
                                accent=BLUE_L, bg=colors.HexColor("#eff6ff")))
                out.append(Spacer(1, 2.5 * mm))
            else:
                group.append(b["text"])
                group_src = sid
                group_pages.append(src.get("page"))
        elif t == "figure":
            flush_group()
            f = fig_by_id.get(b["figure_id"])
            if not f:
                continue
            if f.get("page_role") == "cover":
                # تصویرهای صفحه جلد جزوه، تزئینی هستند و در PDF استفاده نمی‌شوند
                f["used_in_pdf"] = False
                f["exclusion_reason"] = "صفحه جلد/عنوان جزوه — تزئینی"
                continue
            if f["figure_id"] in [u["figure_id"] for u in used_figs]:
                continue
            im = img_flowable(f["file"], content_w - 8 * mm, 105 * mm)
            if im is None:
                continue
            fig_no["n"] += 1
            f["used_in_pdf"] = True
            f["final_figure_number"] = fig_no["n"]
            f["chapter_id"] = ch["chapter_id"]
            f["section_id"] = sec["section_id"]
            f["topic"] = sec["title"]
            used_figs.append(f)
            src = (b.get("sources") or [{}])[0]
            cap = (f"شکل {fig_no['n']} — {sec['title']}  ·  منبع: "
                   f"{src_label(reg, src.get('sid'), src.get('page'))}")
            out.append(CondPageBreak(min(118 * mm, 40 * mm + 105 * mm)))
            out.append(im)
            out.append(Paragraph(fa(cap), S["cap"]))
            out.append(Spacer(1, 3 * mm))
        elif t == "source_conflict":
            flush_group()
            items = []
            for it in b.get("items", []):
                items.append(Paragraph(fa(f"▪ منبع {it['source']} (ص {it['page']}): "
                                          f"«{it['text'][:220]}…»  — اعداد: {', '.join(it['numbers'])}"),
                                       ParagraphStyle("cf", fontName="Vazir", fontSize=8.2,
                                                      leading=13, textColor=TEXT,
                                                      alignment=TA_RIGHT)))
            items.append(Paragraph(fa("وضعیت: " + b.get("status", "بررسی‌نشده")), S["chip"]))
            out.append(Card("⚠ اختلاف منابع — " + b.get("title", ""), items,
                            accent=CONF, bg=CONF_BG))
            out.append(Spacer(1, 3 * mm))
        elif t == "callout":
            flush_group()
            out.append(Card(b.get("title", "نیازمند بررسی"),
                            [Paragraph(fa(esc(b.get("text", ""))), S["card"])],
                            accent=WARN, bg=WARN_BG))
            out.append(Spacer(1, 3 * mm))
    flush_group()
    # باکس یادداشت
    out.append(Spacer(1, 2 * mm))
    sz = next((b.get("size", "medium") for b in sec["blocks"] if b["type"] == "team_notes"), "medium")
    out.append(NoteBox(sz))
    out.append(Spacer(1, 5 * mm))
    return out


def render_appendix(ch, ap, reg, content_w):
    out = []
    out.append(Spacer(1, 3 * mm))
    out.append(Paragraph(fa(f"پیوست تصویری فصل {ch['chapter_id']} — {ap['filename']}"),
                         S["h2"]))
    out.append(Paragraph(fa("متن استخراج‌شده این فایل دچار افت کیفیت است؛ برای حفظ محتوا، "
                            "تصویر صفحه‌های اصلی در ادامه آمده است. هیچ اصلاح حدسی روی متن انجام نشده."),
                         S["small"]))
    out.append(Spacer(1, 2 * mm))
    for p in ap["pages"]:
        im = img_flowable(p["file"], content_w - 20 * mm, 205 * mm)
        if im is None:
            continue
        cap = f"صفحه {p['page']} — {ap['filename']}"
        out.append(CondPageBreak(min(215 * mm, 200 * mm)))
        out.append(im)
        out.append(Paragraph(fa(cap), S["cap"]))
        out.append(Spacer(1, 2 * mm))
    return out


def guide_pages(reg, content_w):
    out = []
    out.append(SectionMarker("guide", "راهنمای استفاده", level=0))
    out.extend(PageTitle("راهنمای استفاده از این سند", "برای اعضای تیم جزوه‌نویسی"))
    rows = [
        ("متن اصلی", "عین متن منابع (جزوات ۱۴۰۴، ۱۴۰۲ خوانا، جزوات دکتر قدیری)؛ بدون بازنویسی آزاد."),
        ("تکمیل از …", "مطلب غیرتکراری منبع دیگر (مثلاً کلاس دکتر قدیری) با ذکر منبع."),
        ("⚠ اختلاف منابع", "دو منبع، جمله مشترک با اعداد متفاوت دارند؛ هیچ‌کدام خودسرانه ترجیح داده نشده."),
        ("پیش از مطالعه این بخش", "پیش‌نیازهای ضروری/پیشنهادی با شماره مبحث دقیق."),
        ("یادداشت و تکمیل عضو تیم", "فضای نوشتن برای iPad یا کاغذ؛ اندازه متناسب با حجم مبحث."),
        ("نیازمند بررسی", "مطلبی که در منابع موجود یافت نشد یا متن آن قابل‌اعتماد نبود."),
        ("پیوست تصویری", "تصویر صفحه‌های جزوه‌هایی که متن استخراجی آن‌ها مخدوش است."),
    ]
    data = [[Paragraph(fa(k), S["cardT"]), Paragraph(fa(v), S["card"])] for k, v in rows]
    t = Table(data, colWidths=[46 * mm, content_w - 46 * mm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, LINE),
                           ("BACKGROUND", (0, 0), (0, -1), BG),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    out.append(t)
    out.append(Spacer(1, 5 * mm))
    out.append(Paragraph(fa("محدودیت‌های ثبت‌شده"), S["h2"]))
    lim = [
        "ویدئوهای جلسات در مخزن GitHub به‌صورت Git LFS نگهداری می‌شوند و در این اجرا دانلود نشدند؛ در نتیجه "
        "متن گفتار استاد در این سند وجود ندارد و بخش ویدئوهای نقشه منابع خالی است.",
        "سه فایل PDF گایتون (نسخه انگلیسی و دو جلد فارسی) نیز Git LFS هستند و در این اجرا دریافت نشدند؛ "
        "لذا تطبیق صفحه‌به‌صفحه با گایتون انجام نشده و به‌جای آن، ارجاع‌های گایتون که در خود جزوات ذکر شده "
        "(مثل «فصل ۵۳ گایتون») حفظ شده است.",
        "متن برخی جزوه‌های ۱۴۰۲ و چند جزوه تایپ‌شده با OCR/تبدیل ناقص تولید شده و کیفیت پایین دارد؛ این "
        "متن‌ها اصلاح حدسی نشده‌اند و تصویر صفحه‌هایشان در پیوست آمده است.",
        "شکل‌ها از PDFهای منبع استخراج شده‌اند؛ عنوان/زیرنویس اصلی شکل‌ها در فایل‌های منبع موجود نبود و "
        "زیرنویس‌ها بر اساس مبحث و صفحه منبع ساخته شده‌اند.",
    ]
    for l in lim:
        out.append(Paragraph(fa("• " + l), S["body"]))
    out.append(Spacer(1, 4 * mm))
    out.append(Paragraph(fa("نقشه منابع و شماره صفحه‌ها"), S["h2"]))
    out.append(Paragraph(fa("برای هر پاراگراف، منبع و شماره صفحه در پایین همان گروه پاراگراف ذکر شده است. "
                            "شناسه منابع (SRC-xxxx) در فایل‌های inventory/INVENTORY.md و "
                            "inventory/SOURCE_MAP.csv قابل جست‌وجو است."), S["body"]))
    return out


def back_matter(chapters, reg, figs, used_figs, content_w):
    out = []
    out.append(SectionMarker("back", "پیوست‌های پایانی", level=0))
    out.extend(PageTitle("پیوست‌های پایانی", "منابع، نمایه شکل‌ها و راهنمای علائم"))
    out.append(Spacer(1, 3 * mm))
    # منابع
    out.append(Paragraph(fa("فهرست منابع پردازش‌شده"), S["h2"]))
    rows = [[Paragraph(fa("شناسه"), S["cardT"]), Paragraph(fa("فایل"), S["cardT"]),
             Paragraph(fa("نوع"), S["cardT"]), Paragraph(fa("حجم (KB)"), S["cardT"]),
             Paragraph(fa("وضعیت"), S["cardT"])]]
    for sid in sorted(reg):
        r = reg[sid]
        cr = r["quality"]["common_ratio"]
        if "Guyton" in r["rel_path"]:
            status = "مرجع انگلیسی (LTR)"
        elif cr >= 0.13:
            status = "متن قابل استفاده"
        elif cr >= 0.05:
            status = "متن نیمه‌مخدوش"
        else:
            status = "متن مخدوش/تصویری"
        rows.append([Paragraph(fa(sid), S["small"]), Paragraph(fa(r["filename"]), S["small"]),
                     Paragraph(fa(r["type"]), S["small"]),
                     Paragraph(fa(f"{r['size']//1024:,}"), S["small"]),
                     Paragraph(fa(status), S["small"])])
    t = Table(rows, colWidths=[18 * mm, content_w - 18 * mm - 14 * mm - 20 * mm - 26 * mm,
                               14 * mm, 20 * mm, 26 * mm], repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, LINE),
                           ("BACKGROUND", (0, 0), (-1, 0), BG),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    out.append(t)
    out.append(Spacer(1, 6 * mm))
    # تطبیق موضوعی با گایتون
    gpath = os.path.join(ROOT, "work", "guyton_index.json")
    if os.path.exists(gpath):
        g = json.load(open(gpath))
        out.append(Paragraph(fa("تطبیق موضوعی با گایتون (نسخه انگلیسی — شماره صفحه چاپی)"), S["h2"]))
        out.append(Paragraph(fa("نسخه PDF گایتون در مخزن Git LFS است و در این اجرا دریافت نشد؛ "
                                "این جدول از نسخه متنی کامل کتاب ساخته شده و فصل/صفحه چاپی "
                                "مطالب مرتبط را نشان می‌دهد."), S["small"]))
        out.append(Spacer(1, 2 * mm))
        grows = [[Paragraph(fa("مبحث درس"), S["cardT"]),
                  Paragraph(fa("فصل‌های مرتبط گایتون (صفحه چاپی)"), S["cardT"])]]
        for c in g["concepts"]:
            chs = "، ".join(f"فصل {h['chapter']} ({h['printed_page']})" for h in c["chapters"]) or "—"
            grows.append([Paragraph(fa(c["concept_fa"]), S["small"]),
                          Paragraph(fa(chs), S["small"])])
        tg = Table(grows, colWidths=[58 * mm, content_w - 58 * mm], repeatRows=1)
        tg.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, LINE),
                                ("BACKGROUND", (0, 0), (-1, 0), BG),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
        out.append(tg)
        out.append(Spacer(1, 5 * mm))
    # نمایه شکل‌ها
    out.append(Paragraph(fa("نمایه شکل‌ها"), S["h2"]))
    rows = [[Paragraph(fa("شکل"), S["cardT"]), Paragraph(fa("فصل/مبحث"), S["cardT"]),
             Paragraph(fa("منبع و صفحه"), S["cardT"])]]
    for f in sorted(used_figs, key=lambda x: x["final_figure_number"]):
        rows.append([Paragraph(fa(str(f["final_figure_number"])), S["small"]),
                     Paragraph(fa(f"{f['section_id'].replace('-S','.')} — {f['topic']}"), S["small"]),
                     Paragraph(fa(f"{f['source_id']} · ص {f['page']}"), S["small"])])
    t2 = Table(rows, colWidths=[16 * mm, content_w - 16 * mm - 46 * mm, 46 * mm], repeatRows=1)
    t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, LINE),
                            ("BACKGROUND", (0, 0), (-1, 0), BG),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("TOPPADDING", (0, 0), (-1, -1), 2),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    out.append(t2)
    out.append(Spacer(1, 6 * mm))
    out.append(Paragraph(fa("گزارش کوتاه وضعیت منابع ناقص یا مبهم"), S["h2"]))
    notes = [
        "ویدئوهای جلسات (Git LFS) دانلود نشدند: متن گفتار استاد، فریم‌های اسلاید ویدئویی و زمان‌بندی "
        "در این نسخه وجود ندارد. برای تکمیل، فایل‌های mp4 باید از مخزن دریافت و با faster-whisper فارسی "
        "ترنسکرایب شوند.",
        "نسخه‌های گایتون (انگلیسی و فارسی) به‌دلیل Git LFS دریافت نشدند؛ تطبیق صفحه‌به‌صفحه با گایتون "
        "انجام نشده است. ارجاع‌های گایتونی که در متن جزوات آمده حفظ شده‌اند.",
        "جزوه‌های ۱۴۰۲ جلسات ۱ تا ۱۱: متن استخراجی مخدوش؛ محتوا به‌صورت تصویر صفحه در پیوست فصل‌های مربوط "
        "ارائه شده و نیازمند OCR فارسی است.",
        "مبحث چشایی و بویایی: در آرشیو منابع، جلسه اختصاصی وجود ندارد؛ فصل ۶ فقط اشاره‌های پراکنده را "
        "گرد آورده و با برچسب «نیازمند بررسی» ثبت شده است.",
        "پاورپوینت (pptx) در مخزن موجود نبود؛ شکل‌ها تنها از PDFها/جزوات استخراج شده‌اند.",
    ]
    for n in notes:
        out.append(Paragraph(fa("• " + n), S["body"]))
    return out


def toc_label(key):
    if key.startswith("CH") and "-S" not in key:
        for ch in CHAPTERS_CACHE:
            if ch["chapter_id"] == key:
                return f"فصل {int(key[2:]):02d} — {ch['chapter_title']}"
    if "-S" in key:
        cid, sid = key.split("-S")
        for ch in CHAPTERS_CACHE:
            if ch["chapter_id"] == cid:
                for sec in ch["sections"]:
                    if sec["section_id"] == key:
                        return f"{int(cid[2:])}.{int(sid)} — {sec['title']}"
    return key


def toc_block(entries, content_w):
    """فهرست مطالب به‌صورت جدول دوستونی (قابل شکست بین صفحه‌ها)."""
    rows = [[Paragraph(fa("صفحه"), ParagraphStyle("th", fontName="VazirB", fontSize=8.4,
                                                  textColor=MUTED, alignment=TA_CENTER)),
             Paragraph(fa("فصل / مبحث"), ParagraphStyle("th2", fontName="VazirB", fontSize=8.4,
                                                       textColor=MUTED, alignment=TA_RIGHT))]]
    styles = [("GRID", (0, 0), (-1, -1), 0.0, colors.white),
              ("LINEBELOW", (0, 0), (-1, 0), 0.8, TEAL),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("TOPPADDING", (0, 0), (-1, -1), 1.6),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
              ("TOPPADDING", (0, 0), (-1, 0), 3),
              ("BOTTOMPADDING", (0, 0), (-1, 0), 4)]
    for i, (key, page) in enumerate(entries, start=1):
        is_ch = re.match(r"^CH\d+$", key) is not None
        rows.append([Paragraph(fa(str(page)),
                               ParagraphStyle("pg", fontName="VazirM" if is_ch else "Vazir",
                                              fontSize=9 if is_ch else 8.2,
                                              textColor=BLUE if is_ch else MUTED, alignment=TA_CENTER)),
                     Paragraph(fa(toc_label(key)),
                               ParagraphStyle("tl", fontName="VazirB" if is_ch else "Vazir",
                                              fontSize=10 if is_ch else 8.7,
                                              leading=15 if is_ch else 13,
                                              textColor=NAVY if is_ch else TEXT,
                                              alignment=TA_RIGHT,
                                              rightIndent=0 if is_ch else 12))])
        if is_ch:
            styles += [("BACKGROUND", (0, i), (-1, i), BG),
                       ("LINEABOVE", (0, i), (-1, i), 0.5, colors.HexColor("#dbeafe")),
                       ("TOPPADDING", (0, i), (-1, i), 6),
                       ("BOTTOMPADDING", (0, i), (-1, i), 4)]
    t = Table(rows, colWidths=[18 * mm, content_w - 18 * mm], repeatRows=1)
    t.setStyle(TableStyle(styles))
    return [t]


CHAPTERS_CACHE = []
REG_CACHE = {}


def main():
    global CHAPTERS_CACHE
    chapters, reg, figs = load()
    CHAPTERS_CACHE = chapters
    REG_CACHE.update(reg)
    final, chapters, reg, used_figs, fig_no = build()
    print("PDF:", final)
    print("شکل‌های استفاده‌شده:", fig_no["n"])


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""رندر مبحث‌ها از فهرست بلوک‌های محتوایی."""
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from rtl_kit import C, fa


from reportlab.lib.units import mm as _mm

DELIVERY_H = 90 * _mm


def _closing_page(k, pending_note, no, title, question):
    """صفحهٔ پایانی مبحث: کادر یادداشت + برگهٔ تحویل، بدون فضای هدررفته."""
    bot = 19 * _mm + 4 * _mm
    avail = k.y - bot
    if avail >= 72 * _mm:
        # یادداشت فضای باقی‌ماندهٔ همین صفحه را پر می‌کند، برگهٔ تحویل صفحهٔ کامل می‌گیرد
        k.note_area("یادداشت این مبحث", lines=max(4, int((avail - 18 * _mm) / 7.6 / _mm)),
                    height=avail - 5 * _mm)
        k.new_page(k.cur_kind)
        k.delivery_sheet(no, title, question, h=(k.y - bot) - 6 * _mm)
        return
    k.new_page(k.cur_kind)
    avail = k.y - bot
    note_h = min(avail - (DELIVERY_H + 6 * _mm), 146 * _mm)
    k.note_area("یادداشت این مبحث", lines=max(4, int((note_h - 13 * _mm) / 7.6 / _mm)),
                height=note_h)
    k.delivery_sheet(no, title, question, h=DELIVERY_H)


def identikit(k, no, title, ident):
    """شناسنامهٔ یکتای مبحث."""
    c = k.c
    fields = [
        ("جای مبحث در مسیر درس", ident["jaygah"]),
        ("هدف این مبحث", ident["hadaf"]),
        ("پیش‌نیاز واقعی", ident["pishniaz"]),
        ("راهنمای اختصاصی خواندن", ident["rahnam"]),
    ]
    pad = 3.0 * mm
    label_w = 33 * mm
    val_w = k.maxw - 2 * pad - label_w
    heights = []
    for _, v in fields:
        lines = k.wrap(v, "r", 8.3, val_w)
        heights.append(max(9 * mm, len(lines) * 8.3 * 1.62 + 4 * mm))
    src_lines = k.wrap(ident.get("manabe", ""), "r", 7.2, k.maxw - 2 * pad)
    src_h = len(src_lines) * 7.2 * 1.55 + 2.5 * mm
    head_h = 9.5 * mm
    total = head_h + sum(heights) + src_h + 2 * pad

    if not k.space(total + 4 * mm):
        k.new_page(k.cur_kind)
    top = k.y
    # کادر
    c.setFillColor(HexColor("#ffffff"))
    c.setStrokeColor(HexColor(C["line"]))
    c.setLineWidth(0.9)
    c.roundRect(k.left, top - total, k.maxw, total, 2.4 * mm, stroke=1, fill=1)
    # سر
    c.setFillColor(HexColor(C["sky"]))
    c.roundRect(k.left, top - head_h, k.maxw, head_h, 2.4 * mm, stroke=0, fill=1)
    c.setFillColor(HexColor(C["ink"]))
    c.rect(k.left, top - head_h, k.maxw, 1.2 * mm, stroke=0, fill=1)
    c.setFillColor(HexColor(C["ink2"]))
    c.setFont(k.F["sb"], 9.2)
    c.drawRightString(k.right - pad, top - 6.4 * mm,
                      k.shape(f"شناسنامهٔ مبحث {fa(no)} — {title}"))
    c.setFillColor(HexColor(C["teal"]))
    c.setFont(k.F["r"], 7.4)
    c.drawString(k.left + pad, top - 6.4 * mm, k.shape("یک شناسنامه برای هر مبحث"))

    y = top - head_h
    for i, ((label, val), h) in enumerate(zip(fields, heights)):
        if i % 2 == 1:
            c.setFillColor(HexColor("#fafcff"))
            c.rect(k.left + 0.6 * mm, y - h, k.maxw - 1.2 * mm, h, stroke=0, fill=1)
        c.setFillColor(HexColor(C["gray"]))
        c.setFont(k.F["sb"], 7.9)
        c.drawRightString(k.right - pad, y - 4.6 * mm, k.shape(label))
        c.setFillColor(HexColor(C["ink"]))
        c.setFont(k.F["r"], 8.3)
        yy = y - 4.6 * mm
        for (_, vis, _) in k.wrap(val, "r", 8.3, val_w):
            c.drawRightString(k.right - pad - label_w, yy, vis)
            yy -= 8.3 * 1.62
        c.setStrokeColor(HexColor("#eef2f7"))
        c.setLineWidth(0.6)
        c.line(k.left + 2 * mm, y - h, k.right - 2 * mm, y - h)
        y -= h
    # منابع مبحث
    y -= 1.6 * mm
    c.setFillColor(HexColor(C["gray"]))
    c.setFont(k.F["r"], 7.2)
    for (_, vis, _) in src_lines:
        c.drawRightString(k.right - pad, y - 1.8 * mm, vis)
        y -= 7.2 * 1.55
    k.y = top - total - 4.5 * mm


def render_mabhas(k, blocks):
    pending_note = None
    for b in blocks:
        kind = b[0]
        if kind == "mabhas":
            _, no, kicker, title, ident = b
            k.new_page("mabhas")
            k.h_section_band(kicker, title, key=f"m{no:02d}", sub=f"مبحث {fa(no)}")
            k.toc.append((1, f"مبحث {fa(no)} — {title}", k.page_no, f"m{no:02d}"))
            identikit(k, no, title, ident)
        elif kind == "h2":
            k.h2(b[1])
        elif kind == "h3":
            k.h3(b[1], color=(b[2] if len(b) > 2 else None))
        elif kind == "p":
            k.para(b[1], size=9.5, space_after=2.4 * mm)
        elif kind == "pl":
            k.para(b[1], size=8.9, color="#3c4757", space_after=2 * mm)
        elif kind == "src":
            k.source_line(b[1])
        elif kind == "bul":
            k.bullets(b[1], size=9.3)
        elif kind == "num":
            k.numbered(b[1], size=9.3)
        elif kind == "fig":
            _, path, cap, src, ratio, maxh = b
            k.figure(path, cap, src, width_ratio=ratio, max_h=maxh * mm)
        elif kind == "tab":
            _, cap, headers, rows, widths, src = b[:6]
            opts = b[6] if len(b) > 6 else {}
            k.table(headers, rows, widths=widths, caption=cap, source=src,
                    size=opts.get("size", 8.1), ltr_cols=opts.get("ltr", ()),
                    align_cols=opts.get("align", None))
        elif kind == "box":
            _, bkind, title, body, src = b[:5]
            items = b[5] if len(b) > 5 else None
            k.box(title, body, source=src, kind=bkind, bullet_items=items)
        elif kind == "note":
            pending_note = b[1] if len(b) > 1 else 7
        elif kind == "delivery":
            _closing_page(k, pending_note, b[1], b[2], b[3])
            pending_note = None
        elif kind == "gap":
            k.gap(b[1] * mm)
        elif kind == "pagebreak":
            k.new_page(k.cur_kind)
        else:
            raise ValueError("بلوک ناشناخته: %r" % (kind,))

# -*- coding: utf-8 -*-
"""صفحه‌های ثابت جزوه: جلد، صفحهٔ دوم، فهرست، آغاز جلسه، چک‌لیست، جلد آخر."""
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from rtl_kit import Kit, C, fa, PAGE_W, PAGE_H, M_TOP, M_BOT, M_SIDE


def _glow(k, cx, cy, r, color, steps=16, alpha0=0.20):
    c = k.c
    for i in range(steps, 0, -1):
        rr = r * i / steps
        a = alpha0 * (1 - i / steps) ** 1.6 + 0.004
        c.saveState()
        c.setFillColor(HexColor(color))
        c.setFillAlpha(a)
        c.circle(cx, cy, rr, stroke=0, fill=1)
        c.restoreState()


def cover(k, data):
    k.new_page("cover")
    c = k.c
    GLOW = "assets/glow/"
    c.setFillColor(HexColor(C["ink"]))
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    k.glow(GLOW + "glow_blue.png", PAGE_W * 0.92, PAGE_H * 0.93, 520)
    k.glow(GLOW + "glow_teal.png", PAGE_W * 0.05, PAGE_H * 0.66, 470)
    k.glow(GLOW + "glow_indigo.png", PAGE_W * 0.62, PAGE_H * 0.12, 560)

    c.setFillColor(HexColor("#ffffff"))
    c.setFont(k.F["b"], 18)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 30 * mm, "HumsYar")
    c.setFillColor(HexColor("#7dd3c8"))
    c.setFont(k.F["sb"], 9.4)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 36.6 * mm, k.shape("گروه جزوه‌نویسی پزشکی · هم‌یار"))
    c.setStrokeColor(HexColor("#20456b"))
    c.setLineWidth(0.9)
    c.line(M_SIDE, PAGE_H - 45 * mm, PAGE_W - M_SIDE, PAGE_H - 45 * mm)

    # برچسب نسخه
    c.setFillColor(HexColor("#0d9488"))
    c.roundRect(PAGE_W - M_SIDE - 56 * mm, PAGE_H - 60 * mm, 56 * mm, 9.5 * mm, 2.2 * mm, stroke=0, fill=1)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont(k.F["sb"], 8.8)
    c.drawCentredString(PAGE_W - M_SIDE - 28 * mm, PAGE_H - 57 * mm, k.shape(data["cover_badge"]))

    # شمارهٔ جلسه
    c.setFillColor(HexColor("#9dc0ea"))
    c.setFont(k.F["m"], 12.5)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 78 * mm, k.shape(data["session_no_label"]))

    # عنوان جلسه با تنظیم اندازه تا جا شود
    avail = PAGE_W - 2 * M_SIDE - 6 * mm
    size = 25
    while size > 14 and k.tw(data["session_title"], "b", size) > avail:
        size -= 1
    c.setFillColor(HexColor("#ffffff"))
    c.setFont(k.F["b"], size)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 93 * mm, k.shape(data["session_title"]))
    # خط تأکید
    tw = k.tw(data["session_title"], "b", size)
    c.setFillColor(HexColor("#0d9488"))
    c.roundRect(PAGE_W - M_SIDE - tw, PAGE_H - 99 * mm, tw, 1.0 * mm, 0.5 * mm, stroke=0, fill=1)

    c.setFillColor(HexColor("#7dd3c8"))
    c.setFont(k.F["sb"], 13)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 108 * mm, k.shape(data["course_title"]))

    c.setFillColor(HexColor("#c3d1e4"))
    c.setFont(k.F["r"], 9.4)
    yy = PAGE_H - 119 * mm
    for ln in data["cover_bullets"]:
        for (_, vis, _) in k.wrap(ln, "r", 9.4, PAGE_W - 2 * M_SIDE - 6 * mm):
            c.drawRightString(PAGE_W - M_SIDE, yy, vis)
            yy -= 6.4 * mm
        yy -= 2.2 * mm

    # کارت منابع
    ch = 13 * mm + len(data["sources_block"]) * 5.6 * mm + 3 * mm
    cy = yy - 6 * mm - ch
    c.setFillColor(HexColor("#0b1220"))
    c.setStrokeColor(HexColor("#1e3a5f"))
    c.setLineWidth(0.9)
    c.roundRect(M_SIDE, cy, PAGE_W - 2 * M_SIDE, ch, 3.2 * mm, stroke=1, fill=1)
    c.setFillColor(HexColor("#7dd3c8"))
    c.rect(M_SIDE + 4 * mm, cy + ch - 9.6 * mm, 2.2 * mm, 2.2 * mm, stroke=0, fill=1)
    c.setFont(k.F["sb"], 8.6)
    c.drawRightString(PAGE_W - M_SIDE - 5 * mm, cy + ch - 9.4 * mm, k.shape("منابع واقعاً استفاده‌شده در این جلسه"))
    c.setFillColor(HexColor("#dbe7f5"))
    c.setFont(k.F["r"], 7.7)
    y2 = cy + ch - 17 * mm
    for ln in data["sources_block"]:
        c.drawRightString(PAGE_W - M_SIDE - 5 * mm, y2, k.shape(ln))
        y2 -= 5.6 * mm

    # خوشه‌های محتوایی
    cl = data.get("cover_clusters") or []
    if cl:
        gap = 4 * mm
        cw = (PAGE_W - 2 * M_SIDE - gap * (len(cl) - 1)) / len(cl)
        cy2 = cy - 10 * mm - 30 * mm
        for i, (t, sub) in enumerate(cl):
            x = PAGE_W - M_SIDE - cw - i * (cw + gap)
            c.setFillColor(HexColor("#0d1728"))
            c.setStrokeColor(HexColor("#1e3a5f"))
            c.setLineWidth(0.8)
            c.roundRect(x, cy2, cw, 30 * mm, 2.6 * mm, stroke=1, fill=1)
            c.setFillColor(HexColor("#0d9488"))
            c.roundRect(x, cy2 + 30 * mm - 1.4 * mm, cw, 1.4 * mm, 0.7 * mm, stroke=0, fill=1)
            c.setFillColor(HexColor("#ffffff"))
            c.setFont(k.F["sb"], 7.9)
            c.drawRightString(x + cw - 3.4 * mm, cy2 + 22 * mm, k.shape(t))
            c.setFillColor(HexColor("#9dc0ea"))
            c.setFont(k.F["r"], 7.2)
            yy2 = cy2 + 15.4 * mm
            for (_, vis, _) in k.wrap(sub, "r", 7.2, cw - 6.8 * mm):
                c.drawRightString(x + cw - 3.4 * mm, yy2, vis)
                yy2 -= 4.6 * mm
        # ردیف آمار
        st = data.get("cover_stats") or []
        if st:
            sy = cy2 - 16 * mm
            c.setFillColor(HexColor("#0b1220"))
            c.setStrokeColor(HexColor("#1e3a5f"))
            c.setLineWidth(0.8)
            c.roundRect(M_SIDE, sy, PAGE_W - 2 * M_SIDE, 18 * mm, 2.4 * mm, stroke=1, fill=1)
            sw = (PAGE_W - 2 * M_SIDE) / len(st)
            for i, (num, lab) in enumerate(st):
                cx = PAGE_W - M_SIDE - sw * i - sw / 2
                c.setFillColor(HexColor("#7dd3c8"))
                c.setFont(k.F["b"], 12.4)
                c.drawCentredString(cx, sy + 7.4 * mm, k.shape(num))
                c.setFillColor(HexColor("#9dc0ea"))
                c.setFont(k.F["sb"], 7.2)
                c.drawCentredString(cx, sy + 3 * mm, k.shape(lab))

    # نوار پایین
    c.setFillColor(HexColor("#0d1524"))
    c.rect(0, 0, PAGE_W, 26 * mm, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#1e3a5f"))
    c.setLineWidth(0.9)
    c.line(M_SIDE, 26 * mm, PAGE_W - M_SIDE, 26 * mm)
    c.setFillColor(HexColor("#8fb3e0"))
    c.setFont(k.F["r"], 7.8)
    c.drawRightString(PAGE_W - M_SIDE, 11 * mm, k.shape(data["cover_foot"]))
    c.drawString(M_SIDE, 11 * mm, k.shape("HumsYar · پایگاه جزوه‌های پزشکی"))
    c.setFillColor(HexColor("#7dd3c8"))
    c.setFont(k.F["sb"], 7.6)
    c.drawRightString(PAGE_W - M_SIDE, 19 * mm, k.shape("جزوهٔ مادر · برای تیم جزوه‌نویسی · نسخهٔ ۱"))


def guide_page(k, data):
    k.new_page("guide")
    c = k.c
    c.setFillColor(HexColor(C["ink"]))
    c.rect(0, PAGE_H - 34 * mm, PAGE_W, 34 * mm, stroke=0, fill=1)
    c.setFillColor(HexColor("#7dd3c8"))
    c.setFont(k.F["sb"], 9)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 15 * mm, k.shape("راهنمای خواندن"))
    c.setFillColor(HexColor("#ffffff"))
    c.setFont(k.F["b"], 17)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 25 * mm, k.shape(data["guide_title"]))
    k.y = PAGE_H - 42 * mm

    k.para(data["guide_intro"], size=9.0, align="justify", space_after=2.6 * mm)

    # کارت‌های دو ستونه
    cards = data["guide_cards"]
    colw = (k.maxw - 5 * mm) / 2
    i = 0
    while i < len(cards):
        pair = cards[i:i + 2]
        # ارتفاع کارت‌ها
        heights = []
        for t, b in pair:
            bl = k.wrap(b, "r", 7.9, colw - 8 * mm)
            heights.append(10 * mm + len(bl) * 7.9 * 1.6 + 3.4 * mm)
        hmax = max(heights)
        if not k.space(hmax + 4 * mm):
            k.new_page("guide")
            c.setFillColor(HexColor(C["ink"]))
            c.rect(0, PAGE_H - 18 * mm, PAGE_W, 18 * mm, stroke=0, fill=1)
            c.setFillColor(HexColor("#7dd3c8"))
            c.setFont(k.F["sb"], 8.4)
            c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 11.6 * mm, k.shape(data["guide_title"] + " (ادامه)"))
            k.y = PAGE_H - 27 * mm
        top = k.y
        for j, (t, b) in enumerate(pair):
            x0 = k.right - colw - j * (colw + 5 * mm) if False else 0
            # ستون اول از راست
            xr = k.right - j * (colw + 5 * mm)
            xl = xr - colw
            c.setFillColor(HexColor("#ffffff"))
            c.setStrokeColor(HexColor(C["line"]))
            c.setLineWidth(0.8)
            c.roundRect(xl, top - hmax, colw, hmax, 2.2 * mm, stroke=1, fill=1)
            c.setFillColor(HexColor(C["teal"]))
            c.roundRect(xr - 1.9 * mm, top - hmax, 1.9 * mm, hmax, 0.9 * mm, stroke=0, fill=1)
            c.setFillColor(HexColor(C["ink"]))
            c.setFont(k.F["sb"], 8.8)
            c.drawRightString(xr - 4.4 * mm, top - 6.4 * mm, k.shape(t))
            c.setFont(k.F["r"], 7.9)
            c.setFillColor(HexColor("#3c4757"))
            yy = top - 10.6 * mm
            for (_, vis, _) in k.wrap(b, "r", 7.9, colw - 8 * mm):
                c.drawRightString(xr - 4.4 * mm, yy, vis)
                yy -= 7.9 * 1.6
        k.y = top - hmax - 3.4 * mm
        i += 2

    k.gap(1 * mm)
    k.box("قاعدهٔ ارجاع در این جزوه", data["guide_citation_rule"],
          source=None, kind="clinic", size=8.4)


def toc(k, entries, clusters=None, total_pages=0):
    """فهرست با شمارهٔ صفحهٔ واقعی؛ اگر مدخلی نباشد صفحهٔ راهنما ساخته می‌شود."""
    k.new_page("toc")
    c = k.c
    c.setFillColor(HexColor(C["ink"]))
    c.rect(0, PAGE_H - 34 * mm, PAGE_W, 34 * mm, stroke=0, fill=1)
    c.setFillColor(HexColor("#7dd3c8"))
    c.setFont(k.F["sb"], 9)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 15 * mm, k.shape("فهرست مطالب"))
    c.setFillColor(HexColor("#ffffff"))
    c.setFont(k.F["b"], 17)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 25 * mm, k.shape("فهرست"))
    k.y = PAGE_H - 38 * mm

    rows = entries
    if not rows:
        k.source_line("فهرست در نسخهٔ نهایی همین‌جا با شمارهٔ صفحهٔ واقعی چاپ می‌شود.")
        return
    clusters = clusters or {}
    for idx, (level, title, page, key) in enumerate(rows):
        if idx in clusters:
            ctitle, crange = clusters[idx]
            if not k.space(9 * mm):
                k.new_page("toc")
                c.setFillColor(HexColor(C["ink"]))
                c.rect(0, PAGE_H - 16 * mm, PAGE_W, 16 * mm, stroke=0, fill=1)
                c.setFillColor(HexColor("#7dd3c8"))
                c.setFont(k.F["sb"], 8.4)
                c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 10.4 * mm, k.shape("فهرست (ادامه)"))
                k.y = PAGE_H - 25 * mm
            y0 = k.y
            c.setFillColor(HexColor(C["ink"]))
            c.roundRect(k.left, y0 - 7.6 * mm, k.maxw, 7.6 * mm, 1.6 * mm, stroke=0, fill=1)
            c.setFillColor(HexColor("#ffffff"))
            c.setFont(k.F["sb"], 8.6)
            c.drawRightString(k.right - 3.4 * mm, y0 - 5.2 * mm, k.shape(ctitle))
            c.setFillColor(HexColor("#7dd3c8"))
            c.setFont(k.F["sb"], 8)
            c.drawString(k.left + 3.4 * mm, y0 - 5.2 * mm, k.shape(crange))
            k.y = y0 - 9.4 * mm
        if not k.space(10 * mm):
            k.new_page("toc")
            c.setFillColor(HexColor(C["ink"]))
            c.rect(0, PAGE_H - 16 * mm, PAGE_W, 16 * mm, stroke=0, fill=1)
            c.setFillColor(HexColor("#7dd3c8"))
            c.setFont(k.F["sb"], 8.4)
            c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 10.4 * mm, k.shape("فهرست (ادامه)"))
            k.y = PAGE_H - 25 * mm
        y = k.y
        indent = 0 if level == 1 else 5 * mm
        xr = k.right - indent
        # نقطه‌چین + شماره
        pw = k.tw(fa(page), "sb", 9)
        c.setFillColor(HexColor(C["ink2"]))
        c.setFont(k.F["m"] if level == 1 else k.F["r"], 9.2)
        c.drawRightString(xr, y - 5.4 * mm, k.shape(title))
        tx = xr - k.tw(title, "m" if level == 1 else "r", 9.2) - 3 * mm
        c.setFont(k.F["r"], 8)
        c.setFillColor(HexColor("#94a3b8"))
        dots = "."
        dx = tx
        while dx - 2.2 * mm > k.left + 16 * mm:
            c.drawRightString(dx, y - 5.2 * mm, "·")
            dx -= 2.4 * mm
        c.setFillColor(HexColor(C["teal"] if level == 1 else C["ink"]))
        c.setFont(k.F["sb"], 9.2)
        c.drawString(k.left + 8 * mm, y - 5.4 * mm, fa(page))
        # خط زیرین faint
        c.setStrokeColor(HexColor("#eef2f7"))
        c.setLineWidth(0.5)
        c.line(k.left + 4 * mm, y - 7 * mm, k.right, y - 7 * mm)
        # پیوند
        try:
            k.c.linkRect("", key, (k.left, y - 7.2 * mm, k.right, y + 0.4 * mm), relative=0, thickness=0)
        except Exception:
            pass
        k.y = y - 8.5 * mm


def session_opener(k, data):
    k.new_page("opener")
    c = k.c
    # سربرگ
    c.setFillColor(HexColor(C["ink"]))
    c.rect(0, PAGE_H - 52 * mm, PAGE_W, 52 * mm, stroke=0, fill=1)
    k.glow("assets/glow/glow_teal.png", PAGE_W * 0.15, PAGE_H - 18 * mm, 260)
    c.setFillColor(HexColor("#7dd3c8"))
    c.setFont(k.F["sb"], 9.4)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 16 * mm, k.shape(data["opener_kicker"]))
    c.setFillColor(HexColor("#ffffff"))
    c.setFont(k.F["b"], 19)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 27 * mm, k.shape(data["opener_title"]))
    c.setFillColor(HexColor("#b9c6da"))
    c.setFont(k.F["r"], 8.8)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 35 * mm, k.shape(data["opener_sub"]))
    c.setFillColor(HexColor("#8fb3e0"))
    c.setFont(k.F["r"], 7.8)
    c.drawRightString(PAGE_W - M_SIDE, PAGE_H - 43 * mm, k.shape(data["opener_meta"]))
    k.y = PAGE_H - 60 * mm

    # منابع جلسه
    k.h2("منابع این جلسه و نقش هر کدام")
    k.table(["منبع", "شناسهٔ فایل / مرجع", "نقش در این جزوه", "دامنهٔ بررسی‌شده"],
            data["sources_rows"],
            widths=[0.16, 0.34, 0.24, 0.26], size=7.8,
            source=data["sources_note"])

    k.h2("نقشهٔ راه مباحث و پیشنهاد تقسیم کار")
    k.para(data["opener_map_intro"], size=9.2, space_after=2.4 * mm)
    k.table(["مبحث", "عنوان", "پیش‌نیاز", "حجم پیشنهادی"],
            data["map_rows"], widths=[0.10, 0.50, 0.24, 0.16], size=7.6,
            source=data["map_note"])


def checklist_page(k, data):
    k.new_page("body")
    k.h1("چک‌لیست پذیرش و خودآزمایی پایان جلسه", key="checklist")
    k.para(data["check_intro"], size=9.2, space_after=3 * mm)
    k.h2("الف) چک‌لیست پوشش و کیفیت")
    for grp in data["check_groups"]:
        k.h3(grp[0], size=9.6)
        for item in grp[1]:
            k.ensure(9 * mm)
            y = k.y
            c = k.c
            c.setStrokeColor(HexColor(C["teal"]))
            c.setLineWidth(0.8)
            c.rect(k.right - 3.2 * mm, y - 5.2 * mm, 3.2 * mm, 3.2 * mm, stroke=1, fill=0)
            lines = k.wrap(item, "r", 8.6, k.maxw - 8 * mm)
            c.setFillColor(HexColor(C["ink"]))
            c.setFont(k.F["r"], 8.6)
            yy = y - 2.4 * mm
            for (_, vis, _) in lines:
                c.drawRightString(k.right - 6 * mm, yy, vis)
                yy -= 8.6 * 1.55
            k.y = yy - 1.8 * mm
    k.gap(2 * mm)
    k.h2("ب) خودآزمایی")
    k.para(data["selftest_intro"], size=9, space_after=2 * mm)
    k.numbered(data["selftest"], size=9)
    k.box("پاسخ‌ها", data["selftest_answers"], kind="note", size=8.2)


def closing_note(k, title="یادداشت پایانی جلسه"):
    """پرکردن فضای باقی‌ماندهٔ صفحهٔ پایانی با کادر خط‌دار."""
    from reportlab.lib.units import mm as _mm
    avail = k.y - (19 * _mm + 4 * _mm)
    if avail >= 40 * _mm:
        k.note_area(title, lines=max(3, int((avail - 18 * _mm) / 7.6 / _mm)), height=avail - 4 * _mm)


def back_cover(k, data):
    k.new_page("back")
    c = k.c
    c.setFillColor(HexColor(C["ink"]))
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    k.glow("assets/glow/glow_teal.png", PAGE_W * 0.5, PAGE_H * 0.62, 480)
    k.glow("assets/glow/glow_blue.png", PAGE_W * 0.18, PAGE_H * 0.18, 420)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont(k.F["b"], 22)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.62, "HumsYar")
    c.setFillColor(HexColor("#7dd3c8"))
    c.setFont(k.F["sb"], 11)
    c.drawCentredString(PAGE_W / 2, PAGE_H * 0.62 - 9 * mm, k.shape("گروه جزوه‌نویسی پزشکی · هم‌یار"))
    c.setStrokeColor(HexColor("#1e3a5f"))
    c.setLineWidth(0.9)
    c.line(PAGE_W * 0.28, PAGE_H * 0.53, PAGE_W * 0.72, PAGE_H * 0.53)
    c.setFillColor(HexColor("#dbe7f5"))
    c.setFont(k.F["r"], 9.4)
    y = PAGE_H * 0.49
    for ln in data["back_lines"]:
        c.drawCentredString(PAGE_W / 2, y, k.shape(ln))
        y -= 6.4 * mm
    c.setFillColor(HexColor("#8fb3e0"))
    c.setFont(k.F["r"], 8)
    c.drawCentredString(PAGE_W / 2, 26 * mm, k.shape(data["back_foot"]))

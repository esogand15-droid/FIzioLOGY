#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مرحله ۳ — استخراج تصاویر و شکل‌ها از PDFهای منبع

- تشخیص آبجکت‌های تصویری هر صفحه و ادغام کادرهای هم‌پوشان/مجاور
- رندر ناحیه شکل با کیفیت بالا (بدون تحریف نسبت ابعاد)
- حذف تصاویر تکراری بر اساس sha256 و ابعاد
- ثبت نمایه کامل در images/INDEX.json
"""
import hashlib
import io
import json
import os

import pypdfium2 as p
import pypdfium2.raw as raw
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "extracted")
WORK = os.path.join(ROOT, "work")
OUT = os.path.join(ROOT, "images", "extracted")
MIN_AREA_RATIO = 0.035
MAX_PER_PAGE = 3
SCALE = 3.0
MAX_PX = 1800


def union(boxes):
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


def merge_boxes(boxes, pad=6.0):
    """ادغام کادرهایی که به هم چسبیده‌اند (تصاویر تکه‌تکه یک شکل)."""
    boxes = sorted(boxes, key=lambda b: -(b[2] - b[0]) * (b[3] - b[1]))
    merged = []
    for b in boxes:
        b = [b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad]
        placed = False
        for i, m in enumerate(merged):
            if not (b[2] < m[0] or b[0] > m[2] or b[3] < m[1] or b[1] > m[3]):
                merged[i] = union([m, b])
                placed = True
                break
        if not placed:
            merged.append(b)
    # ادغام ثانویه پس از گسترش
    changed = True
    while changed:
        changed = False
        out = []
        for b in merged:
            for i, m in enumerate(out):
                if not (b[2] < m[0] or b[0] > m[2] or b[3] < m[1] or b[1] > m[3]):
                    out[i] = union([m, b])
                    changed = True
                    break
            else:
                out.append(b)
        merged = out
    return merged


def main():
    reg = json.load(open(os.path.join(WORK, "source_registry.json")))
    index = []
    seen = {}
    n = 0
    for rec in reg:
        if rec["type"] != "pdf":
            continue
        sid = rec["source_id"]
        path = os.path.join(SRC, rec["rel_path"])
        doc = p.PdfDocument(path)
        for pno, page in enumerate(doc):
            boxes = []
            for obj in page.get_objects(filter=(raw.FPDF_PAGEOBJ_IMAGE,)):
                try:
                    l, b, r, t = obj.get_bounds()
                except Exception:  # noqa: BLE001
                    continue
                if r - l < 20 or t - b < 20:
                    continue
                boxes.append([l, b, r, t])
            if not boxes:
                continue
            W, H = page.get_size()
            cands = []
            for bb in merge_boxes(boxes):
                l, b, r, t = bb
                l, b = max(0.5, l), max(0.5, b)
                r, t = min(W - 0.5, r), min(H - 0.5, t)
                if r - l < 30 or t - b < 30:
                    continue
                ratio = (r - l) * (t - b) / (W * H)
                if ratio < MIN_AREA_RATIO or ratio > 0.97:
                    continue
                w0, h0 = r - l, t - b
                # حذف نوارهای سرصفحه/پانویس تزئینی و برش‌های بی‌ارزش
                if h0 < 70 or w0 < 80 or max(w0 / h0, h0 / w0) > 6.5:
                    continue
                if t > H * 0.94 or b < H * 0.02 and h0 < H * 0.12:
                    continue
                cands.append((ratio, [l, b, r, t]))
            cands.sort(key=lambda x: -x[0])
            for ratio, (l, b, r, t) in cands[:MAX_PER_PAGE]:
                h = (t - b) * SCALE
                w = (r - l) * SCALE
                scale = min(SCALE, MAX_PX / max(w, h, 1))
                bmp = page.render(scale=scale)
                full = bmp.to_pil().convert("RGB")
                sx = full.width / W
                sy = full.height / H
                box = (max(0, int(l * sx)), max(0, int((H - t) * sy)),
                       min(full.width, int(r * sx)), min(full.height, int((H - b) * sy)))
                if box[2] - box[0] < 40 or box[3] - box[1] < 40:
                    continue
                img = full.crop(box)
                # حذف تصویرهای تقریباً یکنواخت (پس‌زمینه/نوار رنگ)
                g = img.convert("L").resize((48, 48))
                px = list(g.getdata())
                mean = sum(px) / len(px)
                var = sum((v - mean) ** 2 for v in px) / len(px)
                if var < 240:
                    continue
                buf = io.BytesIO()
                img.save(buf, "JPEG", quality=84, optimize=True)
                data = buf.getvalue()
                digest = hashlib.sha256(data).hexdigest()[:16]
                key = (img.width // 40, img.height // 40, digest[:8])
                if (sid, digest) in seen:      # حذف تکرار فقط در همان منبع
                    continue
                seen[(sid, digest)] = True
                n += 1
                fid = f"FIG-{n:04d}"
                fn = f"{fid}.jpg"
                with open(os.path.join(OUT, fn), "wb") as f:
                    f.write(data)
                index.append({
                    "figure_id": fid, "file": f"images/extracted/{fn}",
                    "source_id": sid, "source_file": rec["rel_path"],
                    "page": pno + 1, "bbox": [round(v, 1) for v in (l, b, r, t)],
                    "area_ratio": round(ratio, 3), "px": [img.width, img.height],
                    "bytes": len(data), "sha256_16": digest,
                    "topic": "", "chapter_id": "", "used_in_pdf": False,
                    "page_role": "cover" if pno == 0 else "content",
                    "final_figure_number": "", "quality": "ok",
                })
        print(f"{sid}: total figures so far {n}")
    json.dump(index, open(os.path.join(ROOT, "images", "INDEX.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"{len(index)} تصویر استخراج شد")


if __name__ == "__main__":
    main()

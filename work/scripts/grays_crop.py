"""برش شکل‌های گری از رندر صفحه (نه از XObject جاسازی‌شده).

فایل‌های گری لایهٔ متنی سالمی ندارند و XObjectهای شکل هم برچسب‌ها را جدا از
تصویر نگه می‌دارند؛ پس شکل با رندر کردن همان ناحیه از صفحه و با همان dpi ساخته
می‌شود تا برچسب‌های انگلیسی داخل قاب بمانند.

    .venv/bin/python work/scripts/grays_crop.py                        # همهٔ برش‌های ۱–۲۰۰
    .venv/bin/python work/scripts/grays_crop.py --only p0087_fig28
    .venv/bin/python work/scripts/grays_crop.py --part 801_1000
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REF = Path("/home/user/_refs")
OUT = REPO / "images_anatomy"

# part -> (فایل مبدأ، برش‌ها)؛ کلید هر برش = پسوند asset_id
# مقدار: (شمارهٔ صفحهٔ PDF، مستطیل برش به نقطه، توضیح)
PARTS: dict[str, tuple[str, dict[str, tuple[int, tuple[float, float, float, float]]]]] = {
    "1_200": (
        "user - Gray's Anatomy For Students, 3rd Edition-1-200.pdf",
        {
            "p0062_fig136": (62, (58, 392, 562, 722)),     # Fig. 1.36
            "p0063_fig137": (63, (72, 286, 562, 722)),     # Fig. 1.37
            "p0087_fig28": (87, (22, 286, 548, 722)),      # Fig. 2.8
            "p0090_fig211": (90, (300, 52, 602, 716)),     # Fig. 2.11
            "p0091_fig212": (91, (34, 262, 312, 578)),     # Fig. 2.12
        },
    ),
    # جلسهٔ ۵ — ساقهٔ مغز: صفحهٔ چاپی = صفحهٔ PDF + ۷۷۲
    "801_1000": (
        "user - Gray's Anatomy For Students, 3rd Edition-801-1000.pdf",
        {
            "p0869_fig827": (97, (22, 45, 600, 320)),      # Fig. 8.27
            "p0880_fig837": (108, (60, 60, 575, 365)),     # Fig. 8.37
            "p0896_fig850": (124, (20, 350, 600, 692)),    # Fig. 8.50
            "p0897_fig851": (125, (20, 60, 600, 415)),     # Fig. 8.51
        },
    ),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--part", default="1_200", choices=sorted(PARTS))
    ap.add_argument("--dpi", type=int, default=300)
    a = ap.parse_args()

    srcname, crops = PARTS[a.part]
    src = REF / srcname
    idx_path = OUT / "INDEX.json"
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    have = {x["asset_id"] for x in idx["assets"]}
    written = 0
    with pymupdf.open(src) as d:
        for suffix, (page, clip) in crops.items():
            if a.only and suffix not in a.only:
                continue
            aid = f"grays3_{a.part}_{suffix}"
            name = f"{aid}.jpeg"
            pix = d[page - 1].get_pixmap(dpi=a.dpi, clip=pymupdf.Rect(*clip))
            pix.save(OUT / name, jpg_quality=88)
            rect = pymupdf.Rect(*clip)
            pct = round(100 * rect.width * rect.height / (d[page - 1].rect.width
                                                         * d[page - 1].rect.height), 1)
            row = dict(asset_id=aid, book="grays", session=None,
                       source_file="Gray's Anatomy for Students, 3rd ed. — part "
                                   f"{a.part.replace('_', '-')} (page render, labels included)",
                       page=page, w=pix.width, h=pix.height, px=pix.width * pix.height,
                       area_pct=pct, bytes=(OUT / name).stat().st_size,
                       path=f"images_anatomy/{name}")
            if aid in have:
                idx["assets"] = [row if x["asset_id"] == aid else x for x in idx["assets"]]
            else:
                idx["assets"].append(row)
            written += 1
            print(f"{aid:34s} p{page} {pix.width}x{pix.height} {row['bytes']//1024:>4}KB")
    idx["assets"].sort(key=lambda x: x["asset_id"])
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"crops {written} · index total {len(idx['assets'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

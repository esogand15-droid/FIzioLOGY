"""استخراج انتخابی تصاویر آناتومی به ``images_anatomy/``.

فقط دارایی‌هایی که در ``--ids`` می‌آیند نوشته می‌شوند؛ بنابراین مخزن با صدها مگابایت
تصویر پر نمی‌شود و هر جلسه فقط شکل‌های خودش را دارد.

    .venv/bin/python work/scripts/anat_export.py --ids s01_p002_img02 snell_ch01_p0025_img01
    .venv/bin/python work/scripts/anat_export.py --session s01 --kinds figure
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REF = Path("/home/user/_refs")
OUT = REPO / "images_anatomy"
REG_L = REPO / "work" / "anatomy" / "registry_lectures.json"
REG_S = REPO / "work" / "anatomy" / "registry_snell.json"
SNELL = REF / "Snells Clinical Neuroanatomy, 9th Edition (Ryan Splittgerber) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
MAP = json.loads((REPO / "work" / "extraction" / "anat" / "map.json").read_text(encoding="utf-8"))


def source_file(row: dict) -> Path:
    if row.get("book") == "snell":
        return SNELL
    sid = row["session"]
    for p in REF.joinpath("lectures").rglob("*.pdf"):
        if p.name == row["file"]:
            return p
    raise FileNotFoundError(row["file"])


def export(rows: list[dict]) -> list[dict]:
    OUT.mkdir(exist_ok=True)
    written = []
    cache: dict[str, pymupdf.Document] = {}
    for r in rows:
        src = source_file(r)
        key = str(src)
        if key not in cache:
            cache[key] = pymupdf.open(src)
        if "xref" in r:
            info = cache[key].extract_image(r["xref"])
        else:  # registry_snell stores no xref: look the image up by page + index
            page = cache[key][r["page"] - 1]
            imgs = page.get_images(full=True)
            idx = int(r["asset_id"].rsplit("img", 1)[1]) - 1
            info = cache[key].extract_image(imgs[idx][0])
        name = f"{r['asset_id']}.{info['ext']}"
        (OUT / name).write_bytes(info["image"])
        written.append(dict(asset_id=r["asset_id"], path=f"images_anatomy/{name}",
                            bytes=len(info["image"]), w=r["w"], h=r["h"],
                            page=r["page"], session=r.get("session"),
                            chapter=r.get("chapter"), kind=r["kind"]))
    for d in cache.values():
        d.close()
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", default=[])
    ap.add_argument("--session")
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--kinds", nargs="*", default=["figure"])
    ap.add_argument("--min-px", type=int, default=120000)
    a = ap.parse_args()

    rows = json.loads(REG_L.read_text(encoding="utf-8"))["images"]
    rows += json.loads(REG_S.read_text(encoding="utf-8"))["images"]
    by_id = {r["asset_id"]: r for r in rows}

    sel: list[dict] = []
    if a.ids:
        sel = [by_id[i] for i in a.ids if i in by_id]
        missing = [i for i in a.ids if i not in by_id]
        if missing:
            print("NOT FOUND:", missing)
    else:
        sel = [r for r in rows
               if (not a.session or r.get("session") == a.session)
               and (not a.chapter or r.get("chapter") == a.chapter)
               and r["kind"] in a.kinds and r["px"] >= a.min_px
               and not r.get("duplicate_of")]
    done = export(sel)
    idx_path = OUT / "INDEX.json"
    idx = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"assets": []}
    have = {x["asset_id"] for x in idx["assets"]}
    for x in done:
        if x["asset_id"] not in have:
            idx["assets"].append(x)
    idx["assets"].sort(key=lambda x: x["asset_id"])
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in done:
        print(f"{x['asset_id']:26s} {x['w']}x{x['h']:<5} {x['bytes']//1024:>4}KB {x['path']}")
    print(f"exported {len(done)} · registry total {len(idx['assets'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------- Gray's export
GRAY_PARTS = {
    "1-200": REF / "user - Gray's Anatomy For Students, 3rd Edition-1-200.pdf",
    "200-400": REF / "user - Gray's Anatomy For Students, 3rd Edition-200-400.pdf",
    "401-600": REF / "user - Gray's Anatomy For Students, 3rd Edition-401-600.pdf",
    "601-800": REF / "user - Gray's Anatomy For Students, 3rd Edition-601-800.pdf",
    "801-1000": REF / "user - Gray's Anatomy For Students, 3rd Edition-801-1000.pdf",
    "1001-1189": REF / "user - Gray's Anatomy For Students, 3rd Edition-1001-1189.pdf",
}


def export_grays(part: str, pages: list[int], min_px: int = 120000) -> list[dict]:
    """Export figure-like XObjects of specific pages of one Gray's part file."""
    OUT.mkdir(exist_ok=True)
    path = GRAY_PARTS[part]
    reg_path = REPO / "work" / "anatomy" / "registry_grays.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else {"images": []}
    have = {r["asset_id"] for r in reg["images"]}
    written = []
    with pymupdf.open(path) as d:
        for p in pages:
            page = d[p - 1]
            for k, im in enumerate(page.get_images(full=True)):
                w, h = im[2], im[3]
                try:
                    bb = page.get_image_bbox(im)
                except Exception:
                    continue
                pct = 100 * (bb.width * bb.height) / (page.rect.width * page.rect.height)
                if pct > 85 or w * h < min_px:
                    continue
                aid = f"grays3_{part.replace('-', '_')}_p{p:04d}_img{k+1:02d}"
                info = d.extract_image(im[0])
                name = f"{aid}.{info['ext']}"
                (OUT / name).write_bytes(info["image"])
                row = dict(asset_id=aid, book="grays", part=part, page=p, w=w, h=h,
                           px=w * h, area_pct=round(pct, 1),
                           bbox=[round(v, 1) for v in bb],
                           bytes=len(info["image"]),
                           path=f"images_anatomy/{name}")
                if aid not in have:
                    reg["images"].append(row)
                written.append(row)
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    return written

"""Extract text + embedded figures + page facsimiles for one session's PDFs.

Idempotent: skips a figure whose target file already exists with the same
content hash, and never touches the source PDFs.

Usage: python3 work/scripts/extract_session.py s01
"""
from __future__ import annotations

import argparse
import hashlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_common import (  # noqa: E402
    EXTRACTION, IMAGES, REPO, SOURCE_ROOT, dump_json, load_json, persian_score, rel,
)

SESSION_DIRS = {
    "s01": ("جلسه 1", "جلسه 1 نوروفیزیولوژی مهر 1404.pdf", "نوروفیزیولوژی 01 نهایی بهمن 1402.pdf"),
    "s02": ("جلسه 2", "جلسه ۲ نوروفیزیولوژی مهر 1404.pdf", "نوروفیزیولوژی 02 نهایی بهمن 1402.pdf"),
}

MIN_FIG = (120, 90)          # px; below this we still *record* it but do not export
PAGE_RENDER_SCALE = 1.8      # ~130 dpi: readable handwriting, printable facsimile


def extract_pdf(pdf_path: Path, sid: str, tag: str, render_pages: bool) -> dict:
    import pypdf
    import pypdfium2 as pdfium

    reader = pypdf.PdfReader(str(pdf_path))
    doc = pdfium.PdfDocument(str(pdf_path))
    out_dir = IMAGES / ("notes_1404" if "1404" in tag else "notes_1402" if "1402" in tag else "slides")
    out_dir.mkdir(parents=True, exist_ok=True)
    facsimile_dir = IMAGES / ("notes_1402" if "1402" in tag else ("notes_1404" if "1404" in tag else "slides"))

    pages, figure_index = [], []
    for pno in range(len(reader.pages)):
        page = reader.pages[pno]
        text = doc[pno].get_textpage().get_text_bounded()
        page_w_pt, page_h_pt = doc[pno].get_size()
        page_scan_w = page_w_pt * 150 / 72 * 0.9   # a page scan spans the whole sheet
        page_scan_h = page_h_pt * 150 / 72 * 0.9
        figs = []
        try:
            images = list(page.images)
        except Exception:
            images = []
        for idx, img in enumerate(images, start=1):
            try:
                pil = img.image
            except Exception:
                continue
            w, h = pil.size
            asset_id = f"{sid}_p{pno + 1:03d}_fig{idx:02d}"
            entry = {
                "asset_id": asset_id, "source_id": sid, "page": pno + 1, "index_on_page": idx,
                "w": w, "h": h, "exported": False,
            }
            is_page_scan = w >= page_scan_w and h >= page_scan_h
            if is_page_scan:
                entry.update({"exported": False, "kind": "page_scan_redundant_with_facsimile"})
                figs.append(entry)
                continue
            if w >= MIN_FIG[0] and h >= MIN_FIG[1]:
                buf = io.BytesIO()
                pil.convert("RGB").save(buf, format="PNG")
                data = buf.getvalue()
                digest = hashlib.sha256(data).hexdigest()
                target = out_dir / f"{asset_id}.png"
                entry.update({
                    "exported": True, "path": rel(target), "sha256": digest,
                    "kind": "figure",
                })
                if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                    target.write_bytes(data)
                figure_index.append(entry)
            else:
                entry["kind"] = "small_or_decorative_not_exported"
            figs.append(entry)
        page_entry = {"n": pno + 1, "text": text, "figures": figs}
        if render_pages:
            fac = facsimile_dir / f"{sid}_p{pno + 1:03d}_facsimile.jpg"
            if not fac.exists():
                doc[pno].render(scale=PAGE_RENDER_SCALE).to_pil().convert("RGB").save(
                    fac, quality=88, optimize=True, progressive=True)
            page_entry["facsimile"] = rel(fac)
        page_entry["quality"] = persian_score(text)
        pages.append(page_entry)

    result = {
        "session": sid, "tag": tag, "pdf": rel(pdf_path),
        "pages": pages, "figures": figure_index,
        "page_count": len(pages),
        "chars": sum(len(p["text"]) for p in pages),
        "verdict": persian_score("\r".join(p["text"] for p in pages))["verdict"],
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("session", choices=sorted(SESSION_DIRS))
    ap.add_argument("--render-1402-facsimiles", action="store_true", default=True)
    args = ap.parse_args()
    folder, pdf1404, pdf1402 = SESSION_DIRS[args.session]
    base = SOURCE_ROOT / folder
    sid = args.session

    index_path = IMAGES / "INDEX.json"
    index = load_json(index_path, default={"assets": []}) or {"assets": []}
    known = {a["asset_id"]: a for a in index["assets"]}

    for pdf_name, tag, render in ((pdf1404, "notes1404", False), (pdf1402, "notes1402", True)):
        res = extract_pdf(base / pdf_name, sid, tag, render)
        dump_json(EXTRACTION / f"{sid}_{tag}.json", res)
        for fig in res["figures"]:
            known[fig["asset_id"]] = {**fig, "caption": "", "topic_ids": [], "used_in": "pending"}
        print(f"{sid}_{tag}: pages={res['page_count']} chars={res['chars']} "
              f"figures={len(res['figures'])} verdict={res['verdict']}")

    index["assets"] = sorted(known.values(), key=lambda a: a["asset_id"])
    index["note"] = ("Facsimile pages (*_facsimile.png) are page renders of sources whose "
                     "text layer is unreliable; they are faithful copies, not OCR.")
    dump_json(index_path, index)
    print(f"images index: {len(index['assets'])} assets -> {rel(index_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

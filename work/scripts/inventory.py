"""Build INVENTORY.md + work/source_manifest.json from the real repository tree.

Usage:  python3 work/scripts/inventory.py [--force]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_common import (  # noqa: E402
    REPO, SOURCE_ROOT, WORK, dump_json, is_lfs_pointer, lfs_pointer_info,
    load_json, persian_score, rel, sha256_file,
)

TEXT_EXT = {".md", ".txt"}
PDF_EXT = {".pdf"}
VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov"}
SLIDE_EXT = {".pptx", ".ppt"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}


FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
PART_WORDS = {
    "یک": "1", "دو": "2", "سه": "3", "چهار": "4", "چهارم": "4", "پنج": "5",
    "شش": "6", "هفت": "7", "هشت": "8", "نه": "9", "ده": "10",
}
SESSION_RE = re.compile(r"جلسه\s*([0-9۰-۹٠-٩]+)")


def stable_id(rel_path: str) -> str:
    """Readable, stable identifier derived from the path (never from page numbers
    or from the position of a file inside a rendered PDF)."""
    name = Path(rel_path).name
    path_norm = rel_path.translate(FA_DIGITS)
    m = SESSION_RE.search(str(Path(rel_path).parent).translate(FA_DIGITS)) or \
        SESSION_RE.search(path_norm)
    session = f"s{int(m.group(1)):02d}" if m else None
    ext = Path(rel_path).suffix.lower()

    if ext in VIDEO_EXT:
        pm = re.search(r"پارت[_ ]?(\w+)", name.translate(FA_DIGITS))
        part = pm.group(1) if pm else ""
        part = PART_WORDS.get(part, part)
        if not part:
            nm = re.search(r"-(\d)\.mp4$", name)
            part = nm.group(1) if nm else "1"
        kind = f"video-p{int(part):02d}" if str(part).isdigit() else f"video-{part}"
    elif "قدیری" in rel_path or "ایروان" in rel_path:
        stem = Path(name).stem
        sid = re.sub(r"[^\w]+", "-", stem.translate(FA_DIGITS)).strip("-")
        return f"supp-ghadiri_{sid}"
    elif "گایتون" in rel_path:
        if "فارسی" in name:
            kind = "guyton-fa-" + ("vol1" if "اول" in name else "vol2" if "دوم" in name else "vol")
        else:
            kind = "guyton-en"
    elif "1404" in path_norm:
        kind = "notes1404"
    elif "1402" in path_norm:
        kind = "notes1402"
    elif "پری لب" in rel_path:
        kind = "peri-lab"
    else:
        kind = re.sub(r"[^\w]+", "-", Path(name).stem.translate(FA_DIGITS)).strip("-") or "file"

    suffix = f"-{ext[1:]}" if ext in {".pdf", ".md"} else ""
    if session:
        return f"{session}_{kind}{suffix}"
    return f"misc_{kind}{suffix}"


def pdf_pages(path: Path) -> tuple[int, dict]:
    try:
        import pypdfium2 as pdfium
    except ImportError:  # pragma: no cover
        return 0, {}
    try:
        doc = pdfium.PdfDocument(str(path))
    except Exception as exc:  # corrupt file
        return 0, {"error": f"cannot open: {exc}"}
    texts = []
    for i in range(len(doc)):
        try:
            texts.append(doc[i].get_textpage().get_text_bounded())
        except Exception:
            texts.append("")
    joined = "\r".join(texts)
    score = persian_score(joined)
    empty_pages = sum(1 for t in texts if len(t.strip()) < 40)
    score["pages_with_little_text"] = empty_pages
    return len(doc), score


def drive_index() -> dict:
    """Merge optional Google Drive metadata exported to work/drive_manifest.json."""
    data = load_json(WORK / "drive_manifest.json", default={"files": []}) or {"files": []}
    by_name: dict[str, dict] = {}
    for f in data.get("files", []):
        by_name.setdefault(f["name"], f)
    return by_name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="recompute hashes even if cached")
    args = ap.parse_args()

    cache_path = WORK / "source_manifest.json"
    cache = {} if args.force else {
        e["rel_path"]: e for e in (load_json(cache_path, default={"files": []}) or {}).get("files", [])
    }
    drive = drive_index()

    files = sorted(p for p in SOURCE_ROOT.rglob("*") if p.is_file())
    entries = []
    used_ids: dict[str, int] = {}
    for path in files:
        r = rel(path)
        ext = path.suffix.lower()
        size = path.stat().st_size
        pointer = lfs_pointer_info(path)
        cached = cache.get(r)
        digest = None
        if cached and cached.get("size") == (pointer["size"] if pointer else size) and not args.force:
            digest = cached.get("sha256")
        sid = stable_id(r)
        used_ids[sid] = used_ids.get(sid, 0) + 1
        if used_ids[sid] > 1:
            sid = f"{sid}-dup{used_ids[sid]}"
        entry = {
            "source_id": sid,
            "rel_path": r,
            "file_name": path.name,
            "ext": ext,
            "size_on_disk": size,
            "storage": "git_lfs_pointer" if pointer else "inline",
            "lfs_pointer": pointer,
            "sha256": digest,
            "status": "pending",
        }
        if pointer:
            entry["payload_bytes"] = pointer["size"]
        else:
            entry["payload_bytes"] = size
            if ext in PDF_EXT:
                pages, score = pdf_pages(path)
                entry["pages"] = pages
                entry["text_quality"] = score
                entry["status"] = "extracted" if score.get("verdict") == "text_ok" else "needs_ocr_review"
            elif ext in TEXT_EXT:
                txt = path.read_text(encoding="utf-8", errors="replace")
                entry["lines"] = txt.count("\n") + 1
                entry["text_quality"] = persian_score(txt)
                entry["chars"] = len(txt)
                entry["status"] = "text_available"
            elif ext in VIDEO_EXT:
                entry["status"] = "no_payload_needs_drive_retrieval"
            else:
                entry["status"] = "not_processed"
            if digest is None:
                entry["sha256"] = sha256_file(path)
        d = drive.get(path.name)
        entry["drive_match"] = (
            {"id": d.get("id"), "size": int(d.get("size", 0)), "md5": d.get("md5_checksum")}
            if d else None
        )
        if d and entry.get("payload_bytes") and int(d.get("size", 0)) == entry["payload_bytes"]:
            entry["drive_size_matches_lfs_or_file"] = True
        entries.append(entry)

    summary = {}
    for e in entries:
        summary.setdefault(e["ext"] or "noext", {"count": 0, "payload": 0})
        summary[e["ext"] or "noext"]["count"] += 1
        summary[e["ext"] or "noext"]["payload"] += e["payload_bytes"]
    manifest = {
        "root": str(SOURCE_ROOT.name),
        "file_count": len(entries),
        "by_ext": summary,
        "lfs_pointer_count": sum(1 for e in entries if e["storage"] == "git_lfs_pointer"),
        "drive_matched": sum(1 for e in entries if e["drive_match"]),
        "files": entries,
    }
    dump_json(cache_path, manifest)

    # ---------------- INVENTORY.md ----------------
    L = []
    L.append("# INVENTORY — فهرست کامل منابع پروژه\n")
    L.append("> این فایل به‌صورت خودکار از درخت واقعی مخزن ساخته می‌شود "
             "(`work/scripts/inventory.py`) و مبنای همهٔ گزارش‌های پوشش است.\n")
    L.append(f"- تاریخ ساخت: ۲۰۲۶-۱۰-۲۴ (UTC)")
    L.append(f"- ریشهٔ منابع: `{SOURCE_ROOT.name}/`")
    L.append(f"- تعداد کل فایل: **{len(entries)}**")
    L.append(f"- فایل‌های صرفاً Git-LFS pointer (بدون payload در مخزن): **{manifest['lfs_pointer_count']}**")
    L.append(f"- فایل‌های تطبیق‌داده‌شده با متادیتای Google Drive: **{manifest['drive_matched']}**\n")
    L.append("## خلاصه بر اساس نوع فایل\n")
    L.append("| پسوند | تعداد | مجموع حجم payload (بایت) |")
    L.append("|---|---|---|")
    for ext, s in sorted(summary.items()):
        L.append(f"| `{ext}` | {s['count']} | {s['payload']:,} |")
    L.append("")
    L.append("## فهرست فایل‌ها\n")
    L.append("| شناسه | فایل | نوع | حجم/مدت | وضعیت | یادداشت |")
    L.append("|---|---|---|---|---|---|")
    for e in entries:
        note = []
        if e["storage"] == "git_lfs_pointer":
            note.append("LFS pointer؛ payload در Google Drive")
        if e.get("text_quality", {}).get("verdict") == "garbled_needs_ocr":
            note.append("لایهٔ متنی خراب → نیازمند OCR/بازبینی تصویری")
        if e.get("text_quality", {}).get("verdict") == "image_only":
            note.append("بدون لایهٔ متن مفید")
        if e["drive_match"]:
            note.append("در Drive یافت شد" + (" (اندازه برابر)" if e.get("drive_size_matches_lfs_or_file") else " (اندازه متفاوت!)"))
        size_txt = f"{e['payload_bytes']:,} B"
        if e.get("pages"):
            size_txt += f" / {e['pages']} ص"
        if e.get("lines"):
            size_txt += f" / {e['lines']} خط"
        L.append(f"| `{e['source_id']}` | `{e['file_name']}` | `{e['ext']}` | {size_txt} | "
                 f"`{e['status']}` | {'، '.join(note) or '—'} |")
    L.append("")
    (REPO / "INVENTORY.md").write_text("\n".join(L), encoding="utf-8")
    print(f"inventory: {len(entries)} files, {manifest['lfs_pointer_count']} LFS pointers")
    for e in entries:
        if e["ext"] in PDF_EXT:
            print(f"  {e['source_id']:<45} pages={e.get('pages')} "
                  f"verdict={e.get('text_quality', {}).get('verdict')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

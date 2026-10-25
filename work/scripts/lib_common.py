"""Shared helpers for the HumsYar neuro-physiology master-notes project.

All scripts are idempotent: they only rewrite an output when the source hash
changed or the output is missing/broken.  Nothing here mutates source files.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO / "فیزیولوژی اعصاب حواس ویژه"
WORK = REPO / "work"
EXTRACTION = WORK / "extraction"
PAGE_RENDERS = WORK / "page_renders"
IMAGES = REPO / "images"
CONTENT = REPO / "content"
REPORTS = REPO / "reports"
OUTPUT = REPO / "output"
FONTS = REPO / "assets" / "fonts"

LFS_MAGIC = b"version https://git-lfs.github.com/spec/v1"

PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")
LATIN_RE = re.compile(r"[A-Za-z]")
TOKEN_RE = re.compile(r"[^\s]+")


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def is_lfs_pointer(path: Path) -> bool:
    try:
        with open(path, "rb") as fh:
            head = fh.read(len(LFS_MAGIC) + 8)
    except OSError:
        return False
    return head.startswith(LFS_MAGIC)


def lfs_pointer_info(path: Path) -> dict | None:
    if not is_lfs_pointer(path):
        return None
    info: dict[str, str] = {}
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if " " in line:
                k, v = line.split(" ", 1)
                info[k.strip()] = v.strip()
    return {"oid": info.get("oid", ""), "size": int(info.get("size", "0") or 0)}


WORD_RE = re.compile(r"[\w\u0600-\u06FF\u200c]+")
# A PDF whose Persian text layer is a by-product of OCR over handwriting is
# "long but meaningless".  Instead of guessing from glyph statistics we measure
# what fraction of its word tokens occur in a lexicon harvested from a text
# layer that a human (vision) check confirmed to be clean.
LEXICON_REFERENCE = (
    SOURCE_ROOT / "جلسه 1" / "جلسه 1 نوروفیزیولوژی مهر 1404.pdf"
)
_LEXICON_CACHE = WORK / "lexicon_fa.json"


def word_tokens(text: str) -> list[str]:
    return [w for w in WORD_RE.findall(text or "") if len(w) >= 2]


def _lexicon_from_reference() -> set[str]:
    cached = load_json(_LEXICON_CACHE, default=None)
    if cached and cached.get("source") == str(LEXICON_REFERENCE.name):
        return set(cached["words"])
    words: set[str] = set()
    try:
        import pypdfium2 as pdfium

        doc = pdfium.PdfDocument(str(LEXICON_REFERENCE))
        raw = "\r".join(doc[i].get_textpage().get_text_bounded() for i in range(len(doc)))
        words = set(word_tokens(raw))
    except Exception:
        return set()
    dump_json(_LEXICON_CACHE, {"source": LEXICON_REFERENCE.name, "words": sorted(words)})
    return words


def persian_score(text: str) -> dict:
    text = text or ""
    if not text.strip():
        return {"chars": 0, "persian_ratio": 0.0, "lexicon_coverage": 0.0, "verdict": "empty"}
    chars = len(text)
    tokens = word_tokens(text)
    lex = _lexicon_from_reference()
    coverage = (sum(1 for w in tokens if w in lex) / len(tokens)) if tokens and lex else 0.0
    ratio = len(PERSIAN_RE.findall(text)) / max(chars, 1)
    latin_chars = len(LATIN_RE.findall(text))
    if chars < 40:
        verdict = "image_only"
    elif latin_chars > chars * 0.6:
        verdict = "latin_text_ok"
    elif coverage >= 0.60:
        verdict = "text_ok"
    elif coverage >= 0.45:
        verdict = "suspicious"
    else:
        verdict = "garbled_needs_ocr"
    return {
        "chars": chars,
        "persian_ratio": round(ratio, 3),
        "lexicon_coverage": round(coverage, 3),
        "verdict": verdict,
    }


def normalize_fa(text: str) -> str:
    """Light, loss-free cleanup for rendering only (never for source storage)."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u064a", "\u06cc").replace("\u0643", "\u06a9")
    text = text.replace("\u200e", "").replace("\u200f", "")
    # common typographic repairs seen in the extracted layers
    text = text.replace("( ", "(").replace(" )", ")")
    text = text.replace(" )", ")")
    text = text.replace(" ً", "ً ")
    return text


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def dump_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))

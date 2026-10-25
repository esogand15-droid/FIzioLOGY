"""Build per-topic drafts (repaired text, page-anchored) for authoring the master notes.

Output: work/drafts/s01_TXX.md  — a reviewable, page-tagged, raw-but-repaired text
        of the ۱۴۰۴ notes for each topic, with heading/bullet structure kept.
The drafts are *inputs* for the editorial step; they are never shipped as-is.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pymupdf as fitz  # noqa: E402
from fa_text import tanwin_spacing, word_repairs  # noqa: E402
from layout_text import page_lines  # noqa: E402
from lib_common import REPO, SOURCE_ROOT, WORK, dump_json, load_json  # noqa: E402

PDF_1404 = SOURCE_ROOT / "جلسه 1" / "جلسه 1 نوروفیزیولوژی مهر 1404.pdf"
PDF_1402 = SOURCE_ROOT / "جلسه 1" / "نوروفیزیولوژی 01 نهایی بهمن 1402.pdf"
OUT = WORK / "drafts"
PAGE_MARK = re.compile(r"^(.*?)\s*\[\[p(\d+)\]\]\s*$")


def collect(pdf: Path) -> list[dict]:
    doc = fitz.open(str(pdf))
    pages = []
    for pno in range(len(doc)):
        pages.append({"page": pno + 1, "lines": page_lines(doc[pno])})
    return pages


def page_range_by_headings(pages: list[dict], start: str, end: str | None) -> tuple[int, int]:
    start_p, end_p = None, len(pages)
    for p in pages:
        for ln in p["lines"]:
            if start_p is None and ln["is_heading"] and ln["text"].strip() == start.strip():
                start_p = p["page"]
            elif start_p is not None and end and ln["is_heading"] and ln["text"].strip() == end.strip():
                end_p = p["page"]
                break
        if end_p != len(pages):
            break
    return start_p or 1, end_p


def render_topic(pages: list[dict], start_p: int, end_p: int, *, skip_headings: set[str]) -> str:
    out: list[str] = []
    log: dict[str, int] = {}
    current_p = None
    for p in pages:
        if p["page"] < start_p or p["page"] > end_p:
            continue
        for ln in p["lines"]:
            text = tanwin_spacing(word_repairs(ln["text"], log))
            if not text or re.fullmatch(r"[۰-۹0-9]+", text):
                continue            # page numbers
            if p["page"] != current_p:
                out.append(f"\n\n[[p{p['page']}]]\n")
                current_p = p["page"]
            if ln["is_heading"]:
                if text.strip() in skip_headings:
                    continue
                out.append(f"\n### {text}\n")
            elif ln["is_bullet"]:
                out.append(f"- {text}")
            else:
                out.append(text)
    return "\n".join(out).replace("\n\n\n", "\n\n")


def main() -> int:
    spec = load_json(REPO / "content" / "outline" / "s01_topics.json")
    pages = collect(PDF_1404)
    headings = [ln["text"].strip() for p in pages for ln in p["lines"] if ln["is_heading"]]
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    topics = spec["topics"]
    for i, t in enumerate(topics):
        nxt = topics[i + 1]["start_heading"] if i + 1 < len(topics) else None
        start_p, end_p = page_range_by_headings(pages, t["start_heading"], nxt)
        body = render_topic(pages, start_p, end_p, skip_headings={t["start_heading"]})
        path = OUT / f"{t['topic_id']}.md"
        path.write_text(f"# {t['title']}\n\nمنبع: جزوهٔ مهر ۱۴۰۴ (دکتر خوارزمی) — صفحات {start_p}–{end_p}\n\n{body}\n",
                        encoding="utf-8")
        manifest.append({"topic_id": t["topic_id"], "title": t["title"], "pages": [start_p, end_p],
                         "draft": str(path.relative_to(REPO))})
        print(f"{t['topic_id']} {start_p:>3}-{end_p:<3} {t['title'][:60]}")
    dump_json(WORK / "drafts" / "manifest.json", {"pdf": str(PDF_1404.name), "topics": manifest})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

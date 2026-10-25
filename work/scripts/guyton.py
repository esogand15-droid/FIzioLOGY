"""Index the English Guyton markdown and extract verified supplementary sections.

The markdown is a PDF-to-markdown conversion of *Guyton & Hall Textbook of
Medical Physiology* (Unit IX onwards is what this course needs).  It contains
running headers (``Unit IX ...``), printed page numbers, code fences and figure
labels mixed into the prose.  This module

* builds a chapter index (chapter -> line range, printed pages),
* maps every line to the **printed page number** of the book,
* extracts a named section verbatim (prose only, page-anchored) so the master
  notes can quote Guyton with an exact chapter + page citation.

Nothing here paraphrases: the prose is only re-joined (line wrapping, hyphenation).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_common import REPO, SOURCE_ROOT, WORK, dump_json  # noqa: E402

GUYTON_MD = SOURCE_ROOT / "رفرنس گایتون" / "Guyton and Hall Textbook of Medical Physiology English.md"
PAGE_NO = re.compile(r"^\d{1,3}$")
UNIT_LINE = re.compile(r"^Unit [IVX]+ ")
HEADER_LINE = re.compile(r"^Chapter \d+ ")


def load_lines() -> list[str]:
    return GUYTON_MD.read_text(encoding="utf-8", errors="replace").split("\n")


def chapter_index(lines: list[str]) -> dict:
    """Map chapter number -> {first_line, last_line, pages}."""
    entries: dict[str, dict] = {}
    for i, line in enumerate(lines):
        m = re.match(r"^chapter\s+(\d+)\s*$", line.strip())  # body uses lowercase, TOC uppercase
        if m:
            num = m.group(1)
            entries.setdefault(num, {"first_line": i + 1, "header_lines": []})
            entries[num]["header_lines"].append(i + 1)
        m2 = re.match(r"^Chapter\s+(\d+)\s+", line)
        if m2:
            num = m2.group(1)
            if num in entries:
                entries[num]["header_lines"].append(i + 1)
    nums = sorted(int(n) for n in entries)
    for num in nums:
        entries[str(num)]["start"] = min(entries[str(num)]["header_lines"])
    for idx, num in enumerate(nums):
        nxt = str(nums[idx + 1]) if idx + 1 < len(nums) else None
        entries[str(num)]["end"] = entries[nxt]["start"] - 1 if nxt else len(lines)
    return {n: {k: v for k, v in e.items() if k != "header_lines"} for n, e in entries.items()}


def page_map(lines: list[str]) -> dict[int, int]:
    """line number (1-based) -> printed page number that is open at that line."""
    mapping: dict[int, int] = {}
    current = None
    for i, line in enumerate(lines, start=1):
        if PAGE_NO.match(line.strip()):
            current = int(line.strip())
        mapping[i] = current
    return mapping


def clean_section(raw_lines: list[str], pages: dict[int, int], offset: int) -> list[dict]:
    """Turn a raw line range into page-anchored paragraphs."""
    paras: list[dict] = []
    buf: list[str] = []
    buf_page: int | None = None
    buffer_mode: str = "prose"

    def flush():
        nonlocal buf, buf_page, buffer_mode
        if not buf:
            return
        text = " ".join(buf)
        text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)          # de-hyphenate
        text = re.sub(r"\s{2,}", " ", text).strip()
        if text and buffer_mode == "caption":
            paras.append({"page": buf_page, "kind": "caption", "text": text})
        elif text:
            words = len(text.split())
            if words >= 6 and (re.search(r"[.;:]$", text) or words >= 12):
                paras.append({"page": buf_page, "kind": "prose", "text": text})
        buf = []
        buffer_mode = "prose"

    for idx, line in enumerate(raw_lines):
        lineno = offset + idx + 1
        s = line.strip()
        if not s or s == "```":
            flush()
            continue
        if PAGE_NO.match(s) or UNIT_LINE.match(s) or HEADER_LINE.match(s):
            flush()
            continue
        if buf_page is None:
            buf_page = pages.get(lineno)
        if s.startswith("Figure ") or s.startswith("Table "):
            flush()
            buf_page = pages.get(lineno)
            buffer_mode = "caption"
            buf.append(s)
            flush()
            continue
        words = len(s.split())
        if words <= 3 and not re.search(r"[.!?:;,]$", s):
            flush()          # figure label / stray heading fragment
            continue
        buf.append(s)
    flush()
    # merge fragments the PDF->markdown conversion split mid-sentence
    merged: list[dict] = []
    for para in paras:
        if merged and merged[-1]["kind"] == para["kind"] == "prose" and \
                not re.search(r"[.!?:]" + '"' + r"?$", merged[-1]["text"]):
            merged[-1]["text"] = merged[-1]["text"] + " " + para["text"]
        else:
            merged.append(dict(para))
    # carry the printed page forward/backward so every paragraph has a citation
    known = [m for m in merged if m["page"]]
    if known:
        first = known[0]["page"]
        for m in merged:
            if not m["page"]:
                m["page"] = first
    for i in range(1, len(merged)):
        if merged[i]["page"] and merged[i - 1]["page"] and merged[i]["page"] < merged[i - 1]["page"]:
            merged[i]["page"] = merged[i - 1]["page"]
    return merged


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\u2014", "-").replace("\u201c", '"')
                  .replace("\u201d", '"')).strip().lower()


def find_heading(lines: list[str], heading: str, start_from: int = 0) -> int | None:
    """Headings in the converted markdown are wrapped over 2-3 lines -> match a window."""
    target = _norm(heading)
    for i in range(start_from, len(lines)):
        window = _norm(" ".join(lines[i:i + 4]))
        if window.startswith(target):
            return i
    return None


def extract_section(lines, pages, heading: str, stop_headings: list[str]) -> dict:
    """Locate a (possibly wrapped) heading and collect until a stop heading."""
    start = find_heading(lines, heading)
    if start is None:
        return {"heading": heading, "found": False, "paragraphs": []}
    end = len(lines)
    for stop in stop_headings:
        j = find_heading(lines, stop, start_from=start + 1)
        if j is not None and j < end:
            end = j
    raw = lines[start + 1:end]
    return {
        "heading": heading,
        "found": True,
        "start_line": start + 1,
        "end_line": end,
        "page": pages.get(start + 1),
        "paragraphs": clean_section(raw, pages, start + 1),
    }


def main() -> int:
    lines = load_lines()
    idx = chapter_index(lines)
    pages = page_map(lines)
    out = {"chapters": idx, "page_map_lines": len(pages)}

    SECTIONS = {
        "general_design": (
            "General Design of the Nervous System",
            ["Major Levels of Central Nervous System Function",
             "Comparison of the Nervous System with a Computer"],
        ),
        "cns_levels": (
            "Major Levels of Central Nervous System Function",
            ["Comparison of the Nervous System with a Computer"],
        ),
        "transmitter_classes": (
            "Chemical Substances That Function as Synaptic Transmitters",
            ["Neuropeptides", "Electrical Events During Neuronal Excitation"],
        ),
        "neuropeptides": (
            "Neuropeptides",
            ["Electrical Events During Neuronal Excitation"],
        ),
        "receptor_proteins": (
            "Action of the Transmitter Substance on the Postsynaptic Neuron\u2014Function of \u201cReceptor Proteins\u201d",
            ["\u201cSecond Messenger\u201d System in the Postsynaptic Neuron"],
        ),
    }
    # search only inside the real chapter-45 body; the table of contents repeats headings
    ch = idx["45"]
    body = lines[ch["start"] - 1: ch["end"]]
    body_pages = page_map(body)
    extracted = {}
    for key, (heading, stops) in SECTIONS.items():
        sec = extract_section(body, body_pages, heading, stops)
        sec["chapter"] = "45"
        extracted[key] = sec
        print(f"{key:22} found={sec['found']} page={sec.get('page')} "
              f"paragraphs={len(sec['paragraphs'])}")
    dump_json(WORK / "references" / "guyton_ch45_sections.json",
              {"source": str(GUYTON_MD.name), "sections": extracted})
    dump_json(WORK / "references" / "guyton_chapter_index.json", idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

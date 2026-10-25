"""Build clean, page-anchored Guyton excerpts for the master notes.

The previous extractor (``guyton.py``) indexed the chapter and produced *verified*
page anchors, but its paragraph filter dropped short fragments created by the
PDF→markdown conversion (page breaks, table blocks, fenced lines). Those drops
left holes inside sentences (e.g. ``...conductance through ductance...``).

This script takes a different route: it joins **all** prose lines of a section
into one stream (de-hyphenating at real line ends), keeps a page marker for every
sentence, and then splits the stream into sentences. Nothing is paraphrased --
only line wrapping is undone.

Output: ``work/references/guyton_ch45_excerpts.json``
    {"source": ..., "sections": {key: {"heading", "found", "page_start",
                                        "sentences": [{"page", "text"}]}}}
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_common import REPO, SOURCE_ROOT, WORK, dump_json  # noqa: E402

MD = SOURCE_ROOT / "رفرنس گایتون" / "Guyton and Hall Textbook of Medical Physiology English.md"
OUT = WORK / "references" / "guyton_ch45_excerpts.json"

PAGE_NO = re.compile(r"^\d{1,3}$")
RUNNING = re.compile(r"^(Unit\s+[IVX]+\s*$|C\s*h\s*a\s*p\s*t\s*e\s*r\s+45\b)")
SENT_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z“\"(])")

# --------------------------------------------------------------------- repairs
# The PDF->markdown converter dropped table bodies and figure captions *inside*
# running sentences.  These two repairs only delete converter artefacts (a table
# header and figure captions); no book wording is added or changed.  Each repair
# is asserted to fire, so a silent change in the source cannot hide here.
REPAIRS = [
    # table 45-2 header inserted in the middle of the sentence that continues
    # "...cytosol of the presynaptic [terminal and are absorbed ...]"
    (re.compile(r"presynaptic Peptides that act on gut and brain terminal"),
     "presynaptic terminal"),
]

# Sentences that are figure captions spliced together by the converter (they
# carry no book statement, only caption text) are dropped verbatim.
DROP_PATTERNS = [
    re.compile(r"^Thus, Figure 45-1 Structure of a large neuron in the brain"),
    # a caption that survived as a standalone "sentence": "Figure 45-3 Skeletal
    # motor nerve axis ..." (a real sentence starts "Figure 45-1 shows ...")
    re.compile(r"^Figure \d+-\d+ [A-Z]"),
]


SECTIONS = {
    "general_design": (
        "General Design of the Nervous System",
        ["Major Levels of Central Nervous System Function"]),
    "cns_levels": (
        "Major Levels of Central Nervous System Function",
        ["Comparison of the Nervous System with a Computer"]),
    "transmitter_classes": (
        "Chemical Substances That Function as Synaptic Transmitters",
        ["Neuropeptides"]),
    "neuropeptides": (
        "Neuropeptides",
        ["Electrical Events During Neuronal Excitation"]),
    "receptor_proteins": (
        "Action of the Transmitter Substance on the Postsynaptic Neuron—Function of “Receptor Proteins”",
        ["“Second Messenger” System in the Postsynaptic Neuron"]),
}


def norm(s: str) -> str:
    return (s.replace("—", "-").replace("“", '"').replace("”", '"')
             .replace("’", "'").replace("–", "-"))


def load_lines() -> list[str]:
    return MD.read_text(encoding="utf-8", errors="replace").split("\n")


def body_range(lines: list[str], chapter: int) -> tuple[int, int]:
    starts = [i for i, ln in enumerate(lines) if re.match(rf"^chapter\s+{chapter}\s*$", ln.strip())]
    if not starts:
        raise SystemExit(f"chapter {chapter} body not found")
    start = starts[-1]
    nxt = [i for i, ln in enumerate(lines) if re.match(rf"^chapter\s+{chapter + 1}\s*$", ln.strip())]
    end = nxt[-1] if nxt else len(lines)
    return start, end


def find_heading(lines, heading, lo, hi):
    target = re.sub(r"\s+", " ", norm(heading)).strip().lower()
    for i in range(lo, hi):
        window = re.sub(r"\s+", " ", norm(" ".join(lines[i:i + 4]))).strip().lower()
        window = window.split(".")[0]
        if window.startswith(target[:60]):
            return i
    return None


TERM_PUNCT = ".!?:;,"


def is_heading_line(s: str) -> bool:
    """True for a converted *heading* line inside the prose stream.

    Headings survive the PDF->markdown conversion as short lines without a
    terminal full stop.  Prose lines are wrapped mid-sentence too, so the
    discriminator is capitalisation: a heading is mostly Title Case, a wrapped
    prose line is mostly lowercase.
    """
    s = s.strip()
    if not s or len(s) > 90:
        return False
    if s.endswith((".", "!", "?", "...", ":")):
        return False
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-']*", s)]
    if not words or len(words) > 12:
        return False
    caps = sum(1 for w in words if w[0].isupper())
    return caps / len(words) >= 0.75


def heading_lines(lines, lo, hi) -> set[int]:
    """Line indexes (absolute) that belong to heading runs."""
    marks: set[int] = set()
    i = lo
    while i < hi:
        if is_heading_line(lines[i]):
            j = i
            while j < hi and is_heading_line(lines[j]):
                j += 1
            # a heading run must be followed by prose, not by the end of the block
            if j < hi:
                for k in range(i, j):
                    marks.add(k)
            i = j
        else:
            i += 1
    return marks


def is_cellish(s: str) -> bool:
    """A line that looks like a table cell or a heading fragment, not prose."""
    s = s.strip()
    if not s or len(s) > 90 or s.endswith("-"):
        return False
    if s.endswith((".", "!", "?", "...", ":")):
        return False
    words = re.findall(r"[A-Za-z][A-Za-z\-']*", s)
    lower = [w for w in words if w[0].islower()]
    return len(lower) <= 5


def junk_lines(lines, lo, hi) -> set[int]:
    """Line indexes that are headings, table cells or column values.

    The PDF->markdown conversion emits table bodies and headings as standalone
    lines inside the prose stream.  A *run* of at least two cellish lines is a
    table; a single cellish line is a heading only if it is Title Case (wrapped
    prose lines are mostly lowercase, so they are kept).
    """
    junk: set[int] = set()
    i = lo
    while i < hi:
        if is_cellish(lines[i]):
            j = i
            while j < hi and is_cellish(lines[j]):
                j += 1
            if j - i >= 2:
                junk.update(range(i, j))
            elif is_heading_line(lines[i]):
                junk.add(i)
            i = j
        else:
            i += 1
    return junk


def stream_section(lines, lo, hi, page_map, skip: set[int] | None = None) -> list[dict]:
    """Flatten a line range into {page, text} line-group records.

    In this markdown a bare page number is emitted *before* the content of that
    page, so the page of a line is the most recent marker at or above it.
    A line that ends with ``-`` is a hyphenated word split by the conversion:
    the hyphen is dropped and the next line is appended without a space.
    """
    chunks: list[tuple[int | None, str]] = []
    page = page_map.get(lo - 1)
    buf = ""
    buf_page = None
    pending_hyphen = False

    skip = skip or set()
    for i in range(lo, hi):
        s = lines[i].strip()
        if PAGE_NO.match(s):
            page = int(s)
            continue
        if i in skip:
            continue
        if not s or s == "```" or RUNNING.match(s):
            continue
        if s.startswith("Table "):
            continue                 # table caption; the rows are skipped via ``skip``
        if s.startswith("Figure ") and is_cellish(s):
            continue                 # figure caption without a verb
        if buf_page is None:
            buf_page = page
        if pending_hyphen:
            buf += s
            pending_hyphen = False
        else:
            buf += (" " if buf else "") + s
        if s.endswith("-") and not s.endswith("--"):
            buf = buf[:-1]
            pending_hyphen = True
            continue
        if re.search(r"[.!?][\"'\u201d]?$", s):
            chunks.append((buf_page, re.sub(r"\s{2,}", " ", buf).strip()))
            buf, buf_page = "", None
    if buf.strip():
        chunks.append((buf_page, re.sub(r"\s{2,}", " ", buf).strip()))
    return [{"page": p, "text": t} for p, t in chunks if t]


def apply_repairs(records: list[dict]) -> tuple[list[dict], int]:
    """Apply the documented converter repairs; return records and hit count."""
    hits = 0
    out = []
    for rec in records:
        text = rec["text"]
        for pattern, repl in REPAIRS:
            text, n = pattern.subn(repl, text)
            hits += n
        out.append({"page": rec["page"], "text": text})
    return out, hits


def sentences(records: list[dict]) -> list[dict]:
    """Split line groups into sentences; drop conversion fragments.

    A fragment that starts lowercase or does not end with sentence punctuation
    is a piece cut by a page break or a table block, so it is not quoted.
    """
    out: list[dict] = []
    for rec in records:
        for piece in SENT_END.split(rec["text"]):
            piece = re.sub(r"\s{2,}", " ", piece).strip()
            if len(piece.split()) < 4:
                continue
            if not piece[0].isupper() and piece[0] not in ('"', "(", "'"):
                continue
            if not re.search(r"[.!?][\"'\u201d]?$", piece):
                continue
            if any(p.search(piece) for p in DROP_PATTERNS):
                continue
            # a converted heading can end with a full stop.  Headings are short
            # and Title Case; prose sentences have lowercase function words.
            words = piece.split()
            caps = sum(1 for w in words if w[0].isupper())
            if len(words) <= 12 and caps / len(words) >= 0.5:
                continue
            out.append({"page": rec["page"], "text": piece})
    return out


def main() -> int:
    lines = load_lines()
    lo, hi = body_range(lines, 45)

    # printed page map for the body range
    pages: dict[int, int] = {}
    cur = None
    for i, ln in enumerate(lines):
        if PAGE_NO.match(ln.strip()):
            cur = int(ln.strip())
        pages[i] = cur

    out = {"source": MD.name, "chapter": 45,
           "note": "verbatim sentences from the PDF->markdown conversion; line wrapping undone only",
           "sections": {}}
    for key, (heading, stops) in SECTIONS.items():
        start = find_heading(lines, heading, lo, hi)
        if start is None:
            out["sections"][key] = {"heading": heading, "found": False, "sentences": []}
            print("MISSING", key)
            continue
        end = hi
        for stop in stops:
            j = find_heading(lines, stop, start + 1, hi)
            if j is not None:
                end = min(end, j)
        recs = stream_section(lines, start + 1, end, pages,
                             skip=junk_lines(lines, start + 1, end))
        recs, repair_hits = apply_repairs(recs)
        sents = sentences(recs)
        pgs = [s["page"] for s in sents if s["page"]]
        out["sections"][key] = {
            "heading": heading,
            "found": True,
            "start_line": start + 1,
            "end_line": end,
            "page_start": min(pgs) if pgs else None,
            "page_end": max(pgs) if pgs else None,
            "sentences": sents,
            "repair_hits": repair_hits,
        }
        print(f"{key:20s} lines {start + 1}-{end}  sentences {len(sents):3d}  "
              f"pages {min(pgs) if pgs else '?'}-{max(pgs) if pgs else '?'}")
    dump_json(OUT, out)
    print("written", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

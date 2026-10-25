"""Page-anchored Guyton excerpts for session 10 (cerebral cortex, higher functions).

Session 10 is Chapter 57 of the textbook: the histology of the neocortex, the
thalamocortical relations, the primary/secondary/association areas, the
parieto-occipitotemporal area (spatial analysis, Wernicke, angular gyrus,
naming), the prefrontal and limbic association areas, face recognition,
aphasia and the corpus callosum.  The memory sections of the same chapter
(«Thoughts, Consciousness, and Memory» onward) are deliberately **not**
included: they belong to session 11 (limbic system and memory).

Only the shared helpers of ``guyton_excerpts.py`` are used; the printed page of
every sentence is kept and no wording is rewritten.

Output: ``work/references/guyton_s10_excerpts.json``
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guyton_excerpts import (  # noqa: E402
    MD, apply_repairs, body_range, dump_json, find_heading, junk_lines, load_lines,
    sentences, stream_section,
)

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s10_excerpts.json"

CHAPTER_PAGES = {57: (696, 708)}

# key -> (chapter, heading, [stop headings], floor line)
SECTIONS = {
    "s10_anatomy": (57, "Physiologic Anatomy of the Cerebral",
                    ["Anatomical and Functional Relations of the"], 78190),
    "s10_thalamus": (57, "Anatomical and Functional Relations of the",
                     ["Functions of Specific Cortical Areas"], 78280),
    "s10_areas": (57, "Functions of Specific Cortical Areas",
                  ["Association Areas"], 78300),
    "s10_association": (57, "Association Areas",
                        ["Parieto-occipitotemporal Association Area"], 78395),
    "s10_parieto": (57, "Parieto-occipitotemporal Association Area",
                    ["Prefrontal Association Area"], 78415),
    "s10_prefrontal": (57, "Prefrontal Association Area",
                       ["Broca\u2019s Area Provides the Neural Circuitry for Word"], 78535),
    "s10_broca": (57, "Broca\u2019s Area Provides the Neural Circuitry for Word",
                  ["Limbic Association Area"], 78565),
    "s10_limbic": (57, "Limbic Association Area",
                   ["Area for Recognition of Faces"], 78580),
    "s10_face": (57, "Area for Recognition of Faces",
                 ["Comprehensive Interpretative Function of the"], 78595),
    "s10_wernicke": (57, "Comprehensive Interpretative Function of the",
                     ["Angular Gyrus\u2014Interpretation of Visual Infor"], 78615),
    "s10_angular": (57, "Angular Gyrus\u2014Interpretation of Visual Infor",
                    ["Concept of the Dominant Hemisphere"], 78675),
    "s10_dominant": (57, "Concept of the Dominant Hemisphere",
                     ["Role of Language in the Function of Wernicke\u2019s Area"], 78690),
    "s10_language": (57, "Role of Language in the Function of Wernicke\u2019s Area",
                     ["Higher Intellectual Functions of the Prefrontal"], 78770),
    "s10_intellect": (57, "Higher Intellectual Functions of the Prefrontal",
                      ["Function of the Brain in Communication"], 78820),
    "s10_communication": (57, "Function of the Brain in Communication",
                          ["Function of the Corpus Callosum and"], 78950),
    "s10_callosum": (57, "Function of the Corpus Callosum and",
                     ["Thoughts, Consciousness, and Memory"], 79095),
}


def main() -> int:
    lines = load_lines()
    pages = _page_map(lines)
    cache: dict[int, tuple[int, int]] = {}
    out = {"source": MD.name,
           "note": "verbatim sentences from the PDF->markdown conversion; line wrapping undone only",
           "sections": {}}
    for key, (chapter, heading, stops, floor) in SECTIONS.items():
        if chapter not in cache:
            cache[chapter] = body_range(lines, chapter)
        lo, hi = cache[chapter]
        start = find_heading(lines, heading, max(lo, floor), hi)
        if start is None:
            out["sections"][key] = {"heading": heading, "chapter": chapter,
                                    "found": False, "sentences": []}
            print("MISSING", key, "::", heading[:60])
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
        page_lo, page_hi = CHAPTER_PAGES[chapter]
        sents = [x for x in sents
                 if x.get("page") and page_lo <= x["page"] <= page_hi
                 and " Figure 57" not in x["text"]]
        pgs = [s["page"] for s in sents if s["page"]]
        out["sections"][key] = {
            "heading": heading, "chapter": chapter, "found": True,
            "page_start": min(pgs) if pgs else None,
            "page_end": max(pgs) if pgs else None,
            "sentences": sents, "repair_hits": repair_hits,
        }
        print(f"{key:22s} ch{chapter} sentences {len(sents):3d}  "
              f"pages {min(pgs) if pgs else '?'}-{max(pgs) if pgs else '?'}")
    dump_json(OUT, out)
    print("written", OUT)
    return 0


def _page_map(lines):
    page_no = re.compile(r"^\d{1,3}$")
    cur = None
    out = {}
    for i, ln in enumerate(lines):
        s = ln.strip()
        if page_no.match(s):
            cur = int(s)
        out[i] = cur
    return out


if __name__ == "__main__":
    raise SystemExit(main())

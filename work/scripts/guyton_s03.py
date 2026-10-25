"""Page-anchored Guyton excerpts for session 3 (sensory receptors, ascending pathways).

Session 3 covers sensory transduction, receptor potential, adaptation, the five
receptor classes, tactile receptors and proprioception, plus the ascending
pathways (dorsal column-medial lemniscus, anterolateral) and dermatomes.

Sources in the 12th edition:

* **Ch. 46** — Types of sensory receptors, differential sensitivity, the
  "labeled line" principle, receptor potentials, adaptation (pp. 559-570).
* **Ch. 47** — Classification of somatic senses, tactile sensations, dorsal
  column-medial lemniscal system, position senses, dermatomes (pp. 571-582).

Only the shared helpers of ``guyton_excerpts.py`` are used: wrapping is undone,
table/heading junk is skipped and the printed page of every sentence is kept.
No wording is added or rewritten here.

Output: ``work/references/guyton_s03_excerpts.json``
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guyton_excerpts import (  # noqa: E402
    MD, PAGE_NO, apply_repairs, body_range, dump_json, find_heading, junk_lines,
    load_lines, sentences, stream_section,
)

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s03_excerpts.json"

# key -> (chapter, heading, [stop headings])
SECTIONS = {
    "somatic_classes": (
        47, "Classification of Somatic Senses",
        ["Detection and Transmission"]),
    "tactile_interrelations": (
        47, "Interrelations Among the Tactile Sensations",
        ["Dorsal Column—Medial Lemniscal System"]),
    "differential_sensitivity": (
        46, "Differential Sensitivity of Receptors",
        ["Modality of Sensation"]),
    "labeled_line": (
        46, "Modality of Sensation—The “Labeled Line”",
        ["Transduction of Sensory Stimuli"]),
    "receptor_potential": (
        46, "Local Electrical Currents at Nerve",
        ["Maximum Receptor Potential Amplitude"]),
    "max_receptor_potential": (
        46, "Maximum Receptor Potential Amplitude",
        ["Adaptation of Receptors"]),
    "adaptation": (
        46, "Mechanisms by Which Receptors Adapt",
        ["Slowly Adapting Receptors Detect"]),
    "tonic_phasic": (
        46, "Slowly Adapting Receptors Detect",
        ["Nerve Fibers That Transmit"]),
    "dorsal_column": (
        47, "Dorsal Column—Medial Lemniscal Pathway",
        ["Somatosensory Cortex"]),
    "dorsal_overall": (
        47, "Overall Characteristics of Signal Transmission",
        ["Position Senses"]),
    "position_sense": (
        47, "Position Senses",
        ["Dorsal Column–Medial Lemniscal Pathway. Referring"]),
    "dermatomes": (
        47, "Segmental Fields of Sensation—Dermatomes",
        ["Bibliography"]),
}


def main() -> int:
    lines = load_lines()
    cache: dict[int, tuple[int, int]] = {}

    pages: dict[int, int] = {}
    cur = None
    for i, ln in enumerate(lines):
        if PAGE_NO.match(ln.strip()):
            cur = int(ln.strip())
        pages[i] = cur

    out = {"source": MD.name,
           "note": "verbatim sentences from the PDF->markdown conversion; line wrapping undone only",
           "sections": {}}
    for key, (chapter, heading, stops) in SECTIONS.items():
        if chapter not in cache:
            cache[chapter] = body_range(lines, chapter)
        lo, hi = cache[chapter]
        start = find_heading(lines, heading, lo, hi)
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
        pgs = [s["page"] for s in sents if s["page"]]
        out["sections"][key] = {
            "heading": heading,
            "chapter": chapter,
            "found": True,
            "page_start": min(pgs) if pgs else None,
            "page_end": max(pgs) if pgs else None,
            "sentences": sents,
            "repair_hits": repair_hits,
        }
        print(f"{key:24s} ch{chapter} sentences {len(sents):3d}  "
              f"pages {min(pgs) if pgs else '?'}-{max(pgs) if pgs else '?'}")
    dump_json(OUT, out)
    print("written", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

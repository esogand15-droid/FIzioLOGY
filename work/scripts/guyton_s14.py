# -*- coding: utf-8 -*-
"""Page-anchored Guyton excerpts for session 14 (neurologic examination).

The handout of this session is a clinical examination text; Guyton has no
chapter on the examination itself.  The excerpts therefore come from the
physiologic sections that each examination rests on:

  * chapter 51 — visual fields / perimetry, lesions of the optic pathway,
    control of the pupillary diameter, autonomic control of accommodation
  * chapter 52 — hearing abnormalities (conductive vs perceptive deafness)
  * chapter 53 — sense of taste and sense of smell (cranial nerves VII, IX, X
    and the olfactory pathway)
  * chapter 55 — knee jerk and other muscle jerks, clinical applications of the
    stretch reflex, spasticity, lesions of the motor cortex / corticospinal
    tract, stepping and walking movements
  * chapter 56 — clinical abnormalities of the cerebellum
  * chapter 57 — memory

Most of those sections were already extracted for sessions 5, 6, 7 and 9.  This
script *re-uses* those verbatim records (same sentences, same page anchors,
nothing re-typed) and extracts the three new ones (taste, smell, memory) from
the same markdown source.

Output: ``work/references/guyton_s14_excerpts.json``
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guyton_excerpts import (  # noqa: E402
    MD, apply_repairs, body_range, dump_json, find_heading, junk_lines, load_lines,
    sentences, stream_section,
)

REPO = Path(__file__).resolve().parents[2]
REFS = REPO / "work" / "references"
OUT = REFS / "guyton_s14_excerpts.json"

# key -> (source file, key inside that file)
REUSE = {
    "s14_perimetry": ("guyton_s05_excerpts.json", "perimetry"),
    "s14_vision_lesions": ("guyton_s05_excerpts.json", "lesions"),
    "s14_pupil": ("guyton_s05_excerpts.json", "pupil"),
    "s14_accommodation": ("guyton_s05_excerpts.json", "accommodation"),
    "s14_hearing": ("guyton_s06_excerpts.json", "s6_abnormalities"),
    "s14_knee_jerk": ("guyton_s07_excerpts.json", "s7_knee_jerk"),
    "s14_stretch_clinical": ("guyton_s07_excerpts.json", "s7_clinical_stretch"),
    "s14_spasticity": ("guyton_s07_excerpts.json", "s7_spasticity"),
    "s14_motor_lesions": ("guyton_s07_excerpts.json", "s7_lesions"),
    "s14_stepping": ("guyton_s07_excerpts.json", "s7_stepping"),
    "s14_cerebellar": ("guyton_s09_excerpts.json", "s9_clinical"),
}

# key -> (chapter, heading, stops)
NEW = {
    "s14_taste": (53, "Sense of Taste", ["Sense of Smell"]),
    "s14_smell": (53, "Sense of Smell", ["Olfactory Membrane"]),
    "s14_smell_membrane": (53, "Olfactory Membrane", ["Olfactory Cells."]),
    "s14_sensory_paths": (47, "Sensory Pathways for Transmitting Somatic",
                          ["Sensory Cortex"]),
    "s14_dermatomes": (47, "Segmental Fields of Sensation—Dermatomes",
                       ["Somatic Sensations: II"]),
    "s14_sensory_area": (47, "Somatosensory Cortex",
                         ["Layers of the Somatosensory Cortex"]),
    "s14_swallow": (63, "Swallowing (Deglutition)", ["Esophagus"]),
    "s14_memory": (57, "Memory—Roles of Synaptic Facilitation",
                   ["Memory Based on Chemical Changes in the"]),
}


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


def main() -> int:
    lines = load_lines()
    pages = _page_map(lines)
    out = {"source": MD.name,
           "note": "verbatim sentences from the PDF->markdown conversion; line wrapping "
                   "undone only; sections reused from earlier sessions keep their records",
           "sections": {}}

    for key, (fname, old) in REUSE.items():
        sec = json.loads((REFS / fname).read_text(encoding="utf-8"))["sections"][old]
        out["sections"][key] = sec
        print(f"reuse {key:20s} ch{sec.get('chapter')} sentences {len(sec['sentences']):3d}")

    for key, (chapter, heading, stops) in NEW.items():
        lo, hi = body_range(lines, chapter)
        start = find_heading(lines, heading, lo, hi)
        if start is None:
            out["sections"][key] = {"heading": heading, "chapter": chapter,
                                    "found": False, "sentences": []}
            print("MISSING", key, "::", heading)
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
        # page bounds come from the section itself, not from the whole chapter:
        # the chapter marker also appears in the table of contents
        first_pg = next((pages[i] for i in range(start, hi) if pages.get(i)), None)
        last_pg = next((pages[i] for i in range(end - 1, start, -1) if pages.get(i)), None)
        page_lo, page_hi = first_pg, last_pg
        sents = [x for x in sents
                 if x.get("page") and page_lo <= x["page"] <= page_hi
                 and f"Figure {chapter}" not in x["text"]]
        pgs = [s["page"] for s in sents if s["page"]]
        out["sections"][key] = {
            "heading": heading, "chapter": chapter, "found": True,
            "page_start": min(pgs) if pgs else None,
            "page_end": max(pgs) if pgs else None,
            "sentences": sents, "repair_hits": repair_hits,
        }
        print(f"new   {key:20s} ch{chapter} sentences {len(sents):3d}  "
              f"pages {min(pgs) if pgs else '?'}-{max(pgs) if pgs else '?'}")

    dump_json(OUT, out)
    print("written", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

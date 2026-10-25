"""Page-anchored Guyton excerpts for session 13 (autonomic nervous system).

Session 13 is Chapter 60: general organisation, sympathetic and parasympathetic
anatomy, cholinergic and adrenergic fibres, transmitter synthesis and removal,
receptors (muscarinic/nicotinic, alpha/beta), the organ-by-organ effects, the
adrenal medullae, tone, denervation supersensitivity, autonomic reflexes, mass
discharge and the brain-stem control of autonomic centres.

Output: ``work/references/guyton_s13_excerpts.json``
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

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s13_excerpts.json"

CHAPTER_PAGES = {60: (729, 742)}

SECTIONS = {
    "s13_general": (60, "General Organization of the Autonomic",
                    ["Physiologic Anatomy of the Sympathetic Nervous System"], 82120),
    "s13_symp_anat": (60, "Physiologic Anatomy of the Sympathetic Nervous System",
                      ["Physiologic Anatomy of the Parasympathetic"], 82140),
    "s13_para_anat": (60, "Physiologic Anatomy of the Parasympathetic",
                      ["Cholinergic and Adrenergic Fibers"], 82255),
    "s13_transmitters": (60, "Cholinergic and Adrenergic Fibers",
                         ["Mechanisms of Transmitter Secretion"], 82366),
    "s13_secretion": (60, "Mechanisms of Transmitter Secretion",
                      ["Receptors on the Effector Organs"], 82440),
    "s13_receptors": (60, "Receptors on the Effector Organs",
                      ["Excitatory and Inhibitory Actions of Sympathetic"], 82543),
    "s13_effects": (60, "Effects of Sympathetic and Parasympathetic Stimulation",
                    ["Function of the Adrenal Medullae"], 82818),
    "s13_adrenal": (60, "Function of the Adrenal Medullae",
                    ["Relation of Stimulus Rate"], 82967),
    "s13_tone": (60, "Sympathetic and Parasympathetic “Tone”",
                 ["Effect of Loss of Sympathetic or Parasympathetic"], 83067),
    "s13_denervation": (60, "Effect of Loss of Sympathetic or Parasympathetic",
                        ["Autonomic Reflexes"], 83110),
    "s13_reflexes": (60, "Autonomic Reflexes",
                     ["Stimulation of Discrete Organs"], 83191),
    "s13_mass": (60, "Stimulation of Discrete Organs",
                 ["“Alarm” or “Stress” Response"], 83249),
    "s13_alarm": (60, "“Alarm” or “Stress” Response of the Sympathetic",
                  ["Medullary, Pontine, and Mesencephalic Control"], 83303),
    "s13_brainstem": (60, "Medullary, Pontine, and Mesencephalic Control",
                      ["Bibliography"], 83348),
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
    cache = {}
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
                 and f" Figure {chapter}" not in x["text"]]
        pgs = [s["page"] for s in sents if s["page"]]
        out["sections"][key] = {
            "heading": heading, "chapter": chapter, "found": True,
            "page_start": min(pgs) if pgs else None,
            "page_end": max(pgs) if pgs else None,
            "sentences": sents, "repair_hits": repair_hits,
        }
        print(f"{key:16s} ch{chapter} sentences {len(sents):3d}  "
              f"pages {min(pgs) if pgs else '?'}-{max(pgs) if pgs else '?'}")
    dump_json(OUT, out)
    print("written", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

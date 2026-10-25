"""Page-anchored Guyton excerpts for session 2 (synapses, potentials, circuits).

Session 2 of the course covers synaptic transmission, postsynaptic potentials,
electrotonic conduction, the action potential, nerve-fibre classes, presynaptic
facilitation/inhibition and neuronal circuits.  In the 12th edition these sit in
two chapters:

* **Ch. 45** — synapses, calcium-dependent release, EPSP/IPSP, presynaptic
  inhibition, special functions of dendrites (printed pages 547-552).
* **Ch. 46** — nerve-fibre classification, neuronal pools, divergence /
  convergence, afterdischarge, reverberating circuits, synaptic fatigue
  (printed pages 559-570).

The helper functions of ``guyton_excerpts.py`` are reused unchanged: line
wrapping is undone, table/heading junk is skipped and every sentence keeps the
printed page it came from.  No wording is added or rewritten here.

Output: ``work/references/guyton_s02_excerpts.json``
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guyton_excerpts import (  # noqa: E402
    MD, PAGE_NO, apply_repairs, body_range, dump_json, find_heading, junk_lines,
    load_lines, sentences, stream_section,
)

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s02_excerpts.json"

# key -> (chapter, heading, [stop headings])
SECTIONS = {
    "synapse_anatomy": (
        45, "Central Nervous System Synapses",
        ["Action of the Transmitter Substance on the"]),
    "calcium_release": (
        45, "Mechanism by Which an Action Potential Causes Transmitter Release "
            "from the Presynaptic Terminals—Role of Calcium Ions",
        ["Action of the Transmitter Substance on the"]),
    "receptor_proteins": (
        45, "Action of the Transmitter Substance on the Postsynaptic Neuron",
        ["Excitatory or Inhibitory Receptors in the"]),
    "excitation_inhibition": (
        45, "Excitatory or Inhibitory Receptors in the",
        ["Electrical Events During Neuronal Excitation"]),
    "epsp": (
        45, "Electrical Events During Neuronal Excitation",
        ["Electrical Events During Neuronal Inhibition"]),
    "ipsp": (
        45, "Electrical Events During Neuronal Inhibition",
        ["Presynaptic Inhibition"]),
    "presynaptic_inhibition": (
        45, "Presynaptic Inhibition",
        ["Time Course of Postsynaptic Potentials"]),
    "dendrites": (
        45, "Special Functions of Dendrites for Exciting Neurons",
        ["Bibliography"]),
    "nerve_fibers": (
        46, "Nerve Fibers That Transmit Different Types of",
        ["Group Ia"]),
    "neuronal_pools": (
        46, "Relaying of Signals Through Neuronal Pools",
        ["Divergence of Signals Passing"]),
    "divergence": (
        46, "Divergence of Signals Passing",
        ["Convergence of Signals"]),
    "convergence": (
        46, "Convergence of Signals",
        ["Neuronal Circuit with both Excitatory"]),
    "afterdischarge": (
        46, "Prolongation of a Signal by a Neuronal",
        ["Continuous Signal Output from"]),
    "reverberation": (
        46, "Continuous Signal Output from",
        ["Rhythmical Signal Output"]),
    "synaptic_fatigue": (
        46, "Synaptic Fatigue as a Means of Stabilizing",
        ["Automatic Short-Term Adjustment of Pathway"]),
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

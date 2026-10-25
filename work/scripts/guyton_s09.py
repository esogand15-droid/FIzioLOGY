"""Page-anchored Guyton excerpts for session 9 (cerebellum and basal ganglia).

Session 9 is Chapter 56 of the textbook (printed pages 681-695): the functional
areas of the cerebellum, its cortical circuit, the deep nuclei, the climbing and
mossy inputs, the turn-on/turn-off signals, learning in the Purkinje cells, the
three functional divisions (vestibulo-, spino- and cerebrocerebellum), cerebellar
clinical signs, and then the basal ganglia: the putamen and caudate circuits, the
direct and indirect pathways, neurotransmitters and Parkinson's disease.

Only the shared helpers of ``guyton_excerpts.py`` are used; the printed page of
every sentence is kept and no wording is rewritten.

Output: ``work/references/guyton_s09_excerpts.json``
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

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s09_excerpts.json"

CHAPTER_PAGES = {56: (681, 695)}

# key -> (chapter, heading, [stop headings], floor line)
SECTIONS = {
    "s9_intro": (56, "Cerebellum and Its Motor Functions",
                 ["Anatomical Functional Areas of the Cerebellum"], 76405),
    "s9_areas": (56, "Anatomical Functional Areas of the Cerebellum",
                 ["Topographical Representation of the Body in the Vermis"], 76455),
    "s9_topography": (56, "Topographical Representation of the Body in the Vermis",
                      ["Neuronal Circuit of the Cerebellum"], 76499),
    "s9_circuit": (56, "Neuronal Circuit of the Cerebellum",
                   ["Output Signals from the Cerebellum"], 76526),
    "s9_deep_nuclei": (56, "Deep Cerebellar Nuclei and the Efferent",
                       ["Functional Unit of the Cerebellar Cortex"], 76650),
    "s9_cortex_unit": (56, "Functional Unit of the Cerebellar Cortex",
                       ["Purkinje Cells and Deep Nuclear Cells Fire Continuously"], 76760),
    "s9_firing": (56, "Purkinje Cells and Deep Nuclear Cells Fire Continuously",
                  ["Output Signals from the Cerebellum"], 76880),
    "s9_output": (56, "Output Signals from the Cerebellum",
                  ["The Purkinje Cells \u201cLearn\u201d to Correct Motor Errors"], 76928),
    "s9_learn": (56, "The Purkinje Cells \u201cLearn\u201d to Correct Motor Errors",
                 ["Function of the Cerebellum in Overall"], 77010),
    "s9_overall": (56, "Function of the Cerebellum in Overall",
                   ["Vestibulocerebellum Functions in Association"], 77050),
    "s9_vestibulocerebellum": (56, "Vestibulocerebellum Functions in Association",
                               ["Movements by Way of the Intermediate Cerebellar"], 77078),
    "s9_spinocerebellum": (56, "Movements by Way of the Intermediate Cerebellar",
                           ["Cerebellar Control of Ballistic Movements"], 77138),
    "s9_overshoot": (56, "Function of the Cerebellum to Prevent Overshoot",
                     ["Cerebellar Control of Ballistic Movements"], 77195),
    "s9_cerebrocerebellum": (56, "Cerebrocerebellum\u2014Function of the Large Lateral",
                             ["Extramotor Predictive Functions"], 77278),
    "s9_clinical": (56, "Clinical Abnormalities of the Cerebellum",
                    ["Basal Ganglia\u2014Their Motor Functions"], 77388),
    "s9_bg_intro": (56, "Basal Ganglia\u2014Their Motor Functions",
                    ["Function of the Basal Ganglia in Executing"], 77484),
    "s9_putamen": (56, "Function of the Basal Ganglia in Executing",
                   ["Neural Pathways of the Putamen Circuit"], 77520),
    "s9_caudate": (56, "Role of the Basal Ganglia for Cognitive Control",
                   ["Function of the Basal Ganglia to Change the"], 77630),
    "s9_gain": (56, "Function of the Basal Ganglia to Change the",
                ["Functions of Specific Neurotransmitter"], 77712),
    "s9_nt": (56, "Functions of Specific Neurotransmitter",
              ["Parkinson\u2019s Disease"], 77764),
    "s9_parkinson": (56, "Parkinson\u2019s Disease",
                     ["Treatment by Destroying Part"], 77858),
    "s9_bg_summary": (56, "Associated Functions of the Basal Ganglia",
                      ["Bibliography"], 78080),
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
                 and " Figure 56" not in x["text"]]
        pgs = [s["page"] for s in sents if s["page"]]
        out["sections"][key] = {
            "heading": heading, "chapter": chapter, "found": True,
            "page_start": min(pgs) if pgs else None,
            "page_end": max(pgs) if pgs else None,
            "sentences": sents, "repair_hits": repair_hits,
        }
        print(f"{key:24s} ch{chapter} sentences {len(sents):3d}  "
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

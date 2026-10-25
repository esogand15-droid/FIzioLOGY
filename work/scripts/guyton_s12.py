"""Page-anchored Guyton excerpts for session 12 (states of brain activity).

Two chapters are used:

* Chapter 58 — only the *activating-driving* part (reticular excitatory and
  inhibitory areas, the thalamus as distribution centre, the neurohormonal
  systems: locus ceruleus, substantia nigra, raphe nuclei, cholinergic
  gigantocellular neurons).  The limbic and hypothalamic part of the same
  chapter belongs to session 11 and is not repeated here.
* Chapter 59 — sleep, brain waves, the electroencephalogram and epilepsy.

Only the shared helpers of ``guyton_excerpts.py`` are used; the printed page of
every sentence is kept and no wording is rewritten.

Output: ``work/references/guyton_s12_excerpts.json``
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

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s12_excerpts.json"

CHAPTER_PAGES = {58: (706, 720), 59: (721, 731)}

# key -> (chapter, heading, [stop headings], floor line, page filter)
SECTIONS = {
    "s12_reticular": (58, "Control of Cerebral Activity by Continuous",
                      ["Neurohormonal Control of Brain Activity"], 79805),
    "s12_neurohormonal": (58, "Neurohormonal Control of Brain Activity",
                          ["Limbic System"], 79915),
    "s12_sleepdef": (59, "Sleep",
                     ["Slow-Wave Sleep"], 81084),
    "s12_slowwave": (59, "Slow-Wave Sleep",
                     ["REM Sleep (Paradoxical Sleep"], 81122),
    "s12_rem": (59, "REM Sleep (Paradoxical Sleep",
                ["Basic Theories of Sleep"], 81142),
    "s12_sleeptheory": (59, "Basic Theories of Sleep",
                        ["Brain Waves"], 81184),
    "s12_brainwaves": (59, "Brain Waves",
                       ["Origin of Brain Waves"], 81380),
    "s12_waveorigin": (59, "Origin of Brain Waves",
                       ["Effect of Varying Levels of Cerebral Activity"], 81452),
    "s12_eeglevels": (59, "Effect of Varying Levels of Cerebral Activity",
                      ["Changes in the EEG at Different Stages of Wakefulness"], 81504),
    "s12_eegstages": (59, "Changes in the EEG at Different Stages of Wakefulness",
                      ["Epilepsy"], 81558),
    "s12_epilepsy": (59, "Epilepsy",
                     ["Psychotic Behavior and Dementia"], 81587),
    "s12_psychoses": (59, "Psychotic Behavior and Dementia",
                      ["Alzheimer’s Disease—Amyloid Plaques", "Alzheimer's Disease—Amyloid Plaques"], 81806),
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
        print(f"{key:18s} ch{chapter} sentences {len(sents):3d}  "
              f"pages {min(pgs) if pgs else '?'}-{max(pgs) if pgs else '?'}")
    dump_json(OUT, out)
    print("written", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

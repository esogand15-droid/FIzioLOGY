"""Page-anchored Guyton excerpts for session 8 (brain stem and vestibular control).

Session 8 is the brain-stem / equilibrium lecture: the reticular nuclei of the
pons and medulla and their antagonism, the pontine and medullary reticulospinal
tracts, the vestibular nuclei and the excitation of antigravity muscles,
decerebrate rigidity, the vestibular apparatus (cochlea/utricle/saccule and the
semicircular ducts), the macula and the otolithic membrane, linear acceleration,
head rotation and the crista ampullaris, the vestibulo-ocular mechanism that
stabilises the eyes, the other factors of equilibrium (proprioception, vision,
air pressure) and the connections of the vestibular nerves with the rest of the
CNS.

All of this is the last part of **Chapter 55** (printed pages 673-679) of the
file in ``رفرنس گایتون``. The first part of the same chapter (cortical motor
areas and the descending tracts, pages 667-673) belongs to session 7 and is not
repeated here; the cerebellum and basal ganglia (Chapter 56) are session 9.

Only the shared helpers of ``guyton_excerpts.py`` are used: wrapping is undone,
table/heading junk is skipped and the printed page of every sentence is kept.
No wording is added or rewritten here.

Output: ``work/references/guyton_s08_excerpts.json``
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guyton_excerpts import (  # noqa: E402
    MD, body_range, dump_json, find_heading, junk_lines, load_lines, sentences,
    stream_section, apply_repairs,
)

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s08_excerpts.json"

CHAPTER_PAGES = {55: (673, 679)}

# key -> (chapter, heading, [stop headings], floor line)
# keys are prefixed s8_ so the merged gq() index of blocks_common never
# collides with earlier sessions.  The floor is the line of the heading minus a
# few lines; it keeps a section from matching the same phrase in running text.
SECTIONS = {
    "s8_brainstem": (
        55, "Role of the Brain Stem in Controlling",
        ["Excitatory-Inhibitory Antagonism"], 75664),
    "s8_reticular_antagonism": (
        55, "Excitatory-Inhibitory Antagonism Between",
        ["Role of the Vestibular Nuclei to Excite"], 75692),
    "s8_vestibular_antigravity": (
        55, "Role of the Vestibular Nuclei to Excite",
        ["The Decerebrate Animal Develops"], 75763),
    "s8_decerebrate": (
        55, "The Decerebrate Animal Develops Spastic Rigidity",
        ["Vestibular Sensations and Maintenance"], 75779),
    "s8_vestibular_intro": (
        55, "Vestibular Sensations and Maintenance",
        ["Vestibular Apparatus"], 75797),
    "s8_vestibular_apparatus": (
        55, "Vestibular Apparatus",
        ["Saccule for Detecting"], 75799),
    "s8_saccule": (
        55, "Saccule for Detecting",
        ["Function of the Utricle and Saccule"], 75823),
    "s8_utricle_saccule": (
        55, "Function of the Utricle and Saccule",
        ["Detection of Linear Acceleration"], 75997),
    "s8_linear_acceleration": (
        55, "Detection of Linear Acceleration",
        ["Detection of Head Rotation"], 76014),
    "s8_rotation": (
        55, "Detection of Head Rotation",
        ["Vestibular Mechanisms for Stabilizing"], 76057),
    "s8_eye_stabilization": (
        55, "Vestibular Mechanisms for Stabilizing",
        ["Other Factors Concerned with Equilibrium"], 76143),
    "s8_other_factors": (
        55, "Other Factors Concerned with Equilibrium",
        ["Neuronal Connections of the Vestibular"], 76158),
    "s8_connections": (
        55, "Neuronal Connections of the Vestibular",
        ["Functions of Brain Stem Nuclei"], 76232),
    "s8_stereotyped": (
        55, "Functions of Brain Stem Nuclei",
        ["Bibliography"], 76280),
}


def main() -> int:
    lines = load_lines()
    pages = _page_map(lines)
    cache: dict[int, tuple[int, int]] = {}
    out = {"source": MD.name,
           "note": "verbatim sentences from the PDF->markdown conversion; line wrapping undone only",
           "sections": {}}
    for key, spec in SECTIONS.items():
        chapter, heading, stops, floor = spec
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
                 and " Figure 5" not in x["text"]]
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
        print(f"{key:26s} ch{chapter} sentences {len(sents):3d}  "
              f"pages {min(pgs) if pgs else '?'}-{max(pgs) if pgs else '?'}")
    dump_json(OUT, out)
    print("written", OUT)
    return 0


def _page_map(lines):
    """Printed page of every line (the bare number comes before its page)."""
    import re
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

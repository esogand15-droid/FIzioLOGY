"""Page-anchored Guyton excerpts for session 4 (cortical sensory processing and pain).

Session 4 covers the cortical side of the somatic sensory system — somatosensory
areas I and II, the homunculus, cortical layers and functional columns, removal
of S1, association areas and amorphosynthesis, two-point discrimination, lateral
inhibition, intensity coding, thalamic and corticofugal control — and then the
second half of the lecture: pain (fast/slow, nociceptors, dual pathways, the
endogenous analgesia system, gate control, referred and visceral pain,
hyperalgesia) and thermal sensations.

Sources in the 12th edition:

* **Ch. 47** — Somatosensory cortex, cortical columns, association areas,
  two-point discrimination, intensity interpretation, thalamic and corticofugal
  control (pp. 574-582).
* **Ch. 48** — Pain, headache and thermal sensations (pp. 583-593).

Only the shared helpers of ``guyton_excerpts.py`` are used: wrapping is undone,
table/heading junk is skipped and the printed page of every sentence is kept.
No wording is added or rewritten here.

Output: ``work/references/guyton_s04_excerpts.json``
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guyton_excerpts import (  # noqa: E402
    MD, PAGE_NO, apply_repairs, body_range, dump_json, find_heading, junk_lines,
    load_lines, sentences, stream_section,
)

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s04_excerpts.json"

# printed page window of every chapter used here (12th edition)
CHAPTER_PAGES = {47: (574, 582), 48: (583, 593)}

# key -> (chapter, heading, [stop headings])
SECTIONS = {
    # ---- chapter 47: the cortical end of the somatic sensory system ----------
    "somatosensory_areas": (
        47, "Somatosensory Cortex",
        ["Spatial Orientation of Signals from Different Parts"]),
    "cortical_map": (
        47, "Spatial Orientation of Signals from Different Parts",
        ["Layers of the Somatosensory Cortex"]),
    "cortical_layers": (
        47, "Layers of the Somatosensory Cortex and Their",
        ["The Sensory Cortex Is Organized in Vertical"]),
    "cortical_columns": (
        47, "The Sensory Cortex Is Organized in Vertical",
        ["Functions of Somatosensory Area I"]),
    "s1_functions": (
        47, "Functions of Somatosensory Area I",
        ["Somatosensory Association Areas"]),
    "association_area": (
        47, "Somatosensory Association Areas",
        ["Effect of Removing the Somatosensory Association"]),
    "amorphosynthesis": (
        47, "Effect of Removing the Somatosensory Association",
        ["Overall Characteristics of Signal Transmission"]),
    "spatial_discrimination": (
        47, "Two-Point Discrimination",
        ["Transmission of Rapidly Changing and Repetitive"]),
    "intensity": (
        47, "Interpretation of Sensory Stimulus Intensity",
        ["Position Senses"]),
    "thalamus_role": (
        47, "Function of the Thalamus in Somatic Sensation",
        ["Cortical Control of Sensory"]),
    "corticofugal": (
        47, "Cortical Control of Sensory",
        ["Segmental Fields of Sensation"]),
    # ---- chapter 48: pain ----------------------------------------------------
    "pain_protective": (
        48, "Pain Is a Protective Mechanism",
        ["Types of Pain and Their Qualities"]),
    "fast_slow_pain": (
        48, "Types of Pain and Their Qualities—Fast",
        ["Pain Receptors and Their Stimulation"]),
    "pain_receptors": (
        48, "Pain Receptors Are Free Nerve Endings",
        ["Three Types of Stimuli Excite Pain Receptors"]),
    "pain_stimuli": (
        48, "Three Types of Stimuli Excite Pain Receptors",
        ["Nonadapting Nature of Pain Receptors"]),
    "pain_nonadapting": (
        48, "Nonadapting Nature of Pain Receptors",
        ["Rate of Tissue Damage as a Stimulus for Pain"]),
    "tissue_damage": (
        48, "Rate of Tissue Damage as a Stimulus for Pain",
        ["Dual Pathways for Transmission"]),
    "dual_pathways": (
        48, "Dual Pathways for Transmission of Pain",
        ["Dual Pain Pathways in the Cord"]),
    "neo_paleo": (
        48, "Dual Pain Pathways in the Cord and Brain",
        ["Pain Suppression"]),
    "analgesia": (
        48, "Pain Suppression (“Analgesia”) System",
        ["Brain’s Opiate System"]),
    "opiates": (
        48, "Brain’s Opiate System—Endorphins",
        ["Inhibition of Pain Transmission by Simultaneous"]),
    "gate_tactile": (
        48, "Inhibition of Pain Transmission by Simultaneous",
        ["Treatment of Pain by Electrical Stimulation"]),
    "referred_pain": (
        48, "Referred Pain",
        ["Visceral Pain"]),
    "visceral_pain": (
        48, "Visceral Pain",
        ["Some Clinical Abnormalities of Pain"]),
    "hyperalgesia": (
        48, "Some Clinical Abnormalities of Pain",
        ["Herpes Zoster"]),
    "herpes_tic": (
        48, "Herpes Zoster (Shingles)",
        ["Brown-Séquard Syndrome"]),
    "brown_sequard": (
        48, "Brown-Séquard Syndrome",
        ["Headache"]),
    # ---- chapter 48: thermal sensations -------------------------------------
    "thermal_rec": (
        48, "Thermal Receptors and Their Excitation",
        ["Mechanism of Stimulation of Thermal Receptors"]),
    "thermal_mech": (
        48, "Mechanism of Stimulation of Thermal Receptors",
        ["Transmission of Thermal Signals"]),
    "thermal_trans": (
        48, "Transmission of Thermal Signals in the Nervous",
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
        # guard: a stray page marker inside a figure caption (e.g. "44") and
        # caption bleed ("... Figure 47-3 The dorsal column-...") are not part
        # of the running text, so they are dropped instead of mis-cited.
        page_lo, page_hi = CHAPTER_PAGES[chapter]
        sents = [x for x in sents
                 if x.get("page") and page_lo <= x["page"] <= page_hi
                 and " Figure 4" not in x["text"]]
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

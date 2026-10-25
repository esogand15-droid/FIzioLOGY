"""Page-anchored Guyton excerpts for session 5 (the visual system).

Session 5 is the eye/vision lecture: retinal layers, rods and cones, visual
pigments, the rhodopsin cycle, the hyperpolarizing receptor potential and the
phototransduction cascade, dark/light adaptation, colour vision and colour
blindness, the retinal neural circuit (bipolar, horizontal, amacrine, ganglion),
centre-surround receptive fields and lateral inhibition, then the visual
pathway (optic nerve, chiasm, tract, LGN, V1), cortical organisation, visual
field defects, eye movements and fixation, stereopsis, strabismus, and the
pupillary/accommodation reflexes.

Sources in the 12th edition:

* **Ch. 50** — The Eye: II. Receptor and Neural Function of the Retina
  (pp. 609-621).
* **Ch. 51** — The Eye: III. Central Neurophysiology of Vision (pp. 623-632).

Only the shared helpers of ``guyton_excerpts.py`` are used: wrapping is undone,
table/heading junk is skipped and the printed page of every sentence is kept.
No wording is added or rewritten here.

Output: ``work/references/guyton_s05_excerpts.json``
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guyton_excerpts import (  # noqa: E402
    MD, PAGE_NO, apply_repairs, body_range, dump_json, find_heading, junk_lines,
    load_lines, sentences, stream_section,
)

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s05_excerpts.json"

# printed page window of every chapter used here (12th edition)
CHAPTER_PAGES = {50: (609, 621), 51: (623, 632)}

# key -> (chapter, heading, [stop headings])
SECTIONS = {
    # ---- chapter 50: the retina ---------------------------------------------
    "anatomy": (
        50, "Anatomy and Function of the Structural",
        ["Foveal Region of the Retina and Its Importance"]),
    "fovea": (
        50, "Foveal Region of the Retina and Its Importance",
        ["Rods and Cones"]),
    "rods_cones": (
        50, "Rods and Cones",
        ["Pigment Layer of the Retina"]),
    "pigment_layer": (
        50, "Pigment Layer of the Retina",
        ["Blood Supply of the Retina"]),
    "blood_supply": (
        50, "Blood Supply of the Retina",
        ["Photochemistry of Vision"]),
    "photochemistry": (
        50, "Photochemistry of Vision",
        ["Rhodopsin-Retinal Visual Cycle"]),
    "rhodopsin_cycle": (
        50, "Rhodopsin-Retinal Visual Cycle",
        ["Excitation of the Rod When Rhodopsin"]),
    "rod_potential": (
        50, "The Rod Receptor Potential Is Hyperpolarizing",
        ["Mechanism by Which Rhodopsin Decomposition"]),
    "cascade": (
        50, "Mechanism by Which Rhodopsin Decomposition",
        ["Photochemistry of Color Vision by the Cones"]),
    "cone_pigments": (
        50, "Photochemistry of Color Vision by the Cones",
        ["Automatic Regulation of Retinal Sensitivity"]),
    "adaptation": (
        50, "Automatic Regulation of Retinal Sensitivity",
        ["Color Vision"]),
    "color_vision": (
        50, "Color Vision",
        ["Color Blindness"], 69540),
    "color_blindness": (
        50, "Color Blindness",
        ["Neural Function of the Retina"]),
    "retinal_circuit": (
        50, "Neural Circuitry of the Retina",
        ["The Visual Pathway from the Cones"]),
    "cone_pathway": (
        50, "The Visual Pathway from the Cones",
        ["Transmission of Most Signals"]),
    "electrotonic": (
        50, "Transmission of Most Signals",
        ["Lateral Inhibition to Enhance Visual"]),
    "lateral_inhibition": (
        50, "Lateral Inhibition to Enhance Visual",
        ["Excitation of Some Bipolar Cells"]),
    "bipolar_onoff": (
        50, "Excitation of Some Bipolar Cells",
        ["Amacrine Cells and Their Functions"]),
    "amacrine": (
        50, "Amacrine Cells and Their Functions",
        ["Ganglion Cells and Optic Nerve Fibers"]),
    "ganglion_cells": (
        50, "Ganglion Cells and Optic Nerve Fibers",
        ["Three Types of Retinal Ganglion Cells"]),
    "ganglion_types": (
        50, "Three Types of Retinal Ganglion Cells",
        ["Excitation of the Ganglion Cells"]),
    "on_off": (
        50, "Excitation of the Ganglion Cells",
        ["Transmission of Signals Depicting Contrasts"]),
    "contrast_center": (
        50, "Transmission of Signals Depicting Contrasts",
        ["Transmission of Color Signals by the Ganglion"]),
    "color_ganglion": (
        50, "Transmission of Color Signals by the Ganglion",
        ["Bibliography"]),
    # ---- chapter 51: central visual pathways --------------------------------
    "visual_pathways": (
        51, "Visual Pathways",
        ["Function of the Dorsal Lateral Geniculate"]),
    "lgn": (
        51, "Function of the Dorsal Lateral Geniculate",
        ["Organization and Function"]),
    "v1": (
        51, "Organization and Function",
        ["The Primary Visual Cortex Has Six Major Layers"]),
    "cortex_layers": (
        51, "The Primary Visual Cortex Has Six Major Layers",
        ["Two Major Pathways for Analysis"]),
    "pathways_mp": (
        51, "Two Major Pathways for Analysis",
        ["Detection of Color"]),
    "color_cortex": (
        51, "Detection of Color",
        ["Effect of Removing the Primary Visual Cortex"]),
    "cortex_removal": (
        51, "Effect of Removing the Primary Visual Cortex",
        ["Fields of Vision; Perimetry"]),
    "perimetry": (
        51, "Fields of Vision; Perimetry",
        ["Effect of Lesions in the Optic Pathway"]),
    "lesions": (
        51, "Effect of Lesions in the Optic Pathway",
        ["Eye Movements and Their Control"]),
    "eye_movements": (
        51, "Eye Movements and Their Control",
        ["Fixation Movements of the Eyes"]),
    "fixation": (
        51, "Fixation Movements of the Eyes",
        ["Mechanism of Involuntary Locking Fixation"]),
    "involuntary_fixation": (
        51, "Mechanism of Involuntary Locking Fixation",
        ["Saccadic Movement of the Eyes"]),
    "saccades": (
        51, "Saccadic Movement of the Eyes",
        ["Fixation on Moving Objects"]),
    "pursuit": (
        51, "Fixation on Moving Objects",
        ["Superior Colliculi Are Mainly Responsible"]),
    "colliculi": (
        51, "Superior Colliculi Are Mainly Responsible",
        ["Neural Mechanism of Stereopsis"]),
    "stereopsis": (
        51, "Neural Mechanism of Stereopsis",
        ["Strabismus"]),
    "strabismus": (
        51, "Strabismus",
        ["Autonomic Control of Accommodation"]),
    "accommodation": (
        51, "Autonomic Control of Accommodation",
        ["Control of Pupillary Diameter"]),
    "pupil": (
        51, "Control of Pupillary Diameter",
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
    for key, spec in SECTIONS.items():
        chapter, heading, stops = spec[0], spec[1], spec[2]
        floor = spec[3] if len(spec) > 3 else 0
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
        # guard: stray page markers inside figure captions and caption bleed are
        # not part of the running text, so they are dropped instead of mis-cited.
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
        print(f"{key:22s} ch{chapter} sentences {len(sents):3d}  "
              f"pages {min(pgs) if pgs else '?'}-{max(pgs) if pgs else '?'}")
    dump_json(OUT, out)
    print("written", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Page-anchored Guyton excerpts for session 6 (hearing).

Session 6 is the ear/hearing lecture: outer and middle ear, the ossicular
lever system and impedance matching, the attenuation (stapedius/tensor
tympani) reflex, bone versus air conduction, the three scalae, perilymph and
endolymph, the endocochlear potential, the organ of Corti and the two hair-cell
populations, tip links and the K+ transduction current, basilar-membrane
resonance and the traveling wave, the place and volley principles, pitch and
loudness, the decibel scale, the threshold-of-hearing curve, the ascending
auditory pathway (cochlear nuclei -> superior olive -> lateral lemniscus ->
inferior colliculus -> MGN -> auditory cortex), tonotopic maps and lateral
inhibition, cortical lesions, sound localisation, centrifugal (olivocochlear)
control, and the audiometric patterns of nerve versus conduction deafness.

In this edition the hearing chapter is **Chapter 52** (the 12th edition puts
the same material in Chapter 53); all page numbers below follow the file in
``رفرنس گایتون`` and are printed pages, not PDF pages.

Only the shared helpers of ``guyton_excerpts.py`` are used: wrapping is undone,
table/heading junk is skipped and the printed page of every sentence is kept.
No wording is added or rewritten here.

Output: ``work/references/guyton_s06_excerpts.json``
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guyton_excerpts import (  # noqa: E402
    MD, PAGE_NO, apply_repairs, body_range, dump_json, find_heading, junk_lines,
    load_lines, sentences, stream_section,
)

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s06_excerpts.json"

# printed page window of the chapter used here
CHAPTER_PAGES = {52: (633, 646)}

# key -> (chapter, heading, [stop headings])  -- keys are prefixed s6_ so the
# merged gq() index of blocks_common never collides with earlier sessions.
SECTIONS = {
    "s6_tympanic": (
        52, "Tympanic Membrane and the Ossicular System",
        ["\u201cImpedance Matching\u201d by the Ossicular System"]),
    "s6_impedance": (
        52, "\u201cImpedance Matching\u201d by the Ossicular System",
        ["Attenuation of Sound by Contraction"]),
    "s6_attenuation": (
        52, "Attenuation of Sound by Contraction of the Tensor",
        ["Transmission of Sound Through Bone"]),
    "s6_bone_conduction": (
        52, "Transmission of Sound Through Bone", ["Cochlea"]),
    "s6_cochlea": (
        52, "Cochlea", ["Basilar Membrane and Resonance"]),
    "s6_basilar_resonance": (
        52, "Basilar Membrane and Resonance in the Cochlea",
        ["Transmission of Sound Waves"]),
    "s6_traveling_wave": (
        52, "Transmission of Sound Waves",
        ["Pattern of Vibration of the Basilar Membrane"]),
    "s6_wave_pattern": (
        52, "Pattern of Vibration of the Basilar Membrane",
        ["Amplitude Pattern of Vibration of the Basilar"]),
    "s6_amplitude_pattern": (
        52, "Amplitude Pattern of Vibration of the Basilar",
        ["Function of the Organ of Corti"]),
    "s6_organ_corti": (
        52, "Function of the Organ of Corti", ["Excitation of the Hair Cells"]),
    "s6_hair_excitation": (
        52, "Excitation of the Hair Cells",
        ["Auditory Signals Are Transmitted Mainly by the"]),
    "s6_outer_hair_cells": (
        52, "Auditory Signals Are Transmitted Mainly by the",
        ["Hair Cell Receptor Potentials and Excitation of"]),
    "s6_hair_potential": (
        52, "Hair Cell Receptor Potentials and Excitation of",
        ["Determination of Sound Frequency"]),
    "s6_place_principle": (
        52, "Determination of Sound Frequency—The",
        ["Determination of Loudness"]),
    "s6_loudness": (
        52, "Determination of Loudness",
        ["Detection of Changes in Loudness—The Power"]),
    "s6_decibel": (
        52, "Detection of Changes in Loudness—The Power",
        ["Threshold for Hearing Sound at Different Frequencies"]),
    "s6_threshold": (
        52, "Threshold for Hearing Sound at Different Frequencies",
        ["Frequency Range of Hearing"]),
    "s6_freq_range": (
        52, "Frequency Range of Hearing", ["Central Auditory Mechanisms"]),
    "s6_pathways": (
        52, "Central Auditory Mechanisms",
        ["Function of the Cerebral Cortex in Hearing"]),
    "s6_cortex": (
        52, "Function of the Cerebral Cortex in Hearing",
        ["Sound Frequency Perception in the Primary"]),
    "s6_cortex_freq": (
        52, "Sound Frequency Perception in the Primary",
        ["Other auditory cortex areas detect special qualities"]),
    "s6_cortex_special": (
        52, "Other auditory cortex areas detect special qualities",
        ["Discrimination of Sound"]),
    "s6_patterns": (
        52, "Discrimination of Sound",
        ["Determination of the Direction"]),
    "s6_direction": (
        52, "Determination of the Direction",
        ["Centrifugal Signals from the Central Nervous System"]),
    "s6_centrifugal": (
        52, "Centrifugal Signals from the Central Nervous System",
        ["Hearing Abnormalities"]),
    "s6_abnormalities": (
        52, "Hearing Abnormalities", ["Bibliography"]),
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

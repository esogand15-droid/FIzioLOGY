"""Page-anchored Guyton excerpts for session 7 (spinal cord and descending tracts).

Session 7 is the spinal-cord lecture: organisation of the cord, the ventral-horn
alpha and gamma motor neurons and the motor unit, interneurons and Renshaw
cells, the mono- and polysynaptic reflex arc, the muscle spindle (nuclear bag
and nuclear chain fibres, group Ia and group II endings, dynamic and static
responses, dynamic and static gamma efferents), the stretch reflex, the knee
jerk and clonus, reciprocal inhibition, alpha-gamma coactivation, the damping
mechanism, the Golgi tendon organ and its inhibitory (clasp-knife) reflex, the
flexor/withdrawal reflex with afterdischarge, the crossed extensor reflex, the
positive supportive reaction, the cord righting and scratch reflexes, muscle
spasm and cramps, the segmental autonomic reflexes and the mass reflex, spinal
transection and spinal shock; then the cortical motor areas (areas 4 and 6, the
homunculus of Penfield and Rasmussen, the hand-skill area, Broca's area, the
eye-movement area), the sensory input to the motor cortex, the direct and
indirect pathways, the lateral corticospinal tract, the red nucleus and the
rubrospinal tract, the medial system with the ventral corticospinal tract, and
the lesions with Babinski sign, spasticity and hyperreflexia.

The reflexes are **Chapter 54** of the file in ``رفرنس گایتون``; the cortical
motor areas and the descending tracts are the first part of **Chapter 55**
(pages 667-673), which is where this session stops: the brain-stem control of
motor function (page 673 onward) belongs to a later session.

Only the shared helpers of ``guyton_excerpts.py`` are used: wrapping is undone,
table/heading junk is skipped and the printed page of every sentence is kept.
No wording is added or rewritten here.

Output: ``work/references/guyton_s07_excerpts.json``
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guyton_excerpts import (  # noqa: E402
    MD, body_range, dump_json, find_heading, junk_lines, load_lines, sentences,
    stream_section, apply_repairs,
)

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s07_excerpts.json"

CHAPTER_PAGES = {54: (655, 666), 55: (667, 673)}

# key -> (chapter, heading, [stop headings], floor line)
# keys are prefixed s7_ so the merged gq() index of blocks_common never
# collides with earlier sessions.  The floor is the line of the heading minus a
# few lines; it keeps a section from matching the same phrase in running text.
SECTIONS = {
    # ---------------------------------------------------------------- ch 54
    "s7_organization": (
        54, "Organization of the Spinal Cord",
        ["Renshaw Cells Transmit Inhibitory Signals"], 73553),
    "s7_renshaw": (
        54, "Renshaw Cells Transmit Inhibitory Signals to Surrounding",
        ["Multisegmental Connections from One Spinal Cord Level"], 73667),
    "s7_multisegmental": (
        54, "Multisegmental Connections from One Spinal Cord Level to Other Levels",
        ["Muscle Sensory Receptors"], 73683),
    "s7_receptors": (
        54, "Muscle Sensory Receptors",
        ["Receptor Function of the Muscle Spindle"], 73745),
    "s7_spindle_structure": (
        54, "Structure and Motor Innervation of the Muscle Spindle",
        ["Division of the Intrafusal Fibers into Nuclear Bag"], 73779),
    "s7_intrafusal": (
        54, "Division of the Intrafusal Fibers into Nuclear Bag and Nuclear Chain Fibers",
        ["Response of Both the Primary and the Secondary Endings"], 73836),
    "s7_primary_secondary": (
        54, "Response of Both the Primary and the Secondary",
        ["Response of the Primary Ending"], 73905),
    "s7_rate_change": (
        54, "Response of the Primary Ending",
        ["Control of Intensity of the Static and Dynamic Responses"], 73919),
    "s7_gamma_control": (
        54, "Control of Intensity of the Static and Dynamic Responses by the Gamma",
        ["Continuous Discharge of the Muscle Spindles"], 73946),
    "s7_continuous": (
        54, "Continuous Discharge of the Muscle Spindles",
        ["Muscle Stretch Reflex"], 73966),
    "s7_stretch_reflex": (
        54, "Muscle Stretch Reflex",
        ["Dynamic Stretch Reflex and Static Stretch"], 73977),
    "s7_dynamic_static_reflex": (
        54, "Dynamic Stretch Reflex and Static Stretch",
        ["Damping Mechanism"], 74010),
    "s7_damping": (
        54, "Damping Mechanism in Smoothing Muscle",
        ["Role of the Muscle Spindle in Voluntary"], 74049),
    "s7_voluntary_gamma": (
        54, "Role of the Muscle Spindle in Voluntary",
        ["Brain Areas for Control of the Gamma"], 74070),
    "s7_brain_gamma": (
        54, "Brain Areas for Control of the Gamma",
        ["Muscle Spindle System Stabilizes Body Position"], 74099),
    "s7_position_stabilize": (
        54, "Muscle Spindle System Stabilizes Body Position",
        ["Clinical Applications of the Stretch Reflex"], 74140),
    "s7_clinical_stretch": (
        54, "Clinical Applications of the Stretch Reflex",
        ["Knee Jerk and Other Muscle Jerks"], 74171),
    "s7_knee_jerk": (
        54, "Knee Jerk and Other Muscle Jerks",
        ["Golgi Tendon Reflex"], 74177),
    "s7_gto_structure": (
        54, "Golgi Tendon Organ Helps Control Muscle",
        ["Transmission of Impulses from the Tendon"], 74265),
    "s7_gto_transmission": (
        54, "Transmission of Impulses from the Tendon",
        ["Inhibitory Nature of the Tendon Reflex"], 74291),
    "s7_gto_inhibitory": (
        54, "Inhibitory Nature of the Tendon Reflex",
        ["Possible Role of the Tendon Reflex"], 74309),
    "s7_gto_equalize": (
        54, "Possible Role of the Tendon Reflex to Equalize",
        ["Function of the Muscle Spindles and Golgi Tendon"], 74330),
    "s7_flexor": (
        54, "Flexor Reflex and the Withdrawal Reflexes",
        ["Crossed Extensor Reflex"], 74358),
    "s7_crossed": (
        54, "Crossed Extensor Reflex",
        ["Reciprocal Inhibition and Reciprocal Innervation"], 74495),
    "s7_reciprocal": (
        54, "Reciprocal Inhibition and Reciprocal",
        ["Reflexes of Posture and Locomotion"], 74526),
    "s7_postural": (
        54, "Postural and Locomotive Reflexes of the Cord",
        ["Stepping and Walking Movements"], 74550),
    "s7_stepping": (
        54, "Stepping and Walking Movements",
        ["Scratch Reflex"], 74604),
    "s7_scratch": (
        54, "Scratch Reflex",
        ["Spinal Cord Reflexes That Cause Muscle Spasm"], 74678),
    "s7_spasm": (
        54, "Spinal Cord Reflexes That Cause Muscle Spasm",
        ["Autonomic Reflexes in the Spinal Cord"], 74700),
    "s7_autonomic": (
        54, "Autonomic Reflexes in the Spinal Cord",
        ["Spinal Cord Transection and Spinal Shock"], 74752),
    "s7_spinal_shock": (
        54, "Spinal Cord Transection and Spinal Shock",
        ["Bibliography"], 74812),
    # ---------------------------------------------------------------- ch 55
    "s7_motor_cortex": (
        55, "Motor Cortex and Corticospinal Tract",
        ["Primary Motor Cortex"], 74943),
    "s7_primary_motor": (
        55, "Primary Motor Cortex",
        ["Premotor Area"], 74964),
    "s7_premotor": (
        55, "Premotor Area",
        ["Supplementary Motor Area"], 75035),
    "s7_supplementary": (
        55, "Supplementary Motor Area",
        ["Some Specialized Areas of Motor Control"], 75086),
    "s7_specialized": (
        55, "Some Specialized Areas of Motor Control",
        ["Transmission of Signals from the Motor"], 75104),
    "s7_transmission": (
        55, "Transmission of Signals from the Motor",
        ["Corticospinal (Pyramidal) Tract"], 75180),
    "s7_corticospinal": (
        55, "Corticospinal (Pyramidal) Tract",
        ["Incoming Sensory Fiber Pathways to the Motor Cortex"], 75191),
    "s7_sensory_input": (
        55, "Incoming Sensory Fiber Pathways to the Motor Cortex",
        ["Red Nucleus Serves as an Alternative Pathway"], 75299),
    "s7_red_nucleus": (
        55, "Red Nucleus Serves as an Alternative Pathway",
        ["Excitation of the Spinal Cord Motor Control Areas"], 75337),
    "s7_patterns": (
        55, "Patterns of Movement Elicited by Spinal Cord",
        ["Effect of Lesions in the Motor Cortex"], 75555),
    "s7_lesions": (
        55, "Effect of Lesions in the Motor Cortex or in the Corticospinal",
        ["Muscle Spasticity Caused by Lesions"], 75583),
    "s7_spasticity": (
        55, "Muscle Spasticity Caused by Lesions",
        ["Role of the Brain Stem in Controlling"], 75638),
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
        print(f"{key:24s} ch{chapter} sentences {len(sents):3d}  "
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

# -*- coding: utf-8 -*-
"""Page-anchored Guyton excerpts for the *supplement* sections of the master notes.

Same machinery as ``guyton_excerpts.py`` (verbatim sentences, wrapping undone only),
but the sections live in several chapters and feed the «نکته‌های تکمیلی» topics of
sessions 4, 7 and 9.

Output: ``work/references/guyton_supp_excerpts.json`` (schema identical to the
per-chapter files, so ``blocks_common.gq()`` can quote from it).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import guyton_excerpts as GE  # noqa: E402
from lib_common import WORK, dump_json  # noqa: E402

OUT = WORK / "references" / "guyton_supp_excerpts.json"

# key: (chapter, heading, [stop headings])
SECTIONS: dict[str, tuple[int, str, list[str]]] = {
    "supp_headache": (48, "Headache", ["Thermal Sensations"]),
    "supp_withdrawal": (54, "Flexor Reflex and the Withdrawal Reflexes", ["Crossed Extensor Reflex"]),
    "supp_spindle": (54, "Receptor Function of the Muscle Spindle", ["Muscle Stretch Reflex"]),
    "supp_stretch": (54, "Muscle Stretch Reflex", ["Golgi Tendon Reflex"]),
    "supp_renshaw": (54, "Renshaw Cells Transmit Inhibitory Signals", ["Muscle Stretch Reflex"]),
    "supp_spinal_shock": (54, "Spinal Cord Transection and Spinal Shock", ["Bibliography"]),
    "supp_motor_cortex": (55, "Motor Cortex and Corticospinal Tract", ["Premotor Area"]),
    "supp_sma": (55, "Supplementary Motor Area", ["Some Specialized Areas of Motor Control"]),
    "supp_corticospinal": (55, "Corticospinal", ["Vestibulospinal"]),
    "supp_vestibulospinal": (55, "Vestibulospinal and", ["The Decerebrate Animal"]),
    "supp_decerebrate": (55, "The Decerebrate Animal Develops Spastic Rigidity", ["Bibliography"]),
    # ch57 — قشر، حافظه، تکلم (مباحث تکمیلی جلسهٔ ۱۰)
    "supp_assoc": (57, "Association Areas", ["Language"]),
    "supp_wernicke_area": (57, "Function of the Brain in Communication", ["Wernicke\u2019s Aphasia"]),
    "supp_aphasia": (57, "Wernicke\u2019s Aphasia and Global Aphasia", ["Function of the Corpus Callosum"]),
    "supp_corpus_callosum": (57, "Function of the Corpus Callosum", ["Memory\u2014Roles"]),
    "supp_memory_classes": (57, "Memory\u2014Roles of Synaptic Facilitation", ["Memory Based on Chemical"]),
    "supp_habituation": (57, "Positive and Negative Memory", ["Memory Based on Chemical"]),
    "supp_consolidation": (57, "Consolidation of Memory", ["Hippocampus Promotes Storage"]),
    "supp_amnesia": (57, "Hippocampus Promotes Storage of Memories", ["Retrograde Amnesia"]),
    "supp_cerebellar_lesion": (56, "Dysdiadochokinesia", ["Cerebellar Nystagmus"]),
    "supp_cerebellum_unit": (56, "Functional Unit of the Cerebellar Cortex", ["Purkinje Cells and Deep Nuclear"]),
    "supp_vermis_map": (56, "Topographical Representation of the Body in the Vermis",
                        ["Neuronal Circuit of the Cerebellum"]),
    "supp_bg_anatomy": (56, "Basal Ganglia—Their Motor Functions", ["Neuronal Circuitry of the Basal Ganglia"]),
    "supp_bg_circuit": (56, "Neuronal Circuitry of the Basal Ganglia", ["Function of the Basal Ganglia"]),
    "supp_parkinson": (56, "Parkinson’s Disease", ["Huntington’s Disease"]),
    "supp_huntington": (56, "Huntington’s Disease (Huntington", ["Bibliography"]),
}


def section_range(lines, chapter: int, heading: str, stops: list[str]):
    lo, hi = GE.body_range(lines, chapter)
    start = GE.find_heading(lines, heading, lo, hi)
    if start is None:
        return None, None
    end = hi
    for stop in stops:
        j = GE.find_heading(lines, stop, start + 1, hi)
        if j is not None:
            end = min(end, j)
    return start, end


# The PDF->markdown converter sometimes splits a word at a line end *without* a
# hyphen, leaving "cor tex" / "puta men".  These repairs only re-join the split
# word; no wording is changed.  ("in men" in the headache section is real prose
# and is deliberately absent.)
REPAIRS = [
    ("lay ers", "layers"),
    ("representa tions", "representations"),
    ("representa tion", "representation"),
    ("cor tex", "cortex"),
    ("surround ing", "surrounding"),
    ("substan tia", "substantia"),
    ("secre tion", "secretion"),
    ("excita tion", "excitation"),
    ("puta men", "putamen"),
    ("issu ing", "issuing"),
    ("tim ing", "timing"),
    ("func tions", "functions"),
    ("pattern ing", "patterning"),
    ("think ing", "thinking"),
    ("charac terized", "characterized"),
    ("discus sion", "discussion"),
    ("inter connections", "interconnections"),
    ("simulta neously", "simultaneously"),
    ("func tional", "functional"),
    ("continu ally", "continually"),
    ("collat erals", "collaterals"),
    ("collat eral", "collateral"),
    ("syn aptic", "synaptic"),
    ("syn apse", "synapse"),
    ("pro longed", "prolonged"),
    ("mil lions", "millions"),
    ("cere bral", "cerebral"),
    ("hemi spheres", "hemispheres"),
    ("hemi sphere", "hemisphere"),
    ("coor dinating", "coordinating"),
    ("affer ent", "afferent"),
    ("effer ent", "efferent"),
    ("especi ally", "especially"),
    ("prin cipal", "principal"),
    ("charac terized", "characterized"),
    ("charac teristic", "characteristic"),
    ("dysarth ria", "dysarthria"),
    ("inten tion", "intention"),
    ("repre senta tions", "representations"),
    ("topograph ical", "topographical"),
    ("excita tory", "excitatory"),
    ("inhibi tory", "inhibitory"),
    ("anti gravity", "antigravity"),
    ("decreas ing", "decreasing"),
    ("increas ing", "increasing"),
    ("stimu lation", "stimulation"),
    ("contrac tion", "contraction"),
    ("contrac tions", "contractions"),
    ("transmit ted", "transmitted"),
    ("transmit ting", "transmitting"),
    ("sequen tial", "sequential"),
    ("initi ate", "initiate"),
    ("hip pocampus", "hippocampus"),
    ("hip pocampi", "hippocampi"),
    ("cere bellum", "cerebellum"),
    ("nor mally", "normally"),
    ("pro tein", "protein"),
    ("multi ple", "multiple"),
    ("longterm", "long-term"),
    ("congru ent", "congruent"),
]


def rejoin(text: str) -> tuple[str, int]:
    hits = 0
    for bad, good in REPAIRS:
        if bad in text:
            hits += text.count(bad)
            text = text.replace(bad, good)
    return text, hits


def main() -> int:
    lines = GE.load_lines()
    pages: dict[int, int] = {}
    cur = None
    for i, ln in enumerate(lines):
        if GE.PAGE_NO.match(ln.strip()):
            cur = int(ln.strip())
        pages[i] = cur

    out = {"source": GE.MD.name,
           "note": "verbatim sentences from the PDF->markdown conversion; line wrapping undone only",
           "sections": {}}
    for key, (chapter, heading, stops) in SECTIONS.items():
        start, end = section_range(lines, chapter, heading, stops)
        if start is None:
            out["sections"][key] = {"heading": heading, "chapter": chapter,
                                    "found": False, "sentences": []}
            print("MISSING", key)
            continue
        recs = GE.stream_section(lines, start + 1, end, pages,
                                 skip=GE.junk_lines(lines, start + 1, end))
        recs, hits = GE.apply_repairs(recs)
        sents = GE.sentences(recs)
        fixed = 0
        for sent in sents:
            sent["text"], n = rejoin(sent["text"])
            fixed += n
        pgs = [s["page"] for s in sents if s["page"]]
        out["sections"][key] = {
            "heading": heading, "chapter": chapter, "found": True,
            "start_line": start + 1, "end_line": end,
            "page_start": min(pgs) if pgs else None,
            "page_end": max(pgs) if pgs else None,
            "sentences": sents, "repair_hits": hits, "rejoin_hits": fixed,
        }
        print(f"{key:24s} ch{chapter} lines {start + 1}-{end}  sentences {len(sents):3d}  "
              f"pages {min(pgs) if pgs else '?'}-{max(pgs) if pgs else '?'}")
    dump_json(OUT, out)
    print("written", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

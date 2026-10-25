"""Page-anchored Guyton excerpts for session 11 (limbic system and hypothalamus).

Session 11 is Chapter 58 of the textbook: the limbic system, the hypothalamus as
its control headquarters (vegetative, endocrine and behavioural functions),
reward and punishment centres, the hippocampus, the amygdala and the limbic
cortex.  The activating-driving systems of the same chapter (reticular
formation, arousal, neurohormones) and everything from Chapter 59 (sleep,
brain waves, epilepsy) are deliberately **not** included: they belong to
session 12 («فعالیت‌های مغزی»).

Only the shared helpers of ``guyton_excerpts.py`` are used; the printed page of
every sentence is kept and no wording is rewritten.

Output: ``work/references/guyton_s11_excerpts.json``
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

OUT = Path(__file__).resolve().parents[2] / "work" / "references" / "guyton_s11_excerpts.json"

CHAPTER_PAGES = {58: (706, 720)}

# key -> (chapter, heading, [stop headings], floor line)
SECTIONS = {
    "s11_limbic": (58, "Limbic System",
                   ["Key Position of the Hypothalamus"], 80090),
    "s11_position": (58, "Key Position of the Hypothalamus",
                     ["Hypothalamus, a Major Control"], 80110),
    "s11_hq": (58, "Hypothalamus, a Major Control",
               ["Vegetative and Endocrine Control Functions"], 80250),
    "s11_vegetative": (58, "Vegetative and Endocrine Control Functions",
                       ["Behavioral Functions of the Hypothalamus and"], 80285),
    "s11_behavior": (58, "Behavioral Functions of the Hypothalamus and",
                     ["Reward Centers"], 80555),
    "s11_reward": (58, "Reward Centers",
                   ["Punishment Centers"], 80615),
    "s11_punishment": (58, "Punishment Centers",
                       ["Importance of Reward or Punishment on Behavior"], 80645),
    "s11_learning": (58, "Importance of Reward or Punishment on Behavior",
                     ["Specific Functions of Other Parts"], 80700),
    "s11_hippocampus": (58, "Functions of the Hippocampus",
                        ["Functions of the Amygdala"], 80745),
    "s11_amygdala": (58, "Functions of the Amygdala",
                     ["Function of the Limbic Cortex"], 80840),
    "s11_cortex": (58, "Function of the Limbic Cortex",
                   ["Bibliography"], 80955),
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
                 and " Figure 58" not in x["text"]]
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

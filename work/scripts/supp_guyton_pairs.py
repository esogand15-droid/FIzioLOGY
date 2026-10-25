#!/usr/bin/env python3
"""Insert Guyton 12th-ed. (2011) English + Persian pairs into the supplement
sections (``content/sessions/sNN_d.json``).

Design notes
------------
* The English side is **verbatim**: every sentence is pulled by index from
  ``work/references/guyton_supp_excerpts.json`` (produced by
  ``guyton_supp_excerpts.py`` from the project's Guyton markdown), together
  with the printed page number the markdown itself carries.  Nothing is
  retyped here, so a typo cannot silently become a "quotation".
* The Persian side is the team's own translation and is authored once in
  ``content/guyton/supp_pairs.json``; the renderer labels it as an editorial
  translation, never as official wording.
* The script is idempotent: a block added by an earlier run is replaced (same
  title), so it can be re-run after editing the Persian text.

Run:  python work/scripts/supp_guyton_pairs.py [--check]
"""

from __future__ import annotations

import json
import sys

import lib_common as LC

ROOT = LC.REPO
PAIRS = ROOT / "content" / "guyton" / "supp_pairs.json"
EXCERPTS = ROOT / "work" / "references" / "guyton_supp_excerpts.json"

# blocks that carry teaching content; the pair goes after the last of them and
# before the closing editorial cluster (callout / note / handoff)
CONTENT_TYPES = {"h3", "p", "ul", "ol", "table", "figure", "guyton", "guytonpair"}


_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa_num(n: int) -> str:
    return str(n).translate(_FA)


def src_line(chapter: str, pages: list[int]) -> str:
    lo, hi = min(pages), max(pages)
    span = fa_num(lo) if lo == hi else f"{fa_num(lo)}\u2013{fa_num(hi)}"
    return (f"گایتون، فصل {chapter}، ص {span} — متن اصلی انگلیسی؛ "
            "ترجمهٔ روان: تحریریهٔ همین جزوه")


def cite(pages: list[int]) -> str:
    lo, hi = min(pages), max(pages)
    return f"p. {lo}" if lo == hi else f"pp. {lo}\u2013{hi}"


def build_block(key: str, rec: dict, sections: dict) -> dict:
    sec = sections.get(rec["section"])
    if sec is None:
        raise SystemExit(f"{key}: section {rec['section']!r} missing from excerpts")
    sents = sec["sentences"]
    picked = []
    for idx in rec["picks"]:
        if idx >= len(sents):
            raise SystemExit(f"{key}: pick {idx} out of range ({len(sents)} sentences)")
        picked.append(sents[idx])
    pages = [s["page"] for s in picked if s.get("page")]
    if len(pages) != len(picked):
        raise SystemExit(f"{key}: a picked sentence has no page number")
    return {
        "type": "guytonpair",
        "chapter": rec["chapter"],
        "pages": cite(pages),
        "title": rec["title"],
        "english": [{"text": s["text"], "page": s["page"]} for s in picked],
        "fa": rec["fa"],
        "note": rec["note"],
        "src": src_line(rec["chapter"], pages),
    }


def insert(topic: dict, block: dict) -> str:
    blocks = topic["blocks"]
    # drop an earlier copy (idempotency)
    kept = [b for b in blocks if not (b.get("type") == "guytonpair"
                                      and b.get("title") == block["title"])]
    replaced = len(kept) != len(blocks)
    blocks = kept
    pos = 0
    for i, b in enumerate(blocks):
        if b.get("type") in CONTENT_TYPES:
            pos = i + 1
    blocks.insert(pos, block)
    topic["blocks"] = blocks
    return "replaced" if replaced else "added"


def main() -> int:
    check = "--check" in sys.argv
    sections = json.loads(EXCERPTS.read_text(encoding="utf-8"))["sections"]
    pairs = json.loads(PAIRS.read_text(encoding="utf-8"))["pairs"]

    by_session: dict[str, list[tuple[str, dict]]] = {}
    for key, rec in pairs.items():
        by_session.setdefault(key.split("-")[0], []).append((key, rec))

    total = 0
    for session, items in sorted(by_session.items()):
        path = ROOT / "content" / "sessions" / f"{session}_d.json"
        topics = json.loads(path.read_text(encoding="utf-8"))
        index = {t["topic_id"]: t for t in topics}
        sizes = []
        for key, rec in items:
            topic = index.get(key)
            if topic is None:
                raise SystemExit(f"{key}: no such topic in {path.name}")
            block = build_block(key, rec, sections)
            state = insert(topic, block)
            sizes.append((key, block["pages"], len(block["english"]), state))
            total += 1
        if not check:
            path.write_text(json.dumps(topics, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
        print(f"## {path.name} — {len(sizes)} pair(s)")
        for key, pages, n, state in sizes:
            print(f"   {key:9s} {pages:12s} sents={n}  {state}")
    print(f"total pairs: {total}{' (check only, nothing written)' if check else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

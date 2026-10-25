"""Extract text + embedded figures + page facsimiles for session 10.

Session 10 (learning, memory and the higher cortical functions) has no مهر ۱۴۰۴
deck; its source is a single بهمن ۱۴۰۲ notes file, «نوروفیزیولوژی 12 نهایی بهمن
1402.pdf» in the folder «جلسه 12 - حافظه و یادگیری».  The file/slide numbering
runs two ahead of this project (sessions 7 and 8 ran one ahead), because session 9
consumed two decks (files 10 and 11).

Asset ids use the deck tag ``s10`` and the printed page reference is a plain page
number, as in sessions 7 and 8 (single-part deck).

Usage: python3 work/scripts/extract_s10.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_session import extract_pdf  # noqa: E402
from lib_common import EXTRACTION, IMAGES, SOURCE_ROOT, dump_json, load_json, rel  # noqa: E402

DECK = ("s10", "جلسه 12 - حافظه و یادگیری", "نوروفیزیولوژی 12 نهایی بهمن 1402.pdf")


def main() -> int:
    index_path = IMAGES / "INDEX.json"
    index = load_json(index_path, default={"assets": []}) or {"assets": []}
    known = {a["asset_id"]: a for a in index["assets"]}

    sid, folder, pdf_name = DECK
    base = SOURCE_ROOT / folder
    res = extract_pdf(base / pdf_name, sid, "notes1402", True)
    res["deck_folder"] = folder
    dump_json(EXTRACTION / f"{sid}_notes1402.json", res)
    for fig in res["figures"]:
        known[fig["asset_id"]] = {**fig, "caption": "", "topic_ids": [], "used_in": "pending"}
    print(f"{sid}: pages={res['page_count']} chars={res['chars']} "
          f"figures={len(res['figures'])} verdict={res['verdict']}")

    index["assets"] = sorted(known.values(), key=lambda a: a["asset_id"])
    index["note"] = ("Facsimile pages (*_facsimile.png) are page renders of sources whose "
                     "text layer is unreliable; they are faithful copies, not OCR.")
    dump_json(index_path, index)
    print(f"images index: {len(index['assets'])} assets -> {rel(index_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

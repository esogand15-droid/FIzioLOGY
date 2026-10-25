"""Extract text + embedded figures + page facsimiles for session 9.

Session 9 (cerebellum and basal ganglia) has no مهر ۱۴۰۴ deck and its source is
**two** بهمن ۱۴۰۲ notes files, one per half of the lecture:
  * «نوروفیزیولوژی 10 نهایی بهمن 1402.pdf» — the cerebellum (folder «جلسه 10»)
  * «نوروفیزیولوژی 11 نهایی بهمن 1402.pdf» — the basal ganglia (folder «جلسه 11»)
The file/slide numbering runs one ahead of this project, as in sessions 7 and 8.

Both decks start at page 1, so every asset id is prefixed with the deck tag
(``s09c`` = cerebellum, ``s09b`` = basal ganglia) and the printed page reference
in the document names the part.

Idempotent in exactly the same way as ``extract_session.py``.

Usage: python3 work/scripts/extract_s09.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_session import extract_pdf  # noqa: E402
from lib_common import EXTRACTION, IMAGES, SOURCE_ROOT, dump_json, load_json, rel  # noqa: E402

DECKS = (
    ("s09c", "جلسه 10 - مخچه", "نوروفیزیولوژی 10 نهایی بهمن 1402.pdf", "۱"),
    ("s09b", "جلسه 11 - عقده های قاعده ای", "نوروفیزیولوژی 11 نهایی بهمن 1402.pdf", "۲"),
)


def main() -> int:
    index_path = IMAGES / "INDEX.json"
    index = load_json(index_path, default={"assets": []}) or {"assets": []}
    known = {a["asset_id"]: a for a in index["assets"]}

    for sid, folder, pdf_name, part in DECKS:
        base = SOURCE_ROOT / folder
        res = extract_pdf(base / pdf_name, sid, "notes1402", True)
        res["part"] = part
        res["deck_folder"] = folder
        dump_json(EXTRACTION / f"{sid}_notes1402.json", res)
        for fig in res["figures"]:
            known[fig["asset_id"]] = {**fig, "caption": "", "topic_ids": [], "used_in": "pending"}
        print(f"{sid} (پارت {part}): pages={res['page_count']} chars={res['chars']} "
              f"figures={len(res['figures'])} verdict={res['verdict']}")

    index["assets"] = sorted(known.values(), key=lambda a: a["asset_id"])
    index["note"] = ("Facsimile pages (*_facsimile.png) are page renders of sources whose "
                     "text layer is unreliable; they are faithful copies, not OCR.")
    dump_json(index_path, index)
    print(f"images index: {len(index['assets'])} assets -> {rel(index_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Extract text + embedded figures + page facsimiles for session 13.

Session 13 (the autonomic nervous system) has no مهر ۱۴۰۴ deck; its only source
is «فیزیو آفلاین اتونوم.pdf» in the folder «جلسه 15 - سیستم اتونوم» (17 slides).
The file numbering runs two ahead of this project, as in sessions 7 to 12.

The text layer of this deck is unusable (letters are swapped and words reversed),
so the pages are read as images; the facsimiles are kept for that purpose.

Usage: python3 work/scripts/extract_s13.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_session import extract_pdf  # noqa: E402
from lib_common import EXTRACTION, IMAGES, SOURCE_ROOT, dump_json, load_json, rel  # noqa: E402

DECKS = (
    ("s13", "جلسه 15 - سیستم اتونوم", "فیزیو آفلاین اتونوم.pdf", "۱"),
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

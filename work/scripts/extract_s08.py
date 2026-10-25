"""Extract text + embedded figures + page facsimiles for session 8.

Session 8 has no مهر ۱۴۰۴ deck: its source is a single بهمن ۱۴۰۲ notes file for
the lecture on brain-stem and cortical motor function (the file is named
«جلسه 9» because the source numbering runs one ahead of this project).

Idempotent in exactly the same way as ``extract_session.py``.

Usage: python3 work/scripts/extract_s08.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_session import extract_pdf  # noqa: E402
from lib_common import EXTRACTION, IMAGES, SOURCE_ROOT, dump_json, load_json, rel  # noqa: E402

DECKS = (
    ("s08", "نوروفیزیولوژی 09 نهایی بهمن 1402.pdf", "single"),
)
FOLDER = "جلسه 9 - اعمال حرکتی ساقه مغز و کورتکس"


def main() -> int:
    base = SOURCE_ROOT / FOLDER
    index_path = IMAGES / "INDEX.json"
    index = load_json(index_path, default={"assets": []}) or {"assets": []}
    known = {a["asset_id"]: a for a in index["assets"]}

    for sid, pdf_name, tag in DECKS:
        res = extract_pdf(base / pdf_name, sid, "notes1402", True)
        res["part"] = tag
        dump_json(EXTRACTION / f"{sid}_notes1402.json", res)
        for fig in res["figures"]:
            known[fig["asset_id"]] = {**fig, "caption": "", "topic_ids": [], "used_in": "pending"}
        print(f"{sid} ({tag}): pages={res['page_count']} chars={res['chars']} "
              f"figures={len(res['figures'])} verdict={res['verdict']}")

    index["assets"] = sorted(known.values(), key=lambda a: a["asset_id"])
    index["note"] = ("Facsimile pages (*_facsimile.png) are page renders of sources whose "
                     "text layer is unreliable; they are faithful copies, not OCR.")
    dump_json(index_path, index)
    print(f"images index: {len(index['assets'])} assets -> {rel(index_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

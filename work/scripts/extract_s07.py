"""Extract text + embedded figures + page facsimiles for session 7.

Session 7 has no مهر ۱۴۰۴ deck: its source is the بهمن ۱۴۰۲ notes of the same
lecture, delivered in **two parts** (each PDF restarts at page 1), so the two
parts are extracted under two distinct id prefixes (``s07`` and ``s07b``) to
keep every ``asset_id`` unique inside ``images/INDEX.json``.

Idempotent in exactly the same way as ``extract_session.py``.

Usage: python3 work/scripts/extract_s07.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_session import extract_pdf  # noqa: E402
from lib_common import EXTRACTION, IMAGES, SOURCE_ROOT, dump_json, load_json, rel  # noqa: E402

DECKS = (
    ("s07", "نوروفیزیولوژی_8_نهایی_پارت_1_بهمن_1402.pdf", "part1"),
    ("s07b", "جزوه جلسه 8 پارت 2 بهمن 1402.pdf", "part2"),
)
FOLDER = "جلسه 7"


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

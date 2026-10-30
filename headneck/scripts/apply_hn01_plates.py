"""جای‌گذاری قاب‌های تصویر جلسهٔ ۱ در محتوای مبحث‌ها.

فایل ``hn01_plates.py`` ترتیب و متن هر قاب را دارد؛ این اسکریپت هر قاب را بعد از
بلوکی می‌نشاند که «لنگر»ش در آن پیدا شود. اگر لنگر پیدا نشود، کار متوقف می‌شود
تا هیچ قابی بی‌صدا از قلم نیفتد. اجرای دوباره، قاب‌های قبلی را جابه‌جا نمی‌کند.

    .venv/bin/python headneck/scripts/hn01_plates.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hn01_plates import PLATES, _lec  # noqa: E402,F401

REPO = Path(__file__).resolve().parents[2]
CONTENT = REPO / "headneck" / "content"
FILES = ("hn01_a.json", "hn01_b.json")


def searchable(block: dict) -> str:
    parts = [str(block.get(k, "")) for k in
             ("text", "src", "title", "caption", "kicker", "open", "question", "asset")]
    for key in ("items", "rows", "labels", "checklist"):
        for item in block.get(key) or []:
            parts.append(" ".join(str(x) for x in (item if isinstance(item, (list, tuple))
                                                   else (item,))))
    return " ".join(parts)


def main() -> int:
    docs = {f: json.loads((CONTENT / f).read_text(encoding="utf-8")) for f in FILES}
    index = {}
    for fname, topics in docs.items():
        for t in topics:
            index[t["topic_id"]] = (fname, t)

    placed = 0
    for topic_id, anchor, plate in PLATES:
        fname, topic = index[topic_id]
        blocks = topic["blocks"]
        if any(b.get("asset") == plate["asset"] for b in blocks):
            continue                                    # already placed
        if anchor.startswith("asset:"):
            wanted = anchor.split(":", 1)[1]
            pos = next((i for i, b in enumerate(blocks) if b.get("asset", "").endswith(wanted)), None)
        else:
            pos = next((i for i, b in enumerate(blocks) if anchor in searchable(b)), None)
        if pos is None:
            raise SystemExit(f"anchor not found for {plate['asset']} in {topic_id}: {anchor!r}")
        blocks.insert(pos + 1, json.loads(json.dumps(plate, ensure_ascii=False)))
        placed += 1

    for fname, topics in docs.items():
        (CONTENT / fname).write_text(
            json.dumps(topics, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    total = sum(1 for topics in docs.values() for t in topics
                for b in t["blocks"] if b.get("type") == "plate")
    print(f"placed {placed} new plates · {total} plates in this session")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

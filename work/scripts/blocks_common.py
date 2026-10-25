# -*- coding: utf-8 -*-
"""Shared block helpers for the authored session content (JSON dictionaries).

Every block carries a ``src`` (file + page/slide) because the build refuses
blocks without a traceable source.
"""
from __future__ import annotations

import pathlib as _pathlib

SRC04 = "جزوهٔ مهر ۱۴۰۴، ص {}"
SRC02 = "جزوهٔ بهمن ۱۴۰۲، ص {}"


def p(text, src):
    return {"type": "p", "text": text, "src": src}


def ul(items, src):
    return {"type": "ul", "items": items, "src": src}


def ol(items, src):
    return {"type": "ol", "items": items, "src": src}


def h3(text):
    return {"type": "h3", "text": text}


def callout(text, src, kind="key", title=None):
    d = {"type": "callout", "kind": kind, "text": text, "src": src}
    if title:
        d["title"] = title
    return d


_FA = "۰۱۲۳۴۵۶۷۸۹"

# figure numbering state: every session numbers its figures "شکل <جلسه>-N"
FIG = {"session": "۳", "n": 0, "file": None}


def set_session(num: str, reset: bool = False) -> None:
    """Select the session number used by :func:`fig` (and renumber from 1)."""
    FIG["session"] = num
    FIG["file"] = _pathlib.Path(__file__).resolve().parents[2] / "content" / f".figseq_s{num}"
    if reset:
        FIG["file"].unlink(missing_ok=True)
        FIG["n"] = 0
    else:
        FIG["n"] = int(FIG["file"].read_text().strip()) if FIG["file"].exists() else 0


def _fa(n):
    return "".join(_FA[int(d)] for d in str(n))


def fig(asset, caption, src, folder="notes_1404"):
    """Figure block; the "شکل <جلسه>-N" prefix is assigned automatically in order."""
    import re as _re
    if FIG["file"] is None:
        set_session(FIG["session"])
    FIG["n"] += 1
    FIG["file"].write_text(str(FIG["n"]), encoding="utf-8")
    body = _re.sub(r"^شکل [۰-۹]+-[۰-۹]+ — ", "", caption)
    return {"type": "figure", "asset": f"images/{folder}/{asset}.png",
            "caption": f"شکل {FIG['session']}-{_fa(FIG['n'])} — {body}", "src": src}


def note(size, title):
    return {"type": "note", "size": size, "title": title}


def idcard(n, why, goals, prereq, suggested, terms, footer):
    return {"type": "idcard", "title": f"شناسنامهٔ آموزشی — مبحث {n}",
            "kicker": "قبل از شروع این مبحث بخوانید",
            "rows": [
                {"label": "چرا این مبحث مهم است", "text": why},
                {"label": "اهداف یادگیری", "items": goals},
                {"label": "پیش‌نیاز ضروری", "text": prereq},
                {"label": "پیش‌نیاز پیشنهادی", "text": suggested},
                {"label": "اصطلاحات کلیدی", "text": terms},
            ],
            "footer": footer,
            "src": "نقشهٔ مباحث و پیش‌نیازهای همین جزوه"}


def handoff(n, title, sources, checks, extra=""):
    rows = [
        {"label": "نویسنده و بازبین علمی",
         "text": "نویسنده: ……………………………   بازبین علمی: ……………………………"},
        {"label": "منابعی که برای این مبحث خوانده شد", "text": sources},
        {"label": "کارهای پیش از تحویل", "items": checks},
    ]
    if extra:
        rows.append({"label": "یادداشت گردآورنده", "text": extra})
    return {"type": "handoff", "title": f"برگهٔ تحویل — مبحث {n}: {title}",
            "kicker": "این برگه را نویسندهٔ مبحث پر می‌کند", "rows": rows,
            "src": "برگهٔ تحویل تیم یادداشت‌نویسی"}


def guyton(chapter, pages, title, english, fa, note_text, src_pages):
    # the renderer adds the «گایتون — » prefix itself; never repeat it in the title
    for _p in ("گایتون — ", "گایتون —", "گایتون– ", "گایتون "):
        if title.startswith(_p):
            title = title[len(_p):]
            break
    return {"type": "guytonpair", "chapter": chapter, "pages": pages, "title": title,
            "english": english, "fa": fa, "note": note_text,
            "src": f"گایتون، فصل {chapter}، {src_pages} — متن اصلی انگلیسی؛ "
                   "ترجمهٔ روان: تحریریهٔ همین جزوه"}


# --- exact Guyton quotation helper -------------------------------------------
import json as _json
import pathlib as _pathlib

_EXC_DIR = _pathlib.Path(__file__).resolve().parents[2] / "work" / "references"
_EXC = {}
for _f in sorted(_EXC_DIR.glob("guyton_s*_excerpts.json")):
    _EXC.update(_json.loads(_f.read_text(encoding="utf-8"))["sections"])
_INDEX = []
for _sec, _v in _EXC.items():
    for _s in _v.get("sentences", []):
        _INDEX.append((_sec, _s["page"], _s["text"]))


def gq(section, snippet):
    """Return the verbatim excerpt sentence (with its page) containing ``snippet``."""
    hits = [(p, t) for sec, p, t in _INDEX if sec == section and snippet in t]
    if not hits:
        raise KeyError(f"snippet not found in {section}: {snippet!r}")
    if len(hits) > 1:
        raise KeyError(f"snippet ambiguous in {section}: {snippet!r}")
    page, text = hits[0]
    return {"text": text, "page": page}

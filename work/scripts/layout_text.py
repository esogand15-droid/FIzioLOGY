"""Layout-aware reconstruction of the Persian text layers of the course PDFs.

Problem
-------
The course notes were written in Word/Slides and exported with an encoder that
splits every visual line into several short *spans* (one per bidirectional run)
and stores them in an order that is neither the reading order nor the visual
order. A plain ``get_text()`` therefore returns lines such as::

    ".فرار یا دفاع) رو انجام بده"      instead of  "فرار یا دفاع) رو انجام بده."
    "شاملمغز  ونخاع  .هست"            instead of  "شامل مغز و نخاع هست."

The visual geometry is still correct, so we rebuild every visual line from the
span bounding boxes (same baseline, right-to-left), then repair punctuation that
the encoder stored at the wrong end of a span.

Guarantees
----------
* No word is added, removed or replaced here (word-level fixes live in
  ``fa_text.FA_WORD_REPAIRS`` and are logged).
* Every page keeps its source page number, so a block can always be traced back
  to the printed page of the original PDF.
"""
from __future__ import annotations

import re

from fa_text import normalize_letters

SENT_FINAL = ".!?…»"
COLONISH = ":،؛"
OPENERS = "([«"
CLOSERS = ")]»"
LINE_TOL = 4.0

LATIN_RUN = re.compile(r"[A-Za-z][A-Za-z0-9 ,\-/&\.]*")


def _spans(page) -> list[dict]:
    out = []
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for s in line["spans"]:
                if not s["text"].strip():
                    continue
                out.append({
                    "y": (s["bbox"][1] + s["bbox"][3]) / 2,
                    "x0": s["bbox"][0],
                    "text": s["text"],
                    "size": round(s["size"], 1),
                    "bold": "Bold" in s["font"],
                })
    return out


def group_lines(spans: list[dict]) -> list[dict]:
    spans = sorted(spans, key=lambda s: (s["y"], -s["x0"]))
    lines: list[dict] = []
    for s in spans:
        if lines and abs(s["y"] - lines[-1]["y"]) <= LINE_TOL:
            lines[-1]["spans"].append(s)
        else:
            lines.append({"y": s["y"], "spans": [s]})
    for ln in lines:
        ln["spans"].sort(key=lambda s: -s["x0"])           # right-to-left
        ln["size"] = max(s["size"] for s in ln["spans"])
        ln["bold"] = any(s["bold"] for s in ln["spans"])
    return lines


def _prep_span(text: str) -> tuple[str, str, str]:
    """Return (leading sentence punctuation, core text, trailing punctuation)."""
    t = text.strip()
    lead = ""
    while t and (t[0] in SENT_FINAL or t[0] in COLONISH or t[0] in CLOSERS):
        lead += t[0]
        t = t[1:].lstrip()
    trail = ""
    while t and (t[-1] in COLONISH):
        trail = t[-1] + trail
        t = t[:-1].rstrip()
    return lead, t, trail


def _fix_inner(text: str) -> str:
    """Repairs that are local to one span."""
    t = text
    t = re.sub(r"(\S):(\S)", lambda m: m.group(1) + "\u200c" + m.group(2), t)  # می:کنه
    t = re.sub(r"\(\s+", "(", t)
    t = re.sub(r"\s+\)", ")", t)
    t = re.sub(r"(\S)\(", r"\1 (", t)                     # 'شامل(اعصاب' -> 'شامل (اعصاب'
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


def move_parens_around_latin(text: str) -> str:
    """'ناهماهنگی حرکتیAtaxia)' -> 'ناهماهنگی حرکتی (Ataxia)' and similar fixes."""
    def fix_group(m: re.Match) -> str:
        inner = m.group(1).strip()
        tail = ""
        while inner and inner[-1] in ":،؛؟!.":
            tail = inner[-1] + tail
            inner = inner[:-1].rstrip()
        lm = re.search(r"[A-Za-z][A-Za-z0-9 \-/&\.]*$", inner)
        if lm and lm.start() > 0:
            pass
        if lm and lm.start() > 0:
            persian = inner[:lm.start()].strip()
            latin = inner[lm.start():].strip()
            if re.search(r"[\u0600-\u06FF]", persian):
                return f"{persian} ({latin}){tail}"
        lm2 = re.match(r"^[A-Za-z][A-Za-z0-9 \-/&\.]*", inner)
        if lm2 and lm2.end() < len(inner) and re.search(r"[\u0600-\u06FF]", inner[lm2.end():]):
            return f"({inner[:lm2.end()].strip()}){inner[lm2.end():]}"
        return "(" + inner + ")" + tail

    prev = None
    out = text
    while prev != out:
        prev = out
        out = re.sub(r"\(([^()]*)\)", fix_group, out)
    return out


def _wrap_latin_runs(text: str) -> str:
    """A Latin term that follows an unmatched '(' gets its closing ')' etc."""
    if "(" not in text and ")" not in text:
        return text
    if text.count("(") != text.count(")"):
        text = re.sub(r"(?<![\u0600-\u06FF])\(|\)(?!\s*[\u0600-\u06FF])", "", text)
    return text


def _join(parts: list[str]) -> str:
    out = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if not out:
            out = p
        elif out.endswith(tuple(OPENERS)) or p[0] in CLOSERS:
            out += p
        elif out.endswith("\u200c"):
            out += p
        elif re.match(r"^[A-Za-z0-9]", p) and re.search(r"[\u0600-\u06FF]$", out):
            out += " " + p
        elif re.search(r"[A-Za-z0-9]$", out) and re.match(r"^[\u0600-\u06FF]", p):
            out += " " + p
        else:
            out += " " + p
    return re.sub(r"\s{2,}", " ", out).strip()


def logical_line(spans_rtl: list[dict]) -> str:
    """Build one logical line from the right-to-left ordered spans of a visual line."""
    parts: list[str] = []
    line_trail = ""
    for sp in spans_rtl:
        raw = sp["text"]
        if raw.strip() in {"•", "▪", "\u2022", "-"}:
            continue
        if re.fullmatch(r"[.:]\s*", raw):      # ordinal dot after a list number
            if parts and re.fullmatch(r"[\u06F0-\u06F9]+", parts[-1]):
                parts[-1] = parts[-1] + "."
            else:
                line_trail += "."
            continue
        lead, core, trail = _prep_span(raw)
        holder = {"paren": False}
        for ch in lead:
            if ch in COLONISH:
                if parts:
                    parts[-1] = parts[-1] + ch
            elif ch in CLOSERS:
                if parts:
                    parts[-1] = parts[-1] + ch
            elif ch in OPENERS:
                holder["paren"] = True
            else:
                line_trail += ch
        if not core:
            if holder["paren"]:
                parts.append("(")
            continue
        core = _fix_inner(core)
        if holder["paren"]:
            core = "(" + core
        if trail:
            core = core + trail
        parts.append(core)
    text = _join([p for p in parts if p != ""]) if parts else ""
    if line_trail:
        text = text.rstrip() + "".join(dict.fromkeys(line_trail))
    text = _wrap_latin_runs(text)
    text = move_parens_around_latin(text)
    text = fix_word_periods(text)
    text = fix_list_marker_digits(text)
    text = re.sub(r"\s+([.,:؛؟!»])", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def fix_word_periods(text: str) -> str:
    """'می.کنه' -> 'می‌کنه' ، 'سلول.هاست' -> 'سلول‌هاست' (displaced sentence period)."""
    ZWNJ = "\u200c"
    t = re.sub(r"(^|[\s(])می\.(?=[\u0600-\u06FF])", lambda m: m.group(1) + "می" + ZWNJ, text)
    t = re.sub(r"\.(ها|های|هاست|هایی)(?![\u0600-\u06FF])", lambda m: ZWNJ + m.group(1), t)
    t = re.sub(r"([\u0600-\u06FF])\.([\u0600-\u06FF]{2,})", lambda m: m.group(1) + ZWNJ + m.group(2), t)
    return t


def fix_list_marker_digits(text: str) -> str:
    """Render a leading ASCII list number in Persian digits (never touches 5-HT, D1, cAMP)."""
    m = re.match(r"^(\d{1,2})([.)])\s*", text)
    if not m:
        return text
    fa = m.group(1).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    return fa + m.group(2) + " " + text[m.end():]


def page_lines(page) -> list[dict]:
    """Return logical lines of one page with heading/bullet metadata."""
    lines = []
    for ln in group_lines(_spans(page)):
        text = logical_line(ln["spans"])
        text = normalize_letters(text)
        if not text:
            continue
        is_bullet = ln["spans"][0]["text"].strip() in {"•", "▪", "-"} or \
            any(s["text"].strip() == "•" for s in ln["spans"])
        heading = ln["size"] >= 13.4 and ln["bold"] and len(text) <= 120
        lines.append({"text": text, "size": ln["size"], "bold": ln["bold"],
                      "is_bullet": is_bullet, "is_heading": heading})
    return lines

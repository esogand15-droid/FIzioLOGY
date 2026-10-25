"""Bidirectional (RTL) repair for Persian text layers extracted from the course PDFs.

Why this file exists
--------------------
The student notes were produced in Word/Slides and exported to PDF with a
font/encoder that stores right-to-left runs in *visual* order for punctuation.
A naive ``get_text()`` therefore returns e.g. ``".فرار یا دفاع( رو انجام بده"``
instead of ``"فرار یا دفاع) رو انجام بده."`` and ``"می:کنه"`` instead of
``"می‌کنه"``.  On top of that the lam-alef ligature (لا) is stored reversed as
(ال) inside a handful of words (``اطالعات`` → ``اطلاعات``).

The repairs below NEVER change, add or remove words: they only move punctuation,
re-join split tokens, restore lam-alef in a **closed list of verified tokens**
(``FA_WORD_REPAIRS``) and normalise spacing.  Every repair is counted in a log so
an editor can audit it, and the untouched extraction is always kept next to the
repaired text (``raw_text`` vs ``render_text`` in the session JSON).

Rules are deliberately conservative: when in doubt, leave the text as extracted.
"""
from __future__ import annotations

import re

# --- verified lam-alef / spacing repairs (broken token -> correct token) ------
FA_WORD_REPAIRS = {
    "اطالعات": "اطلاعات", "اطالعاتی": "اطلاعاتی", "باال": "بالا", "باالی": "بالای",
    "باالترین": "بالاترین", "باالتر": "بالاتر", "عضالت": "عضلات", "عضالنی": "عضلانی",
    "عضالت": "عضلات", "طوالنی": "طولانی", "طوالنیمدت": "طولانیمدت",
    "کالس": "کلاس", "کالسیک": "کلاسیک", "کالسی": "کلاسی", "حاال": "حالا",
    "برخالف": "برخلاف", "گالیسین": "گلایسین", "عالوه": "علاوه", "اختالالت": "اختلالات",
    "اختالل": "اختلال", "طالیی": "طلایی", "اتصاالت": "اتصالات", "اصطالحا": "اصطلاحا",
    "اصطالح": "اصطلاح", "عالئم": "علائم", "نوروفیالمانها": "نوروفیلامانها",
    "بالفاصله": "بلافاصله", "تاالموس": "تالاموس", "هیپوتاالموس": "هیپوتالاموس",
    "مالتونین": "ملاتونین", "هایپرپوالریزاسیون": "هایپرپلاریزاسیون",
    "مولتیپوالر": "مولتیپلار", "آندوپالسمی": "آندوپلاسمی", "ابالغ": "ابلاغ",
    "بصلالنخاع": "بصل‌النخاع", "سریعاالثر": "سریع‌الاثر", "معموال": "معمولا",
    "کامال": "کاملا", "مثال": "مثال", "اصال": "اصلا", "سوال": "سوال",
    "گلیال": "گلیال", "فانکشنال": "فانکشنال",
}

# a word boundary that also respects Persian half-space (ZWNJ) and punctuation
_WORD_SPLIT = re.compile(r"([\u0600-\u06FF\u200c]+)")

LEAD_PUNCT = ".:،؛؟!)»]"
NUM_LINE = re.compile(r"^[\s.()\-–]*[۰-۹0-9]+[\s.)\-–]*$")

REPAIR_RULES = (
    "strip_markdown_bold",
    "normalize_letters",
    "merge_lone_paren_lines",
    "number_marker_merge",
    "leading_punctuation_to_end",
    "colon_inside_word",
    "paren_space_and_placement",
    "word_repairs_lam_alef",
    "tanwin_spacing",
    "join_lines",
)


def normalize_letters(text: str) -> str:
    return (text.replace("\u064a", "\u06cc").replace("\u0643", "\u06a9")
                .replace("\u0640", "").replace("\u200e", "").replace("\u200f", ""))


def strip_markdown_bold(text: str) -> str:
    return text.replace("**", "")


def _fix_leading_punct(line: str) -> str:
    """'.متن' -> 'متن.' ، ':متن' -> 'متن:' ، '؟متن' -> 'متن؟'"""
    m = re.match(r"^([.:،؛؟!]+)\s*(.+)$", line)
    if m and not re.match(r"^[.:،؛؟!]+$", line):
        return f"{m.group(2).strip()} {m.group(1)}".replace(" :", ":").strip()
    return line


def _fix_colon_inside_word(line: str) -> str:
    # 'می:کنه' -> 'می‌کنه'
    return re.sub(r"(\w):(\w)", lambda m: m.group(1) + "\u200c" + m.group(2), line)


def split_lines(raw: str) -> list[str]:
    lines = [strip_markdown_bold(normalize_letters(x)).strip() for x in raw.split("\n")]
    return [x for x in lines if x and x not in {"```"}]


def merge_line_fragments(lines: list[str]) -> list[str]:
    """Re-assemble fragments the bidi encoder split across lines.

    * a line that contains only a number becomes a list marker for the next line;
    * a line that is only ')' or '(' is glued back to its neighbour;
    * a leading punctuation mark is moved to the end of its line.
    """
    out: list[str] = []
    pending_num: str | None = None
    for line in lines:
        if NUM_LINE.match(line):
            pending_num = re.sub(r"[^۰-۹0-9]", "", line)
            continue
        if line in {")", "("}:            # lone bracket fragment
            if out:
                out[-1] = out[-1] + line
            continue
        if pending_num:
            line = f"{pending_num}. {line.lstrip('.() ')}"
            pending_num = None
        line = _fix_leading_punct(line)
        line = _fix_colon_inside_word(line)
        # ")  سیستم" / "( دهی" -> "(دهی"
        line = re.sub(r"\(\s+", "(", line)
        line = re.sub(r"\s+\)", ")", line)
        out.append(line.strip())
    return out


def repair_parens_in_heading(text: str) -> str:
    """Move an unbalanced '(' to just before the Latin term it belongs to.

    Broken encoders emit ``سازمان( دهی ساختاریStructural Organization`` + ``)``;
    the intended form is ``سازمان‌دهی ساختاری (Structural Organization)``.
    """
    if text.count("(") == text.count(")") or "(" not in text:
        return text
    latin = re.search(r"[A-Za-z][A-Za-z /\-\.]{2,}", text)
    if not latin:
        return text
    cleaned = text.replace("(", "").replace(")", "").strip()
    start, end = latin.start(), latin.end()
    # recompute after removing parens (positions shift by the removed count)
    before = text[:start].count("(") + text[:start].count(")")
    start -= before
    end -= text[:end].count("(") + text[:end].count(")")
    body = text.replace("(", "").replace(")", "")
    if end > len(body):
        return text
    return f"{body[:start].rstrip()} ({body[start:end].strip()}){body[end:]}".strip()


def word_repairs(text: str, log: dict[str, int] | None = None) -> str:
    def repl(match: re.Match) -> str:
        w = match.group(0)
        fixed = FA_WORD_REPAIRS.get(w)
        if fixed and fixed != w:
            if log is not None:
                log[w] = log.get(w, 0) + 1
            return fixed
        return w

    return _WORD_SPLIT.sub(repl, text)


def tanwin_spacing(text: str) -> str:
    # 'اصالًچرا' -> 'اصلاً چرا'
    return re.sub(r"ً(?=[\u0600-\u06FFA-Za-z])", "ً ", text)


def join_lines(lines: list[str]) -> list[str]:
    """Join wrapped lines into paragraphs.

    Kept separate from the PDF/block builder because the caller knows about
    bullets; here we only join a line to the previous one when it looks like a
    soft wrap (no sentence-final punctuation, next line does not start a bullet).
    """
    paras: list[str] = []
    for line in lines:
        is_bullet = bool(re.match(r"^[•\-\u2022]\s*", line)) or bool(re.match(r"^[۰-۹0-9]+[\.\)]\s", line))
        if paras and not is_bullet and not re.search(r"[.!؟:؛]$", paras[-1]) and \
                not re.match(r"^[A-Za-z]", line):
            sep = "" if paras[-1].endswith("\u200c") else " "
            paras[-1] = f"{paras[-1]}{sep}{line}"
        else:
            paras.append(line)
    return paras


def repair_block(raw: str, log: dict[str, int] | None = None) -> list[str]:
    lines = merge_line_fragments(split_lines(raw))
    paras = join_lines(lines)
    out = []
    for p in paras:
        p = repair_parens_in_heading(p) if len(p) < 130 else p
        p = word_repairs(p, log)
        p = tanwin_spacing(p)
        p = re.sub(r"\s{2,}", " ", p).strip()
        out.append(p)
    return out

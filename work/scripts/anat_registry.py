"""رجیستری منابع آناتومی: متن جزوه‌ها + فهرست تصاویر (بدون استخراج بایت‌ها).

چرا بدون استخراج: مخزن نباید با صدها مگابایت تصویر پر شود. این اسکریپت برای هر تصویر
شناسه، صفحه، ابعاد، جعبهٔ مکانی، مساحت نسبی و sha256 را در JSON ثبت می‌کند؛ خودِ فایل
تصویر فقط زمانی نوشته می‌شود که یک جلسه واقعاً به آن نیاز داشته باشد
(``--export سشن``).

خروجی‌ها
--------
work/anatomy/registry_lectures.json   تصاویر ۱۳ جزوه
work/anatomy/registry_snell.json      شکل‌های Snell 9e
work/extraction/anat/map.json         نقشهٔ جلسه ← فایل(ها)
work/extraction/anat/sNN_text.json    متن صفحه‌به‌صفحهٔ جزوه‌های هر جلسه

اجرا
----
    .venv/bin/python work/scripts/anat_registry.py            # همه
    .venv/bin/python work/scripts/anat_registry.py --snell     # فقط Snell
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
REF = Path("/home/user/_refs")          # نسخهٔ محلی فایل‌های شاخهٔ main
OUT = REPO / "work" / "anatomy"
TXT = REPO / "work" / "extraction" / "anat"

SNELL = REF / "Snells Clinical Neuroanatomy, 9th Edition (Ryan Splittgerber) (z-library.sk, 1lib.sk, z-lib.sk).pdf"

# جلسهٔ رسمی ← جزوه(ها). نام‌ها دقیقاً همان فایل‌های مخزن‌اند.
SESSIONS: dict[str, list[Path]] = {
    "s01": [REF / "lectures/جلسه 1 بافت شناسی/نورو آناتومی جلسه 1 و 2 مهر 1404.pdf"],
    "s02": [REF / "lectures/جلسه 2 بافت شناسی 2/نورو آناتومی جلسه 1 و 2 مهر 1404 (2).pdf"],
    "s03": [REF / "lectures/جلسه 3 نخاع/آناتومی اعصاب جلسه ۳ مهر 1404.pdf"],
    "s04": [REF / "lectures/جلسه 4 نخاع 2/نورو آناتومی جلسه ۴ مهر 1404.pdf"],
    "s05": [REF / "lectures/جلسه 5 ساقه مغز/نورو اناتومی جلسه ۵ مهر 1404.pdf"],
    "s06": [REF / "lectures/جلسه 6 ساقه مغز 2/نورو آناتومی جلسه ۶ مهر 1404.pdf"],
    "s07": [REF / "lectures/جلسه 7 مخچه/نورو آناتومی جلسه 7 بهمن 1402.pdf"],
    "s08": [REF / "lectures/جلسه 8 دیانسفال/نور آناتومی جلسه 8 پارت 1 بهمن 1402.pdf"],
    "s09": [REF / "lectures/جلسه 8 دیانسفال/نورو_آناتومی_جلسه_8_پارت_2_و_جلسه_9_پارت_1_بهمن_1402.pdf",
            REF / "lectures/جلسه 9 تلانسفال/نورو آناتومی جلسه 9 پارت 2 بهمن 1402.pdf"],
    "s10": [REF / "lectures/جلسه 10 هسته های قاعده ای/نورو آناتومی جلسه 10 بهمن 1402 .pdf"],
    "s11": [REF / "lectures/جلسه 11 لیمبیک/نورو آناتومی جلسه 11 مهر 1397.pdf"],
    "s12": [REF / "lectures/S12_ANS.pdf"],
    "s13": [REF / "lectures/جلسه 13 تکامل مغز/نورو آناتومی جلسه 13 مهر 1397.pdf"],
}

CHAPTERS = {
    1: "Organization of the Nervous System", 2: "Neurons and Neuroglia",
    3: "Nerve Fibers and Peripheral Innervation",
    4: "Spinal Cord and Ascending, Descending, and Intersegmental Tracts",
    5: "Brainstem", 6: "Cranial Nerve Nuclei", 7: "Cerebellum and Its Connections",
    8: "Reticular Formation and Limbic System", 9: "Basal Nuclei",
    10: "Thalamus", 11: "Hypothalamus", 12: "Autonomic Nervous System",
    13: "Cerebrum", 14: "Structure and Functional Localization of the Cerebral Cortex",
    15: "Meninges", 16: "Ventricular System and CSF",
    17: "Blood Supply of the Brain and Spinal Cord", 18: "Nervous System Development",
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def classify(w: int, h: int, area_pct: float, page_w_h: tuple[float, float]) -> str:
    if area_pct > 85:
        return "fullpage"
    if area_pct < 3 or min(w, h) < 120:
        return "decoration"
    if max(w / max(h, 1), h / max(w, 1)) > 3.2:
        return "strip"
    return "figure"


def scan_booklet(sid: str, path: Path) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    pages_text: list[dict] = []
    if not path.exists():
        return rows, pages_text
    with pymupdf.open(path) as d:
        for i, page in enumerate(d, start=1):
            t = page.get_text()
            pages_text.append({"page": i, "words": len(t.split()), "text": t})
            pw, ph = page.rect.width, page.rect.height
            for k, im in enumerate(page.get_images(full=True)):
                xref, smask, w, h = im[0], im[1], im[2], im[3]
                try:
                    bb = page.get_image_bbox(im)
                except Exception:
                    continue
                pct = 100 * (bb.width * bb.height) / (pw * ph)
                try:
                    info = d.extract_image(xref)
                    digest = sha(info["image"])
                    nbytes = len(info["image"])
                    ext = info["ext"]
                except Exception:
                    digest, nbytes, ext = "", 0, ""
                rows.append(dict(
                    asset_id=f"{sid}_p{i:03d}_img{k+1:02d}", session=sid,
                    file=path.name, page=i, xref=xref, index=k,
                    w=w, h=h, px=w * h, bbox=[round(v, 1) for v in bb],
                    area_pct=round(pct, 1), kind=classify(w, h, pct, (pw, ph)),
                    sha256=digest, bytes=nbytes, ext=ext,
                ))
    return rows, pages_text


def build_lectures() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    TXT.mkdir(parents=True, exist_ok=True)
    allrows: list[dict] = []
    seen_sha: dict[str, str] = {}
    summary = []
    for sid, files in sorted(SESSIONS.items()):
        rows: list[dict] = []
        texts: dict[str, list] = {}
        for f in files:
            r, t = scan_booklet(sid, f)
            rows += r
            texts[f.name] = t
        for r in rows:
            if r["sha256"] and r["sha256"] in seen_sha:
                r["duplicate_of"] = seen_sha[r["sha256"]]
            elif r["sha256"]:
                seen_sha[r["sha256"]] = r["asset_id"]
        allrows += rows
        (TXT / f"{sid}_text.json").write_text(
            json.dumps(texts, ensure_ascii=False, indent=1), encoding="utf-8")
        figs = [r for r in rows if r["kind"] == "figure"]
        summary.append(dict(session=sid, files=[f.name for f in files],
                            pages=sum(len(v) for v in texts.values()),
                            images=len(rows), figures=len(figs),
                            words=sum(p["words"] for v in texts.values() for p in v)))
        print(f"{sid}: {summary[-1]['pages']:>3}p words={summary[-1]['words']:>5} "
              f"images={len(rows):>3} figure={len(figs):>3}")
    (OUT / "registry_lectures.json").write_text(
        json.dumps({"generated_by": "work/scripts/anat_registry.py",
                    "source": "branch main — علوم تشریح دستگاه اعصاب",
                    "summary": summary, "images": allrows},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    (TXT / "map.json").write_text(
        json.dumps({k: [f.name for f in v] for k, v in SESSIONS.items()},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    tot_i = sum(s["images"] for s in summary)
    tot_f = sum(s["figures"] for s in summary)
    dup = sum(1 for r in allrows if r.get("duplicate_of"))
    print(f"TOTAL pages={sum(s['pages'] for s in summary)} images={tot_i} "
          f"figure={tot_f} duplicate_images={dup}")


def build_snell() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(SNELL) as d:
        toc = d.get_toc(simple=True)
        starts = [(t[1], t[2]) for t in toc if t[1].startswith("Chapter")]
        bounds = []
        for i, (title, start) in enumerate(starts):
            end = starts[i + 1][1] - 1 if i + 1 < len(starts) else 1176
            n = int(re.match(r"Chapter (\d+)", title).group(1))
            bounds.append((n, start, end))
        rows = []
        for n, start, end in bounds:
            for p in range(start, end + 1):
                page = d[p - 1]
                for k, im in enumerate(page.get_images(full=True)):
                    try:
                        bb = page.get_image_bbox(im)
                    except Exception:
                        continue
                    pct = 100 * (bb.width * bb.height) / (page.rect.width * page.rect.height)
                    try:
                        info = d.extract_image(im[0])
                        digest, nbytes = sha(info["image"]), len(info["image"])
                    except Exception:
                        digest, nbytes = "", 0
                    rows.append(dict(
                        asset_id=f"snell_ch{n:02d}_p{p:04d}_img{k+1:02d}", book="snell",
                        chapter=n, chapter_title=CHAPTERS[n], page=p,
                        w=im[2], h=im[3], px=im[2] * im[3],
                        bbox=[round(v, 1) for v in bb], area_pct=round(pct, 1),
                        kind=classify(im[2], im[3], pct, (page.rect.width, page.rect.height)),
                        sha256=digest, bytes=nbytes))
    seen: dict[str, str] = {}
    for r in rows:
        if r["sha256"] in seen:
            r["duplicate_of"] = seen[r["sha256"]]
        else:
            seen[r["sha256"]] = r["asset_id"]
    (OUT / "registry_snell.json").write_text(
        json.dumps({"generated_by": "work/scripts/anat_registry.py",
                    "book": "Snell's Clinical Neuroanatomy, 9th ed. (2025), file pages",
                    "note": "شمارهٔ صفحه = صفحهٔ فایل، نه چاپی (بازچینش calibre)",
                    "images": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    figs = [r for r in rows if r["kind"] == "figure"]
    uniq = len({r["sha256"] for r in figs})
    print(f"snell: images={len(rows)} figure={len(figs)} unique_figure_sha={uniq} "
          f"dupes={sum(1 for r in rows if r.get('duplicate_of'))}")
    per = {}
    for r in figs:
        per.setdefault(r["chapter"], 0)
        per[r["chapter"]] += 1
    print("figures per chapter:", dict(sorted(per.items())))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snell", action="store_true")
    ap.add_argument("--lectures", action="store_true")
    a = ap.parse_args()
    if a.snell or not (a.snell or a.lectures):
        build_snell()
    if a.lectures or not (a.snell or a.lectures):
        build_lectures()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

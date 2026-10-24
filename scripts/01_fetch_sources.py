#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HumsYar Neuro Master Book — مرحله ۱: دریافت و اعتبارسنجی منابع از مخزن GitHub

- همه فایل‌های پوشه منابع را پیمایش می‌کند.
- فایل‌های معمولی را با حفظ ساختار در src/extracted کپی می‌کند.
- فایل‌های Git LFS (pointer) را از LFS Batch API مخزن دانلود می‌کند.
- برای هر فایل: اندازه، sha256، وضعیت، تعداد تلاش و یادداشت را در
  work/source_download_manifest.csv ثبت می‌کند.

استفاده:
  python3 scripts/01_fetch_sources.py            # فقط اسناد (بدون ویدئو)
  python3 scripts/01_fetch_sources.py --videos   # همراه ویدئوها
"""
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "فیزیولوژی اعصاب حواس ویژه")
DEST_DIR = os.path.join(ROOT, "src", "extracted")
WORK = os.path.join(ROOT, "work")
MANIFEST = os.path.join(WORK, "source_download_manifest.csv")
REPO = "esogand15-droid/FIzioLOGY"
LFS_ENDPOINT = f"https://github.com/{REPO}.git/info/lfs/objects/batch"

POINTER_RE = re.compile(rb"^version https://git-lfs\.github\.com/spec/v1\s*$")
VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov"}


def sha256_of(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def read_pointer(path):
    """اگر فایل، pointer گیت‌ال‌اف‌اس باشد دیکشنری oid/size برمی‌گرداند."""
    with open(path, "rb") as f:
        head = f.read(400)
    if not POINTER_RE.match(head.split(b"\n", 1)[0] + b""):
        return None
    txt = head.decode("utf-8", "replace")
    oid = re.search(r"oid sha256:([0-9a-f]{64})", txt)
    size = re.search(r"size (\d+)", txt)
    if oid and size:
        return {"oid": oid.group(1), "size": int(size.group(1))}
    return None


def lfs_download(oid, size, dest, retries=4):
    """دانلود یک آبجکت LFS با تلاش مجدد؛ بازگشت (ok, note, retry_count)."""
    note = ""
    last = None
    for attempt in range(1, retries + 1):
        try:
            payload = json.dumps(
                {"operation": "download", "transfers": ["basic"],
                 "objects": [{"oid": oid, "size": size}]}
            ).encode()
            req = urllib.request.Request(
                LFS_ENDPOINT, data=payload,
                headers={"Accept": "application/vnd.git-lfs+json",
                         "Content-Type": "application/vnd.git-lfs+json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                info = json.loads(r.read().decode())
            obj = info["objects"][0]
            href = obj.get("actions", {}).get("download", {}).get("href")
            if not href:
                return False, f"LFS: no download action ({obj.get('error')})", attempt
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            tmp = dest + ".part"
            have = os.path.getsize(tmp) if os.path.exists(tmp) else 0
            h = hashlib.sha256()
            if have:
                with open(tmp, "rb") as f:
                    for b in iter(lambda: f.read(1 << 20), b""):
                        h.update(b)
                if have >= size:
                    have = 0
            headers = {"Range": f"bytes={have}-"} if have else {}
            rq = urllib.request.Request(href, headers=headers)
            with urllib.request.urlopen(rq, timeout=120) as resp, open(tmp, "ab" if have else "wb") as out:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
                    h.update(chunk)
            if os.path.getsize(tmp) != size:
                note = f"size mismatch: {os.path.getsize(tmp)} != {size}"
                continue
            if h.hexdigest() != oid:
                os.remove(tmp)
                note = "sha256 mismatch (downloaded object is not the LFS object)"
                continue
            os.replace(tmp, dest)
            return True, "LFS object verified", attempt
        except Exception as e:  # noqa: BLE001
            last = e
            note = f"attempt {attempt} failed: {e}"
            time.sleep(2 * attempt)
    return False, note or f"failed: {last}", retries


def main():
    want_videos = "--videos" in sys.argv
    os.makedirs(DEST_DIR, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    rows = []
    files = []
    for dirpath, _dirnames, filenames in os.walk(SRC_DIR):
        for fn in sorted(filenames):
            files.append(os.path.join(dirpath, fn))
    files.sort()
    for path in files:
        rel = os.path.relpath(path, ROOT)
        dest = os.path.join(DEST_DIR, os.path.relpath(path, SRC_DIR))
        ext = os.path.splitext(path)[1].lower()
        ptr = read_pointer(path)
        rec = {
            "filename": os.path.basename(path),
            "github_path": rel.replace(os.sep, "/"),
            "expected_size": "",
            "downloaded_size": "",
            "status": "",
            "checksum": "",
            "retry_count": 0,
            "notes": "",
            "extraction_class": "source",
        }
        if ptr is None:
            size = os.path.getsize(path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if not (os.path.exists(dest) and os.path.getsize(dest) == size):
                shutil.copy2(path, dest)
            rec.update(expected_size=size, downloaded_size=os.path.getsize(dest),
                       status="ok-regular", checksum=sha256_of(dest),
                       notes="regular git object; copied verbatim to src/extracted")
        else:
            rec.update(expected_size=ptr["size"], checksum="sha256:" + ptr["oid"],
                       notes="git-lfs pointer in working tree")
            if ext in VIDEO_EXT and not want_videos:
                rec.update(status="skipped-lfs-video",
                           notes=("git-lfs pointer; ویدئو در این اجرا دانلود نشد "
                                  "(حجم بالا + نبود مدل ASR آفلاین). برای دریافت: --videos"))
            else:
                ok, note, tries = lfs_download(ptr["oid"], ptr["size"], dest)
                rec.update(status="ok-lfs" if ok else "failed-lfs",
                           downloaded_size=os.path.getsize(dest) if ok else 0,
                           retry_count=tries, notes=note)
        rows.append(rec)
        print(f"{rec['status']:18s} {rec['github_path']}")

    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    ok = sum(1 for r in rows if r["status"].startswith("ok"))
    print(f"\n{len(rows)} فایل، {ok} دریافت/تأییدشده → {MANIFEST}")


if __name__ == "__main__":
    main()

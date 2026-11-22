#!/usr/bin/env python3
"""Fetch only the already listed V4 portrait candidates and record results.

No new characters, no invented art; never modifies existing 239 assets.
External image retrieval does NOT verify character identity or rights.
"""
from __future__ import annotations
import concurrent.futures
import hashlib
import io
import json
import pathlib
import time
import urllib.request
from PIL import Image, UnidentifiedImageError

ROOT = pathlib.Path(__file__).resolve().parent
MANIFEST = ROOT / "import_manifest.json"
DEST = ROOT / "assets" / "imported"
REPORT = ROOT / "import_report.json"
DEST.mkdir(parents=True, exist_ok=True)

def fetch_one(entry):
    idx, name, url = entry["id"], entry["name"], entry["url"]
    result = {"id": idx, "name": name, "source_url": url, "status": "failed"}
    if not url.startswith(("https://", "http://")):
        result["reason"] = "non_http_url"
        return result
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; V4-Portrait-Archive/1.0)",
            "Accept": "image/avif,image/webp,image/png,image/jpeg,image/*;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=14) as r:
            data = r.read(10_000_001)
        if not 1500 <= len(data) <= 10_000_000:
            raise ValueError("image too small or above 10 MB")
        with Image.open(io.BytesIO(data)) as img:
            fmt = img.format
            width, height = img.size
            img.verify()
        exts = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp", "GIF": "gif", "AVIF": "avif"}
        if fmt not in exts or min(width, height) < 100:
            raise ValueError("invalid format/dimensions: %s %sx%s" % (fmt, width, height))
        checksum = hashlib.sha256(data).hexdigest()
        out = DEST / ("%03d_%s.%s" % (idx, checksum[:10], exts[fmt]))
        if not out.exists():
            out.write_bytes(data)
        result.update(status="downloaded", path=str(out.relative_to(ROOT.parent)),
                      width=width, height=height, bytes=len(data), sha256=checksum,
                      format=fmt)
    except Exception as e:
        result["reason"] = (type(e).__name__ + ": " + str(e))[:250]
    return result

def main():
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["entries"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        report = list(executor.map(fetch_one, entries))
    report.sort(key=lambda x:x["id"])
    REPORT.write_text(json.dumps({"entries": report, "downloaded": sum(x["status"] == "downloaded" for x in report),
                                "total":len(report)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("downloaded", sum(x["status"] == "downloaded" for x in report), "/", len(report))
    for x in report:
        if x["status"] != "downloaded":
            print("FAIL", x["name"], x.get("reason"))
if __name__ == "__main__":
    main()

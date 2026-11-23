#!/usr/bin/env python3
"""Archive already user-approved V4 portrait source bytes, without image edits."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
from PIL import Image, UnidentifiedImageError

ROOT = Path("new-15")
REPO = "fsffsukeuwi-beep/v4-portraits-test"
ITEMS = json.loads((ROOT / "approved_portraits.json").read_text(encoding="utf-8"))["items"]
EXTS = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp", "GIF": "gif"}
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36", "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"}
output = []
folder = ROOT / "assets"
folder.mkdir(parents=True, exist_ok=True)

for item in ITEMS:
    entry = {k: item[k] for k in ("id", "name", "faction", "slug", "source_url", "source_provenance", "combat")}
    entry["status"] = "failed"
    for attempt in range(3):
        try:
            req = urllib.request.Request(item["source_url"], headers=HEADERS)
            with urllib.request.urlopen(req, timeout=22) as response:
                raw = response.read(16 * 1024 * 1024 + 1)
                if len(raw) > 16 * 1024 * 1024:
                    raise ValueError("image exceeds 16 MiB")
            with Image.open(io.BytesIO(raw)) as im:
                fmt = im.format
                w, h = im.size
                im.verify()
            if fmt not in EXTS:
                raise ValueError(f"unsupported image format: {fmt}")
            if w < 100 or h < 100:
                raise ValueError(f"image too small: {w}x{h}")
            filename = f"{item['id']}_{item['slug']}.{EXTS[fmt]}"
            path = folder / filename
            path.write_bytes(raw)
            entry.update(status="saved",path=path.as_posix(),cdn_url=f"https://cdn.jsdelivr.net/gh/{REPO}@main/{path.as_posix()}",format=fmt,width=w,height=h,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            break
        except Exception as exc:
            entry["error"] = str(exc)[:350]
            if attempt < 2:
                time.sleep(1.5 * (attempt+1))
    output.append(entry)
    print(f"{item['id']} {item['name']} {entry['status']} {entry.get('error','')} ",flush=True)

(ROOT/"import_report.json").write_text(json.dumps({"user_approved":"2026-11-23","saved":sum(e["status"]=="saved" for e in output),"total":len(output),"items":output},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
with (ROOT/"portrait_links_15.csv").open("w",encoding="utf-8-sig",newline="") as f:
    wr=csv.writer(f)
    wr.writerow(["ID","인물","소속","공식 승인 상태","원본 확보 상태","저장소 이미지 경로","jsDelivr CDN","원본 출처","출처 유형","근력","이동속도","내구력","반응속도","특수능력","종합전투력","오류"])
    for e in output:
        wr.writerow([e["id"],e["name"],e["faction"],"승인","원본 다운로드 완료" if e["status"]=="saved" else "다운로드 실패",e.get("path",""),e.get("cdn_url",""),e["source_url"],e["source_provenance"],*e["combat"],e.get("error","")])
print("saved",sum(e["status"]=="saved" for e in output),"/",len(output))

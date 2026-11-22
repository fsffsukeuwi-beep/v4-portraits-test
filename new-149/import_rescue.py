#!/usr/bin/env python3
"""Import explicitly reviewed source candidates, never alter the original 239 portraits.

This is an identity-reviewed search shortlist, not copyright or display licensing.
Failed downloads retain '미확보' and do not affect counts.
"""
from __future__ import annotations
import hashlib, io, json, pathlib, re, urllib.request
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parent
DATA=json.loads((ROOT/"rescue_manifest.json").read_text(encoding="utf-8"))["entries"]
DEST=ROOT/"assets"/"rescue"
DEST.mkdir(parents=True,exist_ok=True)
README=ROOT/"README.md"
REPORT=ROOT/"rescue_report.json"
lines=README.read_text(encoding="utf-8").splitlines(keepends=True)
rows=[]
for e in DATA:
  result={"id":e["id"],"name":e["name"],"source_page":e["source_page"],"status":"failed"}
  try:
    req=urllib.request.Request(e["url"],headers={"User-Agent":"Mozilla/5.0 (V4 portrait review; non-commercial)","Accept":"image/webp,image/png,image/jpeg,image/*;q=0.8"})
    with urllib.request.urlopen(req,timeout=20) as conn:
      raw=conn.read(10_000_001)
    if not 1500 <= len(raw) <= 10_000_000:
      raise ValueError("unexpected byte length")
    with Image.open(io.BytesIO(raw)) as im:
      fmt=im.format
      w,h=im.size
      im.verify()
    if fmt not in {"WEBP","PNG","JPEG"} or min(w,h)<150:
      raise ValueError("unexpected image format or dimensions")
    ext={"WEBP":"webp","PNG":"png","JPEG":"jpg"}[fmt]
    path=DEST/("%03d_%s.%s"%(e["id"],hashlib.sha256(raw).hexdigest()[:10],ext))
    if not path.exists(): path.write_bytes(raw)
    rel=str(path.relative_to(ROOT.parent))
    prefix="| "+e["name"]+" ("
    match=[i for i,l in enumerate(lines) if l.startswith(prefix)]
    if len(match)!=1: raise ValueError("README row not unique")
    i=match[0]
    parts=lines[i].strip().split("|")
    if len(parts)<5 or "<img " in parts[2]: raise ValueError("README row already has image")
    tier=parts[1].strip()
    url="https://raw.githubusercontent.com/fsffsukeuwi-beep/v4-portraits-test/main/"+rel
    preview='<img src="'+url+'" width="100" alt="'+e["name"]+'" />'
    source='원작 컷 (외부 재게시, 권리 미확인) · [출처]('+e["source_page"]+') · GitHub 파일 보관'
    lines[i]="| "+tier+" | "+preview+" | "+source+" |\n"
    result.update(status="downloaded",path=rel,bytes=len(raw),width=w,height=h,url=url)
  except Exception as ex:
    result["reason"]=type(ex).__name__+": "+str(ex)
  rows.append(result)
# Count actual media referenced per-character in README, not all extras in the folder.
n=sum(1 for l in lines if re.match(r'^\| [^|]+ \([^)]+\) \|',l) and '<img src=' in l)
# Regex above is intentionally anchored; fallback based on unique row pattern if empty.
if not n:
  n=sum(1 for l in lines if l.startswith("| ") and '<img src=' in l)
md=''.join(lines)
md=re.sub(r'실제 파일 기반 인물별 이미지 확보 \d+명, 미확보 \d+명',f'실제 파일 기반 인물별 이미지 확보 {n}명, 미확보 {149-n}명',md)
asset_count=sum(1 for f in (ROOT/"assets").rglob("*") if f.is_file() and f.suffix.lower() in {".jpg",".jpeg",".png",".webp",".gif"})
md=re.sub(r'총 \d+개 이미지 파일',f'총 {asset_count}개 이미지 파일',md)
README.write_text(md,encoding="utf-8")
REPORT.write_text(json.dumps({"total":len(rows),"downloaded":sum(r["status"]=="downloaded" for r in rows),"entries":rows},ensure_ascii=False,indent=2),encoding="utf-8")
for r in rows: print(r["name"],r["status"],r.get("reason",""))
print("portrait rows archived",n,"unfilled",149-n,"files",asset_count)

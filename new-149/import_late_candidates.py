#!/usr/bin/env python3
"""Grab a few explicitly named portrait candidates, without modifying gallery counts."""
from __future__ import annotations
import concurrent.futures,hashlib,io,json,pathlib,urllib.parse,urllib.request
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parent
DEST=ROOT/'assets'/'late'
DEST.mkdir(parents=True,exist_ok=True)
ARCHIVE=[
 {"id":15,"name":"레니","title":"Leny_original_chimera_sion.PNG","source":"https://knightrun.fandom.com/wiki/Leny"},
 {"id":15,"name":"레니","title":"Leny_vs_tinie.PNG","source":"https://knightrun.fandom.com/wiki/Leny"},
 {"id":15,"name":"레니","title":"Leny_vs_tinie1.PNG","source":"https://knightrun.fandom.com/wiki/Leny"},
 {"id":120,"name":"아린","url":"https://blog.kakaocdn.net/dna/5sAsp/btqGexDmEWt/AAAAAAAAAAAAAAAAAAAAALeMN2gvHbFf4IZckvQ5Us-82zi28lhczDWj1iViKZk3/img.png?allow_ip=&allow_referer=&credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&signature=ICEAMGdAyEZENf0NEkJcLh%2FA9ak%3D","source":"https://ilali90.tistory.com/19"}
]
def one(e):
 r={"id":e["id"],"name":e["name"],"source_page":e["source"],"status":"failed"}
 try:
  url=e.get("url")
  if not url:
   a="https://knightrun.fandom.com/api.php?"+urllib.parse.urlencode({"action":"query","titles":"File:"+e["title"],"prop":"imageinfo","iiprop":"url","iiurlwidth":900,"format":"json","formatversion":2})
   req=urllib.request.Request(a,headers={"User-Agent":"Mozilla/5.0 (V4 review)"})
   with urllib.request.urlopen(req,timeout=18) as f:p=json.load(f)["query"]["pages"][0]
   url=(p.get("imageinfo") or [{}])[0].get("thumburl") or (p.get("imageinfo") or [{}])[0].get("url")
  if not url:raise ValueError("image URL missing")
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"image/avif,image/webp,image/png,image/jpeg,image/*;q=0.8","Referer":e["source"]})
  with urllib.request.urlopen(req,timeout=17) as f: data=f.read(10000001)
  with Image.open(io.BytesIO(data)) as im:
   w,h=im.size;fmt=im.format;im.verify()
  if len(data)<1500 or min(w,h)<100 or fmt not in {"PNG","WEBP","JPEG"}:raise ValueError("bad format/size")
  ext={"PNG":"png","WEBP":"webp","JPEG":"jpg"}[fmt]
  path=DEST/("%03d_%s.%s"%(e["id"],hashlib.sha256(data).hexdigest()[:10],ext))
  if not path.exists():path.write_bytes(data)
  r.update(status="downloaded",path=str(path.relative_to(ROOT.parent)),source_url=url,width=w,height=h,bytes=len(data))
 except Exception as x:r["reason"]=type(x).__name__+": "+str(x)[:210]
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:out=list(p.map(one,ARCHIVE))
(ROOT/"late_candidates_report.json").write_text(json.dumps({"entries":out,"downloaded":sum(x["status"]=="downloaded" for x in out)},ensure_ascii=False,indent=2),encoding="utf-8")
for x in out:print(x["name"],x.get("status"),x.get("reason",""))

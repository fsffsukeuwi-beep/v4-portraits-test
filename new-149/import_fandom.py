#!/usr/bin/env python3
"""Best-effort download of character-specific lead images from exact Fandom wiki pages."""
import concurrent.futures
import hashlib
import io
import json
import pathlib
import re
import urllib.parse
import urllib.request
from PIL import Image

ROOT=pathlib.Path(__file__).resolve().parent
DEST=ROOT/"assets"/"wiki"
DEST.mkdir(parents=True,exist_ok=True)
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; V4-Literary-Image-Review/1.0)","Accept":"application/json,image/*,*/*;q=0.5"}
def req(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=15) as r:
        return r.read(10_000_001)
def fetch(entry):
    result={"id":entry["id"],"name":entry["name"],"wiki":entry["page"],"status":"failed"}
    try:
        p=urllib.parse.urlsplit(entry["page"])
        if not p.hostname or not p.hostname.endswith(".fandom.com") or not p.path.startswith("/wiki/"):
            raise ValueError("not an allowed exact Fandom character page")
        title=urllib.parse.unquote(p.path[len("/wiki/"):])
        api=f"{p.scheme}://{p.netloc}/api.php"
        def query(q):
            return json.loads(req(api+"?"+urllib.parse.urlencode(dict(q,format="json",formatversion=2))))
        j=query(dict(action="query",titles=title,prop="pageimages",pithumbsize=900))
        pages=j.get("query",{}).get("pages",[])
        if not pages or pages[0].get("missing"):
            raise ValueError("wiki page missing")
        thumb=pages[0].get("thumbnail",{}).get("source")
        if not thumb:
            imgs=query(dict(action="parse",page=title,prop="images")).get("parse",{}).get("images",[])
            nameparts=[x.lower() for x in re.split(r"[_ -]+",title) if len(x)>=4]
            likely=[f for f in imgs if any(part in urllib.parse.unquote(f).lower() for part in nameparts)]
            if not likely:
                raise ValueError("no unambiguous lead image")
            selected=likely[0]
            info=query(dict(action="query",titles="File:"+selected,prop="imageinfo",iiprop="url",iiurlwidth=900)).get("query",{}).get("pages",[])
            thumb=(info[0].get("imageinfo") or [{}])[0].get("thumburl") or (info[0].get("imageinfo") or [{}])[0].get("url")
        if not thumb: raise ValueError("no downloadable image url")
        data=req(thumb)
        if not 1400<len(data)<10_000_000:raise ValueError("unexpected image size")
        with Image.open(io.BytesIO(data)) as im:
            fmt=im.format
            w,h=im.size
            im.verify()
        allowed={"PNG":"png","JPEG":"jpg","WEBP":"webp","GIF":"gif"}
        if fmt not in allowed or min(w,h)<100: raise ValueError("invalid image format or dimensions")
        digest=hashlib.sha256(data).hexdigest()
        path=DEST/("%03d_%s.%s"%(entry["id"],digest[:10],allowed[fmt]))
        path.write_bytes(data)
        result.update(status="downloaded",path=str(path.relative_to(ROOT.parent)),image_url=thumb,width=w,height=h,bytes=len(data))
    except Exception as e:
        result["reason"]=(type(e).__name__+": "+str(e))[:300]
    return result
def main():
    e=json.loads((ROOT/"wiki_manifest.json").read_text(encoding="utf8"))["entries"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        rows=list(pool.map(fetch,e))
    rows.sort(key=lambda v:v["id"])
    (ROOT/"wiki_report.json").write_text(json.dumps({"entries":rows,"downloaded":sum(x["status"]=="downloaded" for x in rows)},ensure_ascii=False,indent=2),encoding="utf8")
    print("wiki images archived:",sum(x["status"]=="downloaded" for x in rows),"/",len(rows))
    for r in rows:
        if r["status"]=="failed":print("FAILED",r["name"],r["reason"])
if __name__=="__main__": main()

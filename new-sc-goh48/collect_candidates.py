#!/usr/bin/env python3
"""Download unapproved candidate originals only. Never overwrite existing approved assets."""
import concurrent.futures, hashlib, io, json, pathlib, urllib.parse, urllib.request, urllib.error
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parent
DEST=ROOT/"candidates"
DEST.mkdir(exist_ok=True)
API="https://godofhighschool.fandom.com/api.php"
ALLOWED={"godofhighschool.fandom.com","static.wikia.nocookie.net"}
class AllowedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if urllib.parse.urlsplit(newurl).hostname not in ALLOWED: raise ValueError("unexpected redirect")
        return super().redirect_request(req,fp,code,msg,headers,newurl)
opener=urllib.request.build_opener(AllowedRedirect)
def get(url, limit):
    if urllib.parse.urlsplit(url).hostname not in ALLOWED: raise ValueError("unexpected host")
    req=urllib.request.Request(url,headers={"User-Agent":"V4-PortraitReview/1.0 (candidate image archive)","Accept":"application/json,image/*;q=0.9,*/*;q=0.1"})
    with opener.open(req,timeout=12) as r:
        data=r.read(limit+1)
    if len(data)>limit: raise ValueError("response too large")
    return data
def query(**kwargs):
    return json.loads(get(API+"?"+urllib.parse.urlencode(dict(kwargs,format="json",formatversion=2)),2_000_000))
def work(e):
    result={"id":e["id"],"requested_title":e["title"],"page":"https://godofhighschool.fandom.com/wiki/"+urllib.parse.quote(e["title"].replace(" ","_")),"status":"failed","approved":False}
    try:
        if e.get("source"):
            source=e["source"]
        else:
            pages=query(action="query",titles=e["title"],prop="pageimages",piprop="original|name",pilicense="any").get("query",{}).get("pages",[])
            if len(pages)!=1 or pages[0].get("missing"): raise ValueError("exact page missing")
            page=pages[0]
            if page["title"].replace("_"," ").casefold()!=e["title"].casefold(): raise ValueError("page title mismatch")
            if page.get("pageprops",{}).get("disambiguation") is not None: raise ValueError("disambiguation page")
            result["page_title"]=page["title"]
            source=page.get("original",{}).get("source")
            if not source: raise ValueError("no original lead image")
        result["image_url"]=source
        raw=get(source,12_000_000)
        if len(raw)<1024: raise ValueError("image too small")
        with Image.open(io.BytesIO(raw)) as im:
            fmt=im.format; w,h=im.size; im.verify()
        ext={"JPEG":"jpg","PNG":"png","WEBP":"webp","GIF":"gif"}.get(fmt)
        if not ext or min(w,h)<80: raise ValueError("invalid dimensions or format")
        sha=hashlib.sha256(raw).hexdigest()
        path=DEST/f"{e['id']}_{sha[:12]}.{ext}"
        path.write_bytes(raw)
        result.update(status="candidate_downloaded",sha256=sha,width=w,height=h,bytes=len(raw),path=str(path.relative_to(ROOT.parent)))
    except Exception as exc:
        result["reason"]=str(exc)[:300]
    return result
entries=json.loads((ROOT/"manifest.json").read_text(encoding="utf8"))["entries"]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    rows=list(pool.map(work,entries))
report={"count":len(rows),"downloaded":sum(r["status"]=="candidate_downloaded" for r in rows),"approved":0,"entries":rows}
(ROOT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("Candidates downloaded:",report["downloaded"],"/",report["count"])

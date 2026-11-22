#!/usr/bin/env python3
"""Download a small set of unambiguous Knight Run portrait candidates; no auto assignment."""
import concurrent.futures,hashlib,io,json,pathlib,urllib.request,urllib.parse
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parent
DEST=ROOT/"assets"/"knight"
DEST.mkdir(parents=True,exist_ok=True)
base="https://knightrun.fandom.com/api.php"
UA={"User-Agent":"Mozilla/5.0 (V4 gallery import; visual checks required)"}
def get_json(q):
 u=base+"?"+urllib.parse.urlencode(dict(q,format="json",formatversion=2))
 with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20) as r:return json.loads(r.read(4_000_000))
titles=["Anne_glare.PNG","Anne_gloom.PNG","Knights_magazine.PNG","Anne_after_pray_war.PNG"]
def fetch(filename):
 result={"name":"앤 마이어","filename":filename,"status":"failed"}
 try:
  j=get_json({"action":"query","titles":"File:"+filename,"prop":"imageinfo","iiprop":"url","iiurlwidth":900})
  p=j["query"]["pages"][0]
  if p.get("missing"):raise ValueError("wiki file missing")
  info=p.get("imageinfo",[])
  if not info:raise ValueError("no image data")
  url=info[0].get("thumburl") or info[0].get("url")
  if not url:raise ValueError("no image URL")
  result["image_url"]=url
  with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=20) as r:data=r.read(10_000_001)
  with Image.open(io.BytesIO(data)) as im:
   w,h=im.size;fmt=im.format
   im.verify()
  if min(w,h)<100 or fmt not in {"PNG","WEBP","JPEG"}:raise ValueError("bad format or dimensions")
  ext={"PNG":"png","WEBP":"webp","JPEG":"jpg"}[fmt]
  digest=hashlib.sha256(data).hexdigest()
  path=DEST/("003_%s.%s"%(digest[:10],ext))
  path.write_bytes(data)
  result.update(status="downloaded",path=str(path.relative_to(ROOT.parent)),width=w,height=h,bytes=len(data))
 except Exception as e:result["reason"]=type(e).__name__+": "+str(e)[:220]
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p: images=list(p.map(fetch,titles))
available={}
for prefix in ("Jenny","Jenny_J","Leny","Kamal"):
 try:
  j=get_json({"action":"query","list":"allimages","aifrom":prefix,"ailimit":80})
  available[prefix]=[i["name"] for i in j.get("query",{}).get("allimages",[]) if i["name"].lower().startswith(prefix.lower())][:25]
 except Exception as e:available[prefix]=["ERROR: "+str(e)[:160]]
out={"total":len(images),"downloaded":sum(r["status"]=="downloaded" for r in images),"entries":images,"name_search":available}
(ROOT/"knight_image_candidates.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print('downloads',out['downloaded'],'/',len(images))
print('file matches',available)

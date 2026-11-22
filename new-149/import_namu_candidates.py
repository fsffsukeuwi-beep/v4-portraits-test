#!/usr/bin/env python3
"""Archive only name-matched exact original-file candidates for visual identity review.
No portrait is marked as acquired until separate inspection and README update.
"""
from __future__ import annotations
import concurrent.futures,hashlib,io,json,pathlib,urllib.request
from PIL import Image

ROOT=pathlib.Path(__file__).resolve().parent
ENTRIES=json.loads((ROOT/"namu_scan_report.json").read_text(encoding="utf-8"))["entries"]
BY_ID={x["id"]:x for x in ENTRIES}
CHOICES=[
(3,"attachment/앤 마이어/Knight_Run_-_Anne_Mayer_(1).jpg"),
(12,"attachment/Knight_Run_-_Jenny_J_(1).jpg"),
(15,"attachment/Knight_Run_-_Leny_(1).jpg"),
(20,"attachment/1_2.png"),
(58,"히킬 사이코 전투복.jpg"),
(78,"뮈렐.jpg"),
(79,"시드 베아킨 111.jpg"),
(80,"베히무스.png"),
(80,"베히무스Z.png"),
(82,"카일리이.jpg"),
(83,"아포리오오.jpg"),
(85,"갈타란.jpg"),
(90,"라파.png"),
(94,"토비온.jpg"),
(118,"이령3부.png"),
(120,"아린.png"),
]
DEST=ROOT/"assets"/"namu"
DEST.mkdir(parents=True,exist_ok=True)

def one(pair):
 idx,filename=pair
 item=BY_ID[idx]
 result={"id":idx,"name":item["name"],"filename":filename,"source_page":"https://namu.moe/w/"+item["requested_title"],"status":"failed"}
 image=next((x for x in item.get("images",[]) if x["file"]==filename),None)
 if not image:
  result["reason"]="exact source file absent from scanned wiki page"
  return result
 result["source_url"]=image["url"]
 try:
  request=urllib.request.Request(image["url"],headers={"User-Agent":"Mozilla/5.0 (V4 source archive; copyright remains with author)","Accept":"image/webp,image/jpeg,image/png,image/*"})
  with urllib.request.urlopen(request,timeout=22) as r:data=r.read(10_000_001)
  if len(data)<1600 or len(data)>10_000_000: raise ValueError("file size outside bounds")
  with Image.open(io.BytesIO(data)) as im:
   w,h=im.size;fmt=im.format
   im.verify()
  if fmt not in {"WEBP","JPEG","PNG"} or min(w,h)<100: raise ValueError("not an image portrait candidate")
  ext={"WEBP":"webp","JPEG":"jpg","PNG":"png"}[fmt]
  digest=hashlib.sha256(data).hexdigest()
  outfile=DEST/("%03d_%s.%s"%(idx,digest[:10],ext))
  if not outfile.exists(): outfile.write_bytes(data)
  result.update(status="downloaded",path=str(outfile.relative_to(ROOT.parent)),sha256=digest,width=w,height=h,bytes=len(data),format=fmt)
 except Exception as e: result["reason"]=type(e).__name__+": "+str(e)[:220]
 return result

with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
 results=list(pool.map(one,CHOICES))
report={"total":len(results),"downloaded":sum(r["status"]=="downloaded" for r in results),"entries":results}
(ROOT/"namu_import_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("image downloads",report["downloaded"],"/",report["total"])
for r in results:print(r["id"],r["name"],r["status"],r.get("reason",""))

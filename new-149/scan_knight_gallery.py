#!/usr/bin/env python3
"""Inspect wiki gallery image filenames and character-name search; do not write images."""
import json,urllib.request,urllib.parse,pathlib
root=pathlib.Path(__file__).resolve().parent
base="https://knightrun.fandom.com/api.php"
def query(params):
 u=base+"?"+urllib.parse.urlencode(dict(params,format="json",formatversion=2))
 req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 (V4 Gallery Check/1.0)","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=25) as r:return json.loads(r.read(4000000))
out={}
for word in ["Jenny","Lenny","Anne Mayer","Kamal"]:
 try:
  j=query({"action":"query","list":"search","srsearch":word,"srnamespace":0,"srlimit":20})
  out["search_"+word]=[{"title":x["title"],"snippet":x.get("snippet","")[:140]} for x in j.get("query",{}).get("search",[])]
 except Exception as e:out["search_"+word]={"error":str(e)}
try:
 j=query({"action":"parse","page":"Anne_Mayer/Gallery","prop":"images"})
 files=j.get("parse",{}).get("images",[])
 out["anne_gallery_images"]={"count":len(files),"files":files[:350]}
except Exception as e:out["anne_gallery_images"]={"error":str(e)}
(root/"knight_gallery_scan.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("Anne image files:",out.get("anne_gallery_images",{}).get("count",0))

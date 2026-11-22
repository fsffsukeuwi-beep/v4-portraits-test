#!/usr/bin/env python3
"""Locate per-character lead-image source candidates on a Korean wiki mirror.

No images are imported or promoted at this step. Candidate names are inspected later.
"""
import concurrent.futures
import html
import json
import pathlib
import re
import urllib.parse
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parent
TARGETS=[
(3,"앤 마이어","앤 마이어"),
(12,"제니 제이","제니 제이"),
(15,"레니","레니(나이트런)"),
(20,"카말","카말(나이트런)"),
(51,"제나로","제나로(히어로 킬러)"),
(55,"바이스","바이스(히어로 킬러)"),
(56,"보이드 워커","보이드 워커(히어로 킬러)"),
(58,"사이코","사이코(히어로 킬러)"),
(60,"여섯 번째 손가락","여섯 번째 손가락"),
(61,"요원 23","요원 23(히어로 킬러)"),
(63,"캡틴 커틀러스","캡틴 커틀러스"),
(78,"뮈렐","뮈렐"),
(79,"시드 베아킨","시드(초인의 시대)"),
(80,"베히무스","베히무스"),
(82,"데비아 카일리","데비아 카일리"),
(83,"아포리오 아카반가","아포리오 아카반가"),
(84,"그라브","그라브(초인의 시대)"),
(85,"갈타란","갈타란"),
(86,"모스먼","모스먼(초인의 시대)"),
(87,"바베루사","바베루사"),
(88,"카르멘 오피르","카르멘 오피르"),
(89,"헤치","헤치(초인의 시대)"),
(90,"라파","라파(초인의 시대)"),
(91,"시미온","시미온(초인의 시대)"),
(92,"바빌론 배뉘셔","바빌론 배뉘셔"),
(93,"지즈 하퍼","지즈 하퍼"),
(94,"토비온","토비온"),
(115,"빠르","빠르(호랑이형님)"),
(118,"이령","이령(호랑이형님)"),
(120,"아린","아린(호랑이형님)"),
(121,"구망","구망(호랑이형님)"),
(122,"무커","무커(호랑이형님)"),
(123,"황요","황요(호랑이형님)"),
(142,"하야테","하야테(템빨)"),
]

def scan(target):
 idx,name,title=target
 ret={"id":idx,"name":name,"requested_title":title}
 try:
  url="https://namu.moe/w/"+urllib.parse.quote(title,safe="()")
  req=urllib.request.Request(url,headers={
   "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
   "Accept":"text/html"})
  with urllib.request.urlopen(req,timeout=18) as response:
   data=response.read(2_500_000)
   ret["http_code"]=response.status
  raw=data.decode("utf-8","replace")
  ret["bytes"]=len(data)
  title_match=re.search(r'<title[^>]*>(.*?)</title>',raw,re.I|re.S)
  ret["page_title"]=html.unescape(re.sub(r'<[^>]+>','',title_match.group(1))).strip() if title_match else ""
  imgs=[]
  for tag in re.findall(r'<img\b[^>]{1,4000}>',raw,re.I|re.S):
   alt=re.search(r'\balt=[\x22\x27]([^\x22\x27]{1,320})',tag,re.I)
   source=re.search(r'\bdata-original=[\x22\x27]([^\x22\x27]{1,1500})',tag,re.I)
   if not source: continue
   src=html.unescape(source.group(1))
   if src.startswith("//file.namu.moe/file/"):
    filename=html.unescape(alt.group(1)) if alt else ""
    if filename.startswith("파일:"):
     obj={"file":filename[3:],"url":"https:"+src}
     if obj not in imgs: imgs.append(obj)
  ret["images"]=imgs[:45]
  ret["image_count"]=len(imgs)
 except Exception as e:
  ret["error"]=type(e).__name__+": "+str(e)[:240]
 return ret

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 rows=list(pool.map(scan,TARGETS))
rows.sort(key=lambda r:r["id"])
(ROOT/"namu_scan_report.json").write_text(json.dumps({"targets":len(rows),"entries":rows},ensure_ascii=False,indent=2),encoding="utf-8")
for r in rows:
 print(r["id"],r["name"],r.get("page_title"),r.get("image_count",0),r.get("error",""))

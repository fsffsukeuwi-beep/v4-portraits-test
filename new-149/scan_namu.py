#!/usr/bin/env python3
"""Best-effort HTML image-source discovery only, no gallery promotion."""
import concurrent.futures, json, re, pathlib, urllib.parse, urllib.request, html
root=pathlib.Path(__file__).resolve().parent
targets=[("뮈렐","https://namu.moe/w/뮈렐"),("베히무스","https://www.namu.moe/w/베히무스"),("이령","https://namu.moe/w/이령(호랑이형님)"),("아린","https://d.namu.moe/w/아린(호랑이형님)") ]
def fetch(x):
 name,url=x;url=urllib.parse.quote(url,safe=":/()");result={"name":name,"url":url}
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36","Accept":"text/html"})
  with urllib.request.urlopen(req,timeout=15) as rsp:
   data=rsp.read(2_000_000);result["http_code"]=rsp.status
  s=data.decode("utf-8","replace")
  result["bytes"]=len(data)
  result["page_title"]=re.findall(r"<title[^>]*>(.*?)</title>",s,re.I|re.S)[:1]
  tags=re.findall(r'<img\b[^>]{1,2500}>',s,re.I)
  parsed=[]
  for tag in tags:
   m=re.search(r'(?:src|data-src|alt)="([^"]{1,1900})"',tag,re.I)
   if m:
    alt=re.search(r'\balt="([^"]*)"',tag,re.I)
    src=re.search(r'\bsrc="([^"]*)"',tag,re.I)
    parsed.append({"alt":html.unescape(alt.group(1))[:110] if alt else "","src":html.unescape(src.group(1))[:450] if src else ""})
  result["img_count"]=len(tags)
  result["img_examples"]=parsed[:22]
  result["namu_img_url_count"]=s.count("i.namu.wiki")
  result["file_refs"]=list(dict.fromkeys(re.findall(r'파일:[^\\s\\\\\\"<>]{2,140}',s)))[:30]
 except Exception as exc: result["error"]=type(exc).__name__+": "+str(exc)[:300]
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(fetch,targets))
(root/"namu_scan_report.json").write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
for e in r:print(e["name"],e.get("http_code"),e.get("bytes"),e.get("img_count"),e.get("error"))

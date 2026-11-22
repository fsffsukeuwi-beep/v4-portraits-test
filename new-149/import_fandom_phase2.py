#!/usr/bin/env python3
from __future__ import annotations
import json
import concurrent.futures
from pathlib import Path
from import_fandom import fetch

ROOT=Path(__file__).resolve().parent
entries=json.loads((ROOT/"wiki_manifest_phase2.json").read_text(encoding="utf-8"))["entries"]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    report=list(pool.map(fetch,entries))
report.sort(key=lambda x:x["id"])
count=sum(x["status"]=="downloaded" for x in report)
(ROOT/"wiki_report_phase2.json").write_text(json.dumps({"total":len(report),"downloaded":count,"entries":report},ensure_ascii=False,indent=2),encoding="utf-8")
print("Second Fandom import",count,"/",len(report))
for r in report:
    if r["status"]!="downloaded":print("FAIL",r["name"],r.get("reason"))

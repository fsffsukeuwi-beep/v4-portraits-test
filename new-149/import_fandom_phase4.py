#!/usr/bin/env python3
"""Collect exact-person-page candidate images for human verification; no README changes."""
from import_fandom import fetch
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
root=Path(__file__).resolve().parent
entries=json.loads((root/'wiki_manifest_phase4.json').read_text(encoding='utf8'))['entries']
with ThreadPoolExecutor(max_workers=6) as pool:
    rows=list(pool.map(fetch,entries))
rows.sort(key=lambda x:x['id'])
count=sum(x['status']=='downloaded' for x in rows)
(root/'wiki_report_phase4.json').write_text(json.dumps({'total':len(rows),'downloaded':count,'entries':rows},ensure_ascii=False,indent=2),encoding='utf8')
print('candidate images downloaded',count,'of',len(rows))
for x in rows:
    print(x['name'],x['status'],x.get('image_url',x.get('reason')))

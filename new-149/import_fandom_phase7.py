#!/usr/bin/env python3
"""Fetch exact name-matched pages for review; does not alter character gallery."""
from import_fandom import fetch
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
root=Path(__file__).resolve().parent
entries=json.loads((root/'wiki_manifest_phase7.json').read_text(encoding='utf8'))['entries']
with ThreadPoolExecutor(max_workers=5) as pool: rows=list(pool.map(fetch,entries))
rows.sort(key=lambda r:r['id'])
n=sum(r['status']=='downloaded' for r in rows)
(root/'wiki_report_phase7.json').write_text(json.dumps({'total':len(rows),'downloaded':n,'entries':rows},ensure_ascii=False,indent=2),encoding='utf8')
print('Downloaded',n,'of',len(rows))
for r in rows: print(r['name'],r['status'],r.get('reason',''))

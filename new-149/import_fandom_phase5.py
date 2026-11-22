#!/usr/bin/env python3
"""Archive only proposed named-page candidates from Fandom. Manual review required."""
from import_fandom import fetch
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
root=Path(__file__).resolve().parent
entries=json.loads((root/'wiki_manifest_phase5.json').read_text(encoding='utf8'))['entries']
with ThreadPoolExecutor(max_workers=7) as pool:
    rows=list(pool.map(fetch,entries))
rows.sort(key=lambda x:x['id'])
count=sum(x['status']=='downloaded' for x in rows)
(root/'wiki_report_phase5.json').write_text(json.dumps({'total':len(rows),'downloaded':count,'entries':rows},ensure_ascii=False,indent=2),encoding='utf8')
print('Candidate files:',count,'/',len(rows))
for x in rows: print(x['name'],x['status'],x.get('image_url',x.get('reason')))

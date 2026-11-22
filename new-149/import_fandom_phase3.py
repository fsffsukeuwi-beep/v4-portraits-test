#!/usr/bin/env python3
from import_fandom import fetch
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
root=Path(__file__).resolve().parent
a=json.loads((root/'wiki_manifest_phase3.json').read_text(encoding='utf8'))['entries']
with ThreadPoolExecutor(max_workers=7) as pool:r=list(pool.map(fetch,a))
r.sort(key=lambda x:x['id'])
count=sum(x['status']=='downloaded' for x in r)
(root/'wiki_report_phase3.json').write_text(json.dumps({'total':len(r),'downloaded':count,'entries':r},ensure_ascii=False,indent=2),encoding='utf8')
print('Downloaded',count,'/',len(r))
for x in r:
 if x['status']!='downloaded':print('Failed',x['name'],x.get('reason'))

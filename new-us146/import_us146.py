import concurrent.futures, hashlib, io, json, time, urllib.request, urllib.parse
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
ROWS = json.loads((ROOT / 'us146_candidates.json').read_text())
OUT = ROOT / 'assets'
OUT.mkdir(exist_ok=True)

def download(row):
    errors = []
    url = row['candidate_url']
    dests = list(OUT.glob(row['id']+'.*'))
    if dests:
        data = dests[0].read_bytes()
        try:
            im = Image.open(io.BytesIO(data)); im.load()
            return dict(row, downloaded=True, path=dests[0].name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), width=im.width, height=im.height, format=im.format, fetched_url=url, reused=True)
        except Exception:
            pass
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0', 'Accept':'image/avif,image/webp,image/png,image/jpeg,image/gif,*/*;q=0.8'})
            with urllib.request.urlopen(req, timeout=22) as response:
                data = response.read(25*1024*1024)
                final_url = response.url
                content_type = response.headers.get('Content-Type','')
                status = response.status
            im = Image.open(io.BytesIO(data)); im.load()
            ext = {'JPEG':'jpg','PNG':'png','WEBP':'webp','GIF':'gif','AVIF':'avif'}.get(im.format)
            if not ext: raise ValueError('unsupported image format '+str(im.format))
            if min(im.size) < 40: raise ValueError('image below 40px')
            name = row['id']+'.'+ext
            (OUT / name).write_bytes(data)
            return dict(row, downloaded=True, path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), width=im.width, height=im.height, format=im.format, fetched_url=final_url, http_status=status, content_type=content_type)
        except Exception as exc:
            errors.append(type(exc).__name__+': '+str(exc)[:240])
    return dict(row, downloaded=False, errors=errors)

if __name__ == '__main__':
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for row in pool.map(download, ROWS):
            results.append(row)
            print(row['id'], row['name'], 'OK '+str(row['bytes']) if row['downloaded'] else str(row['errors']), flush=True)
    (ROOT/'us146-download-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    print('SUMMARY',sum(x['downloaded'] for x in results),'/',len(results),flush=True)

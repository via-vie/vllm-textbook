"""Download a fixed, hash-verified reading snapshot, not a runnable installation."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib,json,time,urllib.request
ROOT=Path(__file__).resolve().parents[1]
SHA="ced6857afa0ea7b2e3f0846a62e1394e90f15607"
DEST=ROOT/"_source"/("snapshot-"+SHA[:7])
paths=json.loads((ROOT/"_research"/"source-selection.json").read_text(encoding="utf-8"))
objects={}
for line in (ROOT/"_research"/"repository-objects.txt").read_text(encoding="utf-8").splitlines():
    meta,path=line.split("\t",1)
    objects[path]=meta.split()[2]
def fetch(path):
    if path not in objects:return {"path":path,"error":"not present at fixed commit"}
    out=DEST/path
    expected=objects[path]
    for attempt in range(3):
        try:
            if out.exists():data=out.read_bytes()
            else:
                url=f"https://raw.githubusercontent.com/vllm-project/vllm/{SHA}/{path}"
                req=urllib.request.Request(url,headers={"User-Agent":"vLLM-source-textbook/1.0"})
                with urllib.request.urlopen(req,timeout=35) as response:data=response.read(4*1024*1024)
            blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
            if blob!=expected:raise ValueError("Git blob mismatch")
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_bytes(data)
            return {"path":path,"git_blob":blob,"sha256":hashlib.sha256(data).hexdigest(),
                    "bytes":len(data),"lines":len(data.splitlines())}
        except Exception as exc:
            if attempt==2:return {"path":path,"error":str(exc)}
            time.sleep(attempt+1)
with ThreadPoolExecutor(max_workers=6) as pool:
    records=list(pool.map(fetch,paths))
manifest={"repo":"https://github.com/vllm-project/vllm","tag":"v0.30.0","commit":SHA,
          "date":"2026-10-19","snapshot_root":str(DEST.relative_to(ROOT)).replace("\\","/"),
          "files":records,"scope":"Selected source, docs and tests; not all repository files; not installed or GPU-executed."}
(ROOT/"_research"/"source-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
failures=[r for r in records if "error" in r]
print(json.dumps({"files":len(records),"verified":len(records)-len(failures),"bytes":sum(r.get("bytes",0) for r in records),"failures":failures},ensure_ascii=True))
if failures:raise SystemExit(1)

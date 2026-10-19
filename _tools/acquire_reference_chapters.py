"""Read-only acquisition of the user's tutorial reference and vLLM metadata."""
from pathlib import Path
import json
import urllib.request
import hashlib
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"_research";OUT.mkdir(exist_ok=True)
urls={
    "minimind-inference": "https://tutorial.baimuyuan.online/minimind-tutorial/chapters/07-%E6%8E%A8%E7%90%86%E4%B8%8E%E7%94%9F%E6%88%90",
    "harness-loop": "https://tutorial.baimuyuan.online/deepseek-harness-tutorial/chapters/09-Agent-Loop-%E4%B8%80%E6%AC%A1%E8%BD%AE%E6%AC%A1%E7%9A%84%E4%B8%80%E7%94%9F",
    "vllm_tag": "https://api.github.com/repos/vllm-project/vllm/git/ref/tags/v0.30.0",
}
results={}
for name,url in urls.items():
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"vLLM-educational-source-reader/1.0","Accept":"*/*"})
        with urllib.request.urlopen(req,timeout=30) as response:
            content=response.read(10*1024*1024)
            meta={"url":url,"final_url":response.url,"status":response.status,
                  "content_type":response.headers.get("Content-Type"),"bytes":len(content),
                  "sha256":hashlib.sha256(content).hexdigest()}
        (OUT/(name+(".html" if name in ("minimind-inference","harness-loop") else ".json"))).write_bytes(content)
        results[name]=meta
    except Exception as exc:
        results[name]={"url":url,"error":str(exc)}
(OUT/"reference-chapters-acquisition.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(results,ensure_ascii=True))

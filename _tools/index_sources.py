"""Index a verified vLLM reading snapshot without importing vLLM."""
from pathlib import Path
import ast,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/"_research/source-manifest.json").read_text(encoding="utf-8"))
SNAP=ROOT/manifest["snapshot_root"]
index={}
for record in manifest["files"]:
    if "error" in record:continue
    path=record["path"];raw=(SNAP/path).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==record["sha256"],path
    text=raw.decode("utf-8")
    info={"path":path,"lines":len(text.splitlines()),"sha256":record["sha256"],"symbols":{}}
    if path.endswith(".py"):
        tree=ast.parse(text,filename=path)
        def walk(node,prefix=""):
            for child in ast.iter_child_nodes(node):
                if isinstance(child,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                    name=prefix+child.name
                    info["symbols"][name]={"start":min([child.lineno]+[d.lineno for d in getattr(child,"decorator_list",[])]),
                        "end":child.end_lineno,"kind":"class" if isinstance(child,ast.ClassDef) else "function"}
                    walk(child,name+".")
                elif not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    walk(child,prefix)
        walk(tree)
    index[path]=info
(ROOT/"_research/source-index.json").write_text(json.dumps({"commit":manifest["commit"],"files":index},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"files":len(index),"symbols":sum(len(f["symbols"]) for f in index.values()),"source_lines":sum(f["lines"] for f in index.values())}))

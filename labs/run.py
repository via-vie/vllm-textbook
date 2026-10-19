"""Offline teaching labs. No vLLM import, CUDA execution, HTTP or timing claims."""
from pathlib import Path
import argparse, json, math, hashlib, sys

ROOT=Path(__file__).resolve().parents[1]
CASE=json.loads((ROOT/"_book/case.json").read_text(encoding="utf-8"))
ALIASES=json.loads((ROOT/"_book/aliases.json").read_text(encoding="utf-8"))
def mat(x,w):
    return [sum(a*b for a,b in zip(x,col)) for col in zip(*w)]
def norm(x):
    scale=(sum(t*t for t in x)/len(x)+1e-6)**-.5
    return [t*scale for t in x]
def softmax(x):
    z=max(x); p=[math.exp(t-z) for t in x]; den=sum(p)
    return [t/den for t in p]
def add(a,b):return [x+y for x,y in zip(a,b)]
def rope(x,p):
    c,s=math.cos(p),math.sin(p)
    return [x[0]*c-x[1]*s,x[0]*s+x[1]*c]
def forward(ids,cache=None):
    """Single layer, two heads, RMSNorm scales=1; adjacent-pair RoPE."""
    w=CASE["weights"]
    cache={"K":[[],[]],"V":[[],[]]} if cache is None else json.loads(json.dumps(cache))
    logits=[]; heads=[]; qs=[]; scores_out=[]
    for tok in ids:
        pos=len(cache["K"][0]); h=w["E"][tok]; u=norm(h)
        q,k,v=[mat(u,w[name]) for name in ("Wq","Wk","Wv")]
        out=[]; these_q=[]; these_scores=[]; these_heads=[]
        for head in range(2):
            sl=slice(head*2,head*2+2)
            qr,kr=rope(q[sl],pos),rope(k[sl],pos)
            cache["K"][head].append(kr);cache["V"][head].append(v[sl])
            scores=[sum(x*y for x,y in zip(qr,kk))/math.sqrt(2) for kk in cache["K"][head]]
            probs=softmax(scores)
            oh=[sum(p*vv[j] for p,vv in zip(probs,cache["V"][head])) for j in range(2)]
            out.extend(oh);these_heads.append(oh);these_q.append(qr);these_scores.append(scores)
        r=add(h,mat(out,w["Wo"]));u2=norm(r)
        g,up=mat(u2,w["Wg"]),mat(u2,w["Wu"])
        ff=mat([a/(1+math.exp(-a))*b for a,b in zip(g,up)],w["Wd"])
        z=norm(add(r,ff));logits.append(mat(z,w["Wlm"]))
        heads.append(these_heads);qs.append(these_q);scores_out.append(these_scores)
    return {"logits":logits,"cache":cache,"heads":heads,"q":qs,"scores":scores_out}
def argmax(x):return max(range(len(x)),key=x.__getitem__)
def trace():
    p=forward([11,10,7]);one=argmax(p["logits"][-1])
    d=forward([one],p["cache"]);two=argmax(d["logits"][-1])
    rows=[]
    def row(event,known,computed,flight,ready,status,worker,refs,output):
        rows.append(dict(event=event,known_tokens=known,num_computed_tokens=computed,
            num_in_flight_tokens=flight,ready_tokens_TEACHING_ONLY=ready,status=status,
            worker_row=worker,active_KV_references=refs,accepted_output_ids=output))
    row("提交：前端登记 → ADD → 核心等待",3,0,0,0,"WAITING",False,0,[])
    row("调度 prefill：计划 A3，提前记账",3,3,3,0,"RUNNING",False,1,[])
    row("GPU prefill 完成：候选尚未回填核心",3,3,3,3,"RUNNING",True,1,[])
    row("核心回填：接受鱼 8，发送输出",4,3,0,3,"RUNNING",True,1,[one])
    row("调度 decode：输入鱼，位置 3",4,4,1,3,"RUNNING",True,1,[one])
    row("GPU decode 完成：候选 EOS 尚未回填",4,4,1,4,"RUNNING",True,1,[one])
    row("核心回填并终止：移除活动请求，归还引用",5,4,0,4,"FINISHED_STOPPED",True,0,[one,two])
    row("零 token 清理计划：Worker 删除持久行",5,4,0,4,"REMOVED",False,0,[one,two])
    return {"scope":"Teaching simulation of synchronous main-path contracts, NOT actual vLLM scheduling.",
        "ready_tokens_note":"Teaching field only. Released rows retain historical values, not live allocations.",
        "block_size":16,"physical_block_example":7,"rows":rows,
        "prefill":{"input_ids":[11,10,7],"positions":[0,1,2],"logits":p["logits"][-1],
                   "probabilities":softmax(p["logits"][-1]),"selected":one},
        "decode":{"input_ids":[one],"positions":[3],"logits":d["logits"][-1],
                  "probabilities":softmax(d["logits"][-1]),"selected":two}}
def pack():
    rows=[dict(id="A",state_row=2,n=1,positions=[19],seq_len=20,blocks=[7,2],input_ids=[8]),
          dict(id="B",state_row=0,n=3,positions=[16,17,18],seq_len=19,blocks=[7,11],input_ids=[11,10,7]),
          dict(id="C",state_row=3,n=4,positions=[0,1,2,3],seq_len=4,blocks=[9],input_ids=[11,10,7,8])]
    loc=[0];slots=[]
    for r in rows:
        loc.append(loc[-1]+r["n"])
        slots.extend(r["blocks"][p//16]*16+p%16 for p in r["positions"])
    return dict(scope="Input packing arithmetic; A/B share the same first 16 tokens.",
        rows=rows,query_start_loc=loc,idx_mapping=[r["state_row"] for r in rows],
        positions=sum([r["positions"] for r in rows],[]),
        input_ids=sum([r["input_ids"] for r in rows],[]),
        seq_lens=[r["seq_len"] for r in rows],slot_mapping=slots)
def block_hash(parent,tokens,salt=""):
    # Semantic demonstration only, not vLLM's hash algorithm/serialization.
    return hashlib.sha256(json.dumps([parent,tokens,salt],separators=(",",":")).encode()).hexdigest()
def prefix():
    p=[11,10,7,8]*4
    a=block_hash("ROOT",p);b=block_hash("ROOT",p)
    table={a:7};ref=2;steps=[{"event":"A/B 持有共享块7","ref":ref,"hash_present":a in table}]
    for event in ("A 结束","B 结束"):
        ref-=1;steps.append({"event":event,"ref":ref,"hash_present":a in table})
    del table[a];ref=1
    steps.append({"event":"重新分配块7：淘汰旧身份，交给C","ref":ref,"hash_present":a in table})
    return {"scope":"Hash semantics and ownership simulation, not binary-compatible with vLLM.",
        "prefix_tokens":p,"A_prompt":p+[11,10,7],"B_prompt":p+[11,10,9],
        "hit_tokens":16,"same_prefix":a==b,"different_parent":a!=block_hash("OTHER",p),
        "different_salt":a!=block_hash("ROOT",p,"isolated"),"shared_hash":a,"steps":steps}
def budget(cap=8):
    left=cap;plan={}
    for rid,need in (("A",1),("B",3),("C",20)):
        n=min(left,need)
        if n:plan[rid]=n
        left-=n
    return {"scope":"Simplified running-first budget arithmetic; not actual Scheduler.",
        "budget":cap,"plan":plan,"total":sum(plan.values()),"remaining_C":20-plan.get("C",0)}
def attention():
    p=forward([11,10,7]);d=forward([8],p["cache"]);res=[]
    for head in range(2):
        scores=d["scores"][0][head];vals=d["cache"]["V"][head]
        summaries=[]
        for lo,hi in ((0,2),(2,4)):
            ss=scores[lo:hi];vv=vals[lo:hi];m=max(ss);ww=[math.exp(x-m) for x in ss]
            summaries.append(dict(m=m,l=sum(ww),u=[sum(a*v[j] for a,v in zip(ww,vv)) for j in range(2)]))
        m=max(s["m"] for s in summaries)
        l=sum(math.exp(s["m"]-m)*s["l"] for s in summaries)
        u=[sum(math.exp(s["m"]-m)*s["u"][j] for s in summaries) for j in range(2)]
        merged=[x/l for x in u];direct=d["heads"][0][head]
        res.append(dict(head=head,scores=scores,tiles=summaries,merged=merged,direct=direct,
            max_abs_error=max(abs(x-y) for x,y in zip(merged,direct))))
    return dict(scope="float64 CPU arithmetic; no GPU performance measurements.",heads=res)
def metrics():
    times=[.20,.24,.31];start=0;finish=.32
    return dict(scope="Synthetic timestamp example, not benchmark data.",timestamps=times,
        TTFT=times[0]-start,ITL=[b-a for a,b in zip(times,times[1:])],
        TPOT=(times[-1]-times[0])/(len(times)-1),E2E=finish-start)
def source(alias,symbol=None):
    path=ALIASES.get(alias,alias)
    index=json.loads((ROOT/"_research/source-index.json").read_text(encoding="utf-8"))
    if path not in index["files"]:raise ValueError("Unknown path: "+path)
    info=index["files"][path];r=info["symbols"].get(symbol) if symbol else None
    if symbol and not r:raise ValueError("Unknown qualified symbol: "+symbol)
    lines=(ROOT/"_source/snapshot-ced6857"/path).read_text(encoding="utf-8").splitlines()
    lo,hi=(r["start"],r["end"]) if r else (1,len(lines))
    print(f"{path}  {symbol or ''}  L{lo}-L{hi}  commit {index['commit']}")
    for i in range(lo-1,hi):print(f"{i+1:5}: {lines[i]}")
def check():
    t=trace();pk=pack();pc=prefix();at=attention();full=forward([11,10,7,8])
    assert [t["prefill"]["selected"],t["decode"]["selected"]]==[8,1]
    # Independent references previously produced by the Transformer course.
    err=max(abs(x-y) for x,y in zip(full["logits"][-1],CASE["reference_full_last_logits"]))
    assert err<1e-11,err
    assert max(abs(x-y) for x,y in zip(t["decode"]["logits"],full["logits"][-1]))<1e-12
    assert len(full["cache"]["K"][0])==4
    assert pk["query_start_loc"]==[0,1,4,8]
    assert pk["slot_mapping"]==[35,176,177,178,144,145,146,147]
    assert pk["idx_mapping"]==[2,0,3]
    assert pc["same_prefix"] and pc["different_parent"] and pc["different_salt"]
    assert pc["steps"][2]["ref"]==0 and pc["steps"][2]["hash_present"]
    assert not pc["steps"][3]["hash_present"]
    assert all(h["max_abs_error"]<1e-12 for h in at["heads"])
    assert t["rows"][1]["num_computed_tokens"]==3 and t["rows"][1]["ready_tokens_TEACHING_ONLY"]==0
    assert t["rows"][-2]["num_computed_tokens"]==4 and t["rows"][-2]["known_tokens"]==5
    assert not t["rows"][-1]["worker_row"] and t["rows"][-1]["active_KV_references"]==0
    assert budget()["plan"]=={"A":1,"B":3,"C":4}
    return dict(status="passed",reference_logits_max_abs_error=err,
        attention_max_abs_error=max(h["max_abs_error"] for h in at["heads"]),
        note="CPU teaching labs only; no actual vLLM or CUDA run.")
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab",choices=["trace","pack","prefix","budget","attention","metrics","source","check"])
    parser.add_argument("alias",nargs="?");parser.add_argument("symbol",nargs="?")
    parser.add_argument("--json",action="store_true");parser.add_argument("--budget",type=int,default=8)
    args=parser.parse_args()
    if hasattr(sys.stdout,"reconfigure"):sys.stdout.reconfigure(encoding="utf-8")
    if args.lab=="source":
        if not args.alias:parser.error("source requires a file alias/path")
        source(args.alias,args.symbol)
    else:
        data=budget(args.budget) if args.lab=="budget" else globals()[args.lab]()
        print(json.dumps(data,ensure_ascii=False,indent=2))

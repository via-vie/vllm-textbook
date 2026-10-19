"""Run on a Linux NVIDIA server with vLLM 0.30.0; not executed by book build."""
from pathlib import Path
import argparse, json, os, time, platform, importlib.metadata
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model",required=True)
    p.add_argument("--revision",default=None)
    p.add_argument("--out",default="results/a100.json")
    p.add_argument("--batch",type=int,default=1)
    p.add_argument("--prompt-repeat",type=int,default=1)
    p.add_argument("--max-tokens",type=int,default=32)
    p.add_argument("--runs",type=int,default=5)
    args=p.parse_args()
    if min(args.batch,args.prompt_repeat,args.max_tokens,args.runs)<1:p.error("positive arguments required")
    import torch
    from vllm import LLM, SamplingParams
    version=importlib.metadata.version("vllm")
    if version!="0.30.0":raise RuntimeError("Expected vLLM 0.30.0, found "+version)
    config=dict(model=args.model,tensor_parallel_size=1,dtype="bfloat16",
        async_scheduling=False,enforce_eager=True,enable_prefix_caching=False,
        enable_chunked_prefill=True,max_model_len=2048,max_num_batched_tokens=256,
        max_num_seqs=8,gpu_memory_utilization=.7,seed=0)
    if args.revision:config["revision"]=args.revision
    if args.batch>8:p.error("baseline batch must be <=8; change configuration deliberately")
    llm=LLM(**config)
    tokenizer=llm.get_tokenizer()
    messages=[{"role":"user","content":"请续写：小猫喜欢吃。"*args.prompt_repeat}]
    ids=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False)
    if len(ids)+args.max_tokens>2048:raise ValueError("input + output limit >2048")
    params=SamplingParams(temperature=0,max_tokens=args.max_tokens)
    prompts=[{"prompt_token_ids":ids} for _ in range(args.batch)]
    llm.generate(prompts,params,use_tqdm=False) # warm-up excluded
    runs=[]
    for i in range(args.runs):
        start=time.perf_counter()
        outputs=llm.generate(prompts,params,use_tqdm=False)
        elapsed=time.perf_counter()-start
        records=[]
        for out in outputs:
            choice=out.outputs[0]
            records.append(dict(request_id=out.request_id,prompt_token_ids=out.prompt_token_ids,
                output_token_ids=choice.token_ids,text=choice.text,finish_reason=choice.finish_reason))
        n=sum(len(x["output_token_ids"]) for x in records)
        runs.append(dict(run=i,batch_elapsed_seconds=elapsed,output_tokens=n,
            completed_output_tokens_per_second=n/elapsed,outputs=records))
    result=dict(scope="Offline whole-batch measurement; does NOT measure TTFT/ITL.",
        timing_note="Blocking LLM.generate completion; no frontend CUDA synchronization is assumed to synchronize another process.",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),vllm_version=version,
        reading_commit="ced6857afa0ea7b2e3f0846a62e1394e90f15607",
        wheel_source_commit_note="Wheel version is checked; build provenance must be recorded separately.",
        python=platform.python_version(),torch_version=torch.__version__,cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name(0),total_memory_bytes=torch.cuda.get_device_properties(0).total_memory,
        VLLM_USE_V2_MODEL_RUNNER=os.environ.get("VLLM_USE_V2_MODEL_RUNNER"),
        config=config,cli=vars(args),chat_template_ids=ids,runs=runs)
    target=Path(args.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",target,"; verify startup logs for Runner selection, model revision and driver.")
if __name__=="__main__":main()

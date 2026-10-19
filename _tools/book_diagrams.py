"""Original vector diagrams for the source-grounded textbook."""
from pathlib import Path
import html,unicodedata
R=Path(__file__).resolve().parents[1]/"_book/figures"
R.mkdir(parents=True,exist_ok=True)
SPECS={
"architecture":("进程、对象与设备：先确定边界",[
("API 前端进程",["路由 / OpenAIServingChat|messages → 参数与生成流","Renderer / InputProcessor|模板、Tokenizer、校验、内部 ID","OutputProcessor / Collector|ID → 文本，按请求送回用户"]),
("EngineCore 进程 · 单卡 uni",["Scheduler / KV 管理|请求队列、token 预算、块元数据","Executor → Worker 对象|初始化设备，提交执行；同进程","MRV2|持久请求行、输入打包、模型与采样"]),
("GPU 资源",["权重 / 激活|所有请求共用参数；激活按元数据隔离","KV 张量 / 块表视图|分配块号不等于计算 K/V","内核 / 图 / 设备状态|执行后返回 token 与必要统计"])],
"前端与核心交换消息；核心内单卡对象调用；CPU 元数据通过块表连接 GPU 数值。"),
"startup":("请求到达前：从配置到可用执行器",[
("配置与实现",["CLI → EngineArgs|模型、长度、并行、调度、缓存配置","VllmConfig|兼容性检查，选择 Runner 与执行路径","EngineCore → Executor|单卡 uni；多卡使用其他执行器"]),
("设备与容量",["Worker.init_device|设备、通信环境、内存观察点","load_model / profile|加载权重，估计非 KV 内存开销","KV 配置与初始化|规格分组、物理块数、GPU KV 张量"]),
("执行就绪",["Runner 初始化|持久状态、输入缓冲区和后端","compile / warm-up|按配置编译、预热或捕获图","Scheduler 就绪|空闲块池、请求表与调度预算"])],
"KV 预算不是 nvidia-smi 的全部空闲显存；显式字节预算和 profiling 路径要分清。"),
"contracts":("同一个请求，在不同层是不同合同",[
("前端 → 核心",["HTTP / EngineInput|messages / IDs 与生成参数","EngineCoreRequest|可序列化输入、内部 ID、client_index","Request|核心可变历史、状态与调度计数"]),
("核心 → 设备",["SchedulerOutput|每请求算几个 token、块增量、结束 ID","InputBatch / metadata|拼接 IDs、位置、长度、索引与地址","模型 / Sampler|hidden → logits → token IDs"]),
("设备 → 前端",["ModelRunnerOutput|结果行映射、采样 IDs、统计","EngineCoreOutput|核心接受的新 IDs 与 finish reason","RequestOutput|增量文本、用户 ID、最终标志"])],
"核心 Request、前端 RequestState、GPU 持久行不共享 Python 对象身份，必须显式同步。"),
"trace":("A 的两轮：已知、已调度与真实完成",[
("prefill · 输入 [11,10,7]",["提交|known=3，computed=0，ready=0","调度 A3|computed=3，in_flight=3，ready=0","执行并归账|ready=3，接受鱼8；known=4"]),
("decode · 输入鱼8，position=3",["调度 A1|computed=4，in_flight=1，ready=3","模型与采样|写鱼的 KV；ready=4，选择 EOS1","核心结束|known=5，computed=4；归还引用"]),
("最后清理",["finished_req_ids|下一份计划通知 Worker 删除状态","零 token 执行路径|无 Transformer 前向；仍可有清理","结束|EOS 不再前向；旧计数不是活跃分配"])],
"ready 是教学字段；num_computed_tokens 在 schedule 后提前记账，不能视为 GPU 完成证明。"),
"scheduling":("统一 token 预算：prefill 与 decode 同批",[
("简化条件：预算 8，A/B 已运行",["A：decode 需 1|known-computed=1；安排1","B：剩余 prefill 3|安排3；剩余预算4","C：新输入剩20|分块安排4；输入仍未完成"]),
("计划与约束",["计划 {A:1,B:3,C:4}|总 token=8；不同查询长度同批","其他准入约束|请求数、KV、长度、预留、优先级","未完成 prefill|num_sampled=0；不能提交续写"]),
("容量不足",["申请新块失败|先判断容量与可安全回收空间","可能抢占|PREEMPTED、保留 token、重置进度","后续重算|恢复 KV 有成本，受安全释放限制"])],
"这是手算条件下的教学计划；真实 Scheduler 还考虑更多模型与配置分支。"),
"paging":("逻辑位置 → 逻辑块 → 物理槽",[
("请求 A · b=16 · 块表 [7,2]",["position p=19|逻辑序列位置，与 batch 下标无关","j=19//16=1，r=3|第2个逻辑块，第4个槽","physical=table[1]=2|slot=2×16+3=35"]),
("本轮写入与历史读取",["KVCacheManager|分配/接纳块；更新 CPU 元数据","Runner slot_mapping|本轮 token 的写入位置","Attention backend|按块表读取可见历史 K/V"]),
("必须分清",["逻辑连续|token 顺序保持 0,1,2,…","物理可离散|块7和块2不必相邻","数值何时有效|真实 KV 写入/传输完成之后"])],
"slot 是后端索引语义；实际字节布局还含层、K/V、头、维度、dtype 与对齐。"),
"prefix":("前缀身份与引用生命周期",[
("身份：P 为相同16-token前缀",["A=P+私有尾部|H(ROOT,P,extra) → 物理块7","B=P+不同尾部|同父前缀同身份，可共享块7","改变父前缀 / salt|哈希不同，不能错误复用"]),
("活动引用",["A 与 B 正在使用|ref(7)=2","A 完成|ref(7)=1，不能覆盖","B 完成|ref(7)=0，哈希内容仍可保留"]),
("再利用",["新请求查找|可命中保留身份，再 touch","需要重新分配|从可用队列取块并淘汰旧身份","写入新内容|旧缓存身份失效，不是 cudaFree"])],
"普通 Dense 主线按完整块命中；特殊 Hybrid/Mamba 部分前缀路径需单独阅读。"),
"packing":("MRV2：五种索引不能混在一起",[
("请求 / 持久行 / 本轮查询",["A → row2|n=1；positions=[19]；seq_len=20","B → row0|n=3；positions=[16,17,18]；len=19","C → row3|n=4；positions=[0,1,2,3]；len=4"]),
("拼接布局",["idx_mapping|[2,0,3]：batch → 持久行","query_start_loc|[0,1,4,8]：本轮查询分段","positions|[19,16,17,18,0,1,2,3]"]),
("物理地址 · b=16",["A [7,2] → [35]|p19 → 块2，offset3","B [7,11] → [176,177,178]|p16..18 → 块11","C [9] → [144,145,146,147]|p0..3 → 块9"])],
"A/B 的块7假设内容为同一完整前缀；Attention 元数据必须防止跨请求混读。"),
"attention":("分页管理地址，FlashAttention 优化计算 IO",[
("模型层",["H → Q/K/V|Q/K Norm、RoPE；逻辑位置","KV update|按 slot_mapping 写本轮 K/V","Attention|按块表和长度读取可见历史"]),
("分块在线归并",["每块统计|m=max(score)，l=Σexp(score-m)","加权向量|u=Σexp(score-m)·V","合并与输出|按共同 m 缩放；最后 O=u/l"]),
("性能边界",["prefill|多查询；避免完整 N² S/P 写回 HBM","decode|少查询；历史 KV/权重读取更关键","三种块|KV page、计算 tile、线程块各司其职"])],
"减少中间矩阵读写不等于稀疏近似；真实精度与性能需在选定硬件/后端验证。"),
"lifecycle":("输出、停止、取消与安全释放",[
("正常输出",["Sampler → 核心|结果按 request_id/行索引回填","核心停止检查|EOS / stop ID / 长度；产生输出","前端增量解码|ID → 文本；可能发现 stop 字符串"]),
("取消回路",["用户断开 / 字符串停止|generate 清理或 OutputProcessor abort","ABORT → EngineCore|在采纳结果前处理取消","在途工作|可能仍在写 GPU KV，不能立刻复用"]),
("资源回收",["fence 安全条件|last_sched_seq ≤ processed_step_seq","归还引用 / 核心移除|缓存大张量仍常驻","finished_req_ids → Worker|后续清理持久行，可零 token"])],
"前端结束、核心结束、KV 可复用、Worker 删除是相关但不必同一时刻完成的事件。"),
"execution":("eager、compile、CUDA Graph 的职责",[
("三类机制",["算子融合|减少中间写回与 launch 数","torch.compile|分析/优化图，生成执行代码","CUDA Graph|捕获并重放 GPU 执行结构"]),
("MRV2 路径",["更新本轮输入|新 token 写入稳定缓冲区","dispatch 兼容形状|token/请求/LoRA 等匹配候选","replay 或回退|FULL / PIECEWISE / NONE"]),
("验证收益",["固定负载与采样|同输入、输出、缓存冷暖、并发","分开预热与稳态|记录编译/捕获和回退日志","看瓶颈证据|CPU 间隙、kernel、padding、显存"])],
"图重放不复用旧答案；每次仍用新输入执行，收益取决于当前瓶颈。"),
"parallel":("并行切什么：请求、层、张量还是专家",[
("模型内切分",["TP：切层内矩阵/头|列分片可拼接；行贡献需要求和","PP：切层|阶段间传激活，各持部分层 KV","EP：切专家|MoE token 分发和结果合并"]),
("服务副本",["DP：请求路由到副本|通常每副本独立权重和请求 KV","组合拓扑|TP×PP×DP 等决定 rank 与通信组","执行器边界|多进程/Ray 改变 Worker 位置"]),
("不可简单相除",["KV 头可能复制|Hkv < TP 时按实现复制头","通信有成本|NVLink / PCIe / 网络不同","单 A100 验收|先推导源码；不伪造多卡实测"])],
"并行方式不替代前端/核心/Runner 合同，而是改变其中的张量归属、通信与执行边界。")
}
def wrap(s,limit):
    out=[];line="";n=0
    for c in s:
        w=2 if unicodedata.east_asian_width(c) in "WF" else 1
        if n+w>limit:out.append(line);line="";n=0
        line+=c;n+=w
    if line:out.append(line)
    return out
def generate():
    for key,(title,rows,note) in SPECS.items():
        els=[]
        def text(x,y,s,size=18,color="#233344",bold=False,limit=42):
            for i,line in enumerate(wrap(s,limit)):
                els.append(f'<text x="{x}" y="{y+i*27}" fill="{color}" font-size="{size}" font-weight="{700 if bold else 400}">{html.escape(line)}</text>')
        els.append(f'<title>{html.escape(title)}</title><desc>{html.escape(note)}</desc>')
        els.append('<rect width="1200" height="850" rx="20" fill="#f4f7fb"/>')
        text(34,48,title,27,bold=True,limit=80)
        colors=["#eaf1ff","#e7f5ef","#fff2db"]
        for ri,(label,cards) in enumerate(rows):
            y=84+ri*220
            text(34,y+20,label,19,bold=True,limit=110)
            for ci,card in enumerate(cards):
                x=34+ci*392
                els.append(f'<rect x="{x}" y="{y+40}" width="348" height="156" rx="13" fill="{colors[ri]}" stroke="#bccbd7"/>')
                head,body=card.split("|",1)
                text(x+16,y+69,head,18,bold=True,limit=34)
                headh=len(wrap(head,34))*27
                text(x+16,y+76+headh,body,17,limit=36)
                flow_rows={'startup':{0,1,2},'contracts':{0,1,2},'trace':{0,1,2},'scheduling':{0,2},'paging':{0,1},'prefix':{1,2},'attention':{0,1},'lifecycle':{0,1,2},'execution':{1}}
                if ci<2 and ri in flow_rows.get(key,set()):
                    ax=x+355;ay=y+118
                    els.append(f'<path d="M{ax} {ay}h24m-6 -5l6 5 -6 5" fill="none" stroke="#738696" stroke-width="2"/>')
        text(34,783,note,16,color="#516675",limit=134)
        text(34,831,"vLLM v0.30.0 · ced6857 · 本书原创图解 / 具体条件见对应章节",14,color="#607585",limit=140)
        svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="850" viewBox="0 0 1200 850" role="img" font-family="Microsoft YaHei, Noto Sans SC, sans-serif">'+''.join(els)+'</svg>'
        (R/(key+".svg")).write_text(svg,encoding="utf-8")
    draw_architecture()
    return len(SPECS)

def draw_architecture():
    """Connected swimlanes: two CPU processes and one device, not three processes."""
    els=[]
    def txt(x,y,s,size=17,color="#233344",bold=False,limit=35):
        for i,line in enumerate(wrap(s,limit)):
            els.append(f'<text x="{x}" y="{y+i*25}" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}">{html.escape(line)}</text>')
    def box(x,y,w,h,title,body,color="#fff"):
        els.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{color}" stroke="#aebfce"/>')
        txt(x+14,y+27,title,17,bold=True,limit=36)
        txt(x+14,y+54,body,15,limit=39)
    def edge(path,label=None,x=0,y=0):
        els.append(f'<path d="{path}" stroke="#456b95" stroke-width="2" fill="none" marker-end="url(#arrow)"/>')
        if label:txt(x,y,label,13,color="#456b95",limit=35)
    els.append('<title>单卡在线请求的真实进程与设备边界</title><desc>API前端与EngineCore为CPU进程，单卡uni执行器中的Worker是对象；GPU列为设备资源。箭头展示一条请求及返回链。</desc>')
    els.append('<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="#456b95"/></marker></defs>')
    els.append('<rect width="1200" height="850" rx="18" fill="#f4f7fb"/>')
    txt(26,43,"单卡在线请求：进程边界、数据交接与返回链",27,bold=True,limit=85)
    for x,w,title,color in ((20,365,"API 前端进程","#edf3ff"),(405,390,"EngineCore 进程 · uni","#e8f6ef"),(815,365,"GPU 设备 · 不是第三进程","#fff4df")):
        els.append(f'<rect x="{x}" y="77" width="{w}" height="723" rx="13" fill="{color}" stroke="#c5d3dd"/>')
        txt(x+16,106,title,18,bold=True,limit=40)
    box(45,125,305,78,"① 路由 → Renderer / 输入校验","messages → 模板 → IDs / 参数")
    box(45,250,305,90,"② AsyncLLM / CoreClient","先登记 collector；发送请求")
    box(430,125,340,78,"启动产物","配置、Scheduler、KV池、模型已就绪")
    box(430,250,340,90,"③ EngineCoreRequest → Request","内部 ID、token 历史、WAITING")
    box(430,390,340,90,"④ Scheduler / KVCacheManager","预算与块分配 → 执行计划")
    box(430,530,340,100,"⑤ Executor → Worker → MRV2","同进程对象；打包输入、调用模型")
    box(840,125,310,98,"常驻模型权重","embedding / Attention / MLP / head")
    box(840,270,310,98,"逐层 KV 张量与缓冲区","CPU 块表连接逻辑位置与物理槽")
    box(840,530,310,100,"⑥ 模型内核 / Attention / 采样","写本轮 KV；读历史；选择新 IDs")
    box(430,690,340,80,"⑦ 核心回填与停止 / 释放","计划 + 结果 → 状态 / 核心输出")
    box(45,690,305,80,"⑧ OutputProcessor → 用户","增量解码 → collector → SSE")
    edge("M197 203V250","EngineInput",205,232)
    edge("M350 295H430","ADD",369,284)
    edge("M600 340V390","schedule",612,369)
    edge("M600 480V530","SchedulerOutput",612,511)
    edge("M770 580H840","输入",786,567)
    edge("M995 368V530","读 / 写 KV",1007,451)
    edge("M1150 174H1165V580H1150")
    edge("M995 630V730H770","token IDs / stats",841,700)
    edge("M430 730H350","核心输出",356,714)
    txt(26,826,"主线：TP=PP=DP=1，普通文本、同步调度。取消和零 token 清理另见生命周期章；源码 v0.30.0 / ced6857。",14,color="#526d81",limit=155)
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="850" viewBox="0 0 1200 850" role="img" font-family="Microsoft YaHei,Noto Sans SC,sans-serif">'+''.join(els)+'</svg>'
    (R/"architecture.svg").write_text(svg,encoding="utf-8")

if __name__=="__main__":print(generate())

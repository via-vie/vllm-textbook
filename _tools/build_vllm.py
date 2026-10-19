from pathlib import Path
import json,math,html,hashlib
R=Path(__file__).resolve().parents[1]
DATA=json.loads((R/'_data/transformer_case.json').read_text(encoding='utf-8'))
BG='#f3f6fb';INK='#14243b';MUTED='#52647b';LINE='#d9e3ee';BLUE='#2563eb';TEAL='#087f8c';ORANGE='#b65c12';PALE='#eaf1ff';GREEN='#e5f6f1';WARM='#fff1df'
SOURCES={
'arch':('Architecture Overview','https://docs.vllm.ai/en/stable/design/arch_overview/'),
'v1':('V1 architecture blog (2025)','https://vllm.ai/blog/2025-01-27-v1-alpha-release'),
'paper':('PagedAttention paper · §3–5','https://arxiv.org/html/2309.06180v1'),
'page':('Paged Attention kernel','https://docs.vllm.ai/en/stable/design/paged_attention/'),
'apc':('Prefix Caching design','https://docs.vllm.ai/en/stable/design/prefix_caching/'),
'apcuse':('Automatic Prefix Caching','https://docs.vllm.ai/en/stable/features/automatic_prefix_caching/'),
'opt':('Optimization and Tuning','https://docs.vllm.ai/en/stable/configuration/optimization/'),
'sched':('v0.30.0 · scheduler.py','https://github.com/vllm-project/vllm/blob/v0.30.0/vllm/v1/core/sched/scheduler.py'),
'graph':('CUDA Graphs','https://docs.vllm.ai/en/stable/design/cuda_graphs/'),
'compile':('torch.compile integration','https://docs.vllm.ai/en/stable/design/torch_compile/'),
'flash':('FlashAttention paper (2022)','https://arxiv.org/abs/2205.14135'),
'parallel':('Parallelism and Scaling','https://docs.vllm.ai/en/stable/serving/parallelism_scaling/'),
'kvquant':('Quantized KV Cache','https://docs.vllm.ai/en/stable/features/quantization/quantized_kvcache/'),
'spec':('Speculative Decoding','https://docs.vllm.ai/en/stable/features/speculative_decoding/'),
'specpaper':('Speculative Decoding paper','https://arxiv.org/abs/2211.17192'),
'pd':('Disaggregated Prefilling','https://docs.vllm.ai/en/stable/features/disagg_prefill/'),
'metrics':('Production Metrics','https://docs.vllm.ai/en/stable/usage/metrics/')}
def esc(x):return html.escape(str(x),quote=True)
def fmt(x):return f'{x:.3f}' if isinstance(x,(int,float)) else str(x)
def vec(x):return '['+', '.join(fmt(t) for t in x)+']'
def wrap(t,limit):
    out=[];line='';n=0
    for c in str(t):
        z=1 if ord(c)>255 else .56
        if n+z>limit and line:out.append(line);line='';n=0
        line+=c;n+=z
    if line:out.append(line)
    return out or ['']
class SVG:
    def __init__(self,n,title,sub,inp):
        self.n=n;self.title=title;self.sub=sub;self.a=[];self.y=284;self._active=None
        self.rect(0,0,1600,182,INK,0)
        self.text(56,38,f'vLLM EXPLAINED / {n:02d} / 14',17,'#9ec5ff',700)
        self.text(56,99,title,38,'white',700);self.text(56,145,sub,21,'#cbd9eb')
        self.rect(56,206,1488,58,PALE);self.text(78,243,'本步输入 → '+inp,21,BLUE,700)
    def rect(self,x,y,w,h,fill='white',r=12,stroke=LINE):
        if self._active:self._active["bottom"]=max(self._active["bottom"],y+h)
        self.a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')
    def text(self,x,y,t,size=22,color=INK,weight=400,anchor='start',mono=False):
        if self._active:self._active["bottom"]=max(self._active["bottom"],y+size*.3)
        self.a.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}"'+(' class="mono"' if mono else '')+f'>{esc(t)}</text>')
    def lines(self,x,y,lines,size=22,color=INK,step=34):
        for i,t in enumerate(lines):self.text(x,y+i*step,t,size,color)
    def arrow(self,x1,y1,x2,y2):
        self.a.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{MUTED}" stroke-width="2.4" marker-end="url(#arr{self.n})"/>')
    def box(self,x,y,w,h,title,lines=(),fill=PALE,color=BLUE):
        self.rect(x,y,w,h,fill);self.text(x+18,y+32,title,22,color,700);self.lines(x+18,y+66,lines,20,MUTED,30)
    def _close_sec(self):
        if not self._active:return
        a=self._active;needed=max(a["height"],math.ceil(a["bottom"]-a["top"]+24))
        self.a[a["idx"]]=self.a[a["idx"]].replace(f'height="{a["height"]}"',f'height="{needed}"')
        self.y+=needed-a["height"];self._active=None
    def sec(self,title,height):
        self._close_sec();y=self.y;idx=len(self.a)
        self.rect(56,y,1488,height);self.text(80,y+39,title,26,INK,700)
        self._active={"top":y,"height":height,"idx":idx,"bottom":y+52}
        self.y+=height+22;return y+76
    def prose(self,title,lines):
        ls=[]
        for t in lines:ls+=wrap(t,64)
        y=self.sec(title,90+len(ls)*34);self.lines(80,y,ls)
    def table(self,title,headers,rows,widths=None,size=21):
        widths=widths or [1440/len(headers)]*len(headers);laid=[];rh=[]
        for row in [headers]+rows:
            cells=[wrap(t,(w-28)/size) for t,w in zip(row,widths)];laid.append(cells);rh.append(max(map(len,cells))*30+24)
        y=self.sec(title,76+sum(rh)+20)
        for ri,cells in enumerate(laid):
            x=80
            for ls,w in zip(cells,widths):
                self.rect(x,y,w,rh[ri],PALE if ri==0 else ('#f7f9fc' if ri%2 else 'white'),0)
                self.lines(x+14,y+32,ls,size,BLUE if ri==0 else INK,30);x+=w
            y+=rh[ri]
    def mat(self,x,y,A,label,cw=110,ch=44):
        self.text(x,y-2,label,21,BLUE,700)
        for i,row in enumerate(A):
            for j,v in enumerate(row):
                self.rect(x+j*cw,y+i*ch,cw,ch,'#f4f8ff',0)
                self.text(x+(j+.5)*cw,y+(i+.65)*ch,fmt(v),20,INK,400,'middle',True)
    def tokens(self,x,y,tokens,cw=160):
        for i,t in enumerate(tokens):
            self.rect(x+i*cw,y,cw-8,54,PALE);self.text(x+i*cw+(cw-8)/2,y+35,t,21,BLUE,700,'middle')
    def flow(self,title,stages,note=''):
        y=self.sec(title,290 if note else 240);w=(1440-60*(len(stages)-1))/len(stages)
        for i,(t,ls) in enumerate(stages):
            x=80+i*(w+60);self.box(x,y,w,140,t,ls)
            if i<len(stages)-1:self.arrow(x+w+5,y+66,x+w+52,y+66)
        if note:self.text(80,y+198,note,21,TEAL)
    def finish(self,out,refs):
        self._close_sec();y=self.y;self.rect(56,y,1488,64,GREEN);self.text(80,y+40,'交给下一步 → '+out,21,TEAL,700)
        y+=100;self.text(56,y,'参考原文 · 官方设计 / 论文；案例与数值推导为原创教学示例',17,MUTED)
        for i,key in enumerate(refs):
            name,url=SOURCES[key];xx=56+(i%2)*750;yy=y+36+(i//2)*31
            self.a.append(f'<a href="{esc(url)}" target="_blank"><text x="{xx}" y="{yy}" font-size="17" fill="{BLUE}">{esc(name)}</text></a>')
        self.height=y+75+math.ceil(len(refs)/2)*31
        pre=f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{self.height}" viewBox="0 0 1600 {self.height}" role="img" aria-labelledby="title{self.n} desc{self.n}"><title id="title{self.n}">{esc(self.title)}</title><desc id="desc{self.n}">{esc(self.sub)}。解释每步输入、处理与输出。</desc><defs><marker id="arr{self.n}" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="{MUTED}"/></marker></defs><style>text{{font-family:"Microsoft YaHei","Noto Sans CJK SC",Arial,sans-serif}}.mono{{font-family:Consolas,"Microsoft YaHei",monospace}}</style><rect width="1600" height="{self.height}" fill="{BG}"/>'
        return pre+'\n'+'\n'.join(self.a)+'\n</svg>'
P=DATA['prefill'];D=DATA['decode'];CHAPTERS=[]
def save(s,out,refs,slug):
    svg=s.finish(out,refs);fn=f'{s.n:02d}_{slug}.svg';(R/fn).write_text(svg,encoding='utf-8')
    CHAPTERS.append({'n':s.n,'title':s.title,'file':fn,'height':s.height,'svg':svg,'refs':refs})

# Teaching simulation, deliberately omits async / speculative / full-input reservation paths.
BLOCK=2;BUDGET=4
REQ={'A':{'prompt':[11,10,7],'arrival':1,'output':[8,1]},'B':{'prompt':[11,10,7],'arrival':2,'output':[8,1]},'C':{'prompt':[10,7,8,11,10,7,8],'arrival':2,'output':[10,1]}}
PLAN=[{'A':3},{'A':1,'B':1,'C':2},{'B':1,'C':3},{'C':2},{'C':1}]
free=[5,1,7,3,0,6,2,4,8,9,10,11];pool={i:{'tokens':[],'ref':0,'hash':None} for i in free};states={};trace=[];cache={}
def key(prefix):return hashlib.sha256(json.dumps(prefix,separators=(',',':')).encode()).hexdigest()
for turn,plan in enumerate(PLAN,1):
    arrivals=[]
    for name,r in REQ.items():
        if r['arrival']!=turn:continue
        st={'ids':r['prompt'][:],'computed':0,'blocks':[],'outputs':[],'finished':False,'hit':0}
        for j in range(len(r['prompt'])//BLOCK):
            h=key(r['prompt'][:(j+1)*BLOCK])
            if h not in cache:break
            bid=cache[h];st['blocks'].append(bid);pool[bid]['ref']+=1;st['computed']+=BLOCK;st['hit']+=BLOCK
            if bid in free:free.remove(bid)
        states[name]=st;arrivals.append({'request':name,'cached':st['hit'],'blocks':st['blocks'][:]})
    packed=[];positions=[];slots=[];bounds=[0];entries=[]
    for name,count in plan.items():
        st=states[name];start=st['computed'];end=start+count
        assert not st['finished'] and end<=len(st['ids'])
        while len(st['blocks'])*BLOCK<end:
            bid=free.pop(0);pool[bid]={'tokens':[],'ref':1,'hash':None};st['blocks'].append(bid)
        ids=st['ids'][start:end];sl=[]
        for p,t in zip(range(start,end),ids):
            bid=st['blocks'][p//BLOCK];off=p%BLOCK;assert len(pool[bid]['tokens'])==off
            pool[bid]['tokens'].append(t);sl.append(bid*BLOCK+off)
            if len(pool[bid]['tokens'])==BLOCK:
                h=key(st['ids'][:(p//BLOCK+1)*BLOCK]);pool[bid]['hash']=h;cache.setdefault(h,bid)
        st['computed']=end;out=None
        if end==len(st['ids']):
            out=REQ[name]['output'][len(st['outputs'])];st['outputs'].append(out)
            if out==1:st['finished']=True
            else:st['ids'].append(out)
        entries.append({'request':name,'count':count,'start':start,'end':end,'input_ids':ids,'positions':list(range(start,end)),'slots':sl,'blocks':st['blocks'][:],'output':out,'finished':st['finished']})
        packed+=ids;positions+=list(range(start,end));slots+=sl;bounds.append(len(packed))
    assert len(packed)<=BUDGET
    before=json.loads(json.dumps(pool))
    for e in entries:
        if e['finished']:
            for bid in states[e['request']]['blocks']:
                pool[bid]['ref']-=1
                if pool[bid]['ref']==0 and bid not in free:free.append(bid)
    trace.append({'round':turn,'arrivals':arrivals,'schedule':plan,'entries':entries,'input_ids':packed,'positions':positions,'slot_mapping':slots,'query_start_loc':bounds,'pool_before_release':before,'states':json.loads(json.dumps(states))})
(R/'_data/serving_trace.json').write_text(json.dumps({'block_size':BLOCK,'budget':BUDGET,'requests':REQ,'rounds':trace},ensure_ascii=False,indent=2),encoding='utf-8')

s=SVG(1,'一条请求，如何变成持续输出','模型负责预测；vLLM 组织请求、计算、KV 显存和输出的生命周期。','文本“小猫喜欢吃” + 已加载的模型 / Tokenizer')
s.flow('01  把既有的 Transformer 数学流程放进服务系统',[
('客户端',['提交 Prompt / messages','接收分段文本']),
('vLLM 运行时',['队列 → 调度 → KV 管理','GPU 执行 → 返回输出']),
('模型前向',['IDs → 隐藏状态 → logits','采样得到下一 token ID'])],
'读图顺序：输入是什么 → 这一层做了什么 → 状态变成什么 → 下一步拿走什么。')
s.table('02  本教程固定使用这一套参数',['对象','取值','作用'],[
['Tokenizer','V=12；[11,10,7]=[小猫,喜欢,吃]','ID 是词表索引；沿用上级教程的 BPE。'],
['模型','D=4；h_q=h_kv=2；d=2；L=1；F=6','每 token 每层有 K[2,2] 和 V[2,2]。'],
['运行时','b=2 token / KV 块；T=4 token / 轮','只用于画清地址，不是生产后端参数建议。'],
['输出','A/B：8“鱼” → 1“EOS”','来自上级教学模型的贪心预测。'],
['容量与计算','按 FP16 算容量；数值计算保留完整精度','显示约 3 位小数；不把显示舍入值继续代入。']], [220,600,620])
s.prose('03  本地执行的边界',[
'真实执行：读取既有模型数值，计算分页寻址、分块 Softmax 合并与五轮请求调度模拟，保存完整精度 JSON。',
'没有安装 / 运行 vLLM 或 GPU 基准；模拟省略异步、投机 token、完整输入预留和特殊模型路径。',
'A/B 的预测来自既有模型；长请求 C 只用来展示调度，其 [10,EOS] 是明确指定的模拟输出。',
'生产服务加载自己的模型检查点与 Tokenizer；不会收到请求后重新学习 BPE 或训练输出头。'])
s.prose('04  token ID、向量、KV 和文本是不同对象',[
'ID8 是索引；Embedding 把索引变成 D 维向量；逐层前向产生 K/V；反分词才产生用户看到的“鱼”。',
'采样到 ID8 时它的 KV 尚未计算，下一轮把 8 输入模型才得到位置 3 的 KV。',
'采样 EOS 后结束本例；EOS 不输入模型，所以 A 最终有 4-token KV，而输出 ID 列表是 [8,1]。'])
save(s,'请求 A 与模型配置 → 02：准备进程、权重与 GPU 内存',['arch','v1'],'请求全流程与统一案例')

s=SVG(2,'启动引擎：谁在 CPU，谁在 GPU','执行环境准备一次，再重复处理许多请求；请求之间共享模型权重。','检查点 + Tokenizer + dtype / GPU / 并行配置')
s.flow('01  启动时准备可重复使用的资源',[
('加载模型',['读取结构与权重','选择 dtype / 并行切分']),
('规划内存',['权重与峰值工作区','剩余预算用于 KV']),
('建立 KV 块池',['预留底层张量','按块分配使用权']),
('编译与预热',['准备适用算子 / 形状','捕获可复用执行图'])],
'“分配 KV 块”通常是在既有池中分配块 ID，不是每生成一个 token 都做一次 GPU malloc。')
s.flow('02  V1 典型进程职责：请求向右，结果向左回传',[
('API Server / CPU',['HTTP / 参数检查','模板、分词与流式返回']),
('EngineCore / CPU',['请求状态、调度与 KV 管理','协调模型执行器']),
('Worker / GPU',['ModelRunner 组织输入','前向、KV 读写与采样'])],
'单卡主线：1 API + 1 EngineCore + 1 GPU Worker；API 与 EngineCore 典型使用 IPC 消息。')
s.table('03  内存中分别存什么',['对象','生命周期','谁使用'],[
['模型权重','长期驻留，各请求共享只读','Linear / Norm / Attention / FFN。'],
['KV 块池','底层池长期存在；引用随请求变化','KV manager 管理；Attention 后端读写。'],
['请求元数据','从到达到结束 / 取消','ID、进度、位置、块表与采样配置。'],
['中间激活 / 工作区','在本轮执行中产生并复用','Q、各层隐藏状态和算子临时结果。'],
['编译与 CUDA Graph','按配置和适用形状复用','减少执行开销，也占启动时间和内存。']], [300,570,570])
s.prose('04  请求开始运行时',[
'Tokenizer 产生 [11,10,7] 后建立请求 A，模型权重无须为 A 重新加载。',
'调度器先决定算哪些位置，KV manager 保证有可写槽位，再让 ModelRunner 执行。',
'多卡部署按并行组增加 Worker；进程数和职责拆分随版本、前端与模型路径变化。'])
save(s,'就绪的 Worker / KV 池与请求 A → 03：建立调度状态',['arch','compile','graph'],'进程架构与启动内存')

s=SVG(3,'统一调度：本轮还欠多少 token 的计算','用已知 token 与已计算进度的差，连起 Prefill、Decode 和前缀命中。','A：known_ids=[11,10,7]；已计算 c=0；预算 T=4')
s.table('01  “已有 ID”和“已有 KV”必须同时记录',['时点','已知序列','c','待计算'],[
['刚加入','[11,10,7]','0','3 个 Prompt token。'],
['R1 前向后、采样前','[11,10,7]','3','到达序列尾，可以采样。'],
['R1 采样鱼后','[11,10,7,8]','3','1 个：p3 / ID8。'],
['R2 采样 EOS 后','[11,10,7,8]；输出另记 [8,1]','4','请求结束；EOS 不进入前向。']], [330,620,100,390])
s.flow('02  教学版调度决策：计算缺口，再分配预算',[
('计算需求',['need = len(known_ids) − c','A 初始 need=3']),
('检查资源',['n ≤ need / 剩余预算','准备 [c,c+n) 的 KV 块']),
('下发本轮计划',['R1：{A:3}','执行 positions=[0,1,2]'])],
'执行成功后 c ← c+n；未到 Prompt 尾部的 Prefill chunk 不会产生首个回复 token。')
s.prose('03  三种限制分别管什么',[
'max_num_batched_tokens：一轮允许新计算的 token 总数；本例 T=4 不表示最多只能接收 4 个请求。',
'max_num_seqs：同轮序列数量上限；max_model_len：上下文上限；KV 容量：能保留多少历史状态。',
'普通 Decode 通常每请求算 1 个新 token；Prefill 可分配多个或拆块。',
'实际 V1 还处理抢占、优先级、异步与预留。这里的简化公式解释主线，不替代 Scheduler 源码。'])
s.table('04  三个请求贯穿后续所有图',['请求','到达 / 输入','目的'],[
['A','R1：[11,10,7]','追踪 Prefill → 鱼 → EOS。'],
['B','R2：[11,10,7]','复用 A 已完成的前 2-token KV。'],
['C','R2：[10,7,8,11,10,7,8]','7-token 合成负载，展示分块与动态 batch。']], [150,720,570])
save(s,'R1：{A:3}，需要计算 [0,3) → 04：分配物理 KV 槽位',['v1','sched'],'统一调度与请求状态')

s=SVG(4,'KV 分页：逻辑连续，物理可以不连续','地址间接层把请求位置与底层存储分开；无需为每条请求预留一整段连续 KV。','A 需要位置 0、1、2；b=2；预留的物理块池共 12 块')
y=s.sec('01  按 token 位置分块，每个槽实际放的是向量',300)
s.tokens(80,y,['p0 / 小猫','p1 / 喜欢','p2 / 吃','p3 / 待计算'],cw=250)
s.box(80,y+80,492,86,'逻辑块 ℓ0：位置 [0,1]',[],GREEN,TEAL)
s.box(580,y+80,492,86,'逻辑块 ℓ1：位置 [2,3]',[],WARM,ORANGE)
s.text(80,y+211,'每 token 每层保存 K[2,2] + V[2,2]，共 8 个数；不是把 ID 复制进显存就得到 KV。',22)
y=s.sec('02  A 的 block_table=[5,1]，只存物理块编号',340)
s.box(80,y,390,100,'逻辑块 0 → 物理块 5',['存 p0,p1'],GREEN,TEAL)
s.box(80,y+140,390,100,'逻辑块 1 → 物理块 1',['存 p2,p3'],WARM,ORANGE)
for i in range(6):
    x=610+(i%3)*300;yy=y+(i//3)*130
    fill=GREEN if i==5 else WARM if i==1 else '#f4f6f9'
    s.box(x,yy,280,96,f'物理块 {i}',['p0,p1' if i==5 else 'p2,空槽' if i==1 else '空闲'],fill)
s.arrow(480,y+45,1200,y+175);s.arrow(480,y+185,900,y+45)
s.text(80,y+283,'图只画块 0–5；还有块 6–11。块 1 和块 5 无须搬到相邻地址。',21,MUTED)
s.table('03  位置 p → 逻辑块 → 物理块 → 槽位',['p','ℓ=⌊p/b⌋','offset=p mod b','phys=table[ℓ]','slot=phys×b+offset'],[
['0','0','0','5','10'],['1','0','1','5','11'],['2','1','0','1','2'],['3（下轮）','1','1','1','3']], [240,250,300,300,350])
s.prose('04  当前写入与历史读取',[
'写新 KV：slot_mapping=[10,11,2]，每层把当前 K/V scatter 到对应物理位置。',
'读旧 KV：Attention 通过 block_table 和有效长度，按逻辑顺序找到每个位置的向量。',
'内核可直接读取分页缓存；图中“拼成矩阵”只为推导，不表示每轮先复制完整历史。',
'每层都保存自己的 KV；分页仍有尾块未用槽与元数据开销，不会消除全部显存成本。'])
save(s,'A table=[5,1]、R1 slots=[10,11,2] → 05：执行 Prefill',['paper','page'],'分页KV与地址映射')

s=SVG(5,'Prefill：ID、位置和槽位一起交给模型','沿用上级模型的实际矩阵；分页改变摆放方式，前向仍按模型结构执行。','R1 IDs=[11,10,7]；positions=[0,1,2]；slots=[10,11,2]')
y=s.sec('01  Embedding 查表：ID 变成 D=4 的行向量',280)
s.mat(80,y,P['H'],'H = E[[11,10,7]]，形状 [3,4]',cw=130)
s.box(760,y,740,155,'每一行的身份始终一致',['第 0 行：小猫 / p0 / 槽10','第 1 行：喜欢 / p1 / 槽11','第 2 行：吃 / p2 / 槽2'])
s.text(80,y+195,'RMSNorm → Q/K/V 投影 → 拆成 2 头；Q/K 用各自位置做 RoPE；V 不做 RoPE。',22,TEAL)
y=s.sec('02  head 0 的 Prefill K/V：这些真实数值将被缓存',290)
s.mat(80,y,P['cache']['K'][0],'K₀ [3,2]，已经过 RoPE',cw=130)
s.mat(580,y,P['cache']['V'][0],'V₀ [3,2]，对应同样槽位',cw=130)
s.lines(1000,y+25,['head 1 也有独立 K/V。','Q 只供本轮 Attention。','历史 Q 通常不缓存。','完整矩阵见 _data。'],21,MUTED,35)
s.text(80,y+198,'在多层模型中，每层都重复此过程；该层 KV 来自该层输入，不能只存最后一层。',22)
y=s.sec('03  因果 Attention：多行并行，也不能看未来',280)
s.mat(80,y,P['A'][0],'head 0 的 P=softmax(mask(QKᵀ/√2))',cw=130)
s.lines(650,y+25,['p0 只读 [0]；p1 读 [0,1]；p2 读 [0,1,2]。','Attention → Concat → W_O → 残差。','RMSNorm → SwiGLU FFN → 残差 → 最终归一化。','形状：[3,4] → [3,2,2] → 合并回 [3,4]。'],22,INK,39)
s.text(80,y+197,'批量并行是同时计算多行；因果 mask 保证每行只依赖合法上下文。',22,TEAL)
s.prose('04  取 Prompt 最后一行，预测下一个 ID',[
'尾行最终隐藏状态 [1,4] × W_lm[4,12] → logits[1,12]。',
f'本例 temperature=0 取 argmax，选择 ID8“鱼”；其普通 Softmax 概率是 {P["prob"][-1][8]:.6f}。',
'8 可立即反分词为“鱼”并发送；A 的 c=3，known_ids 已成为 [11,10,7,8]。',
'刚生成的 8 还没有 KV；下轮计算 p3 才会产生它的 K/V。'])
save(s,'缓存 p0–p2、采样 ID8 → 06：输入 8，分页读历史并 Decode',['page','arch'],'Prefill矩阵与KV写入')

s=SVG(6,'Decode：按页读取 KV，算出下一 token','完整数值证明：物理位置分散，仍可得到与连续 Attention 相同的结果。','ID8 / p3；A table=[5,1]；新 K/V 写 slot3')
y=s.sec('01  当前 Q 与追加后的逻辑 K/V（以 head 0 为例）',380)
s.mat(80,y,D['q'][0],'q [1,2]，来自 ID8 / p3',cw=130)
s.text(900,y+28,'先计算 ID8 的 K/V，再让当前 Q 关注 p0–p3。',21,TEAL,700)
s.mat(80,y+130,D['Kall'][0],'逻辑 K [4,2]：前两行在块5，后两行在块1',cw=130)
s.mat(900,y+130,D['Vall'][0],'逻辑 V [4,2]',cw=130)
scores=D['score'][0][0];vals=D['Vall'][0];chunks=[]
for start in (0,2):
    sc=scores[start:start+2];m=max(sc);ww=[math.exp(t-m) for t in sc]
    chunks.append({'m':m,'l':sum(ww),'u':[sum(w*v[j] for w,v in zip(ww,vals[start:start+2])) for j in range(2)]})
m=max(t['m'] for t in chunks);ll=sum(math.exp(t['m']-m)*t['l'] for t in chunks)
uu=[sum(math.exp(t['m']-m)*t['u'][j] for t in chunks) for j in range(2)];paged=[v/ll for v in uu]
s.table('02  每一页算出的打分，最后要在全局归一化',['物理块','逻辑位置','score=q·k/√2','最终概率'],[
['5','0',fmt(scores[0]),fmt(D['A'][0][0][0])],['5','1',fmt(scores[1]),fmt(D['A'][0][0][1])],
['1','2',fmt(scores[2]),fmt(D['A'][0][0][2])],['1','3',fmt(scores[3]),fmt(D['A'][0][0][3])]], [300,300,440,400])
s.prose('03  不能每页独立 Softmax 后把输出简单平均',[
'每页 j 计算 m_j=max(scores_j)，l_j=Σexp(score−m_j)，u_j=Σexp(score−m_j)·v。',
'取 m=max(m_j)，然后 l=Σexp(m_j−m)·l_j，u=Σexp(m_j−m)·u_j，最终 o=u/l。',
'重标定让每页分母处于同一尺度，与所有有效 token 的一次 Softmax 数学等价。',
'分页分配块与 GPU 计算 tile / split 不必一致；这里按两页合并是原理展示。'])
s.table('04  本例逐页统计和完整精度合并',['位置 / 汇总','m','l','u / 输出'],[
['块5 / p0,p1',fmt(chunks[0]['m']),fmt(chunks[0]['l']),vec(chunks[0]['u'])],
['块1 / p2,p3',fmt(chunks[1]['m']),fmt(chunks[1]['l']),vec(chunks[1]['u'])],
['全局同一尺度',fmt(m),fmt(ll),vec(uu)],['最终 o=u/l','—','—',vec(paged)]], [350,200,240,650])
s.prose('05  回到模型与结束状态',[
'head 0 输出 '+vec(paged)+'；head 1 输出 '+vec(D['O'][1][0])+'；Concat 后继续残差、FFN 与 LM head。',
f'最终选择 EOS=1，普通 Softmax 概率 {D["prob"][0][1]:.6f}；c=4，EOS 不进入下一轮。',
'对照完整输入 [11,10,7,8] 的无缓存重算，缓存与分页结果在浮点误差范围内一致。',
'这是 Dense Attention，分页并没有自动减少应读取的历史 token 数。'])
(R/'_data/paged_attention.json').write_text(json.dumps({'scores':scores,'chunks':chunks,'merged':{'m':m,'l':ll,'u':uu,'o':paged},'expected':D['O'][0][0]},indent=2),encoding='utf-8')
save(s,'A 完成；B/C 已加入 → 07：将全过程放回五轮并发调度',['page','paper','flash'],'Decode分页Attention数值')

s=SVG(7,'连续批处理：每轮 batch 都会变化','A 完成即可让出执行位置；长 Prompt 也能拆成几轮与 Decode 共同执行。','A 在 R1 到达；B/C 在 R2 到达；T=4；B 命中 2-token 前缀')
y=s.sec('01  五轮时间线：格子表示新计算量，横向不是实际耗时',390)
for j,label in enumerate(['R1','R2','R3','R4','R5']):s.text(400+j*220,y+12,label,24,BLUE,700,'middle')
labels={'A':['P3 → 鱼','D1 → EOS','完成','—','—'],'B':['未到达','H2+P1 → 鱼','D1 → EOS','完成','—'],'C':['未到达','P2 / 7','P3 / 7','P2 → ID10','D1 → EOS']}
for i,(name,row) in enumerate(labels.items()):
    yy=y+42+i*78;s.text(100,yy+38,'请求 '+name,23,INK,700)
    for j,lab in enumerate(row):
        fill=GREEN if 'H' in lab else WARM if lab.startswith('D') else PALE if lab.startswith('P') else '#f0f3f7'
        s.rect(295+j*220,yy,210,62,fill);s.text(400+j*220,yy+38,lab,20,INK,400,'middle')
s.text(80,y+310,'P=Prefill 新算 token；D=Decode；H=命中缓存，不占本轮新计算 token 预算。',21,MUTED)
s.table('02  计划、输入和输出全部衔接上一轮',['轮次 / 用量','调度字典','packed IDs','轮末结果'],[
['R1：3/4','{A:3}','[11,10,7]','A→鱼，发布前 2-token 完整块。'],
['R2：4/4','{A:1,B:1,C:2}','[8,7,10,7]','A→EOS；B→鱼；C 已算2/7。'],
['R3：4/4','{B:1,C:3}','[8,8,11,10]','B→EOS；C 已算5/7。'],
['R4：2/4','{C:2}','[7,8]','C 完成 Prompt，模拟输出10。'],
['R5：1/4','{C:1}','[10]','C 模拟输出 EOS，全部结束。']], [220,340,390,490])
s.prose('03  Continuous Batching 与 Chunked Prefill 各做什么',[
'连续批处理：每轮更新参与请求，A 完成后不再占 R3 的执行位置，不必等待整批请求一起结束。',
'分块 Prefill：C 的 7-token Prompt 拆成 2+3+2；位置继续递增，后续 chunk 读取之前 chunk 的 KV。',
'R2 共算 4 token，却来自 3 个请求；“请求 batch 大小”不能独自表达本轮计算量。',
'总共新算 14 token：A4+B2+C8；B 另复用 2-token KV；三个 EOS 均未进入前向。'])
s.prose('04  token 预算的取舍',[
'较大 Prefill chunk 往往提高大矩阵执行效率，但可能拉长单轮、影响已在生成请求的 token 间隔。',
'较小 chunk 更容易插入 Decode，但会增加调度、发射及重复访问开销；应结合实际负载测量。',
'本图为原理模拟，省略实际异步与完整输入预留；没有声称所有版本都会产生这五轮相同计划。'])
save(s,'R2 混合输入 [8,7,10,7] → 08：看 packed batch 如何隔离各自上下文',['opt','v1','sched'],'连续批处理与分块Prefill')

s=SVG(8,'打包执行：四个 token 属于三个上下文','Packed / ragged batch 把新 token 排在一起；元数据保证每行只看自己的历史。','R2：A Decode 1；B Prefill 尾部 1；C Prefill 开头 2')
r2=trace[1]
s.table('01  先按请求展开，所有位置都来自各自状态',['请求 / 新 IDs','positions','已有 KV / 本轮写入','有效上下文'],[
['A：[8]','[3]','已有 p0–p2；新写 slot3','A 的 p0–p3，共4 token。'],
['B：[7]','[2]','共享前2；新写 slot14','B 的 p0–p2，共3 token。'],
['C：[10,7]','[0,1]','新写 slots=[6,7]','p0 只看自身；p1 看 p0,p1。']], [310,220,470,440])
y=s.sec('02  把新 token 打包成四行，而不是补齐到统一 Prompt 长度',340)
s.tokens(80,y,['A / 8','B / 7','C / 10','C / 7'],cw=240)
s.lines(80,y+110,[
'input_ids       = '+str(r2['input_ids']),
'positions       = '+str(r2['positions']),
'slot_mapping    = '+str(r2['slot_mapping']),
'query_start_loc = '+str(r2['query_start_loc'])],24,INK,39)
s.lines(1100,y+20,['边界 [0,1,2,4]：','A 占行 [0,1)','B 占行 [1,2)','C 占行 [2,4)'],21,MUTED,36)
s.prose('03  Packed 行号不是 token 的模型位置',[
'positions=[3,2,0,1] 不能改成 [0,1,2,3]；RoPE 使用本请求位置，不使用 packed 全局行号。',
'Attention 还需要 query_start_loc、各请求 block_table 和有效长度，才能找到各自合法上下文。',
'A/B 仅因相同前缀共享物理块5；私有尾部在块1与块7。C 不能关注 A/B。',
'共享权重的线性层可按 packed 大矩阵计算；Attention 后端再依据请求边界与因果关系处理。'])
s.flow('04  前向结束后，恢复请求身份并更新状态',[
('Packed H [4,4]',['查表、Norm、投影','按槽位写新 K/V']),
('Attention 与 FFN',['读各自块表和上下文','保持行与请求的对应']),
('按请求取尾部输出',['A→EOS；B→鱼','C 未到 Prompt 尾部'])],
'本例非投机生成只对到达可采样位置的请求返回 token；部分 Prefill chunk 不生成首 token。')
save(s,'各请求进度与共享块引用 → 09：解释前缀命中的完整生命周期',['v1','page','arch'],'混合批次与GPU输入打包')

s=SVG(9,'前缀缓存：复用已经算过的上下文','先有因果相同的前缀，才有相同 KV；词语相同但之前历史不同，仍不能复用。','A 已发布块5=[11,10]；B 输入 [11,10,7]')
s.flow('01  B 跳过前两行的模型前向，尾部自己计算',[
('A：table=[5,1]',['块5：[11,10] / 完整','块1：[7,空] / R1后']),
('共享物理块5',['保存 p0,p1 的各层 KV','R2 ref_cnt：1 → 2']),
('B：table=[5,7]',['p0,p1 直接指向块5','p2 的7写私有块7'])],
'B 只计算 p2，但 p2 的 Q 仍读取三 token 上下文；复用 KV 不等于直接返回旧回复。')
s.prose('02  缓存键必须体现“当前块之前的全部历史”',[
'概念键：H_j = hash(H_(j−1), 本块 token IDs, 额外身份信息)。父 hash 将前面的上下文带入。',
'同样的 [11,10] 出现在不同历史后面，逐层状态可能不同；不能只对当前块的文字求 hash。',
'LoRA、图像内容等会改变状态，应纳入身份；还可通过 cache salt 控制复用范围。',
'本地模拟用“完整前缀 IDs 的 SHA-256”表达因果身份，并未复制 vLLM 的具体序列化实现。'])
s.table('03  引用数归零，不等于缓存内容立刻被擦除',['时点','块5引用','私有尾块','作用'],[
['R1 后','1','A：块1','完整块5可被缓存索引找到。'],
['R2 B 命中','2','B 新分块7','A/B 共用只读完整块。'],
['R2 A 结束','1','块1引用归零','B 仍在用块5，不可给其他请求覆盖。'],
['R3 B 结束','0','块7引用归零','块5可保留 KV/hash，进入可回收队列。'],
['新分配有压力','可回收缓存被驱逐','物理块再分配','去掉旧 hash 后才能装入新内容。']], [280,200,350,610])
s.prose('04  完整块复用、尾 token 重算与写时复制',[
'本例按普通完整块命中路径，B 命中 2/3 token。混合模型与新版本可有不同的匹配粒度。',
'Prompt 全部命中 KV 也不意味着 logits 被缓存；常见生成路径仍要处理尾 token 才能预测下一 token。',
'原论文为并行采样讨论共享部分块的 copy-on-write；本例 B 只共享完整块，尾块另分配，不触发 COW。',
'V1 append-only 块表可暂时保存内容重复的物理块；不能假设检测相同后总会立即替换运行中的块表。'])
s.prose('05  节省的是哪一段时间',[
'APC 主要省去重复前缀的 Prefill 计算；后续 Decode 仍要读取这段历史 KV。',
'因此 Prefix Cache 不会自动缩短模型上下文，也不会让长上下文 Decode 的显存读取消失。'])
save(s,'活动引用、前缀索引和可回收块 → 10：计算容量并处理内存压力',['apc','apcuse','paper'],'前缀缓存与引用生命周期')

s=SVG(10,'显存容量：多少历史，多少请求','先数每 token 的 K/V，再算分块、共享节省与抢占恢复；不把权重当成 KV。','L、h_kv、d、每元素字节数 s；块大小 b；物理块数量')
s.prose('01  普通 Dense / GQA Transformer 的 KV 公式',[
'M_token = 2 × L × h_kv × d × s；2 分别代表 K 与 V。',
'教学模型 FP16：2×1×2×2×2 = 16 bytes/token；b=2，每物理块跨全部层合计 32 bytes。',
'A 在 c=3 时占2块=64 bytes，其中有效 KV 为48 bytes，最后一槽16 bytes 尚未使用。',
'A 在 c=4 时仍占2块=64 bytes；EOS 不输入，不会产生第5个 token 的 KV。',
'MLA、状态空间、跨层共享等特殊结构需另算；布局、对齐、缓存分组和元数据也占空间。'])
s.table('02  大模型容量算例：不绑定具体模型型号',['假设','计算','结果'],[
['L=32,h_kv=8,d=128,FP16','2×32×8×128×2','131072 bytes = 128 KiB/token。'],
['b=16 token/block','16×128 KiB','每块跨全部层 2 MiB。'],
['可用 KV 预算20 GiB','20 GiB ÷ 2 MiB','10240块，共163840 token槽。'],
['每请求实际驻留4096 token','ceil(4096/16)=256块','理想容量40条；尚未预留未来增长。']], [480,470,490])
s.flow('03  R2 执行后、释放 A 前，数唯一物理块',[
('A：4 token',['table=[5,1]','2 块 / 64 bytes']),
('B：3 token',['table=[5,7]','块5与 A 共享']),
('C：2 token',['table=[3]','1 块 / 32 bytes'])],
'独立块数2+2+1=5；实际唯一物理块 {5,1,7,3}=4，占128 bytes而不是160 bytes。')
s.prose('04  GPU 总预算扣除其他开销后，剩下才是 KV',[
'概念预算：GPU可用份额 − 权重 − 峰值激活/工作区 − 图与运行时开销 − 其他预留。',
'gpu_memory_utilization 影响实例可用显存预算；还要留意其他进程与峰值所需空间。',
'max_model_len、max_num_seqs 与本轮 token 预算分别约束上下文、序列数与计算量，不能互相替代。',
'底层张量池可能已经预留很大；活动请求只引用部分块。池容量与当前活动占用要分别观察。'])
s.flow('05  缺块时的重算式抢占与恢复',[
('分配不足',['回收闲置缓存仍不够','需要暂停某个请求']),
('释放请求 KV 引用',['保留已知 token IDs','请求转为等待恢复']),
('稍后重新调度',['Prompt + 已生成 IDs','重建或命中 KV 后继续'])],
'重算恢复历史状态，不向用户重复发送旧内容；代价是额外计算与等待。')
s.prose('06  与其他内存路径的关系',[
'V1 文档的典型抢占模式是 RECOMPUTE；CPU offload / KV connector 是另外配置和约束的机制。',
'反复抢占通常说明容量或并发配置不适配，应结合 KV 使用、等待队列与请求长度分析。'])
save(s,'容量与计算成本已知 → 11：减少 GPU 读写和逐轮发射成本',['opt','paper','kvquant'],'显存公式与抢占恢复')

s=SVG(11,'执行加速：分页、FlashAttention、编译与图','这些机制作用于不同成本，可以组合；不要把它们当成同一种优化。','带块表的 packed batch + 模型权重 + GPU 工作区')
s.table('01  四类机制分别减少什么',['机制','优化目标','边界'],[
['Paged KV / PagedAttention','定位和分配历史 KV，支持共享，减少浪费','不自动减少 Dense Attention 要读取的历史。'],
['FlashAttention 类内核','tiling + 在线 Softmax，避免完整 S/P 的 HBM 往返','计算 tile 与 KV 分配块不是同一种块。'],
['融合 / torch.compile','减少中间张量、Python 调用和小 kernel 成本','可融合范围取决于模型、算子与后端。'],
['CUDA Graph replay','减少重复执行路径的 CPU 发射开销','不缓存模型预测；本轮输入与 KV 仍然更新。']], [330,600,510])
s.flow('02  本轮执行穿过多层优化',[
('输入打包',['IDs / positions','slot / block 元数据']),
('投影与 Norm',['Linear 矩阵乘法','可融合的执行子图']),
('Attention 后端',['直接读取 paged KV','分块 QK / Softmax / AV']),
('FFN 与输出',['SwiGLU / Linear','logits 与采样'])],
'CUDA Graph 可覆盖适用的整个执行段或子段；不兼容部分采用其他执行路径。')
s.prose('03  Prefill 与 Decode 为什么受益不同',[
'Prefill 的 Q 有很多行，通常更容易利用大矩阵计算；避免 N×N 中间 S/P 全量落显存尤其有价值。',
'Decode 每请求通常只有1个 Q 行；上下文越长，扫描 KV 的带宽与并行度越关键。',
'小 batch 或单轮 GPU 很快时，CPU 调度、输入准备和多次 kernel 发射也会成为明显成本。',
'Prefill偏计算、Decode偏带宽是常见趋势，实际仍由模型、batch、上下文和硬件共同决定。'])
s.flow('04  CUDA Graph 不是把第一次输出拿来复用',[
('预热 / 捕获',['准备适用形状和路径','保持稳定的缓冲区']),
('每轮更新输入',['填入新 IDs / positions','更新 slot 与元数据']),
('分派与重放',['选兼容形状桶 / 图','不匹配时切换路径'])],
'形状桶 / padding 可提高复用率，也可能增加额外计算；捕获还需要启动时间和图内存。')
s.prose('05  原内核文档与现行 vLLM 的关系',[
'官方 Paged Attention 页面描述一个特定单 Query 内核；现行 vLLM 按模型与硬件选择兼容后端。',
'各后端支持的分页布局、head size、dtype、混合 batch 与 CUDA Graph 路径并不完全相同。',
'本图解释寻址和计算原理，不假定每张显卡都使用同一份历史 CUDA 内核。'])
save(s,'单 Worker 的高效执行 → 12：扩展到多个 GPU',['flash','compile','graph','page'],'内核FlashAttention与CUDAGraph')

s=SVG(12,'多 GPU：切权重、切层，还是复制模型','模型并行让一条请求跨设备执行；数据并行把不同请求交给不同实例。','权重单卡装不下，或需要更高的服务吞吐')
s.flow('01  TP：同一层的矩阵切到多张 GPU',[
('共同输入 H [N,D]',['同一批请求的隐藏状态','按需要广播或保持副本']),
('GPU0 / GPU1 分片',['投影 / FFN 分别计算','得到局部中间结果']),
('组合分片结果',['典型行并行 Y=Σ H_rW_r','需要 collective 通信'])],
'KV 可按 heads 分片；KV head 数与 TP 不匹配时可复制，不能一律把 KV 容量直接除以 TP。')
s.flow('02  PP：不同层放到不同 GPU，传递隐藏状态',[
('GPU0：层0…15',['处理上半段网络','本地保存这些层的 KV']),
('GPU1：层16…31',['接收隐藏状态','保存后续层 KV 并计算']),
('输出阶段',['完成最后归一化与输出','向调度器返回结果'])],
'单请求仍穿过多个阶段；通信延迟、流水空泡与微批大小会影响效率。')
s.flow('03  DP：复制模型组，分流不同请求',[
('请求路由',['A / B / C 到达','观察队列和负载']),
('DP rank0',['一套模型或 TP 组','本地 EngineCore / KV']),
('DP rank1',['另一套模型或 TP 组','处理另一批请求'])],
'本地 APC 通常属于各自副本；把 B 发到没有 A 前缀的实例可能错失命中。')
s.table('04  需求与代价要一起看',['需求','常见方向','要核对'],[
['单卡放不下权重','TP / PP 与权重量化','互联、层结构、切分粒度、实际内存。'],
['模型单卡能装下，扩吞吐','增加 DP 副本并合理路由','权重复制与局部前缀命中变化。'],
['MoE 专家层','EP 将专家分布到设备','token 路由与 all-to-all，不等于 Dense TP。'],
['DP2 × TP2 × PP1','示意需要4个 GPU Worker','每个 DP 副本拥有自己的引擎与 TP 组。']], [380,510,550])
s.prose('05  回到请求 A 的块表',[
'各 Worker 保存属于自己的权重和 KV 分片；同一请求需要并行组内协同，而不是任意一张卡单独完成。',
'本教程 D=4、h=2 只是尺寸教学例子，不声称可直接部署成生产级多 GPU 模型。'])
save(s,'多卡执行组与通信代价 → 13：比较其他可选优化',['parallel','opt','arch'],'多GPU并行与通信')

s=SVG(13,'进阶优化：精度、生成轮次与 P/D 分离','沿同一请求链说明收益从何而来，并给出额外计算、内存或传输成本。','已知权重、KV、执行与调度成本，继续寻找容量和延迟改进')
s.table('01  权重量化和 KV 量化，压缩的不是同一对象',['对象','改变什么','边界'],[
['权重量化','压缩权重，使用兼容量化 GEMM / 反量化路径','不能直接等同 KV 容量减半。'],
['KV 量化','用低精度保存 K/V，附带需要的缩放信息','2 bytes→1 byte 时数据部分约减半，还需 scale/对齐。'],
['输出与速度','精度、缩放策略和内核支持决定效果','近似存储可能影响输出；不承诺固定加速倍数。']], [300,670,470])
s.flow('02  投机生成：先提出多个候选，再由目标模型验证',[
('Draft / 提议器',['提出 [t1,t2,t3]','成本要足够低']),
('Target / 验证',['一次前向检查多个位置','得到目标模型分布']),
('接受与修正',['接受连续合法候选','更新输出、进度与 KV'])],
'A 的 [鱼,EOS] 主线未启用投机；t1/t2/t3 仅为解释机制的符号。')
s.prose('03  正确性与收益条件',[
'贪心验证可比对目标选择；随机采样需正确的接受/拒绝与修正采样，不能只比 argmax。',
'正确投机算法可保持目标分布，但不同精度与 kernel 的细小数值差异仍需按实现评估。',
'被拒绝候选的后续状态必须回收或覆盖，调度也可能需要额外 lookahead 空间。',
'接受率低、batch 已饱和或提议器昂贵时，额外工作可能抵消少调用几轮的收益。'])
s.flow('04  Prefill / Decode 分离：在两组设备交接状态',[
('Prefill 池 P',['处理 Prompt 并产生 KV','准备必要的首 token 状态']),
('KV Connector',['传输与布局交接','源块 ID 不等于目标块 ID']),
('Decode 池 D',['目标侧分配自己的槽位','取得状态后继续生成'])],
'传输有效 KV 量约 N×2Lh_kvds；首 token 在哪侧采样、怎样交接取决于实现。')
s.prose('05  为什么分离也有成本',[
'P/D 需保持一致的 token 位置和模型状态语义；分离不是把块表整数发给另一张 GPU 就完成。',
'A 仅3-token Prompt，图只展示交接；网络、同步和传输可能比它的计算还昂贵。',
'长 Prompt 与长 Decode 混合时可分别扩容、降低相互干扰；收益需要覆盖 KV 搬运成本。',
'官方将 P/D 功能标为实验性质；需匹配 connector、设备和布局，不是所有配置都会更快。'])
save(s,'各机制的收益与额外成本 → 14：用完整链路指标检验',['kvquant','spec','specpaper','pd'],'量化投机与PD分离')

s=SVG(14,'闭合整条链：怎么知道优化有效','把等待、首 token、逐 token 和完成时间连起来，理解吞吐与延迟的取舍。','从 API 到调度、KV、执行、返回的完整请求链与观测')
s.flow('01  同一请求的时间轴，测量边界要一致',[
('到达与排队',['模板 / tokenization','等待预算和 KV 空间']),
('首轮执行',['Prefix 命中 / Prefill','采样第一个 token']),
('循环 Decode',['每轮调度与 KV 访问','生成后续 token']),
('输出与结束',['反分词 / 网络发送','EOS 或其他停止条件'])],
'客户端端到端、服务器处理和 GPU kernel 时间是不同观测，不能直接互相替代。')
s.table('02  指标、含义和对应机制',['指标','含义','关联路径'],[
['TTFT','首个输出 token 时间 − 请求到达时间','排队、输入处理、缓存命中、Prefill、传输。'],
['ITL / TPOT','token 间隔 / 每输出 token 时间；按基准定义统计','Decode 调度、混合轮长度、带宽和发射成本。'],
['端到端延迟','完成时间 − 到达时间','TTFT + 后续生成 + 输出处理；观察分位数。'],
['吞吐 / goodput','单位时间的请求或 token；goodput 加上延迟约束','batching、容量、并行；区分输入/输出计数口径。'],
['KV / cache / preemption','块占用、命中 token 和抢占次数','排查容量、低命中与反复重算。']], [290,620,530])
s.table('03  看到现象后，沿数据流找原因',['现象','先拆解什么','比较什么'],[
['TTFT 高','排队久，还是长 Prompt 计算久？','相同负载下，前缀命中与 token 预算。'],
['流式输出抖动','长 Prefill、CPU 或网络是否积压？','ITL 分位数与混合 batch / chunk 大小。'],
['频繁抢占','上下文、并发、权重和图占用？','相同输入分布下，容量与并发上限。'],
['GPU 不忙但延迟高','输入、调度、发射或跨卡通信？','CPU/GPU profile，不直接盲目加大 batch。']], [300,620,520])
s.prose('04  本教程已验证什么',[
'数值验证：五轮输入来源、进度 c、预算、块地址、完整前缀复用、活动引用和 EOS 无额外 KV。',
'分页读取与在线 Softmax 合并，数值对齐既有模型的连续 Attention；完整精度数据保存在 _data。',
'未运行实际 vLLM / GPU 基准，因此不提供虚构的 tokens/s、毫秒耗时或加速倍数。',
'真实测评需固定模型、版本、硬件、精度、输入/输出长度分布、到达率和并发，比较 p50/p95/p99。'])
y=s.sec('05  再完整走一次 A：所有部分处在同一条连续链',340)
s.lines(80,y,[
'“小猫喜欢吃” → Tokenizer [11,10,7] → 请求 A / c=0',
'R1 {A:3} → table=[5,1] → slots=[10,11,2] → Prefill 逐层写 KV',
'尾部 logits → ID8“鱼” → 流式返回；此时 c=3，known_ids 长度=4',
'R2 混合 A/B/C → A 输入8 / p3 / slot3 → 依块5、块1读4-token上下文',
'Attention → 残差 / FFN / 输出头 → EOS → A完成 → 释放块引用',
'块5因 B仍引用而保留 → B结束后可回收或缓存 → 服务继续接收请求'
],23,INK,40)
save(s,'回看各章，或用网页的五轮调度播放器逐项检查输入与状态',['metrics','opt'],'性能指标与全链路回顾')

atlas=[];offsets=[];totalheight=0
for ch in CHAPTERS:
    inner=ch['svg'][ch['svg'].find('>')+1:ch['svg'].rfind('</svg>')]
    atlas.append(f'<g id="chapter{ch["n"]:02d}" transform="translate(0,{totalheight})">{inner}</g>')
    offsets.append({'id':f'chapter{ch["n"]:02d}','y':totalheight,'height':ch['height'],'file':ch['file'],'title':ch['title']})
    totalheight+=ch['height']+24
allsvg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{totalheight}" viewBox="0 0 1600 {totalheight}" role="img" aria-label="vLLM 十四步连续图解">'+''.join(atlas)+'</svg>'
(R/'00_vLLM_连续全景.svg').write_text(allsvg,encoding='utf-8')
(R/'_data/chapters.json').write_text(json.dumps(offsets,ensure_ascii=False,indent=2),encoding='utf-8')
NAV=''.join(f'<a href="#fig{c["n"]}" data-n="{c["n"]}"><span>{c["n"]:02d}</span>{esc(c["title"])}</a>' for c in CHAPTERS)
CONTENT=''.join(f'<section class="chapter" id="fig{c["n"]}"><div class="sectionbar"><span>第 {c["n"]:02d} 步</span><a href="{esc(c["file"])}" download>下载本步 SVG ↗</a></div>{c["svg"]}</section>' for c in CHAPTERS)
STYLE='''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:86px}body{margin:0;color:#14243b;background:#eef2f7;font-family:"Microsoft YaHei",Arial,sans-serif}a{color:#2563eb;text-decoration:none}header{height:70px;position:sticky;top:0;z-index:10;background:#14243b;color:white;display:flex;align-items:center;justify-content:space-between;padding:0 26px;gap:14px}header strong{font-size:21px}header small{color:#afc4df;margin-left:18px}button{border:1px solid #ccd9e8;border-radius:8px;background:white;color:#14243b;padding:8px 13px;cursor:pointer;font:inherit}button:hover{background:#eaf1ff}button:disabled{opacity:.4;cursor:default}aside{position:fixed;top:70px;bottom:0;left:0;width:264px;background:#fff;border-right:1px solid #d9e3ee;overflow:auto;padding:20px 12px}aside a{display:flex;padding:10px 9px;font-size:14px;line-height:1.6;border-radius:7px;color:#52647b;gap:10px}aside a.active{background:#eaf1ff;color:#2563eb;font-weight:bold}aside span{font-family:Consolas,monospace}main{margin-left:264px;padding:28px;max-width:1900px}.intro,.player,.sources{background:white;border:1px solid #d9e3ee;border-radius:16px;padding:26px;margin-bottom:26px}h1{font-size:30px;margin:0 0 12px}h2{font-size:23px;margin:0 0 16px}p{line-height:1.9;margin:8px 0}.muted{color:#52647b}.tag{display:inline-block;padding:5px 9px;background:#e5f6f1;border-radius:6px;color:#087f8c;font-size:13px;margin:0 8px 12px 0}.chapter{margin-bottom:24px;overflow:auto;background:#f3f6fb;border:1px solid #d9e3ee;border-radius:12px;scroll-margin-top:82px}.sectionbar{display:flex;justify-content:space-between;padding:12px 18px;background:white;font-size:14px}.chapter svg{display:block;width:100%;height:auto}body.actual .chapter svg{width:1600px;max-width:none}.controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:16px}.rounds{display:flex;gap:8px}.rounds button.selected{background:#2563eb;color:white;border-color:#2563eb}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card{border:1px solid #d9e3ee;border-radius:10px;padding:16px;background:#f7f9fc}.card h3{margin:0 0 12px;color:#2563eb}.card code,pre{white-space:pre-wrap;word-break:break-word;font-family:Consolas,"Microsoft YaHei",monospace;font-size:14px;line-height:1.8}table{width:100%;border-collapse:collapse;margin-top:16px}td,th{padding:10px;text-align:left;border-bottom:1px solid #d9e3ee;font-size:14px;line-height:1.7}th{color:#52647b;background:#f3f6fb}#roundnote{padding:14px 16px;background:#e5f6f1;border-radius:8px;line-height:1.8}.sources li{line-height:2.1}#progress{height:3px;background:#60a5fa;position:fixed;top:67px;left:0;z-index:12}details{margin-top:18px}summary{cursor:pointer;color:#2563eb}footer{padding:16px;color:#52647b;font-size:13px}@media(max-width:1100px){aside{width:205px}main{margin-left:205px;padding:14px}header small{display:none}.grid{grid-template-columns:1fr}}@media(max-width:760px){aside{display:none}main{margin-left:0}header{padding:0 10px}header strong{font-size:16px}header button{font-size:12px;padding:7px}.intro,.player,.sources{padding:18px}h1{font-size:24px}}'''
JAVASCRIPT='''const trace=TRACE;let round=0;let timer=null;
const notes=[
'R1：A 前向计算3个 Prompt token，输出鱼。c=3；鱼只是刚采样的ID，下轮才计算它的KV。',
'R2：B命中前2-token；A算鱼并输出EOS；B只算吃并输出鱼；C算前2-token。A结束后B仍引用块5。',
'R3：B算鱼并结束；C再算3-token，累计5/7。块5活动引用归零后可保留为缓存。',
'R4：C算最后2个 Prompt token，累计7/7；指定模拟输出ID10，非模型预测。',
'R5：C计算ID10的KV，指定输出EOS。全部结束；EOS不进入下一轮前向。'];
const labels={11:'小猫',10:'喜欢',7:'吃',8:'鱼',1:'EOS'};
const safe=x=>String(x).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
function renderRound(){
 const t=trace[round];document.querySelectorAll('.rounds button').forEach((b,i)=>b.classList.toggle('selected',i===round));
 document.getElementById('roundtitle').textContent='R'+t.round+' · 新算 '+t.input_ids.length+' / 4 token';
 document.getElementById('roundnote').textContent=notes[round];
 document.getElementById('packed').textContent='input_ids       = '+JSON.stringify(t.input_ids)+'\\npositions       = '+JSON.stringify(t.positions)+'\\nslot_mapping    = '+JSON.stringify(t.slot_mapping)+'\\nquery_start_loc = '+JSON.stringify(t.query_start_loc);
 document.getElementById('statecards').innerHTML=['A','B','C'].map(n=>{
  const s=t.states[n],e=t.entries.find(x=>x.request===n);
  if(!s)return '<article class="card"><h3>请求 '+n+'</h3><p>尚未到达</p></article>';
  const state=s.finished?'已结束':s.computed<({A:3,B:3,C:7}[n])?'Prefill中':'等待计算新生成token';
  return '<article class="card"><h3>请求 '+n+' · '+state+'</h3><code>known IDs: '+safe(JSON.stringify(s.ids))+'<br>c='+s.computed+'；前缀命中='+s.hit+'<br>块表='+safe(JSON.stringify(s.blocks))+'<br>输出='+safe(JSON.stringify(s.outputs))+'</code><p class="muted">'+(e?'本轮 p=['+e.start+','+e.end+')；'+(e.output===null?'没有输出':('产生 '+(labels[e.output]||e.output))):'本轮没有新计算')+'</p></article>';
 }).join('');
 const used=Object.entries(t.pool_before_release).filter(([id,b])=>b.tokens.length>0);
 document.getElementById('poolrows').innerHTML=used.map(([id,b])=>'<tr><td>'+id+'</td><td>'+safe(JSON.stringify(b.tokens))+'</td><td>'+b.ref+'</td><td>'+(b.hash?'完整块 / 有hash':'部分块')+'</td></tr>').join('');
}
document.querySelectorAll('.rounds button').forEach((b,i)=>b.addEventListener('click',()=>{round=i;renderRound()}));
document.getElementById('rprev').onclick=()=>{round=Math.max(0,round-1);renderRound()};
document.getElementById('rnext').onclick=()=>{round=Math.min(4,round+1);renderRound()};
document.getElementById('play').onclick=()=>{if(timer){clearInterval(timer);timer=null;document.getElementById('play').textContent='自动播放';return}document.getElementById('play').textContent='暂停';timer=setInterval(()=>{round=(round+1)%5;renderRound()},2400)};
document.getElementById('zoom').onclick=()=>{document.body.classList.toggle('actual');document.getElementById('zoom').textContent=document.body.classList.contains('actual')?'适应宽度':'矩阵1:1'};
const chapters=[...document.querySelectorAll('section.chapter')],links=[...document.querySelectorAll('aside a')];let current=0;
function update(){let k=0;for(let i=0;i<chapters.length;i++)if(chapters[i].getBoundingClientRect().top<180)k=i;current=k;links.forEach((a,i)=>a.classList.toggle('active',i===k));document.getElementById('pageno').textContent=(k+1)+' / 14';document.getElementById('progress').style.width=(100*scrollY/Math.max(1,document.documentElement.scrollHeight-innerHeight))+'%'}
function jump(n){n=Math.max(0,Math.min(13,n));chapters[n].scrollIntoView({behavior:'smooth'});history.replaceState(null,'',new URL('#fig'+(n+1),location.href).href)}
document.getElementById('prev').onclick=()=>jump(current-1);document.getElementById('next').onclick=()=>jump(current+1);
window.addEventListener('scroll',update,{passive:true});renderRound();update();
'''.replace('TRACE',json.dumps(trace,ensure_ascii=False))
SOURCELIST=''.join(f'<li><a href="{esc(v[1])}" target="_blank" rel="noreferrer">{esc(v[0])}</a></li>' for v in SOURCES.values())
PAGE='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>vLLM详解 · 连续SVG教程</title><style>STYLE</style></head><body>
<header><div><strong>vLLM详解</strong><small>同一案例 · 十四步贯通 · 官方资料</small></div><div class="controls" style="margin:0"><button id="prev">上一步</button><span id="pageno">1 / 14</span><button id="next">下一步</button><button id="zoom">矩阵1:1</button></div></header><div id="progress"></div>
<aside>NAV</aside><main>
<div class="intro"><span class="tag">vLLM V1主线</span><span class="tag">资料核对2026-10-18</span><span class="tag">可复现原理模拟</span>
<h1>一条请求如何穿过 vLLM</h1><p>沿用“小猫喜欢吃”的统一模型，从API、调度、分页KV走到Prefill、Decode和流式输出，再把前缀复用、连续批处理与GPU执行优化放回同一条链。</p>
<p class="muted">每幅图都可独立下载SVG。矩阵显示约3位小数，计算与JSON保持完整精度。A/B预测来自上级教学模型，C输出和五轮计划为指定模拟；没有运行真实vLLM或测量GPU性能。</p>
<p><a href="00_vLLM_连续全景.svg" download>下载完整连续SVG</a> · <a href="README.md">说明与源码定位</a> · <a href="../index.html">返回Transformer教程</a> · <a href="_data/serving_trace.json">调度完整数据</a></p></div>
<div class="player" id="player"><h2>先看一遍：五轮调度播放器</h2><p class="muted">点轮次检查输入、进度和输出。物理块表是本轮前向完成、释放已结束请求引用前的快照；请求卡片展示轮末逻辑状态。</p><div class="controls"><button id="rprev">前一轮</button><div class="rounds"><button>R1</button><button>R2</button><button>R3</button><button>R4</button><button>R5</button></div><button id="rnext">后一轮</button><button id="play">自动播放</button></div><h3 id="roundtitle"></h3><div id="roundnote"></div><pre id="packed"></pre><div class="grid" id="statecards"></div><details><summary>展开物理KV块（含可回收旧缓存）</summary><table><thead><tr><th>物理块</th><th>token IDs</th><th>活动引用数</th><th>缓存身份</th></tr></thead><tbody id="poolrows"></tbody></table></details></div>
CONTENT
<div class="sources" id="references"><h2>官方文档、论文与适用范围</h2><p>以V1主线为准。2023论文、2025架构博客与现行文档提供不同层次的说明；类、配置默认值和后端支持随版本变化。源码用固定v0.30.0标签作可查阅样本，不声称它是最新版本。</p><ol>SOURCELIST</ol></div>
<footer>原创SVG / Python构建器 / JSON全精度案例；数值和版面检查见_qa。</footer></main><script>JAVASCRIPT</script></body></html>'''
PAGE=PAGE.replace('STYLE',STYLE).replace('NAV',NAV).replace('CONTENT',CONTENT).replace('SOURCELIST',SOURCELIST).replace('JAVASCRIPT',JAVASCRIPT)
(R/'图解版.html').write_text(PAGE,encoding='utf-8')
readme=['# vLLM详解','','入口：[index.html](index.html)。十四步连续SVG教程，带目录、上下步、矩阵1:1和五轮调度播放器。','','## 统一案例与执行边界','',
'V=12，Prompt=[11,10,7]，D=4，h_q=h_kv=2，d=2，F=6，L=1。A/B沿用上级教学模型的贪心预测：鱼8、EOS1。主体固定、输出头训练的教学模型不代表真实预训练模型。服务请求时不重新训练BPE或模型。','',
'真实执行的是本地分页地址、Softmax归并与简化服务调度模拟；没有安装或运行vLLM/GPU基准。b=2和T=4仅便于画清原理，不保证是生产后端的合法配置。','',
'C的7-token输入是合成负载，输出[10,1]为指定模拟结果。省略异步调度、投机、完整输入预留、特殊模型与完整抢占策略；这五轮不是每种vLLM配置必然产生的计划。','','## 连续阅读顺序','']
for c in CHAPTERS:readme.append(f'{c["n"]}. [{c["title"]}]({c["file"]}) — [网页定位](图解版.html#fig{c["n"]})')
readme+=['','## 文件与复现','',
'- 00_vLLM_连续全景.svg：十四章合成的连续矢量长图。','- _data/transformer_case.json：上级统一案例的完整精度快照。','- _data/serving_trace.json：五轮输入、进度、块表、槽位、引用和输出。','- _data/paged_attention.json：分页Softmax中间统计。','- _tools/build_vllm.py：标准库构建器；运行 python _tools/build_vllm.py 重建。','- _tools/verify_vllm.py：数值、XML、Chrome文字布局和页面交互检查。','- _qa/validation.json：报告；_qa中的PNG用于核验版面。','','## 五轮调度','',
'|轮次|计划|packed IDs|输出|','|---|---|---|---|','|R1|A3|[11,10,7]|A→8|','|R2|A1,B1,C2|[8,7,10,7]|A→EOS,B→8|','|R3|B1,C3|[8,8,11,10]|B→EOS|','|R4|C2|[7,8]|C→10（指定）|','|R5|C1|[10]|C→EOS（指定）|','',
'B复用前2-token，鱼在下一轮才有KV；EOS不参与前向。R2 positions=[3,2,0,1]，slots=[3,14,6,7]，query_start_loc=[0,1,2,4]。','','## 来源与版本','',
'资料核对2026-10-18；stable文档滚动更新。V1博客为2025-01-27架构说明，原PagedAttention论文为2023设计。源码以v0.30.0固定标签作阅读样本，不声明最新。','']
for name,url in SOURCES.values():readme.append(f'- [{name}]({url})')
readme+=['','源码定位（固定v0.30.0标签下按模块阅读）：','',
'- vllm/v1/engine/core.py：引擎循环。','- vllm/v1/core/sched/scheduler.py：调度与输出进度更新。','- vllm/v1/core/kv_cache_manager.py、block_pool.py：前缀命中、分配和引用。','- vllm/v1/worker/gpu_model_runner.py：输入、Attention元数据与执行；新runner路径可能另有模块。','- vllm/entrypoints/openai/：协议与输出。','',
'## 实现边界','',
'- KV分配块、Attention计算tile、CUDA thread block是三种对象。','- 模拟使用完整前缀hash；真实APC键含父hash、块tokens及额外身份。','- 按普通完整块命中路径说明；混合缓存组和新版本可有其他粒度。','- 不把原论文的部分块COW当成所有V1 APC路径；本例完整块共享、尾部私有。','- V1 append-only块表可暂存内容重复块，不是一发现相同就强制改表。','- KV公式适用普通Dense/GQA，特殊结构和多卡复制需另算。','- 量化可能改变数值；投机保持目标采样分布依赖正确的接受/拒绝算法。','- 未给出未经实测的吞吐、加速倍数或毫秒耗时。','']
(R/'图解版说明.md').write_text('\n'.join(readme)+"\n## 验证结果\n\n本目录数值与版面检查均通过：5轮调度共新算14-token，B复用2-token，双头分页Attention最大绝对误差2.220446049250313e-16。14幅SVG无文字重叠或越界，阅读器的14章导航、五轮切换、自动播放开关与1600px矩阵显示通过检查。完整报告见 [_qa/validation.json](_qa/validation.json)。\n",encoding='utf-8')
print(json.dumps({'chapters':len(CHAPTERS),'atlas_height':totalheight},ensure_ascii=True))

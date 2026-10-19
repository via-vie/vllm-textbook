"""Browser-facing experiment guides; all content works offline."""
from pathlib import Path
import html,json
STYLE="""
dialog.experiment-guide{width:min(900px,calc(100% - 28px));max-height:88vh;overflow:auto;border:1px solid #b9cbdc;border-radius:14px;padding:26px;color:var(--ink);background:white}
dialog.experiment-guide::backdrop{background:rgba(13,31,49,.6)}
.guide-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:16px}
.guide-heading h2{font-size:24px;line-height:1.5;margin:0}.guide-close{flex:0 0 auto}
.experiment-guide h3{font-size:19px;margin:26px 0 10px}.experiment-guide p{margin:14px 0}
.guide-note{background:#edf5ff;padding:14px 18px;border-left:4px solid #245cc2}
.guide-result{background:#edf7f1;border:1px solid #b4d9c7;border-radius:8px;padding:14px 18px}
.experiment-guide .codeblock{font-size:14px}.experiment-guide pre{font-size:13px}
.experiment-guide details{margin:18px 0}.guide-path{font-family:Consolas,monospace;overflow-wrap:anywhere}
@media(max-width:600px){dialog.experiment-guide{padding:18px}.guide-heading h2{font-size:21px}.guide-close{padding:5px 9px}}
@media print{dialog.experiment-guide{display:none!important}}
"""
def command(s):
    return '<div class="codeblock"><button class="copy" type="button">复制命令</button><pre><code>'+html.escape(s)+'</code></pre></div>'
def script_block(root,name):
    code=(root/"labs"/name).read_text(encoding="utf-8")
    return '<details><summary>展开脚本源码（可复制）</summary><div class="codeblock"><button class="copy" type="button">复制脚本源码</button><pre><code>'+html.escape(code)+'</code></pre></div></details>'
def build(root):
    local='cd "'+str(root)+'"\npython labs/run.py trace'
    server='cd "/path/to/vllm详解"\nnvidia-smi\nuv venv --python 3.12 .venv-vllm030\nuv pip install --python .venv-vllm030/bin/python vllm==0.30.0 --torch-backend=auto\nexport MODEL="/absolute/path/to/Qwen3-0.6B"\nVLLM_USE_V2_MODEL_RUNNER=1 .venv-vllm030/bin/python labs/a100_offline.py --model "$MODEL" --out results/a100.json'
    cpu='''<dialog id="cpu-guide" class="experiment-guide" aria-labelledby="cpu-guide-title">
<div class="guide-heading"><h2 id="cpu-guide-title">CPU 实验与网页演示</h2><button class="guide-close" type="button" data-close-guide>关闭</button></div>
<p class="guide-note">现在可以先在网页中逐步查看请求状态；Python 脚本供你在电脑终端重新计算与核对。本页面不会自动执行 Python。</p>
<h3>1. 先看网页中的演示</h3><p>沿同一条请求检查提交、prefill、decode、EOS 和资源清理。点击事件 1–8，比较已知 token、乐观计算进度、在途数量与真实完成状态。</p>
<button id="open-web-trace" type="button">打开请求的逐步演示 →</button>
<h3>2. 想亲手复算时，在本机终端执行</h3><p>需要可用的 Python 3。打开 Windows 终端或 PowerShell，复制下列命令。脚本只用标准库，不需要 GPU 或安装 vLLM。</p>'''+command(local)+'''
<div class="guide-result"><strong>预期看到什么？</strong><p>输出 8 个事件的状态账本；prefill 选择 ID 8“鱼”，decode 选择 ID 1 EOS。computed 会在调度后先前移，ready 则在计算完成后前移。ready 是教学字段。</p></div>
<h3>3. 其他可复算的实验</h3>'''+command('python labs/run.py pack\npython labs/run.py prefix\npython labs/run.py attention\npython labs/run.py check')+'''
<p>pack：核对拼接输入和 KV 槽位；prefix：核对共享与引用；attention：比较直接与分块 Softmax；check：统一校验，正常结果含 status: passed。</p>
<p class="small">边界：数值前向使用本书微型 Transformer；调度与引用部分是教学模拟，不是实际 vLLM/GPU 轨迹。对应正文第 7–16 章。</p>
<p>本地文件：<span class="guide-path">labs/run.py</span></p>'''+script_block(root,"run.py")+'''
</dialog>'''
    gpu='''<dialog id="a100-guide" class="experiment-guide" aria-labelledby="a100-guide-title">
<div class="guide-heading"><h2 id="a100-guide-title">A100 服务器实验指南</h2><button class="guide-close" type="button" data-close-guide>关闭</button></div>
<p class="guide-note">这份实验在你的 Linux/A100 服务器终端运行：用真正的 vLLM 加载模型。浏览器在这里提供步骤、命令与源码。</p>
<h3>1. 准备目录和模型</h3><p>把整个“vllm详解”目录复制到服务器，保持 labs/ 与 _book/ 等相对路径。准备 Qwen3-0.6B 的本地模型目录，并记录模型 revision。下面的 /path/to/… 是需要替换的占位路径。</p>
<h3>2. 在服务器终端执行</h3><p>先安装 uv；环境准备参考<a href="https://docs.vllm.ai/en/v0.30.0/getting_started/installation/gpu/" target="_blank" rel="noreferrer">官方 v0.30.0 GPU 安装说明</a>。已有兼容环境时可直接核对版本并运行脚本。</p>'''+command(server)+'''
<h3>3. 怎样判断实验完成</h3>
<div class="guide-result"><p>启动日志确认 vLLM 0.30.0、实际 GPU 和 Model Runner V2；程序生成结果文件 <span class="guide-path">results/a100.json</span>。文件包含真实模板 IDs、生成 token/文本、结束原因、运行配置和多次整批耗时。</p></div>
<p>这里不要求真实模型输出“鱼”。脚本先预热，再重复测量 5 次；离线整批耗时用于观察延迟与输出吞吐，不能直接作为 TTFT/ITL。详细变量控制和验收见第 21 章。</p>
<button id="open-a100-chapter" type="button">阅读第 21 章：环境、测量与验收 →</button>
<p class="small">本机完成的是脚本语法检查；A100 实际运行结果需要在你的服务器产生。</p>
<p>本地文件：<span class="guide-path">labs/a100_offline.py</span></p>'''+script_block(root,"a100_offline.py")+'''
</dialog>'''
    return cpu+gpu
JS=r"""
document.getElementById('open-cpu-guide').onclick=()=>document.getElementById('cpu-guide').showModal();
document.getElementById('open-a100-guide').onclick=()=>document.getElementById('a100-guide').showModal();
document.querySelectorAll('[data-close-guide]').forEach(b=>b.onclick=()=>b.closest('dialog').close());
document.getElementById('open-web-trace').onclick=()=>{
 document.documentElement.style.scrollBehavior='auto';
 document.getElementById('cpu-guide').close();
 location.hash='#ch08';show();
 document.getElementById('traceplayer').scrollIntoView({behavior:'instant',block:'start'});
 // Hash navigation also resets scroll; scroll again after that event has run.
 setTimeout(()=>document.getElementById('traceplayer').scrollIntoView({behavior:'instant',block:'start'}),30);
 document.querySelector('#tracebuttons button')?.focus({preventScroll:true});
};
document.getElementById('open-a100-chapter').onclick=()=>{
 document.getElementById('a100-guide').close();location.hash='#ch21';show();
};
"""

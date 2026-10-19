"""Build the offline vLLM textbook and exact-source reader. Standard library only."""
from pathlib import Path
import html,json,re,hashlib,sys
from urllib.parse import quote
R=Path(__file__).resolve().parents[1];B=R/"_book"
sys.path.insert(0,str(R/"labs"))
import run as labs
from book_diagrams import generate
import book_experiments
import book_readability
COMMIT="ced6857afa0ea7b2e3f0846a62e1394e90f15607"
INDEX=json.loads((R/"_research/source-index.json").read_text(encoding="utf-8"))
ALIASES=json.loads((B/"aliases.json").read_text(encoding="utf-8"))
SNAP=R/"_source/snapshot-ced6857"
EXCERPTS=json.loads((B/"excerpts.json").read_text(encoding="utf-8"))
REFS=[]
def esc(s):return html.escape(str(s),quote=True)
def resolve(a,s):
    path=ALIASES.get(a,a)
    assert path in INDEX["files"],path
    assert s in INDEX["files"][path]["symbols"],(path,s)
    f=INDEX["files"][path]["symbols"][s]
    return path,f["start"],f["end"]
def source_link(a,s):
    path,lo,hi=resolve(a,s)
    local="_book/source/"+quote(path)+".html#L"+str(lo)
    remote=f"https://github.com/vllm-project/vllm/blob/{COMMIT}/{quote(path)}#L{lo}-L{hi}"
    return path,lo,hi,local,remote
def inline(s):
    s=esc(s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^ )]+)\)',r'<a href="\2" target="_blank" rel="noreferrer">\1</a>',s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'\x60([^\x60]+)\x60',r'<code>\1</code>',s)
    return s
def walk(line,full=False):
    alias,symbol,note=line.split("|",2)
    path,lo,hi,local,remote=source_link(alias,symbol)
    REFS.append(dict(path=path,symbol=symbol,start=lo,end=hi))
    lines=(SNAP/path).read_text(encoding="utf-8").splitlines()
    selected=EXCERPTS.get(symbol) if not full else None
    if selected:
        chunks=[]
        for start,stop in selected:
            assert lo<=start<=stop<=hi,(symbol,start,stop,lo,hi)
            chunks.append(f"--- L{start}–L{stop}（非连续选段；完整上下文见源码）---\n"+"\n".join(f"{i:5}  {lines[i-1]}" for i in range(start,stop+1)))
        code="\n\n".join(chunks)
        cut="<p class='small'>为避免只看到长签名，本卡展示关键处理选段；省略了其他分支。请打开完整源码核对控制流与条件。</p>"
    else:
        end=hi if full else min(hi,lo+25)
        code="\n".join(f"{i:5}  {lines[i-1]}" for i in range(lo,end+1))
        cut=f"<p class='small'>这里只展示 L{lo}–L{end}；完整函数至 L{hi}，请打开本地源码阅读全部分支。</p>" if end<hi else "<p class='small'>本卡片展示完整符号范围。</p>"
    return f'<details class="sourcecard"><summary><span>把这一步对应到源码</span><code>{esc(symbol)}</code></summary><div class="sourcecontents"><p>{inline(note)}</p><p class="small">{esc(path)} · L{lo}–L{hi} · 固定 commit</p><p><a href="{local}" target="_blank">打开本地源码 ↗</a>　<a href="{remote}" target="_blank" rel="noreferrer">官方永久链接 ↗</a></p><details><summary>在这里展开真实代码{"" if full else "选段"}</summary>{cut}<pre><code>{esc(code)}</code></pre></details></div></details>'

def render(lines):
    out=[];paragraph=[];i=0
    def flush():
        if paragraph:out.append("<p>"+inline(" ".join(paragraph))+"</p>");paragraph.clear()
    while i<len(lines):
        line=lines[i].strip()
        if not line:flush();i+=1;continue
        if line.startswith("~~~"):
            flush();code=[];i+=1
            while i<len(lines) and not lines[i].strip().startswith("~~~"):
                code.append(lines[i]);i+=1
            out.append('<div class="codeblock"><button class="copy" type="button">复制命令</button><pre><code>'+esc("\n".join(code))+'</code></pre></div>')
        elif line.startswith("## "):
            flush();out.append("<h3>"+esc(line[3:])+"</h3>")
        elif line.startswith("@note "):
            flush();out.append(book_readability.aside(line[6:]))
        elif line.startswith("@pause "):
            flush();out.append(book_readability.aside(line[7:],pause=True))
        elif line.startswith("@walk "):
            flush();out.append(walk(line[6:]))
        elif line.startswith("@fullwalk "):
            flush();out.append(walk(line[10:],True))
        elif line.startswith("@figure "):
            flush();key=line[8:];assert (B/"figures"/(key+".svg")).exists(),key
            out.append(f'<figure><a href="_book/figures/{key}.svg" target="_blank"><img src="_book/figures/{key}.svg" alt="{esc(book_readability.CAPTIONS.get(key,key))}" loading="lazy"></a><figcaption>{esc(book_readability.CAPTIONS.get(key,"点击图可以打开独立 SVG，放大查看。"))}</figcaption></figure>')
            if key=="trace":out.append('<div id="traceplayer" class="lab"><h3>逐事件检查账本</h3><p>控制流教学模拟，ready 为额外教学字段；不是实际 vLLM GPU trace。</p><div id="tracebuttons"></div><h4 id="traceevent"></h4><div id="tracevalues"></div><pre id="tracedetail"></pre></div>')
        elif line.startswith("@exercise "):
            flush();question=line[10:];i+=1
            assert lines[i].startswith("@answer "),lines[i]
            answer=lines[i][8:]
            out.append('<details class="exercise"><summary>理解检查 · '+inline(question)+'</summary><p>'+inline(answer)+'</p></details>')
        elif line.startswith("@next "):
            flush();out.append('<p class="bridge">'+inline(line[6:])+'</p>')
        elif line.startswith("|"):
            flush();rows=[]
            while i<len(lines) and lines[i].strip().startswith("|"):
                rows.append([x.strip() for x in lines[i].strip().strip("|").split("|")]);i+=1
            out.append('<div class="tablewrap"><table><thead><tr>'+''.join("<th>"+inline(c)+"</th>" for c in rows[0])+"</tr></thead><tbody>")
            for row in rows[1:]:
                if all(re.fullmatch(r"[-: ]+",c) for c in row):continue
                out.append("<tr>"+''.join("<td>"+inline(c)+"</td>" for c in row)+"</tr>")
            out.append("</tbody></table></div>");i-=1
        else:paragraph.append(line)
        i+=1
    flush();return "\n".join(out)
CSS="""
:root{--ink:#1c2d3c;--muted:#5a7080;--blue:#245cc2;--bg:#f2f5f8;--paper:#fff;--line:#dce4ec;--read:18px}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;overflow-wrap:anywhere;background:var(--bg);color:var(--ink);font:var(--read)/1.9 "Microsoft YaHei","Noto Sans SC",system-ui,sans-serif}
a{color:var(--blue);text-underline-offset:3px}button,input{font:inherit}button{cursor:pointer;border:1px solid #bdcad8;background:white;color:var(--ink);border-radius:7px;padding:6px 12px}button:hover{background:#edf3ff}button:focus-visible,a:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid #d48a18;outline-offset:3px}button:disabled{opacity:.45;cursor:default}
aside{position:fixed;left:0;top:0;bottom:0;width:286px;padding:23px 19px;background:#15293d;color:#dae6f2;overflow:auto;font-size:14px;line-height:1.7}aside a{color:#cbdcf2;display:block;padding:7px 10px;text-decoration:none;border-radius:5px}aside a.active{background:#2b4c70;color:white}aside a.done:after{content:" ✓";color:#86d9be}aside .part{color:#97b2cd;font-size:12px;margin:18px 7px 5px}aside input{width:100%;padding:8px;border:1px solid #53708b;border-radius:6px;background:#213b55;color:#fff}aside h1{font-size:21px;line-height:1.5;margin:0 0 10px}aside .small{color:#9ab2c8}#searchcount{font-size:12px;min-height:26px}#navtoggle{display:none}
main{margin-left:286px;padding:34px clamp(24px,4vw,68px);max-width:1470px}header,.chapter{max-width:1000px;margin:auto}.masthead{border-bottom:1px solid var(--line);padding-bottom:25px;margin-bottom:25px}.masthead h2{font-size:32px;line-height:1.45;margin:8px 0}.eyebrow{font-size:12px;letter-spacing:1.5px;font-weight:700;color:var(--muted);text-transform:uppercase}.badges{display:flex;gap:8px;flex-wrap:wrap}.badges span{padding:3px 9px;border-radius:4px;background:#e4edf9;font-size:12px}.toolbar{display:flex;gap:9px;flex-wrap:wrap;margin-top:14px;font-size:14px}.chapter{display:none;background:var(--paper);border:1px solid var(--line);padding:clamp(23px,3.5vw,54px);border-radius:12px}.chapter.active{display:block}.chapter h2{font-size:29px;line-height:1.5;margin:0 0 22px}.chapter h3{font-size:22px;line-height:1.6;border-top:1px solid var(--line);padding-top:27px;margin-top:34px}.chapter h4{font-size:17px;margin:8px 0;overflow-wrap:anywhere}.chapter p{margin:16px 0}.handoff{padding:14px 20px;background:#f5f8fb;border:1px solid #dce4ec;font-size:15px}.handoff p{margin:5px 0}.lead{background:#edf5ff;padding:18px 20px;border-left:4px solid var(--blue)}.small,figcaption{font-size:13px;color:var(--muted)}.sourcecard{border:1px solid #cedded;border-left:4px solid #7194c6;padding:16px 20px;margin:25px 0;border-radius:7px;background:#f8fbff}.sourcecard .eyebrow{margin:0}.sourcecard p{margin:8px 0}.sourcecard pre{font-size:12px}pre{white-space:pre;overflow:auto;max-width:100%;background:#13283a;color:#e7f2ff;padding:19px;border-radius:7px;font:13px/1.75 Consolas,monospace;tab-size:4}code{font-family:Consolas,monospace;overflow-wrap:anywhere}.codeblock{position:relative}.codeblock pre{padding-top:48px}.copy{position:absolute;right:10px;top:8px;font-size:12px;background:#26425b;color:white;border-color:#5a7389}.tablewrap{overflow:auto;margin:24px 0}table{border-collapse:collapse;width:100%;font-size:15px;line-height:1.7}th,td{padding:12px 14px;border:1px solid var(--line);text-align:left;vertical-align:top}th{background:#eaf1f8}td{min-width:140px}figure{margin:26px 0}figure img{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:9px}figcaption{margin-top:8px}.exercise{padding:15px 19px;background:#fff8e9;border:1px solid #ead8b4;border-radius:7px;margin:15px 0}summary{cursor:pointer;font-weight:600;line-height:1.8}.exercise p{padding-top:10px;border-top:1px solid #e4d5b5}.bridge{background:#eaf6f1;padding:18px 22px;border-left:4px solid #3c9a7f}.chapterfoot{display:flex;gap:8px;justify-content:space-between;flex-wrap:wrap;border-top:1px solid var(--line);margin-top:34px;padding-top:20px;font-size:14px}.lab{background:#eef5ff;border-radius:10px;padding:20px}.lab h3{border:0;margin:0;padding:0}#tracebuttons{display:flex;gap:6px;flex-wrap:wrap}#tracebuttons button[aria-pressed=true]{background:#245cc2;color:#fff}#tracevalues{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}#tracevalues span{display:block;background:#fff;padding:10px;font-size:13px;border-radius:6px}#tracevalues b{display:block;font-size:25px}.footer{max-width:1000px;margin:20px auto;font-size:12px;color:var(--muted)}.printonly{display:none}
@media(max-width:980px){aside{position:static;width:auto;max-height:none}aside h1{font-size:20px}#navtoggle{display:block;position:absolute;right:20px;top:24px}aside nav,aside label,aside input,#searchcount{display:none}aside.expanded label{display:block}aside.expanded nav,aside.expanded input,aside.expanded #searchcount{display:block}main{margin:0;padding:22px 12px}.masthead h2{font-size:26px}.chapter h2{font-size:25px}#tracevalues{grid-template-columns:repeat(2,1fr)}}
@media print{aside,.toolbar,.chapterfoot,.copy,#tracebuttons{display:none!important}main{margin:0;max-width:none;padding:0}body{background:white;font-size:11pt}.chapter{display:block!important;border:0;padding:0;break-before:page;max-width:none}header{max-width:none}.chapter h3{break-after:avoid}.sourcecard,figure,.exercise{break-inside:avoid}details:not([open])>p{display:block}pre{white-space:pre-wrap;background:#eee;color:#111;font-size:8pt}a{color:#111}figure img{max-height:155mm;object-fit:contain}.printonly{display:block}}
"""
JS=r"""
const chapters=[...document.querySelectorAll('.chapter')],links=[...document.querySelectorAll('nav a')];
let done=new Set;try{done=new Set(JSON.parse(localStorage.getItem('vllm-book-done')||'[]'))}catch(e){}
function mark(){links.forEach(a=>a.classList.toggle('done',done.has(a.hash.slice(1))));document.getElementById('progress').textContent=done.size+' / '+chapters.length+' 章已复查'}
function show(){
 let id=location.hash.slice(1);if(!chapters.some(c=>c.id===id))id='ch01';
 chapters.forEach(c=>c.classList.toggle('active',c.id===id));
 links.forEach(a=>a.classList.toggle('active',a.hash==='#'+id));
 document.title=document.getElementById(id).dataset.title+' · vLLM 源码教材';
 mark();
}
addEventListener('hashchange',()=>{show();window.scrollTo({top:0,behavior:'instant'})});
document.getElementById('search').addEventListener('input',e=>{
 const q=e.target.value.trim().toLowerCase();let n=0;
 links.forEach(a=>{const c=document.querySelector(a.hash);const yes=!q||c.textContent.toLowerCase().includes(q);a.hidden=!yes;if(yes)n++});
 document.getElementById('searchcount').textContent=q?n+' 章包含该词；点击章节阅读':'搜索正文、术语或函数名';
});
document.querySelectorAll('.complete').forEach(b=>b.onclick=()=>{
 const id=b.closest('.chapter').id;done.has(id)?done.delete(id):done.add(id);
 try{localStorage.setItem('vllm-book-done',JSON.stringify([...done]))}catch(e){}mark()
});
document.querySelectorAll('.copy').forEach(b=>b.onclick=async()=>{
 try{await navigator.clipboard.writeText(b.nextElementSibling.textContent);b.textContent='已复制'}catch(e){b.textContent='请选中命令复制'}
});
document.getElementById('navtoggle').onclick=()=>document.querySelector('aside').classList.toggle('expanded');
document.getElementById('print').onclick=()=>print();
let font=18;
document.getElementById('fontup').onclick=()=>{font=Math.min(24,font+1);document.documentElement.style.setProperty('--read',font+'px')};
document.getElementById('fontdown').onclick=()=>{font=Math.max(15,font-1);document.documentElement.style.setProperty('--read',font+'px')};
const trace=JSON.parse(document.getElementById('tracedata').textContent);
function phase(i){
 const r=trace.rows[i];document.getElementById('traceevent').textContent=r.event;
 document.getElementById('tracevalues').innerHTML=[
 ['known',r.known_tokens],['computed（乐观）',r.num_computed_tokens],['in_flight',r.num_in_flight_tokens],
 ['ready（教学）',r.ready_tokens_TEACHING_ONLY],['KV 活动引用',r.active_KV_references],['Worker 行',r.worker_row?'存在':'无']
 ].map(([k,v])=>'<span>'+k+'<b>'+v+'</b></span>').join('');
 document.getElementById('tracedetail').textContent='status='+r.status+'\naccepted_output_ids='+JSON.stringify(r.accepted_output_ids)+'\n注意：结束后的计数为历史快照，不表示仍然占有 KV。';
 [...document.getElementById('tracebuttons').children].forEach((b,j)=>b.setAttribute('aria-pressed',j===i?'true':'false'))
}
trace.rows.forEach((r,i)=>{const b=document.createElement('button');b.textContent=i+1;b.type='button';b.setAttribute('aria-label',r.event);b.onclick=()=>phase(i);document.getElementById('tracebuttons').append(b)});
phase(0);show();
window.bookReady=true;
"""
def main():
    count=generate()
    raw=(B/"manuscript.txt").read_text(encoding="utf-8")
    chapters=[]
    for chunk in re.split(r"(?m)^@chapter ",raw)[1:]:
        first,*lines=chunk.splitlines();num,part,title=first.split("|",2)
        assert lines[0].startswith("@lead ")
        lead=lines.pop(0)[6:];body=render(lines)
        chapters.append(dict(n=int(num),id="ch"+num,part=part,title=title,lead=lead,html=body))
    reading_notes=json.loads((B/"reading_notes.json").read_text(encoding="utf-8"))
    assert len(reading_notes)==len(chapters)
    handoffs=json.loads((B/"handoffs.json").read_text(encoding="utf-8"))
    nav=[];last=None;content=[]
    for i,c in enumerate(chapters):
        handoff="<div class='handoff'><p class='eyebrow'>本章交接</p><p><strong>带着什么来：</strong>"+esc(handoffs[i][0])+"<br><strong>本章怎样处理：</strong>"+esc(handoffs[i][1])+"<br><strong>交给下一步：</strong>"+esc(handoffs[i][2])+"</p></div>"
        if c["part"]!=last:nav.append('<div class="part">'+esc(c["part"])+'</div>');last=c["part"]
        nav.append(f'<a href="#{c["id"]}">{c["n"]:02} · {esc(c["title"])}</a>')
        prev=f'<a href="#{chapters[i-1]["id"]}">← 上一章</a>' if i else '<span>从这里开始</span>'
        nxt=f'<a href="#{chapters[i+1]["id"]}">下一章 →</a>' if i+1<len(chapters) else '<a href="#ch01">回到第一章</a>'
        explained=c["html"].replace('<details class="exercise">',book_readability.recap(reading_notes[i])+'<details class="exercise">',1)
        opening=book_readability.opening(reading_notes[i])
        review=book_readability.review(c["lead"],handoff)
        content.append(f'<section class="chapter" id="{c["id"]}" data-title="{esc(c["title"])}"><p class="eyebrow">{esc(c["part"])} · {c["n"]:02}</p><h2>{esc(c["title"])}</h2>{opening}{explained}{review}<div class="chapterfoot">{prev}<button class="complete" type="button">标记 / 取消已复查</button>{nxt}</div></section>')
    trace=json.dumps(labs.trace(),ensure_ascii=False).replace("<","\\u003c")
    guide_html=book_experiments.build(R)
    page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>vLLM 源码：从请求到 GPU</title><style>{CSS}{book_experiments.STYLE}{book_readability.STYLE}</style></head><body>
<aside><h1>vLLM 源码教材</h1><button id="navtoggle" type="button">目录 / 搜索</button><p class="small">从请求到 GPU，再回到用户<br>固定源码 v0.30.0 / ced6857</p><label for="search">搜索全书</label><input id="search" type="search" placeholder="如 num_computed_tokens"><div id="searchcount">搜索正文、术语或函数名</div><p id="progress" class="small"></p><nav aria-label="章节目录">{''.join(nav)}</nav></aside>
<main><header class="masthead"><p class="eyebrow">源码 · 状态 · 张量 · 实验</p><h2>vLLM 源码：从一条请求开始</h2><p>先看例子，推清过程，再对照源码。22 章正文与复习附录。</p><div class="badges"><span>无需先装 GPU 环境</span><span>精确源码行号</span><span>离线阅读</span><span>单 A100 实验</span></div><div class="toolbar"><a href="source.html">本地源码索引</a><button id="open-cpu-guide" type="button" aria-haspopup="dialog" aria-controls="cpu-guide">CPU 实验与网页演示</button><button id="open-a100-guide" type="button" aria-haspopup="dialog" aria-controls="a100-guide">A100 服务器实验指南</button><a href="图解版.html">旧版图解</a><button id="fontdown" type="button">字号 −</button><button id="fontup" type="button">字号 +</button><button id="print" type="button">打印全书 / PDF</button></div></header>
{''.join(content)}<footer class="footer">源码技术依据：vLLM 官方固定提交；教学组织参考白木原教程。CPU 数值/控制实验与真实 GPU 实验分开标识。完整范围及引用见附录。<br>原始 vLLM 源码按 Apache-2.0 保留；本书 SVG 与教学实验为本地新增。</footer></main>
{guide_html}
<script id="tracedata" type="application/json">{trace}</script><script>{JS}
{book_experiments.JS}</script></body></html>'''
    (R/"index.html").write_text(page,encoding="utf-8")
    # One local page per verified source. No file:// fetch or external JS needed.
    source_dir=B/"source";source_dir.mkdir(exist_ok=True)
    source_nav=[]
    for path,info in INDEX["files"].items():
        text=(SNAP/path).read_text(encoding="utf-8")
        assert hashlib.sha256((SNAP/path).read_bytes()).hexdigest()==info["sha256"],path
        target=source_dir/(path+".html");target.parent.mkdir(parents=True,exist_ok=True)
        back="../"*(len(Path(path).parts)+1)
        choices=''.join(f'<option value="L{s["start"]}">{esc(name)} · L{s["start"]}–L{s["end"]}</option>' for name,s in info["symbols"].items())
        lines=''.join(f'<div class="line" id="L{i}"><a class="ln" href="#L{i}">{i}</a><code>{esc(line) or " "}</code></div>' for i,line in enumerate(text.splitlines(),1))
        source_css='body{margin:0;font:14px/1.7 Consolas,monospace;color:#203344;background:#f7f9fc}header{padding:20px;border-bottom:1px solid #ccd6e0;background:white;overflow-wrap:anywhere}a{color:#245cc2}h1{font-size:18px}select{max-width:95%;padding:8px}main{overflow:auto;padding:14px 0}.line{display:flex;min-width:max-content;scroll-margin-top:12px}.line:target{background:#fff0a6}.ln{display:inline-block;flex:0 0 65px;text-align:right;padding-right:15px;color:#6c8092;text-decoration:none;user-select:none}code{white-space:pre;font:inherit;padding-right:24px}.line:hover{background:#eaf0f8}'
        sourcepage=f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{esc(path)} · 固定源码</title><style>{source_css}</style><header><a href="{back}index.html">← 教材</a> · <a href="{back}source.html">源码索引</a> · <a href="https://github.com/vllm-project/vllm/blob/{COMMIT}/{quote(path)}" target="_blank">官方固定提交</a><h1>{esc(path)}</h1><p>v0.30.0 · {COMMIT} · {info["lines"]} 行 · 原文件未修改 · Apache-2.0</p><label for="symbols">符号跳转：</label><select id="symbols"><option value="">选择类或函数</option>{choices}</select></header><main>{lines}</main><script>document.getElementById("symbols").onchange=e=>{{if(e.target.value)location.hash=e.target.value}}</script></html>'
        target.write_text(sourcepage,encoding="utf-8")
        source_nav.append(f'<li><a href="_book/source/{quote(path)}.html">{esc(path)}</a> <small>({info["lines"]} 行)</small></li>')
    srcindex=f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>vLLM 本地源码索引</title><style>body{{max-width:1100px;margin:30px auto;padding:15px;font:16px/1.8 system-ui}}li{{overflow-wrap:anywhere}}a{{color:#245cc2}}input{{padding:10px;min-width:60%}}small{{color:#678}}</style><a href="index.html">← 返回教材</a><h1>固定源码阅读索引</h1><p>v0.30.0 · {COMMIT}。选取 {len(INDEX["files"])} 个文件，不是完整可安装仓库。<a href="_book/source/LICENSE.html">原始 LICENSE</a>。每个文件保留原始行号与符号跳转。</p><input id="q" aria-label="搜索源码路径" placeholder="输入 scheduler、test、design 等"><ul>{"".join(source_nav)}</ul><script>document.getElementById("q").oninput=e=>{{document.querySelectorAll("li").forEach(li=>li.hidden=!li.textContent.toLowerCase().includes(e.target.value.toLowerCase()))}}</script></html>'
    (R/"source.html").write_text(srcindex,encoding="utf-8")
    for name in ("trace","pack","prefix","budget","attention","metrics"):
        (B/(name+".json")).write_text(json.dumps(getattr(labs,name)(),ensure_ascii=False,indent=2),encoding="utf-8")
    stats=dict(chapters=len(chapters),figures=count,source_files=len(INDEX["files"]),
        source_references=len(REFS),unique_source_symbols=len({(x["path"],x["symbol"]) for x in REFS}),
        exercises=raw.count("@exercise "),manuscript_characters=len(raw),reading_pauses=raw.count("@pause "),
        commit=COMMIT,lab_check=labs.check())
    (B/"chapters.json").write_text(json.dumps(chapters,ensure_ascii=False,indent=2),encoding="utf-8")
    (B/"references.json").write_text(json.dumps(REFS,ensure_ascii=False,indent=2),encoding="utf-8")
    (B/"build.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(stats,ensure_ascii=True))
if __name__=="__main__":main()

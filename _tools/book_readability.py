"""Reading aids and quiet book typography. Original pedagogical text."""
import html
def escape(s):return html.escape(s,quote=True)
def opening(note):
    q='<p class="chapter-question"><span>这一章，从一个问题开始</span>'+escape(note["question"])+'</p>'
    if note.get("scene"):q+='<p class="chapter-scene">'+escape(note["scene"])+'</p>'
    return q
def recap(note):
    return '<div class="chapter-recap"><strong>先把这一点带走</strong><p>'+escape(note["remember"])+'</p></div>'
def review(lead,handoff):
    return '<details class="chapter-review"><summary>回看本章的目标与输入输出</summary><p>'+escape(lead)+'</p>'+handoff+'</details>'
def aside(line,pause=False):
    title,body=line.split("|",1)
    if pause:return '<details class="reading-pause"><summary><span>停一下，自己想一想</span>'+escape(title)+'</summary><p>'+escape(body)+'</p></details>'
    return '<div class="reading-note" role="note"><strong>'+escape(title)+'</strong><p>'+escape(body)+'</p></div>'
CAPTIONS={
"architecture":"先认三列：前端进程、核心进程与 GPU 设备。再沿 ①–⑧ 看请求怎样进入、计算并返回；不必一次记住所有类名。",
"startup":"按“配置与实现 → 设备与容量 → 执行就绪”读三行。每一行都在为下一行提供条件；启动完成不等于某条请求的 KV 已经算出。",
"contracts":"同一条请求会换用不同的数据表示。先顺着输入、计划和输出读，再检查每份记录由谁持有。",
"trace":"先看 prefill 与 decode 两行。computed 提前变化，ready 随实际完成变化；ready 只用于教学说明。",
"scheduling":"先手算 8 个预算如何分给 A/B/C，再看容量不足的处理。图中计划采用隔离的教学条件。",
"paging":"从 position=19 开始，先算逻辑块和块内偏移，再查物理块；最后才得到槽位 35。",
"prefix":"分两次读：第一行看“内容是不是同一个前缀”，后两行看“还有谁持有它、什么时候可以换内容”。",
"packing":"把每个数字都回答成一句话：这是哪条请求、哪一行、哪个位置，还是哪个槽？不要把几种索引混在一起。",
"attention":"第一行连接模型、KV 写入与读取；第二行对应刚才的 m/l/u 推导；最后比较 prefill 和 decode 的侧重点。",
"lifecycle":"先沿正常输出走一遍，再看取消怎么逆向送回核心。最后检查不同状态和资源怎样安全结束。",
"execution":"先分清融合、编译与图重放分别省什么，再看图是否匹配本轮输入。收益需要通过下方的对照实验确认。",
"parallel":"先问每种并行“切什么”，再看不同 rank 之间传什么。单卡上可以推导这些关系，多卡性能仍需要实际测量。"
}
STYLE="""
:root{--ink:#29342f;--muted:#647169;--blue:#287566;--bg:#f5f3ed;--paper:#fffefb;--line:#e1e2d9}
body{line-height:1.95}
aside{background:#253b36}aside a{color:#d4e1da}aside a.active{background:#3c5d51}aside .part{color:#a7c1b2}aside .small{color:#b5c9bd}aside input{background:#304b41;border-color:#698678}
main{max-width:1390px;padding-top:24px}header,.chapter{max-width:920px}
.masthead{margin-bottom:22px;padding-bottom:17px}.masthead h2{font-size:24px;margin:5px 0;letter-spacing:.2px}.masthead>p:not(.eyebrow){font-size:14px;color:var(--muted);margin:7px 0}.masthead .eyebrow{font-size:11px;margin:0}.badges{display:none}.toolbar{margin-top:13px;align-items:center;font-size:13px}
.chapter{border:1px solid #e3e3d9;border-radius:3px;padding:42px clamp(25px,3.6vw,54px);box-shadow:0 2px 9px #37423805}
.chapter h2{font-size:30px;line-height:1.6;letter-spacing:.3px;margin:5px 0 23px}
.chapter h3{font-size:22px;border:0;padding-top:0;margin:39px 0 15px;line-height:1.65}
.chapter p{margin:17px 0}.chapter>.eyebrow{font-size:12px;color:#69776b;margin:0}
.chapter-question{border-top:1px solid #c7d3c4;border-bottom:1px solid #c7d3c4;padding:19px 0;font-size:22px;line-height:1.75;font-weight:600;background:none}
.chapter-question>span{display:block;font-size:12px;font-weight:400;color:var(--muted);margin-bottom:7px;letter-spacing:1px}
.chapter-scene{color:#4b5c52}
.reading-note{border-left:3px solid #ba9d60;background:#f7f3e7;padding:14px 20px;margin:25px 0;font-size:16px;line-height:1.9}.reading-note p{margin:5px 0 0}.reading-note strong{font-size:15px}
.reading-pause{border-top:1px dashed #c1cfc3;border-bottom:1px dashed #c1cfc3;padding:17px 0;margin:27px 0;background:none}.reading-pause summary{font-weight:500}.reading-pause summary span{display:block;font-size:12px;color:#43765e;font-weight:700;letter-spacing:.6px;margin-bottom:5px}.reading-pause p{color:#4b6155;padding:10px 18px;background:#f0f5ed;border-radius:2px;font-size:16px}
details.sourcecard{background:#f2f4ee;border:1px solid #dbe1d5;border-left:2px solid #aabfa9;border-radius:2px;padding:12px 16px;margin:20px 0;font-size:15px}
.sourcecard>summary{font-size:14px;font-weight:400;line-height:1.9;overflow-wrap:anywhere}
.sourcecard>summary>span{color:#5f7564;font-size:12px;margin-right:12px}.sourcecard>summary code{font-size:13px}
.sourcecontents{padding-top:12px}.sourcecontents p{font-size:15px}
.chapter-recap{margin:30px 0 20px;padding:18px 21px;background:#edf3e9;border-radius:2px}.chapter-recap>strong{font-size:13px;letter-spacing:.7px;color:#527158}.chapter-recap p{margin:6px 0 0;font-size:17px}
.exercise{background:#faf7ee;border:1px solid #e6e0cd;border-radius:2px;padding:13px 17px}.exercise summary{font-size:15px;font-weight:500}.exercise p{font-size:16px}
.chapter-review{font-size:14px;color:#607263;margin:22px 0 0}.chapter-review summary{font-weight:400}.chapter-review .handoff{background:none;border:0;padding:0}
.bridge{font-size:16px;background:none;border:0;border-top:1px solid #d8e0d4;padding:21px 0 0;margin-top:30px!important;color:#426d55}
figure{margin:28px 0}figure img{border-color:#dfe4db;border-radius:3px}figcaption{font-size:14px;line-height:1.9;margin-top:12px;padding:0 4px;color:#69776b}
th{background:#eff2e9}th,td{padding:12px 14px}table{font-size:15px;line-height:1.9}
pre{font-size:14px;line-height:1.9;background:#233a35}.codeblock pre{padding-top:48px}.copy{background:#37584c;border-color:#6f8c7c}
.lab{background:#edf4eb;border-radius:3px}.lab h3{margin:0}.chapterfoot{margin-top:29px}
@media(max-width:980px){main{padding:20px 12px}.masthead h2{font-size:22px}.chapter{padding:27px 23px}.chapter h2{font-size:26px}.chapter h3{font-size:21px}.chapter-question{font-size:21px}aside h1{font-size:20px}}
@media print{.chapter{box-shadow:none;border:0;padding:0}.chapter-question{font-size:15pt}.chapter h2{font-size:22pt}.chapter h3{font-size:16pt}.chapter-review[open]{display:block}details.sourcecard{break-inside:auto}.chapter-recap,.reading-note,.reading-pause{break-inside:avoid}details.sourcecard:not([open])>div{display:block}}
"""

# vllm-textbook

面向推理优化学习者的 vLLM 源码教材，以一条请求串联完整架构，涵盖调度、KV Cache、模型执行与性能优化，配套 SVG 图解、源码导读及 CPU/A100 实验。

## vLLM 源码教材：从一条请求理解完整架构

入口：[index.html](index.html)。22 章正文与 1 章附录，约 5.6 万字符的源稿，12 幅原创 SVG，69 道带答案的理解检查，77 个源码导读卡片。无需联网或启动服务器，支持搜索、章节导航、复查标记、字号、打印全书与请求事件播放器。

## 这次可读性调整

全书 23 章改为从具体问题进入，再沿同一请求推进；每章有情境导入与简短回顾。前四章重新编写，启动内存、矩阵形状、在线 Softmax 和 TP 增加分步推导。正文新增 22 个可展开答案的思考停顿，源码入口默认收起，图注说明阅读顺序。完整参数、行号和原始代码继续保留。

## 如何开始

面向没读过 vLLM 源码、有 Python/基本 Transformer 概念的读者。先用单卡、同步、eager、普通文本生成建立连续主线，再展开异步调度、图执行、多卡、量化、投机、多模态及 P/D 分离。开始阅读不需要先安装 GPU 环境。

1. 第一天：第 1–3 章，画进程/对象/GPU 边界，打印入口源码。
2. 第二天：第 4–6 章，画配置、文本渲染、请求提交与回程。
3. 第三天：第 7–8 章，运行 trace，对照 known/computed/in-flight/ready。
4. 第四天：第 9–11 章，运行 budget、prefix，手算地址与引用。
5. 第五天：第 12 章，运行 pack，解释五种索引。
6. 第六天：第 13–16 章，运行 attention，闭合模型、采样、解码和回收。
7. 第七天：完成第 22 章架构图与请求账本，找源码佐证。

之后用第 17–21 章深入执行路径与 A100 实验。前期目标是掌握架构和证据，后续再选研究路线与论文问题。

## 版本与证据

- 官方标签：v0.30.0；固定提交：ced6857afa0ea7b2e3f0846a62e1394e90f15607。
- [官方固定仓库](https://github.com/vllm-project/vllm/tree/ced6857afa0ea7b2e3f0846a62e1394e90f15607)。
- _source/snapshot-ced6857/：123 个选择性阅读文件，保留原始 LICENSE，不是完整可安装仓库。
- _research/source-manifest.json：文件 Git blob 身份、SHA256 与行数。
- _research/source-index.json：AST 提取的真实类/函数范围。
- [source.html](source.html)：可离线查行号、跳符号的源码阅读器；各章同时提供官方永久链接。
- _research/：参考教程、官方版本元数据及获取记录。

源码按核心闭环阅读：入口、配置、输入输出、消息、EngineCore、调度、KV、MRV2、Qwen3、FlashAttention、采样与生命周期。扩展章区分直接导读与后续入口，不声称逐行讲授全部 123 个文件或全部硬件后端。

教学组织参考[白木原教程](https://tutorial.baimuyuan.online/)，阅读其 MiniMind/Harness 目录与代表章节，借鉴固定源码、先概念再代码、实验与习题的递进方法。vLLM 技术结论以官方固定源码和设计文档为准。论文依据：[PagedAttention](https://arxiv.org/abs/2309.06180)、[FlashAttention](https://arxiv.org/abs/2205.14135)。

## 浏览器中的实验入口

页顶“CPU 实验与网页演示”和“A100 服务器实验指南”会打开页面内指南，提供命令、预期结果与可复制源码。CPU 入口可直接跳到网页的逐事件演示；Python 实际计算在本机/服务器终端运行。

## CPU 实验

在本目录执行，Python 标准库即可，无需导入 vLLM：

~~~
python labs/run.py source core EngineCore.step
python labs/run.py trace
python labs/run.py pack
python labs/run.py prefix
python labs/run.py budget --budget 8
python labs/run.py attention
python labs/run.py metrics
python labs/run.py check
~~~

- trace：固定微型 Transformer 的真实 CPU 前向 + 简化同步控制流账本，生成鱼 8、EOS 1。**不是实际 vLLM Scheduler/GPU trace。**
- pack：手算变长查询、持久行映射、位置、长度、分页槽位。
- prefix：前缀身份、salt、引用归还与身份淘汰。
- budget：隔离条件下的简化 token 预算，不代替生产 Scheduler。
- attention：直接 softmax 与分块在线归并的数值对照。
- metrics：合成时间线解释 TTFT/ITL/TPOT/E2E，没有性能成绩。

微型模型来自上级 Transformer 教程实际训练 2000 步的全部 232 个可学习矩阵标量，RMSNorm scale 固定为 1。它省略 Qwen3 的 Q/K Norm，词表/权重与真实 Qwen3 无关。参数与参考 logits 保存在 _book/case.json；计算保留完整精度。

## A100 实验

[labs/a100_offline.py](labs/a100_offline.py) 在 Linux/A100、vLLM 0.30.0 环境运行，具体命令、配置和验收见第 21 章。需准备真实模型路径与 revision。脚本保存实际模板 IDs、环境、配置、输出和多次整批耗时，**不将离线整批耗时冒充 TTFT**。

本机只验证脚本语法，没有执行 CUDA/vLLM 安装、模型下载或 A100 基准。40GB/80GB A100、驱动和后端支持应由服务器日志确认。

## 生成与验证

~~~
python _tools/build_textbook.py
python _tools/verify_textbook.py --static
python _tools/verify_textbook.py
~~~

源稿为 _book/manuscript.txt；别名和数值实验数据在 _book/。构建器使用标准库生成离线正文、源码页和 SVG。完整验证额外使用本机 Chrome、lxml、websocket-client。报告为 _qa/textbook-validation.json，截图为 _qa/textbook-*.png。

## 旧版资料

旧图解保留在[图解版.html](图解版.html)，备份在 _archive/图解版_20261019/。旧图解的固定主体/仅训练输出头数值与简化服务轨迹是独立旧案例，不能与本书重新训练后的模型和真实 MRV2 源码路径混合。

旧构建器只写图解版.html 与图解版说明.md，避免覆盖新教材入口。新入口由 build_textbook.py 管理。

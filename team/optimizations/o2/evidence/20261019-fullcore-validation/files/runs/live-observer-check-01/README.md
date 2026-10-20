# 真实 O2 首轮日志的部分诊断

状态：发现检查器误拒绝；不是 RTL 失败，不是正式验收。快照时间：2026-10-19T05:48:41.283591+00:00。

本目录仅复制 core-01/hello-vadd 标准输出和标准错误；未修改源日志、硬件、运行工具，未启动新 EMU。冻结工具提交 20e353dc17ae455d4ad2bb65b56c4d58797c6367，硬件冻结提交 b218cbc6e6b135e4ff219a902a9284a59d3c82c9。完整 SHA、读入字节范围与命令见 diagnostic.json。复现分析器由冻结 Git blob 单独复制到本目录，防止随后修复工具混淆反例。

## 可复现问题

旧 analyze.py 在 parse_fields 中对所有 prob/rrob 无条件要求 index < 48，而实际无效槽中可以出现 6 位寄存器随机初值 63。SCHEMA 声明无效槽身份不解释。

实际首个 STATE：

    O2_STATE cycle=                   0 pvalid=0 pseq=                   0 prob=0:16 ppdest=142 rvalid=0 rseq=                   0 rrob=1:63 rpdest=236 occupancy=0 invalid=0 inready=0 vready=1 outvalid=0 outready=1 move=0 killp=0 killr=0 divactive=0 divseq=                   0 divoccupied=0 busy=0

pvalid=0、rvalid=0，因此 rrob=1:63 是无效槽字段。旧严格解析器在 cycle=0 抛出 ValueError: pointer outside pinned configuration。复现使用冻结分析器、require_complete=False，退出码 1，真实 traceback 保存于 analyzer.stderr.log。没有为通过诊断而修改、清洗该记录。

建议修复：所有 ROB 字段始终检查原始六位编码范围；STATE prob/rrob 只有对应 valid=1 时才进一步要求 index < 48。实际有效槽和所有事件中的 ROB 指针仍严格限制 <48。补充无效 48..63 接受、有效 48..63 拒绝、无效 >=64 仍拒绝的回归。Root 已协调修复并计划重新冻结启动独立新 campaign，见主任务后续证据。

## 其他真实观察

实际 schema：O2_SCHEMA version=1 clock=global latency=2 slots=2 rob_size=48 ftq_size= 8 vlen=128 vpu_width=195 perf_width= 577。

可安全截取的前缀保留 114075 字节，剔除了最新观察周期 39497 的全部记录，避免半拍事件。该前缀事件周期顺序非递减；观察到 162 对 ROB redirect 与下一周期 VFEX4 redirect，同 ROB/self 匹配结果为 True。具体原记录逐对保存在 diagnostic.json。此检查只说明已观察前缀，无全核完成、覆盖或性能结论。

快照与原始日志后来增长相互独立。任何修复后的正式 campaign 必须重新冻结来源，并由 root 决定复跑；当前失败记录保留。

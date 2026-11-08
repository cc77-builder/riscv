# SP1-E 第20项 timed DIV/SQRT：三角色完整调用有界校准

**结论：HOLD，候选正常角色达到1500秒墙钟上限，按合同停止余下角色。** bit100拒错通过；未得到完整正常样本、0f配对或9格退化结果。不是已确认的RTL数值故障，也不是一次通过的性能验收。

|角色|状态|墙钟|guest / 覆盖|
|---|---|---:|---|
|candidate bit100|PASS，真实拒错及收据通过|23.572946秒|9205 guest；vd10 bit100/目标PC绑定通过|
|candidate normal|FAIL/EXTERNAL_WALL_LIMIT，校准HOLD|启动至触发1500.000183秒|最终guest未知；最后完整观察cycle591064，26/54标记窗、208/432算子退休|
|0f normal|NOT_STARTED|未运行|前一角色失败即停|

整批外部监督1524.176042秒（约25分24秒），实际启动2个EMU/NEMU差分会话（其中1个使用bit100包装参考库），没有独立NEMU进程、重试或重放。原计划3角色/目标3300秒/宿主900秒/外层4200秒、每角色300/1500/1500秒及10万/100万/100万guest保持，不借未启动基线的预算。

## 运行身份、准入与边界

执行者@cc77-builder / Agent。本地分支`local/zjhwork-integration-20261024`，HEAD `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。本轮预执行快照2026-11-07T07:03:12.690385+00:00，记录生成2026-11-07T15:33:19.171714+08:00；单调时钟回执用于运行耗时，不把墙钟当人工工时。

执行仍用已冻结入口`sp1-e-timed-div-sqrt-host-20261107/launch_target.py`，冻结操作ID`SP1-E-TIMED-DIV-SQRT-HOST-20261107-01`，新收口ID`SP1-E-TIMED-DIV-SQRT-CALIBRATION-20261107-01`。已用本轮真实请求生成独立授权，绑定CONTRACT、35项EXECUTION_FREEZE和host/RESULT；读取Issue活动后核对无活跃目标冲突，没有远程写入。

ELF `f23d58d3fda48427fcf7963c1b5fcf0e36a8394051246504b0d6764e58d68ae5`；BIN `90f14db3d81720ce46d36aed7d16d35e1760b104614b5dab176fa1ef2900e79c`。两核EMU/参考/flash完整pins见[RESULT.json](RESULT.json)及执行冻结。没有更改任何冻结运行器、宿主检查器、镜像或生产RTL。

## 终态与资源

外部监督在TARGET阶段触发`EXTERNAL_WALL_LIMIT`，SIGKILL本轮worker及候选EMU，`cleanup_ok=true`，所有已记录PID＋出生标识复核已退出，当前无EMU/NEMU目标残留。

候选角色来不及写最终record.json和validation.json；batch.json保留`RUNNING`、目标计数1，是worker被终止前的中间态，**不是任务仍在后台运行**。根据两个launch、两个实际执行身份及外部监督进程事件，真实目标数是2。原中间文件不重写、不伪造正常收据；终态以external-batch/RESULT.json和本轮TERMINAL_AUDIT为准。

候选25748个完整资源采样，最大1线程、75235328B RSS（约71.75MiB），采样中所有TID仅CPU4；未见资源超限。候选stdout4096B、stderr1679360B，连同bit100共1706500B，低于2GiB。采样不是瞬时内核硬限证明，且缺候选完整收据，不能将其称为正常运行收据PASS。

## 部分覆盖的严格边界

完整行中有520条T13退休，26组起止标记、208条vdivu/vfdiv/vfsqrt退休及208对父级接受/输出。UART仅14条完整行（seq0～13），另有seq14截断行；完整结果、CSR、退休和父级全量绑定未闭合，无SP1E_SUMMARY、无GOOD TRAP及最终guest计数。

局部日志未出现数值失配终止标记，但这不等于54窗全部正确。26个窗口指的是标记闭合的观察数量，不是26个完整验证PASS；不能把208条算子外推为432条通过。跨硬件逐窗控制、9格2%和精确重放均NOT_TESTED。

一次收口诊断初稿未兼容ROB编号空格补齐，统计偏少；已用全行匹配修正并保留初稿`partial-diagnostic-draft-rob-spacing.json`。这只影响只读诊断摘要，未改执行检查器、原日志或本轮失败判定。

## 预算含义与接续

26个标记区间总8463周期，仅占591064观察前缀约1.43%；窗口起点间隔中位22974周期，提示主要开销在窗口外，但尚未把检查、格式化和UART逐项定量。简单等间隔情景约125.5万guest、3185秒，**仅是规划外推，不是实测全调用或保守上界**。原正常1500秒和100万guest、原正式6300/7200预算继续HOLD。

下一步集中评审窗口外成本及一份可执行的新合同，复用已通过项，不重复同预算盲跑。详情见[预算](BUDGET_REVIEW.md)和[下一轮](NEXT_STEP.md)。

## 计分板、版本与三项指标

正式进度仍为18/20；第19项F2v压力补测暂存，第20项缺完整正常、配对与重放。默认0f＋firstdot V2＋原C8不变，SP1候选未采用。新加速比、面积和STA均NOT_TESTED；18组历史性能、局部FU/完整父级面积和五档时序在[METRICS](METRICS.md)完整续档，原成本NO-GO和所有失败保留。

已复核生产445文件、候选398文件、原准备目录68文件及425份受保护材料无漂移，35项执行冻结一致。没有RTL改动、新核构建、EDA、默认切换或GitHub上传。

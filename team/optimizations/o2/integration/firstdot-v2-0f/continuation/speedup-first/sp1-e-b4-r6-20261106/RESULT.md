# B4-R6：两次重放接入与宿主准入收口

**结论：STOPPED / HOLD。唯一正式宿主尝试发生导入错误，已按失败即停终止；没有运行两个EMU目标，也没有进入成本测量。** 默认仍为 **0f＋firstdot V2＋原C8**，正式验收 **17/20**。

操作`SP1-E-B4-R6-20261106-01`；@cc77-builder / Agent；起止`2026-11-06T13:37:05.817023+00:00` → `2026-11-06T14:16:37.393124+00:00`（UTC+00:00）。此墙钟记录包含WSL等待和实现审查，不是人工工时或目标预算。HEAD `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`；分支`local/zjhwork-integration-20261024`，未提交/未上传。

## 本轮实际完成与停止位置

|阶段|结果|证据边界|
|---|---|---|
|两角色运行器|实现、静态核对完成|只允许candidate-replay→baseline-replay；实际目标未执行|
|历史绑定|静态适用|三原角色、两R5完整summary及39项历史pins；历史boot独立|
|生产执行冻结|完成|47份Python source version；351项执行输入，R5全部303项包含|
|独立静态审查|当时PASS，原记录保留|未实际覆盖冷进程完整导入冲突，不等于宿主实测通过|
|宿主预检与消费锁|完成，唯一尝试已消费|57份source、363份input；不能重启本次入口|
|宿主测试模块导入|FAIL|ImportError，实际加载旧G0 fixtures.py|
|9项增量测试|NOT_RUN，执行0项|在加载TestCase之前退出，不能写成9项失败或通过|
|成本准入|NOT_RUN|没有budget CLAIM，不能据此判预算足够或不足|
|候选/0f重放|NOT_RUN，0目标|没有RUN_AUTHORIZATION、target目录或external-batch|
|外层监督|正常停止并清理|exit1；1.395338548秒；cleanup_ok=true；无剩余存活子进程|

## 确切原因与审查漏项

实际顺序为`run_once.py:37 load_adapter` → R5 adapter → B4 C48 adapter-r1/base → R7 negative_checker → B3 collector。旧collector将G0 `protection/host`目录插到`sys.path`首位。随后`host-tests/test_delta.py:6`执行裸`from fixtures import authorization_fixture, current_entry, schedule_trace`，选中了旧G0同名文件，该文件不含所需函数，触发ImportError。

Traceback直接记录错误模块路径，events已记录IMPORT_COMPLETE后HOST_ATTEMPT_STOPPED。没有保存当时完整sys.modules快照，因此不把“缓存先占位”当额外实证。成本脚本`budget-review/measure_once.py:6`也有同一裸导入，但本次未运行到它。

这是本轮新增宿主包装的模块装载隔离遗漏。AST语法检查和静态审查没发现运行时搜索路径变化，原STATIC_REVIEW_PASS保持其历史记录，同时明确此漏项；不能拿它替代本次真实FAIL。已有数据没有新的RTL、C48数值或资源超限失败结论。

## 输入保护及环境事件

终态只读校验：57/57源码、363/363宿主输入、351/351执行输入、445/445生产文件、406/406旧轮次文件均匹配；4份before文档快照匹配，HEAD/分支不变。原独立静态结果及其manifest保持原pin。`final_inputs_unchanged=false`是异常分支未到收尾校验的状态，不是实际输入漂移证据；独立哈希复核另行给出MATCH。

准备期间WSL命令入口停止响应，UNC文件共享可读且未发现工程目标运行。保存诊断后仅重启Ubuntu-22.04发行版一次，入口恢复；内核boot_id未变，没有更改配置或源码。被终止的是本轮挂起的准备命令，当时正式宿主尝试0、目标0。该事件和一次首次启动的systemd用户会话警告均留档，不混入实际1.395秒宿主结果。

## 三项指标与验收进度

新加速比、面积、时序全部 **NOT_TESTED**；[指标表](METRICS.md)保留18条历史性能、FU/真实父级面积、五档STA及关键路径，数值不变。历史chain候选周期下降13.772213%等成绩没有因本次包装失败失效，也没有形成新的成绩。

原G0固定20项清单里，C48普通C48调用是独立功能项，48调用/12 C8调用/1008custom，性能窗口数0。未来新合同下两实际重放和所有门闭合，可考虑仅此项17→18；本轮不能提前计数。O2取消覆盖和timed DIV/SQRT仍独立待验，不自动切默认。

## 最小下一轮

只修新宿主测试与成本脚本的helper装载，采用绝对文件路径＋唯一模块名并核对来源。不得改旧G0模块、清空旧全局模块缓存或靠调整导入先后掩盖问题。补实际顺序的冷进程完整导入集成检查，再复用未变的运行器、监督、三历史角色和原门槛；新独立身份/输出/冻结/授权，不重启B4-R6旧消费锁。

未来预算提案仍是最多2新目标，各2400秒/150万guest、target累计4800秒、host900秒、outer5700秒；实际host成本本轮未测，下一轮必须完成。用户一次条件授权后可以宿主门通过即同轮两重放，无需多开只问许可回合。

[下一轮指令](NEXT_STEP.md) · [宿主失败归因](host-failure-review/RESULT.md) · [独立保护审计](terminal-review/AUDIT.json) · [机器记录](RESULT.json)。本轮追加计分板及数据档案记录87，所有旧FAIL和锁保留。

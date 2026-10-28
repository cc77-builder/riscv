# C2 公平周期控制器：最小适配清单（草稿，未运行）

本文件只说明旧 r3-div-gate/performance/ 到 C2 新身份的适配点，不修改旧实现，也不启动任何 EMU。本轮成本过筛、C2 新全核实际回归及生成物独立审查全部完成后才能冻结正式周期控制器。

| 旧入口 | C2 必须调整的部分 | 保留不变的判据 |
| --- | --- | --- |
| build_profile.py：SOURCE_COMMITS、PIN_SHA、EMU_SHA、products、DEFAULT_ACCEPTANCE | before固定0f/2d1db77c；after固定C2 6704ce35与新build实际pins/EMU；使用本轮最终C2接受回执 | 两版同MinimalConfig、核/线程、全部flag、依赖、429源清单和仅ExeUnit差异；Git blob与实体哈希验证 |
| verify_accepted_receipts | before复核既有0f正常/负控/复算，after要求新C2最终接受收据（不可接受PENDING_GENERATED_REVIEW），并绑定当前成本screen及独立审计SHA | 真正全核接收在公平周期之前；运行PASS、成本PASS、采用、周期资格分别判定 |
| generated manifest审查 | 核对实际新增/删除/变化集合，引用本轮生成审查收据；不套旧六文件白名单或旧elasticDivCancelled字符串 | 每份实际产物SHA；VDotElastic相同；SimTop/reset/TE与其它变化逐项说明；没有形式等价冒称 |
| build_profile内normalized_verilator及工具检查 | 正确规范化不同检出根及build绝对路径，不只替换旧ROOT/build；同时按独立源码SHA验证路径重定位确实仅位置不同 | 实际编译选项/工具版本一致，包括OPT_FAST=-O3、OPT_SLOW=-O0、单线程；不能删除不理解的参数来强制相等 |
| compare.py：ROOT/HERE/DEFAULT_WORK/BEFORE_PINS/AFTER_PINS | 新模块入口和新输出；实际运行cwd指向C2根，before物理EMU仍在MAIN/build/emu | 输出必须全新；baseline build原地保留，不挪动旧产物；记录完整命令、路径及exit |
| compare.py：辅助文件与输入冻结 | 两版constantin.txt/plusArgs逐字节比较，并记录真实运行环境NOOP_HOME/NEMU_HOME/CONSTANTIN_ROOT；运行前后保护固定实体 | 正常NEMU、flash、16镜像208载荷、检查器及原生成器都冻结；正负参考库不改 |
| compare.py：controller说明和状态 | 新身份说明C2 readyless门控组合；新报告/接收状态不得伪装成旧8b→0f实验；新CONTRACT与控制器先SHA冻结 | 使用同一既有analyze/runtime_gate/unified checker，均绑定Git blob；新本地控制器以SHA和预运行快照绑定 |
| recheck.py/results导出 | 新cmp/profile模块导入、来源/接受回执和结果文字；原日志逐项重算后输出C2结果 | 真实状态与周期不退化独立判定；失败保留，数据档案追加，不覆盖旧实验 |

可以直接复用原 compare.py 的纯函数及调度逻辑，但正式文件复制到新C2材料目录后，必须校对上表中所有全局常量与路径，按新身份做主机测试。不能修改旧冻结脚本后仍声称同一检查器快照。

计划固定的统计合同：1校准+3功能+4场景×3数据集，两版共36实际EMU；4正式重复和batch/d0额外两次确定性重放；478全部校验窗口、192正式窗口形成96配对。最大2进程，单线程EMU，seed=1，128MB、120分钟/200万周期保护。每个正式after窗口多1周期即退化；加速比sum(RVV)/sum(vdot)，不扣开销，不算宿主耗时。4个额外重放只检查确定性，不加入正式样本。

全核草稿控制器的终点故意是 C2_FULLCORE_REGRESSION_PASS_PENDING_GENERATED_REVIEW，cycle_comparison_authorized=false。根任务在新生成结构、比较合同、真实原始回归回执完成独立审查后另写最终接受收据；这一步必须是真实检查，不能仅重命名JSON状态。

当前状态：以上为可执行控制器的设计输入，**C2周期 NOT_TESTED**。

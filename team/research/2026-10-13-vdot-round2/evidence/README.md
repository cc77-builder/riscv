# 实际执行证据与复现

所有以下实验在本次ChatGPT隔离Linux容器中执行，**不是Windows本机Codex、NEMU、QEMU、香山RTL、综合、STA或功耗测量**。三份结果包含实际UTC时间与源文件SHA256；北京时间为UTC+08:00。没有把论文性能数字加入实验结果。

## 1. 已运行且通过

| 证据 | 实际范围 | 不能证明 |
|---|---|---|
| [arithmetic.json](arithmetic.json) | 65,536对编码字节的符号修正；8个全加器真值；4,104个八项输入比较平衡树、乘积CSA、共享部分积模型；160个长点积数学检查 | Chisel网表等价、CSR/异常、全核功能或PPA |
| [assembly.json](assembly.json) | Clang17成功汇编；四个B5变体各20字节/5条核心指令；K-RVV函数静态80字节 | 目标执行正确、五周期、任意K可调用 |
| [assembly-symbols.txt](assembly-symbols.txt) | 真实ELF符号表，begin/end明确核心计数边界 | 动态指令数、周期或反汇编执行轨迹 |
| [git-handoff.json](git-handoff.json) | 临时bare仓库与独立clone的12项实验；实际并发push、固定SHA、交接、未发布工作保留与双fork反例 | 已部署团队锁服务、GitHub权限或实际成员试行 |
| [artifact-integrity.json](artifact-integrity.json) | 8个上传实验/结果文件的Git blob与实际本地文件一致；3份结果关联源摘要一致 | 新平台上独立复现 |

算术结果里的8条错误捷径反例包括窄位宽、e8取数、高位布局、跨缩放合并、错误取消等。其中取消/ROB示例是逻辑反例，不是已执行的RTL状态机故障注入。不是发现了现有仓库8个真实bug。

本轮另运行3个Python脚本的`py_compile`语法检查。Git并发试验的胜者不固定，最终结果文件记录的是该次真实胜者；只有一个成功等不变量才是验收条件。

## 2. 复现命令

在已检出的研究目录运行，输出到新的临时目录，避免覆盖归档证据：

```bash
python3 experiments/check_arithmetic.py --output /tmp/vdot-round2/arithmetic.json
python3 experiments/check_git_handoff.py --output /tmp/vdot-round2/git-handoff.json
python3 experiments/check_assembly.py --output /tmp/vdot-round2/assembly.json \
  --symbols-output /tmp/vdot-round2/assembly-symbols.txt
python3 -m py_compile experiments/check_arithmetic.py experiments/check_git_handoff.py experiments/check_assembly.py
```

依赖：Python3.10+；Git实验另需Git；汇编检查另需支持RISC-V的Clang及llvm-readelf/readelf，可用参数指定可执行文件。Windows使用可写临时路径替换`/tmp`；本轮没有独立验证Windows运行。前两个脚本使用assert作为实验判定，会拒绝Python `-O`；不能关闭断言后把运行结束当通过。

Git实验只创建并删除自己拥有的临时目录，不读取团队仓库、联网、改GitHub设置或调用用户凭据。复现会生成新时间/临时Git提交，JSON不必逐字相同；源摘要、输入摘要和逻辑检查应对应。不同汇编工具版本可能生成不同对象摘要，须保留版本并重新检查边界。

## 3. 原型调用边界

`rvv_candidates.S`是隔离研究源码，未接入正式构建。B5的入口策略必须与变体匹配，当前只给固定寄存器示例。K-RVV入口只接受8的倍数且0≤K≤131064，要求输入范围可读；**目标执行前需补长度/尾部/溢出处理包装**。不要把host中包含尾部的数学检查理解为该汇编已支持任意长度。

正式下一门槛：扩展现有T09进行目标ISS验证，再接香山全核、真实DiffTest、事件计时及PPA流程。所有未运行层级保留未运行，不用本目录结果替代。

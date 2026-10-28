# firstdot 中断续跑的原文审计

工具 resume_audit.py 只读取已经完成的 continuation，不启动 EMU，不修改原日志、cwd 或过程记录。
本工具绑定原组合审计器 SHA-256 1daf43dcebba9c40569af8b767c42ecb2360ac387be6d7834d46244bebdbe980。
矩阵和 C 的 controller 必须传实际执行时的最终路径，因为各自 source lock 核验 __file__。

## 计数和合同

新合同 zjhwork-0f-firstdot-continuation-raw-audit-v1。
矩阵：原启动13，12完成/1中断；新增21，共34实际启动/33完整验收。
普通C：原启动2，1完成/1中断；新增2，共4实际启动/3完整验收。
合计38实际启动、36完整验收、2中断；本次续跑新增23。中断结果不计入384正式性能窗口或96次C正常调用。
PID在WSL重启后可能复用，完整过程身份采用实际cwd、带时区started和PID，不以PID独自代表身份。

## 原文检查

矩阵沿用冻结完整检查器：实际命令/闭包、NEMU加载与退出、完整128位结果、CSR、O2协议、
24窗口、normal/replay一致、firstdot bit100拒错、缓存summary逐值复算。
C调用原 normal_check 和 negative_check，核验48 distinct case、96次实际输出、O2协议、公开函数内负例PC及恢复链。
公开C的48项机器码锚定仍绑定到本轮完整矩阵，不借用历史T17成绩。
每个进程由run-locations.json/record_locations解析到原实际目录；旧记录不重写。
两个controller资格函数核验各自完整旧目录快照、原中断记录、执行源码锁与显式计数。

## 输出

最终status=CURRENT_FIRSTDOT_CONTINUATION_RAW_AUDIT_AND_ARCHIVE_PASS。
state单独列qualified_processes=36、actual_launched_processes=38、interrupted_processes=2、
continuation_new_emu_processes=23、inherited_launched_processes=15，审计自身new_emu_runs=0。
输出evidence-inputs.json、external-inputs.json、matrix-raw-proof.json、c-raw-proof.json、
combination-qualification.json，以及archive/manifest.json。
归档既保存完成证据也保存旧partial原目录，未覆盖原文件。原文复算仍需原外部构建输入；
字节归档通过不等于离线独立复现。之后仍须新目录实际clean构建/运行。

命令形式：

    python3 -B resume_audit.py --repo "$REPO" --identity "$IDENTITY" \
      --matrix-build "$WORK/combination-build-02" --matrix-run "$WORK/combination-resume-01" \
      --c-build "$WORK/c-build-01" --c-run "$WORK/c-run-02" \
      --matrix-controller "$REPO/team/optimizations/o2/integration/firstdot-v2-0f/continuation/matrix/continuation.py" \
      --c-controller "$REPO/team/optimizations/o2/integration/firstdot-v2-0f/continuation/c/resume_c.py" \
      --interruption-receipt "$WORK/interruption-01/receipt.json" --output "$WORK/combination-audit-resumed-01"

目录名称以实际运行记录为准；所有输出必须全新且不与输入互相包含。

## 本次工具验证

20 tests PASS、0 skips，tests-01.log。
其中17项使用实际旧C负例的完整来源与输入闭包检查：空退出、RUNNING、错误退出、PID、未启动、
超时、漏输入、篡改cwd/command/reference/rawhash/性能范围/合同/replay/故障环境/时间均被拒绝。
三项检查新归档合同、压缩载荷破坏拒绝和输出隔离。实际旧证据hash前后不变。
完整33+3 logical continuation原文审计尚未运行，必须等两个新campaign完成。

## 本轮审计v2补充

新增chronology.py固定唯一已记录的墙钟异常。当前功能/周期通过与墙钟FAIL分列，实际证据和合同见[组合结果](../../RESULT.md)。原v1严格时间审计失败保留，不能把v2结果写成v1全部通过；新干净运行仍使用标准无中断审计合同。

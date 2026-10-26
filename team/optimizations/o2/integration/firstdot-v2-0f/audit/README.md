# 当前 firstdot 组合：原文复算与归档工具

这是独立审计草稿，不修改生产 RTL、冻结的 combination.py 或上游检查器，不启动 EMU/NEMU。当前工具 SHA-256：1daf43dcebba9c40569af8b767c42ecb2360ac387be6d7834d46244bebdbe980。

当前验证：补充独立C实际launcher绑定后，40项主机测试通过（reviews/identity/integrated-audit-02）；已对 matrix 的 negative-firstdot-8x32 与 recovery-firstdot-8x32 两个完成记录做真实原文复算，完整结果与缓存相符，原证据所有文件 hash 不变。证据分别在 tests-final.log、readonly-smoke.json。33 次 matrix + 3 次普通 C 的完整审计尚未执行，必须等待两组 campaign 完成。

## 执行

2026-10-26当前批因进程中断，已改用[续跑审计](../continuation/audit/README.md)。本工具保留给无中断的完整campaign及后续clean批，不直接把中断旧目录当作完整结果。

可以把 audit_combination.py 和 test_audit_combination.py 原样复制到主叶级目录的 audit/，此路径不在冻结 runtime 的 adapter_files 固定四文件中，不影响正在运行的组合身份。完整输入保留在原目录，输出必须是新目录且与所有输入互不包含。

    python3 -B audit_combination.py \
      --repo /home/riscv/riscv-lab/zjhwork2-review-20261018/repo \
      --identity /home/riscv/riscv-lab/software-import-20261026/reviews/identity/current-identity-v3.json \
      --matrix-build /home/riscv/riscv-lab/software-import-20261026/combination-build-02 \
      --matrix-run /home/riscv/riscv-lab/software-import-20261026/combination-run-01 \
      --c-build /home/riscv/riscv-lab/software-import-20261026/c-build-01 \
      --c-run /home/riscv/riscv-lab/software-import-20261026/c-run-01 \
      --output /home/riscv/riscv-lab/software-import-20261026/combination-audit-01

测试：

    python3 -B -m unittest discover -s <audit-directory> -p test_audit_combination.py -v

## 检查范围

1. 固定 combination.py 的实际 SHA 22a418c4…及 entry_c_api.py 的上游 SHA 4e1ae340…；沿用当前身份适配器的完整物理来源核验。
2. 24 个矩阵镜像逐个 g.verify_build，重算配对布局与 12 对公平性报告；重建完整 common 输入闭包并精确匹配。
3. 33 个运行逐一检查原 process_started、PID、真实 exit、超时、命令、CWD、镜像、配置、reference、负控环境、全部 inputs、stdout/stderr hash 和时间顺序。
4. 32 个正常运行通过原 f.verify_runtime 重算完整 128 位结果、CSR、计数和 O2 协议；所有 window/sample/observation 与缓存逐项一致。再重算 384 个正式窗口、8 个 replay、summary 和 qualification。
5. 负控在临时目录调用原 negative_check，不修改原 negative.json/observation.json；确认 vd0、bit100、0x0388000b，以及 negative/recovery 链。负控构建的编译/链接命令、真实退出和日志 hash 同样核对。
6. 普通 C 调用原 base.audit_run：检查 16 个函数、48 个独立案例、96 次正常调用和 3 个真实进程；48 个公开叶节点比较绑定到已审计矩阵。
7. 全部 build/run 证据在审计开始形成摘要快照，在归档前后复核；外部硬件、工具和输入闭包也再次复核。

## C 审计的唯一适配

旧 entry_c_api.audit_run 的 expected 字典只含旧 merged_screen 返回的少量硬件文件；当前运行使用完整硬件闭包。直接套用旧函数会因 common inventory 不一致被拒绝。

本工具只在精确固定 SHA 的原 audit_run 函数中、common==expected 检查前插入：

    expected.update(_current_hardware_files)

_current_hardware_files 由当前身份硬件检查重新物理读取。原函数其余逻辑保持逐字节，新的私有函数 hash 和插入说明保存在 c-raw-proof.json。没有删去 extra 字段，没有裁剪原证据，没有改写磁盘上的源文件或旧固定值。

## 归档

archive/manifest.json 列出每个逻辑路径、原绝对路径、原大小/hash、gzip payload 大小/hash。gzip 固定 mtime=0；归档后逐成员解压重算 hash，并核对原输入仍相同。

收录：四个完整 build/run 目录（原文、JSON、源码快照、ELF/BIN/object）、当前软件源码及合同、identity/固定锁、旧硬件构建元数据、审计工具、原文复算结果和输入清单。不会复制全核 EMU、整个硬件依赖树或 NEMU 工程。

可以只用 archive/ 校验全部压缩内容的完整性：

    import audit_combination
    audit_combination.verify_archive("<archive-directory>")

**这只证明归档内容 hash 一致。原文复算仍依赖原 build 目录、当前源码及外部固定输入；本工具不宣称脱离原构建的独立复现，不替代下一阶段干净构建与新运行。** 所有结果明确写 standalone_raw_recomputation=false、independent_clean_reproduction=false、new_emu_runs=0。失败输出保留，不复用同名输出目录。

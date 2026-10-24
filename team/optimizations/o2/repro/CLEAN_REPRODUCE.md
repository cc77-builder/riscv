# T17 复现与原始证据复算

先读 [CLEAN_CONTRACT.md](CLEAN_CONTRACT.md) 的固定身份和范围，再按需要选择“重新构建并执行”或“只复算封存原文”。实际本轮结果与回执见 [CLEAN_RESULT.md](CLEAN_RESULT.md)。所有输出使用新目录/新文件；下面命令不是续跑或覆盖旧实验的方法。

## 1. 前置输入

使用 Linux/WSL 原生目录构建和仿真。NTFS 发布树的状态、暂存、提交及推送使用 Windows 原生 Git。先读协作 Issue，核实认领、运行和四核总预算；性能阶段不得与其他重任务并行。

以下 `taskset -c 0-3` 示例要求当前进程获准使用 CPU 0～3；其他 cpuset 或不足四核的环境，应替换为实际许可 CPU 集合，并相应降低并发，仍以全体任务合计最多四核为限。

需要准备：

- 含本版原九份团队脚本及新增传输工具 `clean_portable_evidence.py` 的发布 checkout；其中的 Git 历史含完整 `34bae6d4acceac939f958199dae53c14bc1f6183`。
- 可只读访问的硬件递归 Git 缓存，含固定 Gitlink 提交；xs-env、NEMU 及其依赖的对象缓存。入口会新 clone，不使用缓存工作树的修改。
- [合同](CLEAN_CONTRACT.md) 指定 SHA 的历史 `hardware-inputs.json`，作为源码/依赖字节对照；它不是旧 EMU 运行资格。
- 已安装的 Java、Mill、Verilator、Clang、Make、Python、firtool、RISC-V GNU 工具链及其可用依赖。实际版本写入新构建记录。
- 冻结 hello/vadd、flash、功能分片、control、dense 和两项 O2 supplement 镜像及其构建记录。`clean_fullcore.py` v1 仍使用 [run_suite.py](../fullcore/run_suite.py) 的冻结 T12/T14/dense 路径和 [run_supplements.py](../fullcore/run_supplements.py) 的原位置；本轮直接输入的原位置与字节身份另见[整核封存清单](evidence/clean-reproduction-v1/fullcore-archive/archive-manifest.json)。必须按原记录恢复，不能把新路径或相似镜像填进旧身份。本版不是所有历史 workload 的路径迁移工具。

源码发布树可含新合同/审计工具；硬件执行树的 HEAD 必须留在固定34bae。不要把发布树的新提交直接当作构建源码身份。

## 2. 恢复新源码树

在 bash 中填写本机实际路径。不要把尖括号占位内容或环境变量字样直接写入 JSON；配置解析器不展开 `$VAR`。

~~~bash
export T17_RECIPE=/absolute/published/checkout
export T17_RUN_ROOT=/absolute/new/t17-attempt
export T17_HARDWARE_CACHE=/absolute/read-only/full-hardware-checkout
export T17_ENV_CACHE=/absolute/read-only/xs-env
export T17_NEMU_CACHE=/absolute/read-only/nemu-with-dependencies
export T17_BASELINE_PINS=/absolute/restored/hardware-inputs.json
export T17_JAVA_HOME=/absolute/graalvm-jdk-21
export T17_VERILATOR_ROOT=/absolute/verilator
export T17_FIRTOOL_DIR=/absolute/firtool/bin
export T17_EXECUTOR='@verified-user / Agent; operation-id'

taskset -c 0-3 python3 -B \
  "$T17_RECIPE/team/optimizations/o2/repro/clean_prepare.py" \
  --source "$T17_RECIPE" \
  --revision 34bae6d4acceac939f958199dae53c14bc1f6183 \
  --hardware-cache "$T17_HARDWARE_CACHE" \
  --environment-cache "$T17_ENV_CACHE" \
  --output "$T17_RUN_ROOT/clean" --executor "$T17_EXECUTOR"
~~~

检查 `prepare-state.json` 为 `T17_CLEAN_SOURCE_PREPARED`、133仓库/126硬件子库。该提交早于新 T17 工具，因此只把下列原九份脚本及新增传输工具（共十份**团队新脚本**）从发布 checkout 复制到新源码树；不覆盖任何旧检查器、RTL、官方程序或旧锁。复制后按合同及发布清单核对 SHA。

~~~bash
export T17_SOURCE="$T17_RUN_ROOT/clean/source"
for T17_FILE in clean_prepare.py clean_build.py clean_support.py clean_profile.py \
  clean_entry.py clean_fullcore.py clean_evidence.py clean_fullcore_evidence.py \
  test_clean_evidence.py clean_portable_evidence.py; do
  test ! -e "$T17_SOURCE/team/optimizations/o2/repro/$T17_FILE" || exit 1
  cp "$T17_RECIPE/team/optimizations/o2/repro/$T17_FILE" \
     "$T17_SOURCE/team/optimizations/o2/repro/$T17_FILE"
done
cd "$T17_SOURCE"
git rev-parse HEAD
sha256sum team/optimizations/o2/repro/clean_*.py
~~~

后续运行前后源码和适配器都会再次核对。不要在该执行树提交、切分支或修改受保护输入。

## 3. 实际构建 EMU、参考模型与 AM

~~~bash
taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_build.py \
  --repo "$T17_SOURCE" --output "$T17_RUN_ROOT/build" \
  --baseline-pins "$T17_BASELINE_PINS" \
  --java-home "$T17_JAVA_HOME" --verilator-root "$T17_VERILATOR_ROOT" \
  --firtool-dir "$T17_FIRTOOL_DIR" \
  --environment-root "$T17_RUN_ROOT/clean/xs-env" \
  --jobs 4 --executor "$T17_EXECUTOR"

taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_support.py \
  --repo "$T17_SOURCE" --output "$T17_RUN_ROOT/support" \
  --nemu-source "$T17_RUN_ROOT/clean/xs-env/NEMU" \
  --nemu-cache "$T17_NEMU_CACHE" \
  --am-home "$T17_RUN_ROOT/clean/xs-env/nexus-am" \
  --environment-root "$T17_RUN_ROOT/clean/xs-env" \
  --executor "$T17_EXECUTOR"
~~~

这两条按顺序执行最容易控制总预算。支持构建内部允许 NEMU `-j2` 与 AM/klib `-j2` 并行。它们成功只表示实际构建完成，`runtime_qualified` 仍为 false。

复制 [clean-config.example.json](clean-config.example.json) 到 checkout 外的 `$T17_RUN_ROOT/runtime.local.json`，六个路径字段填写实际绝对路径，`cross_prefix` 填可用交叉工具链的名称或完整前缀，例如 `riscv64-linux-gnu-`。`build_driver` 必须是本次构建输出中的 `executed-builder.py`；`reference` 必须是本次 support 的正常参考库；不要选旧 EMU/NEMU。然后固定 identity 和支持来源：

~~~bash
taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_entry.py \
  --repo "$T17_SOURCE" --action identity \
  --config "$T17_RUN_ROOT/runtime.local.json" --output "$T17_RUN_ROOT/identity.json"

taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_evidence.py \
  --repo "$T17_SOURCE" --action support --identity "$T17_RUN_ROOT/identity.json" \
  --output "$T17_RUN_ROOT/support-proof.json"
~~~

`support-proof.json` 文件名是归档接口的固定名称。后续任何适配器、配置或输入变更都应使用新 identity/输出，不修改已启动任务。

## 4. 软件构建和正确性运行

~~~bash
taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_entry.py \
  --repo "$T17_SOURCE" --action build-matrix \
  --config "$T17_RUN_ROOT/runtime.local.json" \
  --output "$T17_RUN_ROOT/matrix-build" --jobs 4

taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_entry.py \
  --repo "$T17_SOURCE" --action build-c \
  --config "$T17_RUN_ROOT/runtime.local.json" --output "$T17_RUN_ROOT/c-build"

taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_fullcore.py \
  --repo "$T17_SOURCE" --action run --identity "$T17_RUN_ROOT/identity.json" \
  --output "$T17_RUN_ROOT/fullcore-run" --jobs 4 \
  --operation-id 'unique-fullcore-operation-id'

taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_entry.py \
  --repo "$T17_SOURCE" --action run-c --identity "$T17_RUN_ROOT/identity.json" \
  --build "$T17_RUN_ROOT/c-build" --output "$T17_RUN_ROOT/c-run" \
  --operation-id 'unique-c-operation-id'
~~~

也可把整核设 `--jobs 3`，与一个普通 C 执行器同时运行；必须隔离输出并确认总计不超过四核。本轮的实际3+1方式记录于结果。普通 C 执行器内部3个进程顺序执行；不会同时启动3个 EMU。

完成后先审计正确性原文：

~~~bash
taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_fullcore_evidence.py \
  --repo "$T17_SOURCE" --action physical --run "$T17_RUN_ROOT/fullcore-run" \
  --output "$T17_RUN_ROOT/fullcore-audit"

taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_entry.py \
  --repo "$T17_SOURCE" --action audit-c --identity "$T17_RUN_ROOT/identity.json" \
  --build "$T17_RUN_ROOT/c-build" --run "$T17_RUN_ROOT/c-run" \
  --output "$T17_RUN_ROOT/c-audit.json"
~~~

不要根据 shell 的 running 回执、后台进程消失或已有一项 PASS 推断整体完成。读取各自 state、实际退出码、stdout/stderr 和完整结果；未知交付只查询原 operation，不重新执行。

## 5. 串行公平性能矩阵

确认其他重型构建、EMU、压缩/原文审计已经结束。保存启动前进程/资源事实并在协调 Issue 更新运行保护，然后执行：

~~~bash
taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_entry.py \
  --repo "$T17_SOURCE" --action run-matrix --identity "$T17_RUN_ROOT/identity.json" \
  --build "$T17_RUN_ROOT/matrix-build" --output "$T17_RUN_ROOT/matrix-run" \
  --operation-id 'unique-matrix-operation-id' --negative --replay
~~~

本命令内部串行启动33个进程。不要把 `--jobs` 当作性能并行开关，也不要在多个外部 shell 拆跑该冻结批次。必须以完整384正式窗口和192 replay比较完成为准，再选择每个形状的最快合格同入口 RVV。宿主秒数不作为处理器周期。

## 6. 封存和离线原文复算

打包操作新建的 `--archive` 必须使用新目录；`pack-matrix`、`pack-c` 的 `--source` 也必须是新目录。审计和索引操作读取已有归档。每次 `--output` 均使用新文件或新目录。运行阶段用 `clean_entry.py`；归档阶段统一用下列两个新审计器，避免旧归档分支重复封存同一个 builder 原路径。

~~~bash
taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_fullcore_evidence.py \
  --repo "$T17_SOURCE" --action pack --run "$T17_RUN_ROOT/fullcore-run" \
  --audit "$T17_RUN_ROOT/fullcore-audit" --support "$T17_RUN_ROOT/support-proof.json" \
  --archive "$T17_RUN_ROOT/fullcore-archive" --output "$T17_RUN_ROOT/fullcore-pack.json"

taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_fullcore_evidence.py \
  --repo "$T17_SOURCE" --action audit --archive "$T17_RUN_ROOT/fullcore-archive" \
  --output "$T17_RUN_ROOT/fullcore-archive-audit.json"

taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_portable_evidence.py \
  --repo "$T17_SOURCE" --action pack-matrix --source "$T17_RUN_ROOT/matrix-pack-source" --identity "$T17_RUN_ROOT/identity.json" \
  --run "$T17_RUN_ROOT/matrix-run" --support "$T17_RUN_ROOT/support-proof.json" \
  --archive "$T17_RUN_ROOT/matrix-archive" --output "$T17_RUN_ROOT/matrix-pack.json"

taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_portable_evidence.py \
  --repo "$T17_SOURCE" --action audit-matrix --identity "$T17_RUN_ROOT/identity.json" \
  --archive "$T17_RUN_ROOT/matrix-archive" --output "$T17_RUN_ROOT/matrix-archive-audit.json"

taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_portable_evidence.py \
  --repo "$T17_SOURCE" --action pack-c --source "$T17_RUN_ROOT/c-pack-source" --identity "$T17_RUN_ROOT/identity.json" \
  --build "$T17_RUN_ROOT/c-build" --run "$T17_RUN_ROOT/c-run" \
  --matrix "$T17_RUN_ROOT/matrix-archive" --archive "$T17_RUN_ROOT/c-archive" \
  --output "$T17_RUN_ROOT/c-pack.json"

taskset -c 0-3 python3 -B team/optimizations/o2/repro/clean_portable_evidence.py \
  --repo "$T17_SOURCE" --action audit-c --identity "$T17_RUN_ROOT/identity.json" \
  --matrix "$T17_RUN_ROOT/matrix-archive" --archive "$T17_RUN_ROOT/c-archive" \
  --output "$T17_RUN_ROOT/c-archive-audit.json"
~~~

只复算已发布封存包时，在含相同团队源码的 Linux checkout 运行上述 `audit`/`audit-matrix`/`audit-c` 三条，替换为发布包实际路径和其中封存的同一 identity。identity 必须保留原文件名和原始字节，不改名、不重新序列化；本轮有效文件名为 `identity-02.json`，复算本轮包也必须使用该名。它们不启动新 EMU，不需要原物理 EMU 文件；完整源码、依赖和工具安装的重建另属前述步骤。不要把 Windows 字节清单检查称为 Linux 原始语义复算。

### 独立源码检出与原目录依赖检查

只复算发布证据时，另建固定34bae源码检出，并按第2节复制十份团队脚本；不要把原构建目录复制进去。以下 `T17_AUDIT_SOURCE` 必须没有 `build/`、`out/`。`T17_ORIGINAL_ROOT` 填运行记录中的原始T17根目录（允许它已经不存在）；归档、identity、新检出和审计输出放在该根之外。若还有其他历史物理输入根，可追加 `--deny-root`。本轮实际拒绝目录与完整命令保存在三个 `*-detached-guard-*.json` 报告中。

~~~bash
export T17_AUDIT_SOURCE=/absolute/new/source-only-checkout
export T17_EVIDENCE="$T17_RECIPE/team/optimizations/o2/repro/evidence/clean-reproduction-v1"
export T17_ORIGINAL_ROOT=/absolute/original/t17-attempt
export T17_AUDIT_OUT=/absolute/new/detached-audit-output
mkdir -p "$T17_AUDIT_OUT"

run_t17_guard() {
  taskset -c 0-3 python3 -B "$T17_EVIDENCE/analysis/detached-audit.py" \
    --checkout "$T17_AUDIT_SOURCE" \
    --script "$T17_AUDIT_SOURCE/team/optimizations/o2/repro/$1" \
    --report "$T17_AUDIT_OUT/$2.guard.json" \
    --deny-root "$T17_ORIGINAL_ROOT" -- --repo "$T17_AUDIT_SOURCE" "${@:3}"
}
run_t17_guard clean_fullcore_evidence.py fullcore --action audit \
  --archive "$T17_EVIDENCE/fullcore-archive" --output "$T17_AUDIT_OUT/fullcore.json"
run_t17_guard clean_portable_evidence.py matrix --action audit-matrix \
  --identity "$T17_EVIDENCE/reports/identity-02.json" \
  --archive "$T17_EVIDENCE/matrix-archive" --output "$T17_AUDIT_OUT/matrix.json"
run_t17_guard clean_portable_evidence.py c --action audit-c \
  --identity "$T17_EVIDENCE/reports/identity-02.json" \
  --archive "$T17_EVIDENCE/c-archive" --matrix "$T17_EVIDENCE/matrix-archive" \
  --output "$T17_AUDIT_OUT/c.json"
~~~

传输层保留冻结打包器的源包，另写最终包。实际本轮最终目录为原生 `matrix-archive-03`、`c-archive-02`，发布位置分别为上述 `matrix-archive`、`c-archive`；C始终绑定最终矩阵manifest。M01中误封入EMU但独立复算可通过；原C staging在独立检出会寻找不存在的全局AUX，已保存预期失败。新传输工具修正这一依赖，没有重跑EMU。

依赖探针只检查Python文件/目录访问及显式子进程参数/cwd，不是OS沙箱；子进程和原生代码内部访问没有完整系统级监视。三份最终raw报告与各自guard输出SHA必须配套使用，不能只看guard的PASS字符串。原17项夹具测试覆盖原审计器；传输层另由原包拒绝和最终包独立原文复算验证。

## 7. 边界测试、跨系统交付和恢复

针对本次审计器的实际夹具测试：

~~~bash
taskset -c 0-3 python3 -B team/optimizations/o2/repro/test_clean_evidence.py \
  --repo "$T17_SOURCE" --support "$T17_RUN_ROOT/support-proof.json" \
  --identity "$T17_RUN_ROOT/identity.json" \
  --completed-job "$T17_RUN_ROOT/fullcore-run/runs/hello-vadd"
~~~

这组17项测试需要本次真实已完成回执。旧 `unittest discover` 会明确 SKIP 这组夹具测试，避免隐式读取机器个人目录；SKIP 不算17项测试通过。

发布树以 `.gitattributes` 保留证据原字节。复制后比较源/目标完整清单；暂存后分别运行各格式的 `index`、`index-matrix`、`index-c`，并对所有新增工具、文档、外部回执逐 blob 核验。索引报告写在 checkout 外，随后以独立最终检查纳入交付；避免报告自包含循环。再按协作规定 READY、短 INTEGRATE 窗口、正常快进和远端读回。

Windows上的深归档路径可能超过普通路径限制。本轮已实际验证以Windows扩展路径前缀 `\\?\D:\path\checkout` 传给Python脚本、`--repo`及归档参数可完成原生Git索引检查；不需要改系统设置、冻结检查器或归档内容。索引调用中的各路径应使用一致前缀，Git仍为Windows原生版本。

任何失败均保留原输出和命令回执。源码准备失败使用新的 clean 目录；构建失败不能删除旧产物后冒用原 attempt；运行中断先核实各 PID 和受保护输入，控制器没有自动断点续跑保证。确需修复审计器时保留旧源码/失败原文，记录新工具身份，只重做受影响的审计，不凭此重跑已成功的 EMU。

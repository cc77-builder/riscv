# G3 执行与离线复核

## 当前 Linux LF 与新输入入口（2026-10-21）

本次来源和结果以[当前源码复验记录](../../../docs/o5-current-fullcore-20261021.md)为准；下方2026-10-19身份保留为历史说明。先准备干净的Linux LF检出、递归依赖和显式 `o2-g3-current-inputs-v1` 合同，运行 O5 预检。重新构建的输入须保留源码、命令、工具及产物回执；不能仅改旧路径或SHA。

内存受限机器显式使用 `build_fullcore.py --recipe split-v1 --output /absolute/new/build-receipt`，其schema 3阶段合同与默认direct合同分别记录。先将已有checkout `build/`完整保存到其他目录。成功回执必须为 `O2_FULLCORE_BUILD_PASS`；随后使用其 `hardware-inputs.json` 和同一个新EMU运行：

```bash
python3 -B team/optimizations/o2/fullcore/run_suite.py \
  --hardware-pins /absolute/build-receipt/hardware-inputs.json --emu /absolute/repo/build/emu \
  --input-contract /absolute/inputs/input-contract-v1.json \
  --t12-root /absolute/inputs/t12 --t14-root /absolute/inputs/t14 \
  --dense-build /absolute/inputs/dense --output /absolute/new/core --jobs 2
python3 -B team/optimizations/o2/fullcore/run_supplements.py \
  --hardware-pins /absolute/build-receipt/hardware-inputs.json --emu /absolute/repo/build/emu \
  --input-contract /absolute/inputs/input-contract-v1.json \
  --diagnostic-build /absolute/inputs/supplement-diagnostic \
  --control-build /absolute/inputs/supplement-control --output /absolute/new/supplements --jobs 2
python3 -B team/optimizations/o2/fullcore/recheck.py \
  --campaign /absolute/new/core --supplements /absolute/new/supplements --output /absolute/new/recheck
```

两个运行入口必须使用同一输入合同、硬件pins和EMU。预检只判输入就绪；完整G3还要求全部实际作业、真实DiffTest负控、同镜像正常恢复、六项覆盖和离线重审通过。下方旧便携归档流程不能直接作为新输入合同的跨机执行证明。

本页是工程操作说明，不是 T16 报告。已有运行不要覆盖或重启；最终结论及证据位置见 README。所有命令均从完整香山 checkout 的根目录执行。Windows 材料目录不是硬件构建目录。

## 1. 先辨认三种身份

- 本轮硬件源码：b218cbc6e6b135e4ff219a902a9284a59d3c82c9。
- 正式 core-02 运行工具：e2d9c063ac716665f4596bc95a806bd62a56d3a7。该时点包含真实日志暴露的无效槽 ROB 索引检查修复。
- 修正后的补充测试工具：079351c122e35b77c1a0e01a6c3b60d562eac1cd；诊断构建源码：237f6a7。原 core-02 工具与日志不变。
- 文档、归档及便携工具可以在后续提交集成；它们不是新的 EMU 构建。各自 SHA 和提交应从回执读取。

受测 EMU SHA-256：ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57。构建标志为 O2_ELASTIC=1、O1_HANDOFF=0、T14_FUSED_INPUT=1、O2_TRACE=1、O1_TRACE=0、T12_TRACE=0、T13_TRACE=1，实际变量均加 VDOT_ 前缀。MinimalConfig、单核、单线程 EMU；没有性能 A/B。

## 2. 本机复跑的输入前提

原 T12、T13、T14 冻结镜像、正常/故障 NEMU、flash、源码及数据目录必须存在，见 WORKLOADS.md 和运行脚本的 FROZEN 常量。故障参考库绑定原正常参考库绝对路径。新机器不能只改路径或只复制 bin 后声称输入身份完整；需要按相应原阶段材料恢复并核验依赖。这份说明不代表 T17 已完成。

以下命令只预检输入，不运行 EMU：

```bash
python3 -B team/optimizations/o2/fullcore/run_suite.py --output /absolute/new/g3-preflight --preflight-only
python3 -B -m unittest discover -s team/optimizations/o2/fullcore -p 'test_*.py' -v
python3 -B -m unittest discover -s team/optimizations/o2/fullcore/workloads -p 'test_*.py' -v
```

输出目录必须全新；保留失败尝试。若确实需要重新构建，先在干净、已恢复配套依赖的 checkout 中确认 build/ 不存在，再运行 build_fullcore.py --output /absolute/new/g3-build。脚本遇已有 build/ 会拒绝覆盖；不要删除现有受测二进制或证据来绕过保护。构建默认 -j2、12G JVM，环境来源与精确命令由回执记录。

## 3. 使用当前已核验 EMU 运行新一轮

下例使用当前机器的 build-03 身份，所有输出换成全新目录。实际回归源码、输入及硬件文件在运行期间不得修改；文档整理不应触碰冻结检查器。

```bash
repo=/home/riscv/riscv-lab/zjhwork2-review-20261018/repo
original=/home/riscv/riscv-lab/o2-fullcore-20261019
campaign=/absolute/new/o2-g3-replay
python3 -B team/optimizations/o2/fullcore/run_suite.py --output "$campaign/core" --hardware-pins "$original/build-03/hardware-inputs.json" --emu "$repo/build/emu" --jobs 2
python3 -B team/optimizations/o2/fullcore/run_supplements.py --output "$campaign/supplements" --hardware-pins "$original/build-03/hardware-inputs.json" --emu "$repo/build/emu" --diagnostic-build "$original/diagnostic-build-03" --control-build "$original/control-diagnostic-build-04" --jobs 2
python3 -B team/optimizations/o2/fullcore/recheck.py --campaign "$campaign/core" --supplements "$campaign/supplements" --output "$campaign/recheck"
```

不要同时另开一组 EMU。core 驱动先跑 hello，然后让 bit100 负控及同镜像正常恢复在同一工作线程顺序执行，其他独立分片可在第二线程推进。stdout、stderr、真实退出码分别保存；run.log 是 stderr+stdout 的派生文件，不表示两流的时间交错顺序。

原十二项通过与六项新覆盖分别判定；两项补充作业不能替代冻结矩阵、原 F2v 七项或 dense 自身的窗口/并发要求。负控的预期非零退出不是普通作业通过，也不贡献正常覆盖。任何缺项都不得改写为 G3 完成。

修正前 supplements-01/recheck-01 保留失败状态。修正后 supplements-02/recheck-02 是本轮合格候选，使用同一 EMU；原 core-02 十二项不重新运行，由新版离线审计从原日志和原 Git blob 复核。

## 4. 封存与 Windows 查看

全部运行和 Linux 严格离线复算结束后，再用 archive.py 导出到输入目录以外的新目录。先将便携工具纳入 Git 跟踪，因为归档只复制跟踪的 fullcore 工具。不要把封存输出放进正在遍历的 work-root。

```bash
python3 -B team/optimizations/o2/fullcore/archive.py --work-root /absolute/completed/work-root --output /absolute/new/archive
python3 -B team/optimizations/o2/fullcore/archive.py --output /absolute/new/archive --verify-only
```

复制归档到 Windows 后，用 Python 3.10+ 运行 portable.py；本机可用 D:\python location\python.exe。针对本次命名的参数示例：

```powershell
& 'D:\python location\python.exe' '<portable.py 的绝对路径>' --archive '<归档绝对目录>' --core-campaign core-02 --supplement-campaign supplements-02 --output '<新回执文件.json>'
```

便携审计复算归档字节、13 份完整轨迹及1份预期故障的部分轨迹；它不重新运行 EMU/NEMU，不替代 Linux Git/输入来源核验或全部架构用例审计，不产生 G4 性能结论。

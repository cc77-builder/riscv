# dot16 首次整核构建的 C++ 续接合同 v2

本入口只接续已明确定位的 `build-01` 原生编译器选择失败。准备完成不表示运行完成；原 `build-01` 保持 FAILED，所有原日志和生成物保留。原 [六例差分合同](CONTRACT.md) 的指令语义、镜像、reference、ABI 检查和运行上限保持原样；本合同替代其新 EMU 的 GNU 原生编译选择，并明确成功生成阶段的复用来源。

## 已验证的失败来源

`build-01` 基于 HEAD `c981529dc6e493fb7deee8429b9ce05fd197497b` 与生产补丁 `5b5824bac200c2a775598686e550854f8276d5db007b72f4b7be92437b4d3416`。
2026-11-06 03:32:21.548–03:43:44.414Z 的实际外层回执为 exit=1、cleanup=true，682.810秒，无超时/取消。Scala预编译完成；官方 elaboration 5:09.93、Verilator生成5:38.95均退出0；C++编译在0.40秒后退出2。

错误是 GNU g++-11 拒绝当前 Verilator 配置中的 Clang 参数 `-fbracket-depth=4096`、`-Xclang`、`-fno-pch-timestamp`、`-Qunused-arguments`。实际 installed `verilated.mk` 明确记录配置编译器 Clang 19.1.7，CXX/LINK均为clang++，PCH采用`.gch`和`-include-pch`。

| 固定入口或失败记录 | SHA256 |
|---|---|
| 原 build.py | `38d27240c83763a265dbc1b2d01b65639bc1b7984782bd289d6e6b7d7b0c7ebb` |
| build-01/emu-build.log | `a700694214f771653c9f2402e9214bfa458ff0c73c1e2ac2c68e20cf4eed7f30` |
| ROOT/build/time.log | `58bae1b648884dd30211f8663d57580ed6fd1e4fbb9acf547ebabda546e72986` |
| ROOT/build/emu-compile/VSimTop.mk | `60e83de481c10859af494d354652c48f3cca8e661a3afd1655da7d7e298703e5` |
| installed include/verilated.mk | `e3053baaccc51c5050faeb4ef437b5fe67e94d5578b8fa087b92b457b449a99f` |

Verilator v5.052 的[官方 `--compiler` 说明](https://github.com/verilator/verilator/blob/v5.052/docs/guide/exe_verilator.rst)指出该开关不替换configure时确定的编译参数；其[原始Make规则模板](https://github.com/verilator/verilator/blob/v5.052/include/verilated.mk.in)分别设置CXX和LINK。因此恢复采用与已安装配置匹配的Clang，不为切换这个开关重新生成。

## 唯一新增的构建工作

新入口 `resume_native.py` 直接调用原 `build/emu-compile/VSimTop.mk` 的默认目标 `ROOT/build/emu`，只生成原生对象、PCH、归档和EMU。不运行Scala、Chisel、firtool、Verilator，不调用完整旧split executor，不更改官方程序或配置。

它借用现有 `build_recipe.probe_tools("split-clang-v2")`、`verilator_support`、`compiler_runtime` 的工具和运行库采证，并借用其显式编译/链接绑定方式；这不表示执行了旧 `split-clang-v2` 的完整多阶段合同。

原 `native-01` 在2026-11-06 04:10:52.074–04:11:03.173Z执行11.065秒，工具探测退出1，进程组已清理，未执行make或生成原生对象。实际 `verilator -V` 的compiled-in默认根仍是安装前的 `xiangshan-validation-20261013/tools/verilator-5.052/share/verilator`，Environment有效根是当前 `riscv-tools/verilator-5.052/share/verilator`。旧共享探测器要求两者唯一同根，因此拒绝；这不是工具缺失或RTL功能失败。

v2只在本叶入口选择 `-V` 的Environment有效根（为空时才用compiled-in默认根），并要求它与已冻结的 `VSimTop.mk` 根一致；保留完整 `-V` 输出、两个原根及有效根记录。原共享探测器、官方Verilator与Make规则均不改。原 `native-01` 的FAILED、源码快照和所有记录原样保留；新运行使用 `native-02`。

| 选择 | 本次规定 |
|---|---|
| CXX / CC | 实际已安装的clang++-19 / clang-19，保留C++ driver调用路径，另记其解析后的payload路径与SHA |
| LINK | 同一clang++-19，使用显式`--ld-path`绑定已探测的GNU链接器 |
| AR、make、bash、python、perl | 绑定实际路径、版本和SHA |
| 已配置PCH | 复用原`.gch`和`-include-pch`，不改Make文件 |
| VM_PARALLEL_BUILDS | 1 |
| OPT_FAST / OPT_SLOW | -O3 / -O0 |
| PGO_CFLAGS / PGO_LDFLAGS | 均为空 |
| CPU / make并发 | 拟CPU1,2,3 / -j3，以主端释放的具体窗口为准 |
| 墙钟保护 | 本窗口累计原生尝试预算不超过1800秒；native-01已耗11.065秒，新native-02使用1760秒，余量留给只读工具预检；覆盖工具采证、编译与最终身份检查 |

失败构建没有产生`.o`、`.a`或EMU。续接还要求`.gch`和`.pch`不存在；若发现任何此类残留则停止并保留证据，不自动删除或混用。

## 复用边界与证据

原失败构建在原生阶段报错后未执行最后的源身份收尾。因此续接前必须将实际完整硬件文件、递归依赖、候选八路径和原驱动文件重新对照 `build-01/inputs-before.json`。原HEAD与生产功能开关也须相同。

2026-11-06 04:01Z 已实际采集外部 `pre-native-freeze.json`：2014个生成文件、2018152258字节，以及原 `build-01` 的34个记录文件、3849919字节。该清单300998字节，SHA256为 `5f67b21a879e23e734683293ce5bfdd418559e5488e37b90bf17569d2196ff6d`。Windows可读副本在本轮独立验证目录，和WSL清单字节一致。

续编入口要求通过两个显式参数选择上述清单及完整SHA，核对所属源码/HEAD/生成目录/原失败目录，再把当前两个目录的完整文件集合与大小/SHA逐项对照。结束后要求这些原文件均未改变，且原失败记录目录没有增删。原C++、头文件、Make规则、FIR/RTL及旧time.log均保留。新GNU time输出、工具探测、执行命令、环境、源快照、内存采样和终态只写入新 `native-02`。现有生成Makefile仅向原生成目录添加原生产物及最终EMU。

新工具清单记录Clang编译器、C++链接驱动、链接器、归档器、动态实现库和Verilator支持文件，全部前后复核。原生成阶段的Java/Mill/Verilator/firtool等工具也继续与原工具清单一致。

新入口复用原进程组清理辅助，阶段开始、每30秒采样和结束均输出到原作业stdout；完整采样保存在新目录，不需要额外监控进程才能了解阶段状态。

只有C++编译/链接真实退出0、受控进程组不存在、EMU生成、原输入/失败记录和新工具身份稳定，才写 `DOT16_FULLCORE_BUILD_PASS`。该状态只表示新EMU可进入既定差分，`fullcore_difftest_qualified`仍为false。

## 执行与六例差分衔接

必须先得到具体资源窗口。示例：

```sh
python3 -B team/optimizations/o2/dot16/rtl-integration/fullcore/resume_native.py \
  --repo /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/checkout/source \
  --parent-build /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-fullcore-20261106-pro2/build-01 \
  --generation-freeze /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-fullcore-20261106-pro2/pre-native-freeze.json \
  --generation-freeze-sha256 5f67b21a879e23e734683293ce5bfdd418559e5488e37b90bf17569d2196ff6d \
  --output /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-fullcore-20261106-pro2/native-02 \
  --expected-head c981529dc6e493fb7deee8429b9ce05fd197497b \
  --cpus 1,2,3 --jobs 3 --budget-seconds 1760
```

成功后只把原 `smoke.py run` 的 `--build-record` 改指 `native-02`；镜像继续使用实际合格的 `image-01`，输出仍用尚未存在的 `smoke-01`。新`tools.json`采用原smoke要求的平面结构，ABI探针会使用实际EMU的Clang编译器。生成头仍须与新构建清单的SHA和大小绑定。固定feature1 reference、1400字节布局、六例次序、300000cycle/600秒上限与全部失败门保持原样，不增添矩阵或授予应用性能、G3、非法trap、PPA资格。

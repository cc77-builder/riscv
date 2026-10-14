# T12 第二轮可复核证据

原190计划与独立lean199计划各自完成，不把重复的功能输入加成389个唯一ISA用例。原始日志保留全部字符，仅以确定性gzip归档；`raw-metrics.json/csv` 保留每条窗口的四个64位计数、差值、顺序、输入hash及点积次数。没有最快样本筛选或空窗口扣除。绝对64位计数超过2^53，复核器使用Python整数保持精度。最终通过数量、源SHA和逐片退出码见 `matrix-summary.json`。

`archive-origins.json` 记录归档来源和原始字节hash；`SHA256SUMS` 可做文件完整性校验。它们是普通本地记录，不是防恶意伪造的签名证明。二进制、生成向量和大编译输出保存在工作区runs，未加入Git。`data/manifest.json` 只保存精确计划及生成输入hash；完整向量可由固定提交的生成器重建。

主证据目录：

- `matrix-190`：a4fea8f69f8c2c58f986858481257d3424a903f0，保留原190项、旧RVV和27条窗口。
- `matrix-199-lean`：8af7b21857ba2c65dbc4d835f7b2152cd6684875，完整重新执行同75组双路输入、13项stress/非法恢复，36条窗口包含新RAW链。
- `legacy-shard0-*`：旧117矩阵的本轮新编译原shard0；完成范围以checked.json为准。
- `diagnosis-*`：旧原镜像50k/90k限周期仍退休的对照及仅加阶段记录的最小完成；限周期exit0不计PASS。
- `fixed-minimal-*`：保持原80秒预算的三项完成对照。
- `historical`：只读复制旧initial、compact和四个timeout切片，不更改其未验收结论。
- `lean-reference-final`：固定NEMU参考层16,800双路组、75 known、75 batch；不是全核数据。
- `final-host`：28项Python测试、25项原C judge和98,321项精确逐位C检查；不是DUT数据。

在原本地工作区独立审计（实际重读BIN/ELF、生成文件、Git blobs、工具、原日志及进程回执）：

```bash
python3 -B repo/team/scripts/verify_t12_evidence.py --runs runs/matrix-190 --expected-source a4fea8f69f8c2c58f986858481257d3424a903f0 --complete --output /tmp/t12-original-audit.json
python3 -B repo/team/scripts/verify_t12_evidence.py --runs runs/matrix-199-lean --expected-source 8af7b21857ba2c65dbc4d835f7b2152cd6684875 --complete --output /tmp/t12-lean-audit.json
```

归档校验成功不能替代重新运行。以下是原本地布局下重新构建和运行lean首13项的命令（输出路径必须尚不存在）：

```bash
root=/home/lizufan/chatpc-workspaces/xiangshan-t12-20261014-r2
old=/home/lizufan/xiangshan-t10-t11-supervisor-20261013
rev=8af7b21857ba2c65dbc4d835f7b2152cd6684875
replay=$root/deps/t12-replay-8af
git clone --no-hardlinks "$root/repo" "$replay"
git -C "$replay" checkout --detach "$rev"
python3 -B "$replay/team/scripts/t12-tests.py" build --expected-source "$rev" --output "$root/runs/replay-lean-build-000" --am "$root/deps/nexus-am" --toolchain "$old/tools/ubuntu-root" --start 0 --count 13 --baseline lean --include-chain
python3 -B "$replay/team/scripts/t12-tests.py" run --expected-source "$rev" --output "$root/runs/replay-lean-run-000" --build "$root/runs/replay-lean-build-000" --emu "$old/repo/build/emu" --reference "$old/nemu-xs-tval/reference/build/riscv64-nemu-interpreter-so" --nemu "$old/nemu-xs-tval/reference" --flash "$old/runs/final-acceptance-20261013-2155/run-0/evidence/boot-flash.bin" --cycles 600000 --timeout 600
```

其余lean分片(start,count)为(13,50)、(63,50)、(113,50)、(163,36)，每片各用新build/run目录；原190使用a4fea8f提交、original且不加include-chain，末片(163,27)。重建需使用清单所列固定AM、便携工具链及已验收EMU/ref/flash；`tools/matrix.py` 与 `tools/matrix-lean.py` 保存本轮真实逐片build/run命令，但其绝对路径绑定本机布局。可用 `team/scripts/t12-tests.py --help` 按相同参数创建新输出目录，禁止覆写本证据。编译-j1、最多一个EMU。

功能PASS不等于实际观察到年轻vdot已发射后取消、ROB/FTQ索引绕回、共享WB冲突。计数器未校准，不宣称FU latency/Fmax/STA/PPA或候选融合完成。生产RTL、参考NEMU、flash、时钟与复位均未改。

固定资产路径与完整SHA256见 `preflight/assets.json`，AM固定086a238062fdfb3281b745a537b361983d0154b5；源/src树及build.sc已与EMU来源fcb16a8764d342339670df0bbf1bc67ef2028b86核同。各build的tools.json保存GCC11.4.0、binutils2.38、cc1/libgcc及便携动态库的实际hash，preflight/host-tools.json补充Python3.10.12、Make4.3、Git2.34.1与主机GCC。参考库1.1.0配置/来源完整校验保存在preflight/reference-verification.json.gz。

本目录.gitattributes对gzip明确禁用文本换行转换，提交前另逐blob核对暂存区与SHA256SUMS，防止上级team/** text规则改写压缩字节。

# C8延后归约独立宿主候选

当前资格见[结果](RESULT.md)，固定行为见[宿主合同](CONTRACT.md)。这是实验目录，未替换稳定C8。public/gemv.S/h可构建两个实验C入口；public/caller.c仅用于静态链接审计。

从完整香山仓库运行（选择全新且位于仓库外的输出目录）：

~~~bash
python3 -B team/optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-v1/verify.py \
  --output /home/riscv/riscv-lab/software-import-20261026/c8-deferred-host-reproduce-NEW
~~~

需要Python3.10+和GNU riscv64-linux-gnu工具。验证器只运行宿主Python与交叉编译/链接/反汇编，不启动EMU/NEMU；候选源码重生只作内存逐字校验，不覆盖已有gemv.S。已有输出拒绝覆盖，失败记录保留。
INPUTS.json绑定旧源码/445RTL/合同，旧模型和数据均只读；源码若漂移先处理身份，不能更新哈希凑通过。
generated API的返回CSR、输入输出容量、向量clobber详见合同。静态ELF/BIN夹具没有AM运行环境，不是可执行比赛程序；下一阶段按[探针合同](PROBE_CONTRACT.md)另构建实际应用。

evidence含三次宿主尝试；大文本采用gzip，其原文/存储SHA都在manifest中。不把文件封存校验等价于重新执行验证。

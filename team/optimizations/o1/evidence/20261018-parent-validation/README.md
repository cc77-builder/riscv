# O1 真实 VFEX4 父级验证证据 · 2026-10-18

正式运行 `parent-02` 在源码 `99d5f6c751234622b8f824ed7fcee39f3aae711d` 上通过；运行开始工作树干净，结束校验 427 个源码文件及 126 个依赖未变化。全部 117 项制品摘要已独立重算。完整范围、数字及边界见 [父级工程记录](../../parent/README.md)，机器回执见 [verification.json](verification.json)。本轮本地保存，未推送。

## 内容

- `parent-02/`：成功运行的逐字日志、33 项命令及退出码、工具版本、源码/依赖/制品摘要。7 项故障注入预期退出 1；其余 26 项命令退出 0，总 runner 退出 0。
- `parent-elab-01/`：首次适配器探索失败，CDE 每次查询重建 core 导致 backendParam 未绑定；保留当时源文件、调用与异常栈。
- `parent-elab-02/`：固定 core 对象后真实 elaboration 通过；尚未执行仿真，不算功能通过。
- `parent-01/`：源码 `517afab27e1bc021b7cc51b86a9bd7f567b7b926` 的正式尝试。elaboration 通过，但 firtool 输出为包含虚拟 FILE 分段的单文件，脚本因缺少独立资源清单退出 1，未启动 Verilator。
- 修复提交 `99d5f6c`：使用 Chisel stage 原生 `--split-verilog`，收集实际生成的 57 个 HDL 文件与资源清单；保留原始 ClockGate，不手写替代模块、不关闭其功能。新目录 `parent-02` 执行两模式及七项负控后通过。
- `post-validation-comment.patch/json`：封存验证后仅纠正测试源码注释。“T14 测试限制”不等于“已证明的上游合同”；非注释行逐行一致，没有改测试逻辑或重复硬件构建。
- `local-artifact-archive.json`：本地 ZIP 的大小与 SHA256；包含原运行文件、生成 RTL、两个 Linux x86_64 可执行文件、固定 TSV、受测测试源码及两笔提交补丁。大文件不放入 Git。
- `manifest.json`：本目录所有其他文件的大小和 SHA256，包含 `.gitattributes`，不包含自身。文本禁止 Git 换行转换，便于搬迁复核。

ClockGate 的模块体与原 utility inline 逐字一致，三门控实际实例化；选中 VPU 观测只向外读取。相对上次发布 `c3c417a`，生产 src 和依赖 gitlink 无改动。两模式的边界 valid 刺激不同、DIV 取消当拍旧 valid 与取消后门控开启现象均已披露。总周期不作性能对比，七项负控只是 C++ 观测值检错。未获得团队人工 ACK，本记录不代替成员评审。

原始 WSL 输出：`/home/riscv/riscv-lab/zjhwork2-review-20261018/runs/parent-02`。Windows 入口：`D:\yanyi\riscv大赛\doc\O1父级联调_20261018`。历史 FU 证据目录原字节保留。

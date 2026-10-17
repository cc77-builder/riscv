# 四项目统一 vdot 全核测试（本地实验）

本目录为 2026-10-17 新建的统一测试，不把公开项目原报告的数字当作本次实测。未上传 GitHub。

## 固定比较条件

- 基础处理器：香山 `16ae9ddcda54fc9a2fddffad73174cf793ac7814`，`MinimalConfig`，单核，VLEN=128；固定子模块、Verilator 5.052、同一编译器、相同编译选项。
- 用户实现：T14 `VDOT_T14_FUSED_INPUT=1` 的已封存 EMU；T15 的独立 INT16 扩展不参与本次 INT8 比较。复用二进制有原始源码、构建参数和 SHA256 记录。
- 公共任务：低八对 signed INT8 点积，结果为 low32，high96 全部清零。外部接口 `e8/m1/VL8/vstart0/vm1/tu/mu`；输入高64位包含非零填充值，不假定其为零。
- 公共项目保留本身的译码与数据通路；在同一基础版本下接入。仅公共计时 observer 为跨项目相同的非功能观察代码。Redoop 因原始代码版本较新，仅提取指令相关修改，并保留移植补丁。
- 四组使用同一 C 检查器、三组性能输入、循环数、寄存器分配和 RVV 基线。每个内核从4 KiB边界开始；链接脚本固定输入、golden、结果缓冲地址。实际 ELF 审计通过后才接受比较。

## 四个实现

| 实现 | 公共/本地版本 | 原生工作与适配 |
|---|---|---|
| 用户项目 | zjhwork 05e07de；生产性能来自 T14 封存版 | 一条指令完成 dot8/full128 契约 |
| [Jade](https://github.com/Jade0x13157A6/cie2026-xiangshan-vdot) | a17e38128e589d745152f3ef4b595b4572b22b3d | 一条指令完成同一契约 |
| [试水](https://github.com/vienna-0FFH/cie2026-shishui-vdot) | 4421d88beb39f8e95e23e25c78eaaaf1a7de4b52 | 一条指令完成同一契约 |
| [Redoop](https://github.com/redoop/xiangshan-vdot) | fba90f8eb0818ed9539aa097691b371fd852f7a1 | 原生是每32位lane做dot4累加；以7条软件序列完成统一dot8；batch4共享配置，共19条，全部计入周期 |

Redoop 的适配先在 e32/VL4 清零 scratch，执行原生指令，再清零目标，只归约前两个32位结果，最后恢复 e8/VL8。高两lane额外计算不进入结果。先读取输入再清零目标，支持目标与源别名。此结果只回答“完成统一 dot8 接口需要多少周期”，不能直接评价其原生16对乘加或 GEMM 性能。

## 验证与计时

1. 10,022 组原有定向和随机数据：独立 NEMU 参考验证，含寄存器别名、完整128位、非scratch寄存器与CSR检查。这个步骤本身不证明RTL通过。
2. 全核校准：空窗口、短整数运算、依赖除法及四种工作负载；实时 DiffTest、GOOD TRAP、UART结果和硬件计数事件同时校验。
3. 全核功能：22组定向+8组固定随机，每组比较自定义实现与共同RVV，检查完整寄存器状态、CSR及缓冲区哨兵。
4. 周期测试：single=1 dot；chain=256 dot；batch=32轮×4个独立dot=128 dot；stream=64 dot，含两次128位加载和一次128位存储。
5. 每种场景、每组输入运行6轮配对：第1轮保留为first，第2轮为warmup，后4轮measured；自定义/RVV顺序交替。报告中位数、范围、窗口cycles/dot与配对加速比，不只挑最小值。
6. `fence` 包围四次CSR读。CSR采样与ROB提交日志验证边界、ELF执行路径、退休指令数及每窗实际自定义指令数；不把 `rdcycle` 自身视为序列化指令。
7. 所有计时包括窗口固定开销及循环开销，不扣空循环。单次窗口不能称为功能单元固有延迟；batch的cycles/dot也不能直接称为硬件II。

完整模拟输出、命令、输入/EMU/NEMU/flash SHA256、生成源码与ELF均在本次工作区 `runs/`；补丁与版本说明在 `audit/`。第一轮 images-01 为布局审计前的预备构建，其运行结果不进入正式比较；正式使用 images-02。

## 执行入口

```bash
python3 -B campaign.py build --variant ours --output "$OUT/ours-images-02" --am "$AM"
# 其余 variant 为 jade、shishui、redoop，分别生成编码与必要适配。
python3 -B compare-images.py --runs "$OUT" --output "$OUT/image-identity.json"
python3 -B reference.py --variant ours --reference "$NEMU_SO" --output "$OUT/ours-reference"
python3 -B run-suite.py --variant ours --images "$OUT/ours-images-02"   --output "$OUT/ours-suite" --emu "$EMU" --reference "$NEMU_SO" --flash "$FLASH" --jobs 2
```

`run-suite.py` 必须先通过校准与功能门禁，才接受性能结果。计时来源为香山 RTL 仿真周期，NEMU只用于功能比对。各项目使用相同基线的独立NEMU，匹配各自指令语义。

## 解读边界

这是固定配置下的体系结构周期比较，不是赛事官方跑分，也不是最高可运行频率或芯片功耗比较。Jade和试水的组合逻辑路径可能影响实际频率；尚无同一工艺、约束下的STA/PPA数据，不据此宣称端到端物理性能排名。公开项目原数字使用其他基线、工作量或统计方法，另行保存为背景资料，不混入本表。

# dot16 真实 NEMU API 验证结果

2026-11-06 UTC。主端完成实际构建、执行、终态回读和证据复核；独立审查未发现本层资格阻塞。本记录不表示已启用默认实现。

## 结果

在固定 NEMU `a48a11f208ff81ad765591d83271d1b339fb3861` 上依次应用既有dot8 1.1.0和独立dot16候选补丁，已分别完成feature0、feature1的真实构建、归档、导出/链接检查，以及规定的M-mode状态注入API矩阵。既有8af reference先完成feature0 bootstrap。九个API进程包括三次正常执行和每态两项负控，全部取得预期结果并记录进程组已清空。

外层实际操作从2026-11-06 01:32:24.370Z开始，最后feature1 API于01:36:40.394Z结束；01:45:54Z完成只读post-audit。CPU0、make -j1、阶段顺序执行。此处时长仅为执行回执，不是性能数据。

## 配置与身份

两个新库使用相同固定源码，仅切换CUSTOM_VDOT16。共同开启RVV、旧dot8及其既有xTVAL profile、TVAL_EX_II、NMIE_INIT；关闭LIGHTQS、MDT_INIT和新CUSTOM_VDOT16_XS_TVAL。新平台策略尚未获得硬件资格，本轮未开启。

| 身份 | 库SHA-256 | 大小 |
| --- | --- | ---: |
| 旧reference bootstrap | `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9` | 原冻结库 |
| feature0 | `04af279b0fc5de1626b4fd11778c87a8f9384d94e7b26d982ea76db431fdb7b2` | 1,459,040字节 |
| feature1 | `cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae` | 1,463,176字节 |

实际API probe可执行文件SHA为 `ddddcf8885b8d45fc842518d69fac9f1a7be94a938799e37e54f3820b74c729a`，固定生成diffstate头SHA为 `6a2ce3ab51893908f74452522ab03c553cf7fa7e8aa25f74ea84d79aa45f044d`。实际导出ABI为1400字节，LIGHTQS关闭时regcpy为两参数；没有沿用旧三参C++声明。

## 实际验证

| 实际库 | dot8合法 | dot16合法 | 非法 | 普通冒烟 | 正常退出 |
| --- | ---: | ---: | ---: | --- | ---: |
| 旧reference | 1168 | — | 82 | addi/ebreak/vadd各1 | 0 |
| feature0 | 1168 | — | 82 | addi/ebreak/vadd各1 | 0 |
| feature1 | 1168 | 132240 | 50 | addi/ebreak/vadd各1 | 0 |

合法检查覆盖独立signed-byte/int64期望、16项源贡献、目的低32位与高96位清零、全部32个向量寄存器、目的/源重叠和四种vta/vma；保留GPR/FPR与相关CSR，检查VS Dirty。非法检查验证真实handler PC、mepc、cause、精确mtval与无部分写入。旧dot8仅VL非法的零mtval与新dot16关闭平台flag时的指令字mtval分别判定。

每态oracle负控只改变预期结果，均以full-vector-result错误、退出2拒绝；错feature身份负控亦均退出2，并分别由legal-pc或trap-pc拒绝。未改reference比较行为，未用环境错误代替负控。

## 证据与复现边界

原运行目录：`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-nemu-reference-20261106-0105`。两库和完整构建对象保留于各feature归档目录；旧reference未被替换。

原始[审查包](evidence/reference-api-v1/raw.zip)为388104字节，SHA为 `99eef701f03d62cc00a4ccb1a35095dd687bbdbab083e032d07ef237d6c3a0cd`，包括artifact-manifest和100个逐bytes/SHA核验成员。已落仓证据见 [`evidence/reference-api-v1/artifact-manifest.json`](evidence/reference-api-v1/artifact-manifest.json)；其中包含controls、各阶段state、原stdout/stderr、实际nemu.config/autoconf、源快照、post-audit及operation-receipts。源码控制身份以controls SHA `0834842dae2e35bfb76632e8c0d8a9f89fd7fcd1bcc522c8b6b39ede2baf78bb` 为准。

post-audit核对2507项源码/生成输入身份，旧reference仍为8af。-MMD未记录系统头，ldd-r仅证明当次链接解析成功，不能据此声称系统头/系统动态库的完整字节冻结。空flash路径提示保留在原日志中；本次RAM注入API不验证flash启动。

本结果授予固定候选的有界ISS/API验证范围，不授予新RTL、整核DiffTest、新平台dot16 xTVAL、完整应用周期或加速比资格。注入的保留位/vill等状态不全部属于正常程序可达状态；未验证trap handler恢复、全ISA或并发harts。硬件的FU、父级、译码和整核结果由各自合同记录，本报告不转移这些层级的资格。

## 复现入口与冻结身份

详细验收及执行参数见 [`API_CONTRACT.md`](API_CONTRACT.md)。`build_reference.py` 的 prepare 阶段要求固定主仓基点 `c981529dc6e493fb7deee8429b9ce05fd197497b`，并叠加本次四份控制文件；它有意拒绝任意新HEAD，不能直接把后续提交的工作树视为本轮冻结输入。现有运行目录 `inputs/` 保存全部实际控制字节，`controls.json` 保存其摘要。

复现应在已协调的版本隔离工作区还原该基点及同摘要控制文件，使用干净的固定NEMU donor、固定diffstate头和全新输出路径，按 prepare → legacy API → feature0 build/API → feature1 build/API 顺序运行。禁止覆盖已有阶段输出、修改旧reference或把后续控制器的运行归入本轮。两份新库及其完整构建输出仍保留在原运行目录，可直接按报告中的库SHA核验。

| 本轮控制文件 | SHA-256 |
| --- | --- |
| `API_CONTRACT.md` | `d5fff80674bbc16c676b5de606e8300c734a55ac77b020ac8c42ea5d53826518` |
| `build_reference.py` | `b1a3f301df0bfeb1d20907f88a16c46a9e05e82ee1f65056f9a01ea173f418f0` |
| `reference_api.cpp` | `23056586264f8aacff65ba7ab5ceca6f8e5fddf680da8dd3e731c2a5673a7012` |
| `run_reference_api.py` | `cf12d702279cb2a8dd2bc2f7ed019d3479cf3cc55ccdcfb64602b3493004e7c5` |

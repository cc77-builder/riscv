# FA 序列化差异的有限只读诊断

时间：2026-11-08 03:56:29Z–03:57:31Z（两次闭合只读计算的外层回执）。
身份：本团队性能微架构领域专家 74a9fc48e2804155921bcf0c39ada503。
来源：首席任务 98cf2ea1c4684d0d873dd8627ad0629a；成果消息 67dc26b0a01b482383de2c17f66ef3dc。
范围：首席已闭合的 local-01、serialization-01、input-serial-01；不修改原输入、原失败结果、主仓或官方程序，不启动 Yosys、ABC、STA、EMU。

## 结论与决策建议

本次原始图比较失败可以被一个完整、无碰撞的内部单元名称双射精确解释。它不是本诊断发现的端口元数据、单元参数、常量或实际连接改变。

原 mapped.json 的 6,150 个单元名映射到 reparsed.json：仅原来以美元符号开头的单元名增加一个字面反斜杠，其他名字不变。该映射覆盖双方全集且无碰撞。共改变 5,196 个名字，其中 3,518 个 $abc、1,678 个 $auto；954 个命名 FA 单元不变。映射集合 SHA256 为 9d8441a6457bb230eee9404f9c131e0c906aae00738ac2bb53d6ef49c04c41d7。

本诊断仅对回读设计的 cells 字典键应用该逆双射，再执行原 controller 的 need()/circuit() 原样函数。220 个顶层端口、6,150 个单元、10,729 个网、26,529 个端点严格相等，未删减任何比较字段。原图与逆重标号后的图 SHA256 同为 4bf4c350e4a464e4e875a4f32cb9b7e44f207f80b62bfe3fd0519de24ba32acd。未重标号的原始回读图 SHA256 为 e7756a07a3ed19c9e6585edffdf8e8d3977e437fa3dbaa26baf638ebe80fb31c。

因此，值得由首席判断是否对这个已有映射点做一次 STA 续接。最窄范围是：在新的续接合同与新输出中显式记录上述已验证的全集双射，并继续使用原严格图比较；复用已写出的 mapped.v，保持原库与时序约束，不重新映射、不重新综合、不修改官方程序、不把旧 FAILED 改写为 PASS。不应通过对所有字符串 lstrip、忽略 cell identity、删除常量或仅比较计数来放宽门禁。若新续接仍出现其他实际差异，停止并保留证据。

此结论仅说明两个被哈希绑定的已映射 JSON 在该内部名字双射下具有相同端点图。它不是 RTL-to-mapped 等价证明，不是 STA 解析成功或时序达标，不是整核/应用/PPA 资格。该诊断未读取或重新哈希 mapped.v 本体；后续 STA 应由执行者绑定实际输入文本及其现有产生/回读证据。

## 实际证据身份

- controller：input-serial-01/fa_serialization.py，13,071 B，82738e4ca6c0d84de04cb8a77e9143ab2d646bc025e087dddc3ff62a12109a8a
- 原图：local-01/mapped.json，7,063,807 B，7117718b7d29be886b948d70d7a0486a472f341e1ffcf1bec827728b8cc8f53c
- split 图：serialization-01/split.json，8,832,272 B，f391cf3a7185582c19ca11750c25124dceae0c09aa7190884df90e85c6fc2283
- 回读图：serialization-01/reparsed.json，7,664,463 B，dca75effeb69eccf2c406ba7436c607b82af36558465bfb491f2fa61fb416ce3
- 原失败：serialization-01/result.json，2,031 B，861ccfa472deb1e08057fa57bec36fe245bd4ebfdcf51f13767fb7c06bc19d8f

以上路径共同前缀：
/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main

原失败状态仍为 FAILED，错误为 ValueError('serialized Verilog changed complete circuit graph')。其中 splitnets-help、serialize、reparse 三个命令均 exit0/reaped/group_absent，流程在 STA 之前停止。诊断前后所有实际读取文件的 SHA 均一致。

## 严格比较的具体范围

circuit() 取自实际 controller，通过 AST 仅提取 need/circuit 两个函数；未 import 或调用其 main，也未执行 EDA 子进程。

端口比较保留名称、方向、宽度、offset、upto、signed 及端点位序。单元比较保留类型、参数、全部端口方向及宽度；每个引脚位均进入端点图。连线按端点集合比较，不要求 JSON bit ID 或内部线网别名相同。常量保留独立标签，实际有 0 常量网 119 个端点、1 常量网 2 个端点；没有删除常量或悬空端点。原函数对 memories/processes 和 init 属性的约束保持不变。

原图与 split 图未做任何名字重标号就严格相等。原图与回读图第一次原样比较：端口完全相同，单元类型直方图和所有计数相同，单元名字集合出现 5,196 对差异；954 个同名 FA 单元的元数据没有变化。第二次计算验证整个名字双射，并对逆映射后的完整图严格比较，结果相等。该判断不依赖抽样例子或单元数量推断。

## 执行与资源

1. 分类诊断 operation 0250d6044ba18f5fd71831ae3131d2ce.3ed6c74ea85bcf34aa806f8a19fbc246：
   03:56:29.1969427Z–03:56:30.5759005Z，host 1,332 ms，Python 0.538 s。
2. 名字双射与完整图验证 operation 0250d6044ba18f5fd71831ae3131d2ce.8f9bb1da2476559c309ef001f7a00d61：
   03:57:29.8964031Z–03:57:31.0439839Z，host 1,104 ms，Python 0.451 s。

二者均 CPU3、nice5、单线程、exit0、cleanup_complete=true、无取消/超时，未生成子 EDA 任务，原输入均未写入。申报资源为上述三个闭合输入目录的只读锁，没有主仓/Git 元数据访问。CPU3 计算已结束，不占用后续资源。本报告不额外声称独立 /proc 进程组核验；外层清理状态来自工具真实回执。

## 本目录文件

- REVIEW.md：本结论与适用边界。
- diagnose.py：第一次实际执行的只读分类程序。
- bijection.py：第二次实际执行的有限双射验证程序。
- diagnosis.json：第一次完整诊断输出。
- bijection.json：第二次完整验证输出。
- host-receipts.json：两次提案、执行回执、实际 PowerShell 入口及文件来源摘要。

原始失败目录与所有工程输入仍为权威原始证据；本目录是诊断入口，不替代原始记录。

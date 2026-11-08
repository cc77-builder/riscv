# 最终提交目录

```text
仓库根目录/
├─ README.md                       提交首页
├─ src/                            香山源码、vdot 数据通路和 FU 接入
├─ build.sc、Makefile、.gitmodules  原构建入口、固定子模块
├─ team/
│  ├─ models/、tests/、rtl/         参考模型、数据、检查器和 RTL 测试
│  ├─ scripts/                     原环境、NEMU、测试和运行工具
│  ├─ workloads/                   hello/vadd、vdot、RVV 基线与测试程序
│  ├─ patches/nemu/                当前 NEMU 补丁和 manifest
│  ├─ optimizations/               最终软件及构建所需辅助源码
│  └─ spec/vdot.md、versions.env   当前指令合同、依赖版本
└─ submission/
   ├─ REPRODUCE.md、reproduce.sh   统一复现入口
   ├─ reports/                    一套报告源码及三个阶段 PDF、合订本
   ├─ logs/                       全部保留日志、元数据、索引和读取工具
   ├─ docs/                       环境说明
   ├─ FINAL_VERSION.json           最终代码与配置身份
   ├─ MANIFEST.json、verify.py     当前交付文件校验
   ├─ tools/make_manifest.py       重新生成 MANIFEST.json
   └─ verification/              检查命令与日志
```

## 代码在哪里

| 内容 | 位置 |
| --- | --- |
| 生产 vdot 数据通路 | [VDotDatapath.scala](../src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala) |
| FU 两槽和控制 | [wrapper](../src/main/scala/xiangshan/backend/fu/wrapper/) |
| 译码接入 | [decode](../src/main/scala/xiangshan/backend/decode/) |
| NEMU 扩展 | [patches/nemu](../team/patches/nemu/) |
| 数学模型 | [models/vdot](../team/models/vdot/) |
| RVV 基线 | [rvv-baseline](../team/workloads/rvv-baseline/) |
| firstdot 库入口 | [Makefile / 头文件 / 示例](../team/optimizations/o2/r2-select/public/firstdot/) |
| C8 库入口 | [Makefile / 头文件 / 示例](../team/optimizations/o2/integration/firstdot-v2-0f/package/c8/public/) |
| C8 汇编及数据接口 | [public](../team/optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-c8-v2/public/) |

为保持原构建和 include 关系，源码路径不作大范围改名。`optimizations` 中只留下最终软件、构建目标引用的 harness 和当前 EMU 构建器，旧候选实验、旧报告及历史快照不在提交目录中。

三份阶段 PDF 是不同阶段的提交材料，合订本是同一套内容的便于查看版本，不是多个历史版本。

# 四项目统一 vdot 验证记录（2026-10-17）

任务编号：`UNIFIED-VDOT-20261017`。用户授权上传到 `cc77-builder/riscv:zjhwork`。

[结果报告](../../docs/unified-vdot-comparison-20261017.md) · [统一测试程序](../../workloads/unified-vdot/README.md) · [交付说明](../../docs/unified-vdot-publication-20261017.md)

`archive/` 是上一轮已验收 Windows 归档的逐字节副本，439 个清单条目均已核对 SHA256。其文件校验、验收记录、原始报告及历史状态原字节保留；其中“未上传/no_github_push”表示测试完成及归档时点，并非本次发布后的状态。提交本身不代表新增硬件运行或团队人工 ACK。

## 验证范围

- 四实现共64个全核镜像、860个已校验窗口；其中384个正式性能样本，16条汇总统计。
- 完整128位结果、实时DiffTest、GOOD TRAP、CSR计时边界及实际指令路径检查通过。
- 另有每实现10,022组NEMU参考功能检查；与全核RTL验证分别记录。
- 原始日志→suite样本→汇总样本→独立重算统计逐项一致，硬件源码封存检查通过。

## 归档入口

| 内容 | 路径 |
|---|---|
| 汇总、逐样本CSV与原始报告 | [archive/结果](archive/结果/) |
| 全部压缩UART/硬件观察日志、逐运行检查与运行依赖摘要 | [archive/验证证据](archive/验证证据/) |
| 公共来源版本、移植补丁、配置和RVV分母审计 | [archive/版本与适配审计](archive/版本与适配审计/) |
| 验收及样本/统计闭合回执 | [验收记录.json](archive/验收记录.json) |
| 439个文件的存储字节校验 | [文件校验.json](archive/文件校验.json) |
| 密封测试镜像、ELF与生成源码快照 | [测试镜像与构建快照.tar.gz](archive/测试镜像与构建快照.tar.gz) |
| 离线核对与重新执行的区别 | [复核说明.md](archive/复核说明.md) |

压缩日志的原始字节摘要保存在运行检查记录中；`文件校验.json`记录存储字节。大型EMU/NEMU/flash保留在原工作区，只归档其路径与SHA256。镜像快照是复核机器码和输入/黄金结果的必要证据，不含生成C++、对象、波形或构建缓存。

## 存储字节核对

从仓库根执行，仅需Python3标准库：

```bash
python3 -B - <<'PY'
import hashlib, json
from pathlib import Path
root = Path('team/evidence/unified-vdot-20261017/archive')
files = json.loads((root / '文件校验.json').read_text(encoding='utf-8'))['files']
for name, expected in files.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
print('UNIFIED_ARCHIVE_STORAGE_PASS', len(files))
PY
```

完整日志/ELF重验入口是 `check.verify`。原工作区中可按归档的 `archive-results.py` 预检流程重验；迁移后需解包镜像，并通过 `external` 参数提供记录的依赖摘要，具体边界见复核说明。只核对哈希不等于重跑RTL。Redoop包含dot8接口适配；本轮不提供统一工艺STA/Fmax/PPA或官方排名。

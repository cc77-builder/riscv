# O0/O1 整合验证证据

本轮验证及限制见[审查报告](../../docs/james-o1-integration-20261018.md)。全部历史输入归档保持原字节。

- `verification.json`：本轮最终检查清单；`host-validation.json`保留首次主机运行，包括已修复的诊断计数失败和Windows C编译失败。最终有效日志单列，不覆盖失败尝试。
- `hardware-source.tar.gz`、`hardware-source-binding.json`、`workspace-hardware-match.json`：实际FU编译源码、原快照与FuType补丁、436项当前编译输入一致性。`source-pack.json`绑定126个子模块；它是原51d7b1928快照，实际变更另外记录。
- `hardware-validation.tar.gz`：三次构建尝试与开关验证的日志、RTL、测试程序/向量；01缺rg，02Scala编译错误，03真实三模式FU通过。没有生成或运行真实父级/全核。`hardware-validation.json`记录工具版本和范围。
- `o0-current-recheck.json`、`unified-replay.json`、`t13-current-recheck.json`：加固后当前工具复算54次/648窗口、64镜像/860窗口、T13 126次/1404性能窗口及13校准窗口，所有接受结果保持一致。
- `functional-replay.json`、`performance-replay.json`：新增O0工具与当前解析器兼容；batch128更正为6次真实接受前取消和6次同拍抑制，738个同请求等待关联不变。
- `fullcore-archive-recheck.log`：旧冻结入口拒绝源码漂移的预期记录。`recheck-t13.py`使用独立固定归档与当前检查器重验T13，保存实际检查器/解析器身份；它没有声称重验全部旧T12或新硬件。
- `files.json`：本目录载荷的SHA256；它是完整性清单，真实性以已审阅Git版本为准。

复现当前O0检查：`python -OO -B team/optimizations/o0/recheck_matrix.py --output /new/directory`。
复现当前T13检查：`python -OO -B team/evidence/o1-integration-20261018/recheck-t13.py --output /new/directory`。
Windows添加`-X utf8`。输出目录必须不存在。旧O0逐源码复算使用b12a97b86，原严格入口不会接受当前安全修复后的不同检查器字节。

`run-hardware.sh`、`check-switches.sh`保留实际环境/命令，其缓存路径是本次记录；重跑须配置相同固定工具和依赖并选择新的输出目录。新增ripgrep只解包在项目缓存，不改系统安装；没有默认启用O1、推送远端或修改main。

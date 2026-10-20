# 最小修复独立只读复核

审查提交 079351c122e35b77c1a0e01a6c3b60d562eac1cd。本次仅读取仓库、已编译镜像和原记录，在本目录保存快照与主机检查；没有改 checkout、重建镜像或启动 EMU。

- core-02 的七项 driver 当前字节、提交字节、原 preflight SHA 全部一致；补充任务共用四项也未改变。
- 原 control 镜像仍为 45cdf2a6...，1208 提交、16 组、256 次 trial 的合同未改。旧失败 supplements-01 / recheck-01 保留；不能把其总体失败当最终通过。
- 新 diagnostic 镜像为 56915e3a...。前九 cases 完全一致；第十 case 仅六条 scalar li 常量改变。before、expected 完整寄存器、ops 和1158提交均不变。
- 实际 ELF 反汇编逐条解释 li/lui/addiw/xor，并结合独立 SEW 提取重放，确认18次 scalar提取后 AVL 正确，19次配置含最后 e8/VL8 恢复全部正确。第一次为 0x21 xor 41 = 8。
- fatal 门禁在 supplemental 原始流、workload 入口、离线原始流入口、portable 原始流入口拒绝 CRITICAL ERROR / double trap / PMA check failed；旧共享 O1 runtime_gate 未改。原 bit100 预期故障仍保留专门负控语义。
- 独立再次执行 final checkout 的7项fatal、10项supplement、6项transition host tests，共23项通过。主机检查不证明新镜像全核通过，最终必须等待 supplements-02 与严格 recheck-02。

细节见 review.json、minimal-source.diff、source/ 和 host-*.log。

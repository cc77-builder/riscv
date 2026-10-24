# bc9/e66 G3 补充验收 v1

以 `66f641747` 封存的本机原14项campaign和v5定向运行作为固定输入。
原核心功能、异常、F2v七项义务、dense独立覆盖、精确负控及同镜像正常恢复全部保留。
只允许同一bc9源码/e66 EMU、同一硬件pins、输入合同、正常NEMU和flash的v5补足PARTIAL_KILL。
负控的截断轨迹不贡献覆盖；v5必须同时通过全宽状态、CSR、真实槽身份及退休检查。

入口核验两个固定manifest、全部载荷与共享对象，再把原生输入逐字节绑定封存；
使用各自固定LF检出的原检查器，重新执行14项原流复算和v5检查。
旧入口预期退出1并保持`O2_G3_OFFLINE_RECHECK_INCOMPLETE`；只有缺项恰为PARTIAL_KILL、
核心/补充/恢复均通过，且v5真实目标通过，才产生新的`O2_G3_SUPPLEMENTED_RECHECK_PASS`。
旧合同、旧结果和原始运行目录均不修改；不能用本入口接受任意新硬件、语料或新分支。

```sh
python3 -B team/optimizations/o2/fullcore/g3_supplement/audit.py \
  --evidence /absolute/repository/team/evidence \
  --output /absolute/new-native-output
```

需原生Linux、原始来源路径仍在且内容正确、原依赖和Git对象完整；归档不是可迁移运行环境。
输出必须为受保护源码、证据和运行树以外的新绝对目录。只启动两个离线Python检查器，新增EMU为0。
本验收仅闭合该固定硬件的G3正确性及六项覆盖，不授予性能、PPA、T17、上游实现或默认采用资格。
O1/O2生产默认保持关闭。审查和实际结果记入现有整合报告与计分板。

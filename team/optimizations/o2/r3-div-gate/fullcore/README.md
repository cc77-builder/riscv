# R3 DIV关钟修复全核回归

新EMU、12项core、2项supplement及严格原文复算已通过。先读[结果与边界](RESULT.md)和[执行合同](CONTRACT.md)。
源码0f12df675378556670afd0dd2153f47fcb330610；EMU SHA256 2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8。
本轮仅本地验证，未推送GitHub；下一步是同镜像周期不退化与同约束综合STA。

本地原始工作根/home/riscv/riscv-lab/o2-r3-div-gate-fullcore-20261024，状态campaign-state.json；
交付状态在同级o2-r3-div-gate-fullcore-delivery-20261024/finish-state.json。
已完成输出不可覆盖或重复启动launch.py/finish.py，新运行须使用新目录与明确身份。
本轮存在执行暂停／墙钟长间隔，原进程继续运行，详情和证据见RESULT.md。

只读复算本批归档字节及轨迹：

~~~bash
python3 -B team/optimizations/o2/fullcore/portable.py \
  --archive team/optimizations/o2/r3-div-gate/fullcore/evidence/20261024-fullcore \
  --core-campaign core-01 --supplement-campaign supplements-01 \
  --output /tmp/r3-div-gate-portable-new.json
~~~

便携复算不执行EMU/NEMU，也不代替原Linux严格来源／架构复核。原始执行命令及返回码已封存。

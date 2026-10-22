# O3应用测试封存证据

O1/O2同镜像GEMV，四尺寸、三数据集、两计时口径、两软件版本及公平RVV对照。
56项合格作业（46项原通过复用、10项恢复补跑，另2项中断尝试保留）、1280校验窗口、768正式性能窗口和4项代表重放通过Linux严格重审。

- [工程结果及全部预定尺寸](files/runs/results-03/结果与工程记录.md)
- [配对比较CSV](files/runs/results-03/comparison.csv)
- [较快RVV对照](files/runs/results-03/best-rvv.csv)
- [原始日志重审](files/runs/results-03/verification.json)
- [测试合同](../../CONTRACT.md)

archive-manifest.json绑定每份原始/存储字节与压缩方式，archive-check.json只证明字节保真；功能/性能结论来自严格重审。原始失败和前期镜像均保留，编译objects排除。

Windows原生复算和实际退出码保存delivery/；复算不新跑EMU，也不重复Linux的工具/依赖来源审核。O4/O5/G5、Fmax/PPA、最终模式和人工ACK仍未完成，本轮不push，正式T16后置。

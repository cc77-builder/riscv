# T14 本地消融证据

入口：../../scripts/verify-t14-archive.py。原始日志无损 gzip 压缩，mtime=0。
fu/ 为两模式单元验证；t12/ 为候选全核回归；fullcore/ 为校准与固定镜像性能运行；ablation/ 为同镜像比较。
hardware-build/ 固定实际硬件源码、构建命令和 EMU 摘要；support/ 保留主机检查与结构审计。
编译镜像复用相邻 t13-performance-20261015；不重复打包构建缓存或大型模拟器。
离线复算只检查已保存的运行证据，不等于重新运行硬件。未经综合/STA，不能推导面积、Fmax 或功耗。

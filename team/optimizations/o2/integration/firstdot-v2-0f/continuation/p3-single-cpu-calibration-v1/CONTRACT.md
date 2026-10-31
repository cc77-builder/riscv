# P3单核亲和独立有界校准合同

本轮用户授权校准，生产仍为0f＋firstdot V2＋原C8。不改RTL、镜像、NEMU，不构建新核，不上传GitHub。R1宿主封存、V1失败及旧记录保持不变。

1. 冻结 execution.py、audit.py、run.py、test_execution.py、CONTRACT.md，以及全部直接Python文件；完整复用R1运行器和父级输入闭包。必须先通过宿主门禁再写排他INPUT_FREEZE，随后启动目标。每次启动前后检查物理哈希。
2. 仅CPU4，进程组含诊断shell/子进程最多4个OS线程；RSS合计12GiB、原始stdout+stderr合计2GiB。超限使用R1触发快照后回收整组，不豁免诊断。/proc轮询非硬实时，采样边界与回收开销分开记录。
3. 最多两个串行目标进程：bit100拒错300秒，通过完整日志/首条指令/退出码与资源收据后，才运行正常校准2400秒。各限100万guest，原生999984预留16拍；两项目标墙钟合计最多2700秒（清理开销单列）；无重试，失败即停。预检、封存与离线分析时间另记，不扩大目标运行额度。
4. 使用新目录独立运行CWD，constantin.txt/plusArgs按原字节复制并冻结；固定PATH=/usr/local/bin:/usr/bin:/bin。实际spike-dasm若不存在，记录真实缺失，保留运行时既有回退，不引入宿主占位程序。
5. 复用原probe.elf/bin、0f EMU和正常/bit100 NEMU，身份来自R1完整freeze；随机种子1，RAM128MB，OMP_NUM_THREADS=1。只更改原允许CPU4–7集合内的启动亲和为CPU4。
6. 墙钟或guest限额停止的正常校准标记INCOMPLETE，仅提供吞吐/进度/资源，不宣称完整数值、CSR/ABI或性能PASS。限额、日志不完整和负控失败全部保留。正式3% selector/重放不自动启动；7200秒必须依据本轮实测重新审查，缺上界仍HOLD。
7. 新运行状态排他创建；每次尝试先占用序号，再启动；不能重启已有campaign恢复/重试。R1进程监督器原字节复用，执行入口与审计代码全量纳入本轮冻结。
8. GitHub仅只读核实身份/Issue；未授权发布WORK。当前独立叶和CPU4不触碰Issue所载队友CPU0–2保护与输入。

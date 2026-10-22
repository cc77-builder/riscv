# O2 G3 调度与共享输出复核

提交：20e353dc17ae455d4ad2bb65b56c4d58797c6367。状态：SCHEDULING_AND_SHARED_OUTPUT_REVIEW_PASS。

保留最多两个 EMU：hello 完成后，negative→functional-0 仍严格串行，但与另一槽的独立分片并行。两个工作线程之间使用锁保护进度文件更新；负控环境变量仅写入对应子进程环境。

实际 Python threading.Event 主机测试 1 项通过（rc=0），原始 stdout、stderr、退出码和源码 SHA 保存在本目录。测试不启动 EMU。

共享输出复核：当前无波形/IPC 输出，数据库 dump 默认关闭且初始化立即返回，NEMU 不启用 nemu-hart 日志；各运行标准输出、错误流和结果文件写入各自目录，EMU/镜像/参考库共同只读。

旧 O1 全套约 213.9 分钟，累计任务约 343.8 分钟；前 74.5 分钟 hello、negative、functional-0 基本独占。新调度减少空槽，实际缩短多少需运行后确定。

没有 EMU 峰值 RSS/VmHWM 证据，因此不建议直接提高到四并发。current-memory.txt 只反映审阅时系统空闲内存，不代表仿真峰值。

本次没有修改硬件或运行工具，没有启动 EMU，没有改变测量条件，也不提供加速比结论。

# R3 DIV 取消关钟修复：全核验证合同

本轮承接局部G1/G2，新授权为全核构建与NEMU差分，先不上传GitHub。
基点4669c487；修复已保存为本地提交0f12df675378556670afd0dd2153f47fcb330610。
生产改动仅ExeUnit，五个父级测试文件同步固定。其他本地文档改动保留。

复用未修改的build_fullcore.py、run_suite.py、run_supplements.py、recheck.py。
MinimalConfig、单核、EMU_THREADS=1、O2=1、T14_FUSED=1、O1=0；
O2_TRACE=1、T13_TRACE=1，其他TRACE=0。Java12G、构建j2、最多2个EMU。
先验证固定输入和主机检查；原H1 build目录完整移存且校验EMU哈希，再新建build。
硬件、递归依赖、工具、配置、生成物、命令、返回码均记录；实际构建成功才启动回归。
正常NEMU efbed077、bit100负控9b3aecf3、flash及镜像沿原固定合同，启动前逐字节与来源核对。
旧固定负控已在本机找到且哈希匹配，无须替换锁或转借别的主机运行资格。

完整执行12项core和2项supplements：hello/vadd、8片功能/异常、负控、控制、dense及两项O2补充。
负控必须真实DiffTest捕获高位错误，再以同镜像正常参考恢复。117唯一case/124执行case。
正常完整128位结果、身份、异常、七项legacy控制、六项O2联合覆盖必须满足原门禁。
新EMU与原始日志通过Git绑定的原检查器独立复算后才宣布全核通过。
出现失败保留原目录、定位并仅重跑受影响阶段；不降低覆盖或把部分检查升格为PASS。

本轮不作公平A/B周期测量或综合STA，不宣告功耗/面积/频率收益、最终采用、人工ACK。
局部取消后零脉冲由前轮严格真实父级证据证明；全核回归用于验证修复未破坏整体正确性。
不发Issue评论、不修改他人独立T17/R5输入，不推送GitHub。

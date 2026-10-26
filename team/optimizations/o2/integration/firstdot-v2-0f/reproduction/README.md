# 当前组合与干净复现的对照

工具：compare_reproduction.py。44 项主机测试通过（0 skips）；仅工具测试，不代表干净复现已经完成。
初次 ELF 探针的字节转义错误、首次测试 fixture 缺 image_sha256 字段的失败保留在 review 记录。
真实两批构建/运行比较尚待执行。

工具分两次使用，输出分别用新的 JSON 路径：

1. 新建24个矩阵镜像与普通C镜像后，只传 --current-build、--clean-build、
   --current-c-build、--clean-c-build、--output：核对全部 BIN、ELF PT_LOAD 内容、地址、
   权限、入口与BSS大小。允许非加载调试段包含不同路径。通过仅表示程序字节相同。
2. 两批完整原文审计通过后，再加 --current-audit、--clean-audit、--current-run、
   --clean-run、--current-c-run、--clean-c-run：核对审计映射及归档封存，实际输入不得漂移；
   区分当前0f与独立干净构建身份，逐一比较32正常运行的768窗口（含first/warmup/重放）、
   cycles、instructions、原始计数与采样时刻，并比较普通C的96次实际输出。

每侧 raw audit 已分别要求全128位结果、CSR、NEMU差分、O2协议通过。本工具不替代这些检查。
EMU宿主二进制hash仅记录是否相同；目标程序加载字节必须相同。不得把不同镜像的均值相近
当成干净复现相等，也不得以主机执行耗时作为加速比。

示例测试：

    python3 -B -m unittest discover -s team/optimizations/o2/integration/firstdot-v2-0f/reproduction -v

真实路径及调用命令由本轮运行记录保存；本目录不携带大体积模拟器或缓存。

当前侧允许明确的续跑合同：矩阵34次实际启动/33完成、C4次实际启动/3完成；2次中断不计PASS。
clean侧仍要求无中断完整批次，不能用当前侧的续跑资格冒充新干净运行。对照仍为768全窗与96次实际C输出。

当前侧另明确支持v2-wall-clock-limited审计，并验证归档中的chronology证明；clean侧仍须标准无中断资格。全部24 BIN、PT_LOAD、768完整窗口与96实际C输出比较保持。55项主机检查通过，实际clean对照尚未开始。

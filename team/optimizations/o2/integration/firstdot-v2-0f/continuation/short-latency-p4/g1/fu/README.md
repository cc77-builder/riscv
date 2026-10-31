# P4-G1 独立 FU 验证入口

本目录与原 O2 测试分离，使用原真实 `GenerateVDotElasticFu` 顶层/IO。只在 `VDOT_P4_ONE_CYCLE=1` 下运行本 C++ 测试；默认0f应继续使用旧测试。旧顶层本身没有固定两拍假设，其 IO 保持不变。

## Oracle 与覆盖

- 冻结22组定向＋10000组随机向量，逐项比较全部128位；未改输入数据或manifest。
- 事务队列仅由独立计算的接受/取消/复位/输出事件更新。DUT 的 P/R/occupancy 只作为被检查的观察量，不反过来控制 oracle。
- 每笔保存输入身份、最早可见周期、接受时刻、directR和满槽旧P优先标签。尾项在旧头释放后仍须经过一拍提升屏障，不能在取消头的当拍输出。
- 连续10022笔全部验证最早响应1拍、10021个II1间隔。反压下不要求所有请求固定1拍。
- 保留混合非法、v0、反压输入噪声、ROB代际/接收顺序反向、逐槽与全取消、复位、20,000拍确定随机控制。新增显式满槽拒绝第三条和pop/move/push场景。
- 验证FU顶层公开的ROB、pdest、目标类、完整结果、exception、27位控制打包和两个perf字段。所有VPU/perf字段由真实父级测试的whole-bundle观察补充，不能把此FU顶层描述为暴露所有位。
- 任意前缀检查：接受=响应+取消+reset丢弃+在途，在途最多2；完整输出及身份逐拍稳定。

九类注入：identity、wen、high、cancel、directRidentity、priority、zerolatency、fullaccept、resetdouble。均修改C++捕获的观察值以验证checker，**不是RTL故障容错测试**。每个负控必须实际命中独立条件，打印指定trigger/tick，立即被相应检查拒绝；不接受未触发、错误异常、重复、逃逸或只有PASS字符串。

## 命令

根Agent负责生成/构建，不能并行改共享生成器。新测试链接至真实P4 FU，二进制接受下列参数：

    <VVDotElasticFuTestTop> <frozen-vectors.tsv>
    <VVDotElasticFuTestTop> <frozen-vectors.tsv> <fault>
    python3 -B check_negative.py --positive --return-code 0 --log <result.log>
    python3 -B check_negative.py --fault <fault> --return-code 1 --log <inject.log>
    python3 -B -m unittest discover -s <this-directory> -p test_negative.py -v

`test_negative.py` 的正向字符串仅为解析器人工fixture，不是DUT结果。准备阶段没有构建或运行RTL，真实资格由根Agent的新运行给出。

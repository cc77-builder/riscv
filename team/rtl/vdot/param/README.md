# T15 参数化算术与独立测试包装

VDotParam.scala 包含参数校验、逐 lane 有符号乘法、逐层扩位归约和单请求实验包装。GenerateVDotParam.scala 在基本配置中同时实例化未经修改的生产 VDotDatapath，用相同输入交叉比较组合结果；扩展配置没有生产 ISA 对应物。

ParamPipe 的 E0 锁存乘积及测试 tag、E1 锁存结果、E2 响应，最小接受间隔 3 拍。响应未接受期间保持结果和 tag，flush/reset 优先阻止输出并取消事务。该接口只用于本实验；32 位 tag 不是 ROB 指针，flush 不是香山重定向/精确异常的完整实现。新配置未接入原 FU。

```bash
python3 -B team/scripts/check-vdot-param.py --output /tmp/t15-unit-new
python3 -B team/scripts/verify-t15.py --run /tmp/t15-unit-new --output /tmp/t15-recheck-new.json
```

完整构建需要已有 Linux/WSL 开发环境和与基线相同的依赖；输出目录不可复用，正式运行要求先提交源码。只需运行原始证据的离线复核时，见 [证据入口](../../../evidence/t15-parameters-20261017/README.md)。

C++ 测试逐条比较全部 128 位组合与寄存结果，测试各种 stall 下输入改变、取消/复位落在第 1/2/5 拍及 10000 周期固定随机控制；事务守恒和 tag 绑定逐周期检查。结果位 0/33/63/127 与 tag 的读回错误注入必须失败；这证明检查器能检出受控错误，不表示实际 RTL 曾存在这些错误。

周期由相同实验包装测得，不代表全核指令延迟。两个配置的乘法输入位宽、归约宽度及寄存器声明见 [报告](../../../docs/t15-parameter-extension.md)；没有综合/STA，不从算子数推断面积、功耗或频率。

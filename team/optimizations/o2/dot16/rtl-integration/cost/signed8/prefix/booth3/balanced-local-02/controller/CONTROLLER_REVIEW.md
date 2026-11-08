# Booth3 balanced-02：独立控制器审查

**未发现阻止这一新合同、单次Gold配方尝试的静态问题。** 本审查只核结合顺序、控制器派生、输入边界及预算；没有执行EDA或扩大源码数学测试，不预言本次SAT成功。

## 身份与完整派生

- controller/booth3.py：51,820 B / `9ced0b6414e37af9369e7ae5793f3dc8d1b6cb0f6a2f3e38c003c36f688e7bcd`。
- controller/controller-derivation.json：6,510 B / `ada7b1c636c9a2c8c8913a42a502ec40128af575eb944efea2ecb56252eaef71`。
- derive_controller.py：7,644 B / `f42baf35445d32535f63063d09dd624cdde79e436c192db422c38cc63509d93e`。
- BOOTH_CONTRACT.md：4,823 B / `be1bb568849c8d431c9df82b6fac4885d55865cc7bd5a657b9c535211631960c`。

18项编辑在内存中正向精确生成当前控制器，逆向精确恢复原49,573 B / bcde44c580003a0a99e18cc30a2795a9c7a9af08ed56ef38a8f740987ec8241f；重新计算的diff与controller.diff完全一致。两Scala、P checker、source派生/diff及verifier派生均与原候选逐字相同，DUT/source/checker没有伴随改动。wrapper_binding、check、command、interrupt的AST也与父版完全一致。

## Gold宽度与证明门禁

R20唯一算术变更为`(a0+a1+a2)+(a3+a4+a5)`。六个输入仍分别为独立unsigned20位，输出仍为完整20位；加法结合顺序不改变总和模2^20，无需假设各组和不溢出。该Gold仍使用行为加法，没有复制DUT的CSA/prefix实现，也未增加assume、偏置输入域、范围限制或省略输出位。R19仍为`a0+a1+a2`。

Gate继续逐端口连接本次真实DUT；模块头与3/6输入位宽必须精确匹配。miter及solver选项保持，SAT30秒、命令60秒，每项要求rc0、唯一SUCCESS、无反例和ERROR。两项新PASS之前不会启动FU/cost；超时、错误和UNKNOWN都不能通过门禁，失败路径不重试。旧R19 PASS也没有直接填入新列表。

## 原失败与新输入边界

控制器固定核对原FAILED结果SHA `7eb958143cc41f98cad195e0e7089b8924f827af340c51abca18ba573174d050`和R20 timeout日志SHA `957987acdcf4a9a90f8762444b0bad0c65b4618b19cf7e563201fb99094486a8`，要求原八个命令均已回收、没有FU/cost、R19 PASS而R20 FAILED且非反例。旧结果和日志只读并复制到新快照，不改写旧状态。

旧result列出的全部生成SV先纳入原始pins；新生成的DUT/public-top SV必须逐文件匹配其完整SHA。唯一不作旧字节相等要求的extern_modules.sv，仍受原精确producer header加两条模块注释的两种顺序约束，没有允许逻辑变化。新实际DUT还保留四套文件/resource闭包、cost/FU对应R模块相等及原wrapper绑定。

source-derivation继续按原source合同及202bc499…身份核验，未伪造一次新RTL派生。旧失败、旧SV、新Gold/Gate/脚本/日志和其余生成物进入各自原始或生成pins，最终按原路径复核。previous-failed被加入输出隔离检查；输出必须不存在且与所有输入树互不包含。input-02/local-02及外层启动回执由主端固定，本审查没有访问本机目录。

## 次数、预算与资格

新结果明确proof_formulation_attempt=2、prior_run_remains_failed=true；两项新miter均retried=true，并记录原合同及实际gold_expression，不伪称第一次尝试。R20配方变化与DUT未变分别标明，没有自动换配方或重放旧operation的循环。

控制器只接受CPU2和300秒，从run入口设绝对总截止。命令启动前固定截止，SAT/FU/cost共享这一预算；最终成功落盘后再核deadline/信号，越界重写FAILED。清理、reap及失败保存仍执行。原1200秒默认和验收值已同时改为300秒；合同外层360秒由主端启动器落实。

完整流程完成前不授予新的FU/cost资格；旧FAILED不会因无反例变为PASS。生产默认、parent/core/application及物理PPA边界不变。若此配方仍超时，合同要求停止P3分支，没有新增超时、第三配方或扫描授权。

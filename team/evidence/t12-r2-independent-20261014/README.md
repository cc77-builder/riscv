> 整合更新：本机`e5d084bbdcfad6936ccad29dff4c1df00f5abfef`及其全部审查历史已保留。该提交中的gzip曾被上级文本规则转换，未能匹配原`archive.json`；本次从两份相同的本机原包恢复，SHA256重新匹配原声明`8916a64dc4bf2c21e1c772f4d927f338ecb4ec2a290019e423ca5b2c64d03a96`，全部738个文本文件通过清单核验，新增`.gitattributes`保护。旧坏blob、原清单及失败回执保留，详见[整合报告](../../docs/t12-zufan-integration-20261014.md)。以下正文、展示报告及包内历史结论均不回填为后继运行。

# T12 第二轮独立审查与可复现实验证据

本目录保留 Astra/Max 独立审查产物及主审另一次独立复跑回执。审查固定对象是 b8272f2e8a62557437869c936b6ea9ce5fff84fe，不能把旧版本上的发现直接当成后继实现仍然存在的 bug。

## 内容与复现

- EARLY_TIMING_REVIEW.md：真实输入寄存边界、共享busy、clockgate/operand-isolation风险、晋升前STA清单。
- RVV_BASELINE_REVIEW.md：参考层真实汇编、32768寄存器组合、2016边界/状态、1000随机、328旧序列和2种batch。独立短版8/6/15条；主实现后继的7/5/14条是另一个经过独立测试的实现，不混称同一序列。
- TIMEOUT_REVIEW.md：原四片超时、C格式化与短参考执行、计数器与来源绑定反例、循环和恢复前快照覆盖缺口。
- review-findings.json / review-final.json：原始机器回执，不改写审查者当时不知道的后继运行状态。
- parent-replay-phase1/2.json：主审从独立副本重新执行全部6个短参考/反例/结构检查的命令与退出码，全部exit0；不是额外全核或物理时序执行。

`independent-review-text.tar.gz` 是可复现文本证据包。先核对 archive.json 的 SHA256，再解压；内部 ARCHIVE_MANIFEST.json 列出每个文件的精确 SHA256，主审已重新读取全部成员逐一核验。它保留固定源、实际汇编文本、原始日志、JSON与脚本，省略15个可再生二进制/缓存文件；清单见 archive.json。未分发参考共享库或工具链，需要使用回执中相同哈希的本机资产。目录中展示版Markdown引用的相对路径在包内目录有效。

```bash
sha256sum independent-review-text.tar.gz
mkdir review-check && tar -xzf independent-review-text.tar.gz -C review-check
cd review-check/independent-review
# 本机原参考库是外部依赖，不在文本归档中；其他环境替换路径但必须匹配哈希。
REF=/home/lizufan/xiangshan-t10-t11-supervisor-20261013/nemu-xs-tval/reference/build/riscv64-nemu-interpreter-so
printf '%s  %s\n' e5f04192ad782581eef8cd17648933aa6da0fd0543944cb6e59eb931efc60cae "$REF" | sha256sum -c -
cp --no-clobber "$REF" evidence/reference.so
python3 -B scripts/run_validation.py
```

运行会在解压后的目录生成编译输出，禁止直接在历史冻结目录重跑。脚本使用固定本机路径，迁移时须显式确认同一源码与二进制哈希，不能用另一参考模型代替。

## 必须保留的结论边界

这是前期时序/微架构与参考ISA审查，不是实际STA、候选RTL或全核性能验收。库/PVT/时钟约束尚未确定，没有面积/Fmax/功耗数字，不晋升输入级融合。独立审查当时无法在它读到的旧本地对象库解析原Draft f8e8276，主审已在独立发布库读取并合并该历史；不篡改原回执伪称审查者读过它。

后继主实现 a4fea8f 已修复测试框架运行成本，8af7b21 又加入循环次数、恢复前全32寄存器快照、64位计数器和精确退休跨度校验。最终处理状态应以本轮最终交付报告为准；本目录保留原反例用于防止回归，不将旧合成反例当新DUT失败。

主审另外从归档解压到全新目录，仅补入上述哈希匹配的外部参考库，运行完整 run_validation.py 真实 exit0，回执见 archive-replay.json；不是依赖旧解压目录的表面复现。

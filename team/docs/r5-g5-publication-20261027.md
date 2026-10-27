# R5/G5、C8及版本三指标资料发布到zjhwork

发布操作ID：20261027-cc77-builder-publish-r5-g5；执行者：@cc77-builder / Agent。用户本轮明确授权上传到 `cc77-builder/riscv:zjhwork`。本记录随发布提交保存；实际完成以远端分支回读与本机命令回执为准，不用历史报告中的“未上传”状态覆盖本次发布。

## 发布内容与版本身份

- 生产硬件：`0f12df675378556670afd0dd2153f47fcb330610`，O2两槽＋H1低32位保存＋DIV取消关钟修复；本次没有修改生产RTL。
- 已有集成提交：`c823a8786e052c6e26f6915563c42b6d730dd8e3`，包含firstdot V2及当前硬件复现工具。
- 当前提交补齐：clean-02完成记录、配置复用扩展、8×32普通C验证、C8最小包与最终镜像等价、R5/G5验收材料，以及29条版本数据档案和三指标对照。
- C1/C2/C3及其他未采用实验保留在实验/证据目录，生产源码仍为0f。它们的全核加速比写NOT_TESTED，不能当作当前硬件或当前已通过的整核版本。
- 原R5冻结仍绑定c823a基点加freeze.json文件清单；新发布提交还包含冻结之后形成的版本对照及发布元数据。不要只用当前HEAD冒充当时受测身份。

## 三项主要指标

| 指标 | 当前保留实测 | 条件与证据 |
| --- | --- | --- |
| 批量点积加速比 | RVV 678 / vdot 221 cycles，3.067873× | 原固定batch128微基准，[0f周期与成本](../optimizations/o2/r3-div-gate/PERFORMANCE_COST_RESULT.md) |
| 8×32 GEMV加速比 | RVV 299 / C8候选273 cycles，1.095238× | 同轮最快合格RVV，3数据集×4正式样本，[配置复用扩展](../optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-expanded-v1/RESULT.md) |
| 面积 | FU 17298.246μm²；父级284614.946μm² | Nangate45标准单元面积；两个边界有包含关系，不能相加 |
| 时序 | nominal父级r2r到达3.261218ns；已报告路径最差slack −2.393998ns | 1ns/5fF布局前参考STA；1ns未收敛，不是整核Fmax |

全部版本的比较条件、未测项及五档STA见[详细版本表](version-comparison-r5-g5-20261027.md)和[配套JSON](version-comparison-r5-g5-20261027.json)；永久实测档案保留[29条原记录](version-data-ledger.md)。本次发布没有新性能或PPA测量。

## 代码与使用入口

- [工程路线](development-route-current.md)、[开发计分板](../../开发计分板.md)。
- [R5/G5使用、冻结与验收入口](../optimizations/o2/integration/firstdot-v2-0f/acceptance/README.md)。
- [C8构建与使用](../optimizations/o2/integration/firstdot-v2-0f/package/c8/README.md)、[C8调用合同](../optimizations/o2/integration/firstdot-v2-0f/package/c8/CONTRACT.md)。
- [普通C最终接入及重建](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/README.md)。
- [干净复现完成记录](../optimizations/o2/integration/firstdot-v2-0f/continuation/clean02-final/README.md)。

从GitHub取得本分支：

~~~bash
git clone --branch zjhwork https://github.com/cc77-builder/riscv.git
cd riscv
git log -3 --oneline
~~~

私有仓库需要成员已有访问权限；构建依赖、子库和工具仍按环境/clean清单恢复。历史验收工具按对应冻结身份和显式路径使用，不把新提交的Git名称替换进旧锁。

## 发布前检查与封存字节

发布前逐项验证R5的24,157文件原冻结清单，无差异；运行模型检查35项和5份生成数据一致性通过。既有R5全核/差分/审计、C8最终镜像与成本资料按原身份保留，本次不重跑EMU或EDA。

为使Git提交和后续检出保留封存gzip、ELF及原始文本字节，本次在根 `.gitattributes` 补充0f/C1/C2/C3及当前集成证据目录的 `-text -whitespace` 规则。**这是发布元数据差异**；原freeze.json中的根属性文件哈希保留原值，原快照不被改写。除这项声明与原已排除的导航资料外，不改变已冻结源与证据。提交前另检查Git index blob与工作树输入逐字节一致，并按受控目录验证归档manifest。

仓库包含复现所需测试源及封存证据；EMU/NEMU可执行文件、大型工作树恢复tar、构建缓存和波形保留在本机。封存manifest所需的小型测试ELF属于证据，不是完整硬件构建输出。

原clean-02墙钟失败、C1/C2/C3否决、1ns负slack、功耗/整核Fmax未测和非目标尺寸未决均保留；发布不扩大这些项目的验证资格。

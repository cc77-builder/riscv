# 下一轮：R4-R1 注解侧文件收口

开始第19项构建入口R4-R1：仅修复独立导出工具重复生成的注解侧文件，保留FIR内完整注解和所有原附属文件。复用R4默认小样的逐字节一致证据，完成修订后的闭包及PrintControl检查；全部准入后冻结完整入口，执行一次3600秒总预算、16GiB有界构建。保留原FAIL，失败即停、不重试、不加时；不运行EMU/NEMU、不改生产RTL或软件镜像、不做EDA、不切默认、不上传GitHub。

## 最小修订已定位

本轮不是FIR、SV内容不等价：原10个RTL目录文件和6个尾部文件全部逐字节一致。唯一多出的ClosureTop.anno.json为722字节，包含与FIR内完全相同的5条注解。失败后没有运行disable-all小样，没有启动全核构建。

本地WriteOutputAnnotations字节码确认：移除CircuitSerializationAnnotation后，没有WriteableCircuitAnnotation接收内嵌注解；原隐式OutputAnnotationFileAnnotation仍在，因此Stage尾部额外写出独立JSON。下一轮只在ExportStage完成完整FIR序列化之后，抑制这一隐式侧文件输出请求（firrtl.options.OutputAnnotationFileAnnotation）。不要丢弃FIR内注解、删除黑盒资源或在检查器中忽略差异。

冻结Make参数没有显式--output-annotation-file请求；独立firtool的-output-annotation-file circt.anno.json是另一个阶段的原参数，必须保持，不能混淆。其余ArgParser、原阶段变换、CustomFileEmission处理、FileRegisters和Make后处理不变。

新身份修订保留本轮源码/锁/FAIL。复用本轮默认FIR/原10文件内容一致证据；执行最少必要的修订闭包检查及尚未执行的disable-all路径。全部通过才补齐独立完整源码副本、Make适配器、执行冻结和原资源监督，串行运行一次3600秒构建（总预算，不分阶段重置）。若再次失败立即停止。

正式验收19/20，稳定版0f＋firstdot V2＋原C8。没有新EMU或可恢复构建进程。后续目标诊断仍须单独授权。

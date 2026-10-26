# firstdot V2 当前静态包验证

工具verify_package.py按显式--repo/--package/--matrix/--output运行，输出须全新且与输入不重叠；限单CPU，不启动EMU/NEMU，也不修改源码输入。

run-01已实际通过，exit0。完整命令与外层日志见run-01.command.json、run-01.stdout.log/stderr.log；每个GNU命令独立保留argv/cwd/时间/exit/stdout/stderr哈希。工具、源代码、导入清单、包与矩阵输入身份在run-01/tools.json和inputs.json。

通过内容：
- 包内两个头与导入源逐字节相同；公开源manifest的S/h哈希相同；45件导入源重新核验。
- 独立真实汇编重建完整gemv.o，27416字节，b65d4ca4faf3550ad2e95d3fb7d1d452923b71ae50776420bfcd679d098238af。
- .a恰好gemv.o成员，成员完整字节等于独立对象及包旁对象；恰好16个有尺寸代码符号，无xs_gemv运行时wrapper符号。
- 12个当前firstdot矩阵对象，每形状3数据集，48次leaf机器码逐字节相同；每个矩阵构建重跑原g.verify_build。
- 默认/显式0/显式1三模式，各8个宏别名；真实编译caller对象、链接对象与显式目标函数调用完整字节相同，nm未解析为空。
- 默认三个整形状走firstdot/reuse/vdot、K13走RVV；强制模式/显式_rvv均走RVV。
- 脱离仓库布局搬移SDK后，真实编译并链接原example.c。
- 10项负控：非法宏2/-1/(1)/true；错误4x8默认别名；错误K13选择；有效ELF内的机器码篡改后重打包；错库链接仍有未解析；缺公共头；V1先于V2包含拒绝。V2先于V1保持V2检查通过。
- 所有负控只修改新输出目录的副本。输入前后SHA一致。

边界：
本结果仅静态包/调用别名/当前矩阵构建对象一致性。当前矩阵、普通C运行资格标记均为false，待主任务的真实EMU结果另行绑定。未把历史T17或firstdot PASS换成当前硬件资格，也未改默认选择。
工具可复制到主仓库integration/firstdot-v2-0f/package/子目录；无需修改被冻结combination.py/current_hardware.py/CONTRACT/import-manifest。

运行范例：
python3 -B verify_package.py --repo /path/to/repo --package /path/to/package --matrix /path/to/matrix-build --output /path/to/new-output

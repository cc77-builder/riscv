# C8 接回既有普通 C 程序

当前结果见 [RESULT.md](RESULT.md)，等价判据见 [CONTRACT.md](CONTRACT.md)。

这里只改变普通C夹具的包含头、8×32两入口的6个表项别名及链接对象来源；测试数据、48项次序、校验和观察器合同不变。`source/`保留真实已构建的最小适配源码，原冻结源码及运行仍在原位置。

## 重建接入程序

先使用已验收的C8 SDK及同身份AM/klib库，并设置实际路径。`OUT`使用新的外部目录；不运行clean，不改旧输出。

~~~bash
export AM_HOME="/absolute/path/to/qualified/nexus-am"
export LINUX_GNU_TOOLCHAIN=1
SDK="/absolute/path/to/qualified/c8-sdk"
SRC="/absolute/path/to/relink/source"
OUT="/absolute/path/to/fresh-relink-build"
mkdir "$OUT"
make --trace -C "$SRC" ARCH=riscv64-xs MARCH=rv64gcv \
  CROSS_COMPILE=/usr/bin/riscv64-linux-gnu- C8_SDK="$SDK" \
  R4_OBJ_ROOT="$OUT/objects" BINARY="$OUT/vdot-perf" \
  R4_LINK_MAP="$OUT/link.map" -o am -o klib -j1 image
~~~

`-o am -o klib`复用固定库，不写共享AM构建目录。改变工具链、AM库、选用宏或数据后，不能直接继承当前等价结论。该source镜像仅验证缺省C8选择；强制RVV的包级编译资格不能代替改变了调用表的整程序资格。

## 完整核验

以下integrate.py在完整源码仓库的本目录运行；程序与镜像压缩包不替代完整验证仓库及原运行输入。

脚本读取当前完整物理输入及封存运行；不是跨机器原文档案搬移器。使用固定角色对应路径，输出必须全新、与所有输入分离：

~~~bash
python3 -B integrate.py \
  --repo "$REPO" --identity "$CURRENT_IDENTITY" \
  --matrix "$QUALIFIED_MATRIX" --c8 "$QUALIFIED_C8_RUN" \
  --package "$QUALIFIED_C8_PACKAGE_RUN" --output "$FRESH_OUTPUT"
~~~

实际参数、工具SHA、起止及退出码保存在`evidence/pipeline.command.json`。脚本检查完整输入闭包及已复审原文的封存树，然后真实构建复制对照与SDK接入版本，比较最终可执行内容并做7项负控。它不会自动启动EMU；出现差异即保存失败，由开发者判断缺陷或合法新行为，再按用户授权补全核。

正常运行的`report.json`只有在完整装载内容、BIN、入口、表项和输入计划一致后才允许明确复用第26条原运行。不得把只比较叶代码或只看PASS字段当作同镜像证明。补充证据以GNU objcopy --strip-debug独立验证三份完整ELF去调试后相同，原ELF保持。

源工具已通过实际ELF代码/调用表/入口/BSS/ISA属性负控、输入计划负控、真实GNU错库拒绝，以及仅改调试字节的正控；不启动相同镜像的重复仿真。

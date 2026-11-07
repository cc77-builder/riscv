# whole2 Q288 原始证据 v1

`raw.zip` 保存完成运行的全部70份文件（9,180,763B），含独立输入快照、GNU source/object/ELF/BIN、preflight、原始stdout/stderr、status/checks、分析结果；另含原ChatPC宿主回执和内嵌manifest，共72个ZIP成员。没有删除原件或重新执行guest。

- ZIP 3,768,978B，SHA256 `7f2d3f732c98a394318c1dd0eacf4f10e344bda1f10e97f44421121e09694d65`。
- manifest SHA256 `748c46f7a3d39f06d159dd0101b0fd4849c852f3e3450ca00a7060dc9cd5dd3f`。
- external-operations SHA256 `b9147127a8455a2baaa89418767c70dcdd6df2185ec7b41913db08df48d271d6`。
- 归档操作 `49cbde030e5643f0cccfca5cec8a79c1.00a2767a9ddd64c78b5f5ded05199220`，2026-11-07 09:47:54.503929Z–09:47:56.1820712Z，exit0、cleanup_complete=true。

解压后按manifest逐文件核对；`files/preflight-01/profile.json`记录全部81个实际输入和外部依赖身份。外部EMU、feature1 NEMU、flash及编译库不因归档获得独立重建资格，使用前仍须核实实际路径和SHA。原调用命令在GNU commands、target status和宿主回执中。新运行须使用新的输出、冻结profile及资源协调，不覆盖本案。

结论入口为父目录RESULT.md/REFERENCE.json。本案仅有固定完整Q288调用资格，不提供完整应用、formal-performance、完整退休或ASIC PPA结论。

# P1实施边界

本包按相邻split-input-p0/CONTRACT.md及MEASUREMENT_PLAN.json实施。用户本轮授权本地实现、构建、steady-d0探针及仅在门槛通过后的扩展，不上传GitHub。

工作区唯一新叶为本目录，生产RTL/旧C8/default/供体与P0均不修改。运行输出使用独立SOFTWARE_IMPORT_ROOT/p1-split-input-20261028-01。主Agent负责运行监督、统计与归档；并行子任务独立文件所有权，完成后交叉复核。

- workload.py、source/、test_workload.py：工作负载与宿主测试。
- verify.py、test_verify.py：最终ELF/寻址与退休路径核查。
- build.py、identity.py、test_identity.py：当前身份与GNU九镜像构建。
- runtime.py、test_runtime.py及其余文档/归档：主Agent。

所有新镜像/调用清单、工具、源码必须在首个EMU前冻结；新文件仍在开发时不得启动目标。历史失败保留，不更改P0门槛。

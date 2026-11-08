# 下一轮指令

开始 SP1-E micro chain-d1 五角色有界探针：先核查已有进程、冻结输入和本轮 NEXT_STEP，使用已冻结运行器与同镜像、0f/SP1 EMU及NEMU；准入全部通过后，依次运行bit100拒错、候选恢复、0f校准、候选重放和0f重放。保持6300/7200秒、CPU4/4线程、原guest/RSS/日志上限，完整12窗和1536custom，10%收益、2%RVV退化、AB/BA均正及精确重放。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序并给下一轮指令。

宿主准备GO，目标执行未授权且未开始；新指令到达后按runtime/ANNEX_REQUIREMENTS.md生成一次性运行记录，原EXECUTION_FREEZE和旧失败保留。

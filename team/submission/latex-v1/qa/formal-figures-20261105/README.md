# 正式工程图的构建与复核

当前成品为Build09，四份PDF为102／34／33／38页。main与stage3由Build09构建；stage1精确复用Build08，stage2精确复用Build07，来源见回执。Build07的段落分隔错误及日志保留，Build08修复后完成；Build09只修正三处命令标记以保存双连字符。

build09-automated-inspection.json保存原始自动检查；root-visual-review.json写实际查看范围。独立Pro和原生Agent审查分别归档，未扩大为新硬件、性能或人工审美验收。命令审查保留六张实际页渲染；其余完整成品与指定页可从output PDF重新渲染。

build09-frozen-sources.json保存340项构建输入。发布后说明同步涉及六个不进入正文渲染的文件（五份说明／状态与一份Git属性）；精确构建时版本在build09-input-documents，闭合校验见package-source-closure.json。selected-diagrams的选图数组、哈希和支持源均未改变，仅更新状态说明。pre-build09-current-metadata是此前当前位元数据，保留其原历史身份，不能作为当前PASS。

Git发布额外为本目录设置-text，避免原生编译stdout的CRLF被继承规则归一化；原始.gitattributes随构建时说明一起保存，PDF与图件没有因此重建。

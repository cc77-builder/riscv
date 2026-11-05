from pathlib import Path
import re, json
from figure_placeholders import apply_figure_slots, tex_text
from report_structure import source_blocks, assemble
from report_layout import format_report
root = Path(__file__).resolve().parent
backup = root / "content/baseline"
tick = chr(96)
tokens = re.compile(r"(\[[^\]]+\]\([^)]+\)|\*\*.+?\*\*|" + tick + r"[^" + tick + r"]+" + tick + r")")
def escape(text):
    mapping = {"\\":r"\textbackslash{}", "&":r"\&", "%":r"\%", "$":r"\$", "#":r"\#", "_":r"\_", "{":r"\{", "}":r"\}", "~":r"\textasciitilde{}", "^":r"\textasciicircum{}", "→":r"\allowbreak{}→\allowbreak{}"}
    return "".join(mapping.get(c,c) for c in text)
def plain(text):
    return "".join(r"\seqsplit{"+escape(x)+"}" if re.fullmatch(r"[A-Za-z0-9_./:=+-]{16,}",x) else escape(x) for x in re.split(r"([A-Za-z0-9_./:=+-]{16,})", text))
def inline(text):
    math = re.compile(r"(?<![\\$])\$(?!\$)(?:\\[^\n]|[^$\\`\n])+\$(?!\$)")
    inline_tokens = re.compile(
        "(" + tick + "[^" + tick + "]+" + tick
        + r"|\\\$|" + math.pattern
        + r"|\[[^\]]+\]\([^)]+\)|\*\*.+?\*\*)"
    )
    result=[]
    for part in inline_tokens.split(text):
        if part.startswith("[") and "](" in part:
            label, url = part[1:].split("](",1)
            url=url[:-1]
            if not url.startswith("http"):
                result.append(plain(label))
            else:
                result.append(r"\href{"+escape(url)+"}{"+plain(label)+"}")
        elif part.startswith("**"):
            result.append(r"\textbf{"+plain(part[2:-2])+"}")
        elif part.startswith(tick):
            # Keep literal command hyphens distinct from TeX punctuation ligatures.
            result.append(plain(part[1:-1]).replace("--", "-{}-"))
        elif part == r"\$":
            result.append(r"\$")
        elif math.fullmatch(part):
            result.append(part)
        else:
            result.append(plain(part))
    return "".join(result)
def cells(line):
    result=[];value="";quoted=False
    for c in line.strip().strip("|"):
        if c==tick: quoted=not quoted
        if c=="|" and not quoted:
            result.append(value.strip());value=""
        else: value+=c
    result.append(value.strip())
    return result
def convert(markdown):
    lines=markdown.splitlines();result=[];i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:result.append("\n");i+=1;continue
        if line.startswith("# "):i+=1;continue
        if line.startswith("##"):
            level=len(line)-len(line.lstrip("#"))
            title=re.sub(r"^\d+(?:\.\d+)*[.、]?\s*","",line[level:].strip())
            command="subsection" if level==2 else "subsubsection"
            result.append("\\"+command+"{"+inline(title)+"}");i+=1;continue
        if line.startswith(tick*3) or line.startswith("~~~"):
            marker=line[:3];lang=line[3:];i+=1;block=[]
            while i<len(lines) and not lines[i].strip().startswith(marker):block.append(lines[i]);i+=1
            i+=1
            if lang!="mermaid":
                reserve = (r"\Needspace{"+str(len(block)+2)+r"\baselineskip}"+"\n") if len(block)<=6 else ""
                result.append(reserve+"\\begin{Verbatim}[breaklines,breakanywhere,breaksymbolleft={},breaksymbolright={},fontsize=\\small]\n"+"\n".join(block)+"\n\\end{Verbatim}")
            continue
        if line.startswith("|"):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith("|"):
                row=cells(lines[i])
                if not all(re.fullmatch(r"[-: ]+",x) for x in row):rows.append(row)
                i+=1
            n=len(rows[0])
            weights={2:[.29,.65],3:[.27,.30,.35],4:[.20,.24,.24,.22],5:[.15,.18,.18,.18,.18]}.get(n,[.86/n]*n)
            columns="".join(r">{\raggedright\arraybackslash}p{"+str(x)+r"\linewidth}" for x in weights)
            result.append(r"{\small\setlength{\tabcolsep}{3pt}\begin{longtable}{"+columns+"}\n\\toprule\n"+" & ".join(r"\textbf{"+inline(x)+"}" for x in rows[0])+r"\\\midrule\endhead")
            for row in rows[1:]:
                row=(row+[""]*n)[:n]
                result.append(" & ".join("{"+inline(x)+"}" for x in row)+r"\\")
            result.append(r"\bottomrule\end{longtable}}")
            continue
        if line.startswith("- "):
            items=[]
            while i<len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:]);i+=1
            result.append("\\begin{itemize}\n"+"\n".join(r"\item "+inline(x) for x in items)+"\n\\end{itemize}")
            continue
        if line.startswith(">"):line=line.lstrip("> ").strip()
        result.append(inline(line)+r"\par");i+=1
    return "\n".join(result)
for stage in (1,2,3):
    overview = root / 'content' / f'overview-stage{stage}.tex'
    if not overview.exists():
        overview = backup / 'sections' / f'stage{stage}.tex'
    original=overview.read_text(encoding="utf-8")
    narrative=(root/"content"/("narrative-stage"+str(stage)+".md")).read_text(encoding="utf-8")
    technical = root / 'content' / f'technical-stage{stage}.json'
    if not technical.exists():
        technical = root / 'content' / f'evidence-stage{stage}.json'
    sources=json.loads(technical.read_text(encoding="utf-8"))
    structured=(root / 'content' / f'structure-stage{stage}.json').exists()
    if structured:
        body=assemble(stage, source_blocks(original,narrative,sources,convert),tex_text)
    else:
        body=original
        method_titles={1:'环境搭建与运行分析',2:'数据通路与控制实现',3:'协同仿真与性能评估方法'}
        body+=r"\section{"+method_titles[stage]+"}\n"+convert(narrative)
        for title,path,text in sources:
            body+=r"\section{"+escape(title)+"}\n"+convert(text)
    body+=r"\subsection{技术资料索引}"+'\n'
    references=[]
    for title,path,text in sources:
        references.append(r"\href{https://github.com/cc77-builder/riscv/blob/347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e/"+escape(path)+"}{"+plain(title)+"}")
    body+=r"{\small\noindent "+"；".join(references)+r"。\par}"+'\n'
    if stage==1:
        body+=r"\section{原始操作日志}"+"\n"
        for title,name in [("10月25日生产模型原始输出","rendered/hello-vadd-production-20261025.txt"),("10月25日FST模型原始输出","rendered/hello-vadd-trace-20261025.txt"),("程序构建原始日志","workload-build.log"),("历史hello与vadd运行摘要","hello-vadd-summary.log"),("NEMU构建原始日志","nemu-build.log"),("EMU构建原始日志","emu-build-20261009-204228.log"),("工具与编译链版本原始输出","tool-versions.txt"),("固定子模块版本清单","submodules-after-build.lock.txt"),("原始波形事件记录","vadd-commit-events.csv"),("向量运算单元事件记录","vector-fix-alu-events.csv")]:
            body+=r"\subsection{"+title+"}\n"
            body+="以下列出该次构建或运行的记录。\n"
            display_name = "rendered/nemu-build.txt" if name == "nemu-build.log" else name
            body+=r"\VerbatimInput[breaklines,breakanywhere,breaksymbolleft={},breaksymbolright={},fontsize=\small]{evidence/"+display_name+"}\n"
    if not structured:
        body = apply_figure_slots(body, stage)
    supplement = root / "sections" / ("screenshots-stage" + str(stage) + ".tex")
    if supplement.exists() and not structured:
        body += "\n" + supplement.read_text(encoding="utf-8")
    body=re.sub(r"图S([123])-([0-9]{2})", lambda m: "图\\ref{fig:S"+m[1]+"-"+m[2]+"}", body)
    body = format_report(body, stage)
    (root/"sections"/("stage"+str(stage)+".tex")).write_text(body,encoding="utf-8",newline="\n")

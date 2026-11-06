from pathlib import Path
import re, json
from figure_placeholders import apply_figure_slots
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
    result=[]
    for part in tokens.split(text):
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
            result.append(plain(part[1:-1]))
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
                result.append("\\begin{Verbatim}[breaklines,breakanywhere,breaksymbolleft={},breaksymbolright={},fontsize=\\small]\n"+"\n".join(block)+"\n\\end{Verbatim}")
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
    original=(backup/"sections"/("stage"+str(stage)+".tex")).read_text(encoding="utf-8")
    body=original
    body+=r"\section{工程实现与验证方法补充}"+"\n"+convert((root/"content"/("narrative-stage"+str(stage)+".md")).read_text(encoding="utf-8"))
    sources=json.loads((root/"content"/("evidence-stage"+str(stage)+".json")).read_text(encoding="utf-8"))
    for title,path,text in sources:
        body+=r"\section{"+escape(title)+"}\n"
        body+="本节整理固定项目材料中的详细方法和原始合同。设计阶段的“拟实现”“必须验证”等表述属于原合同约束，当前完成状态以本报告正文和R5/P5证据为准。原日期、比较合同及未测边界按来源保留。\n"
        body+=r"\par\smallskip\noindent 来源："+r"\href{https://github.com/cc77-builder/riscv/blob/347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e/"+escape(path)+"}{"+plain(path)+"}"+r"\par"+"\n"
        body+=convert(text)
    if stage==1:
        for title,name in [("NEMU构建原始日志","nemu-build.log"),("EMU构建原始日志","emu-build-20261009-204228.log"),("工具与编译链版本原始输出","tool-versions.txt"),("固定子模块版本清单","submodules-after-build.lock.txt"),("原始波形事件记录","vadd-commit-events.csv"),("向量运算单元事件记录","vector-fix-alu-events.csv")]:
            body+=r"\section{"+title+"}\n"
            body+="以下为对应历史记录的原始输出，日期、路径和提交身份保留原值。\n"
            display_name = "rendered/nemu-build.txt" if name == "nemu-build.log" else name
            body+=r"\VerbatimInput[breaklines,breakanywhere,breaksymbolleft={},breaksymbolright={},fontsize=\small]{evidence/"+display_name+"}\n"
    body = apply_figure_slots(body, stage)
    supplement = root / "sections" / ("screenshots-stage" + str(stage) + ".tex")
    if supplement.exists():
        body += "\n" + supplement.read_text(encoding="utf-8")
    (root/"sections"/("stage"+str(stage)+".tex")).write_text(body,encoding="utf-8")

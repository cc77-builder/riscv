"""Apply consistent report typography to regenerated documentary material."""
import re


def format_report(body, stage):
    # The fixed-source table begins immediately after this heading; reserve
    # room for the heading, caption and first rows to avoid a stranded title.
    if stage == 1:
        body = body.replace(r"\subsection{固定源码}",
                            r"\Needspace{8\baselineskip}" + "\n" + r"\subsection{固定源码}")
        body = body.replace(r"\subsection{源码版本与依赖恢复}",
                            r"\Needspace{8\baselineskip}" + "\n" + r"\subsection{源码版本与依赖恢复}")
    if stage == 3:
        for title in ("优化候选的实测取舍", "取消关钟修复的对照输入"):
            heading = r"\subsection{" + title + "}"
            body = body.replace(heading, r"\Needspace{8\baselineskip}" + "\n" + heading)
    # Identity fields live on the cover; keep historical logs untouched.
    body = re.sub(r"^团队名称（待团队确认）[^\n]*\n", "", body, flags=re.M)
    body = body.replace(r"fontsize=\small", r"fontsize=\footnotesize,baselinestretch=1")
    body = body.replace(r"{parent/vdot\_r2o}", r"{parent/\allowbreak{}vdot\_r2o}")
    body = body.replace(r"\seqsplit{O1\_HANDOFF/O2\_ELASTIC}",
                        r"\shortstack[l]{O1\_HANDOFF /\\O2\_ELASTIC}")
    # Technical paragraphs with long paths/formulas should not be stretched
    # across the full line. This is local, not global loose justification.
    technical_starts = ("完整FST位于", "实现路径包括", "给定同一合同下", "周期降低按", "同一映射的五档条件")
    body = "\n".join(
        r"{\raggedright " + line + "}" if line.startswith(technical_starts) and line.endswith(r"\par")
        else line for line in body.split("\n")
    )
    table = re.compile(r"(\\begin\{longtable\}[^\n]*\n)(\\toprule\s*\n)(.*?)(\\endhead)", re.S)
    index = 0

    def caption(match):
        nonlocal index
        index += 1
        headings = re.findall(r"\\(?:subsubsection|subsection|section)\{([^{}]+)\}", body[:match.start()])
        title = headings[-1] if headings else "技术数据"
        label = f"tab:{stage}-{index}"
        header = match.group(2) + match.group(3)
        return (match.group(1) + r"\caption{" + title + r"}\label{" + label
                + r"}\\" + "\n" + header + r"\endfirsthead" + "\n"
                + r"\caption[]{" + title + r"（续）}\\" + "\n"
                + header + r"\endhead")

    return table.sub(caption, body)

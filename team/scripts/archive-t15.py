"""Seal a completed T15 standalone run without caches or simulator executables."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive(run, output):
    result=json.loads((run/"result.json").read_text())
    if result["status"]!="T15_UNIT_CAMPAIGN_PASS":
        raise ValueError("run is not accepted")
    manifest=json.loads((run/"file-manifest.json").read_text())["files"]
    output.mkdir(parents=True,exist_ok=False)
    for name,expected in manifest.items():
        source=(run/name).resolve()
        if not source.is_relative_to(run.resolve()):raise ValueError("source path escape")
        data=source.read_bytes()
        if digest(data)!=expected:raise ValueError("raw evidence changed: "+name)
        target=output/"run"/name
        if source.suffix in (".log",".tsv") and len(data)>1024:
            target=target.with_name(target.name+".gz")
            data=gzip.compress(data,mtime=0)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    (output/"run/file-manifest.json").write_bytes((run/"file-manifest.json").read_bytes())
    (output/".gitattributes").write_text("* -text -whitespace\n")
    (output/".gitignore").write_text("!**/\n!*.log\n!*.gz\n!*.json\n!*.sv\n!*.tsv\n")
    (output/"README.md").write_text("""# T15 独立参数单元证据

本包保存基本 s8x8/r32 与扩展 s16x8/r64 的真实 Chisel RTL、Verilator 全宽读回、逐周期握手、错误注入、参数拒绝及模型检查。原始日志/TSV 超过 1 KiB 时无损 gzip；run/file-manifest.json 校验解压后的原字节，file-manifest.json 校验存储字节。

从仓库根执行（输出文件必须不存在）：

```bash
python3 -B team/scripts/verify-t15.py --run team/evidence/t15-parameters-20261017/run --output /tmp/t15-offline-new.json
```

通过标志 T15_OFFLINE_RECHECK_PASS。只需 Python 3.10+ 标准库；脚本与数据源码必须与 run/source.json 固定摘要相同。大型 Verilator 生成 C++、对象及可执行文件不进入证据包；原二进制摘要和完整构建命令已保存。

这不是新 ISA 或全核 SEW=16 验收，也不是重新执行硬件仿真或物理时序/PPA 验证。旧生产硬件与 NEMU 未被修改。最终报告见 ../../docs/t15-parameter-extension.md。
""",encoding="utf-8")
    files={str(p.relative_to(output)):digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output/"file-manifest.json").write_text(json.dumps({"files":files},indent=2)+"\n")
    print(json.dumps(dict(status="T15_ARCHIVED",stored_files=len(files),stored_bytes=sum(p.stat().st_size for p in output.rglob("*") if p.is_file()))))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    archive(args.run.resolve(),args.output.resolve())

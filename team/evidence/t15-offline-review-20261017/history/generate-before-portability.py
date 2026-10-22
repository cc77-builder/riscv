"""Generate only the new T15 corpus; old T05 vectors are read-only inputs."""
import argparse
import hashlib
import json
from pathlib import Path
from oracle import PROFILES, EXTENSION, pack, exact_sum, result

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SEED = "20261017-t15-s16x8-v1"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def row(suite, ident, a, b, p, category):
    return dict(suite=suite, id=ident, category=category, vs1=f"{a:032x}", vs2=f"{b:032x}",
                expected_sum=exact_sum(a, b, p), expected_vd=f"{result(a, b, p):032x}")


def corpus():
    base = []
    originals = {}
    for suite in ("directed", "random"):
        path = ROOT / "team/models/vdot/data" / (suite + ".jsonl")
        originals[str(path.relative_to(ROOT))] = sha(path.read_bytes())
        for item in map(json.loads, path.read_text(encoding="utf-8").splitlines()):
            entry = row(suite, item["id"], int(item["vs1"], 16), int(item["vs2"], 16), PROFILES["s8x8"], "original-t05")
            if entry["expected_sum"] != item["expected_sum"] or int(entry["expected_vd"], 16) != int(item["expected_vd"], 16):
                raise ValueError("old golden disagrees with independent T15 oracle")
            base.append(entry)
    if len(base) != 10022:
        raise ValueError("frozen T05 inventory changed")
    p = EXTENSION
    ext = []
    def add(a, b, category):
        ext.append(row("directed", f"E{len(ext):03d}", pack(a, p), pack(b, p), p, category))
    # Human-readable extremes and values which distinguish int16 from int8.
    for a, b, category in [
        ([0]*8, [-32768]*8, "zero"), ([1]*8, [1]*8, "ones"),
        ([-1]*8, [1]*8, "negative"), ([-1]*8, [-1]*8, "double-negative"),
        ([-32768]*8, [-32768]*8, "positive-2pow33-needs35bits"),
        ([-32768]*8, [32767]*8, "minimum"),
        ([32767]*8, [32767]*8, "maximum-positive-inputs"),
        ([32767]*8, [-32768]*8, "minimum-commuted"),
        ([-32768,32767]*4, [32767,-32768]*4, "mixed-sign"),
        ([-32768]*8, [-1,1]*4, "cancellation"),
        ([128,255,256,257,-129,-256,-257,32767], [1,2,3,4,5,6,7,8], "not-int8"),
        ([1,256,2,512,3,768,4,1024], [8,7,6,5,4,3,2,1], "byte-and-lane-order"),
        ([0]*4+[-32768]*4, [0]*4+[-32768]*4, "upper-half-required"),
        ([1,2,3,4,5,6,7,8], [1,2,3,4,5,6,7,8], "sum-of-squares"),
    ]:
        add(a, b, category)
    for lane in range(8):
        for a, b, category in [(-32768,-32768,"single-positive-limit"),(-32768,32767,"single-negative-limit")]:
            x=[0]*8; y=[0]*8; x[lane]=a; y[lane]=b; add(x,y,f"{category}-lane{lane}")
    for left in range(8):
        for right in range(8):
            x=[0]*8; y=[0]*8; x[left]=-(257+left); y[right]=1024+right
            add(x,y,f"lane-pair-{left}-{right}")
    for i in range(10000):
        raw=hashlib.sha256(f"{SEED}:{i}".encode("ascii")).digest()
        ext.append(row("random",f"R{i:05d}",int.from_bytes(raw[:16],"little"),int.from_bytes(raw[16:],"little"),p,"sha256-uniform-source"))
    return {"s8x8":base,"s16x8":ext}, originals


def files():
    data, originals=corpus()
    outputs={}
    stats={}
    for name, rows in data.items():
        outputs[name+".jsonl"]=("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows)).encode()
        outputs[name+".tsv"]=("".join(f"{x['suite']} {x['id']} {x['vs1']} {x['vs2']} {x['expected_vd']}\n" for x in rows)).encode()
        p=PROFILES[name]
        stats[name]=dict(parameters=p.__dict__,limits=p.limits,required_bits=p.required_bits,
                         directed=sum(x["suite"]=="directed" for x in rows),random=sum(x["suite"]=="random" for x in rows),total=len(rows))
    manifest=dict(contract="t15-standalone-s16x8-r64-v1",seed=SEED,profiles=stats,originals=originals,
                  source_sha256={name:sha((HERE/name).read_bytes()) for name in ("oracle.py","generate.py")},
                  files={name:sha(value) for name,value in outputs.items()})
    outputs["manifest.json"]=(json.dumps(manifest,indent=2)+"\n").encode()
    return outputs


def check(output):
    for name,data in files().items():
        path=output/name
        if not path.is_file() or path.read_bytes()!=data:
            raise ValueError("T15 corpus missing or changed: "+name)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=HERE/"data")
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    if args.check:
        check(args.output)
        print("T15_CORPUS_CHECK_PASS")
    else:
        args.output.mkdir(parents=True,exist_ok=False)
        for name,data in files().items(): (args.output/name).write_bytes(data)
        print("T15_CORPUS_GENERATED",args.output)

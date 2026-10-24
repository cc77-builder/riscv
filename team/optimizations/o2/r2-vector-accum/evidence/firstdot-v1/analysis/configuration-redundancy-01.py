"""Count repeated literal vector configurations in an audited firstdot matrix.

This is a source observation and future experiment hypothesis, not an optimizer,
semantic proof, benchmark, or estimate of cycles saved.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def inspect(archive, audit_path, output):
    assert not output.exists()
    raw_manifest = (archive / "archive-manifest.json").read_bytes()
    manifest, audit = json.loads(raw_manifest), json.loads(audit_path.read_bytes())
    assert manifest["contract"] == audit["contract"] == "r2-s1-firstdot-c-abi-v1"
    assert manifest["qualification_scope"] == audit["qualification_scope"] == "matrix"
    assert audit["status"] == "FIRSTDOT_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS"
    assert audit["archive"]["archive_manifest_sha256"] == digest(raw_manifest)
    grouped = {}
    for record in manifest["files"]:
        logical = record["stored"][len("files/"):]
        if record["encoding"] == "gzip":
            logical = logical[:-3]
        if not (logical.startswith("builds/") and logical.endswith("/data/manifest.json")):
            continue
        encoded = (archive / record["stored"]).read_bytes()
        assert digest(encoded) == record["stored_sha256"] and len(encoded) == record["stored_bytes"]
        raw = gzip.decompress(encoded) if record["encoding"] == "gzip" else encoded
        assert digest(raw) == record["raw_sha256"] and len(raw) == record["raw_bytes"]
        image = json.loads(raw)
        for row in image["rows"]:
            key = (image["r2_variant"], row["m"], row["k"], row["software"], row["method"])
            if key not in grouped:
                grouped[key] = dict(body=row["body"], datasets=[], origins=[])
            item = grouped[key]
            assert item["body"] == row["body"] and image["dataset"] not in item["datasets"]
            item["datasets"].append(image["dataset"])
            item["origins"].append(dict(logical=logical, raw_sha256=record["raw_sha256"]))
    assert len(grouped) == 32
    rows = []
    for key, item in sorted(grouped.items()):
        assert sorted(item["datasets"]) == [0, 1, 2]
        previous, setter, duplicates, configurations = None, None, [], 0
        for number, line in enumerate(item["body"], 1):
            if line.startswith("vsetivli "):
                assert re.fullmatch(r"vsetivli zero, \d+, e(?:8|16|32), m[12], tu, mu", line)
                configurations += 1
                if line == previous:
                    duplicates.append(dict(body_line=number, prior_configuration_line=setter, instruction=line))
                previous, setter = line, number
            elif line.startswith("vset") or re.search(r"\b(?:vl|vtype|vstart)\b", line):
                previous, setter = None, None
        variant, m, k, software, method = key
        rows.append(dict(variant=variant, shape=[m, k], software=software, method=method,
            datasets=[0, 1, 2], literal_configurations=configurations,
            repeated_literal_configurations=len(duplicates), repetitions=duplicates, inputs=item["origins"]))
    result = dict(status="FIRSTDOT_CONFIGURATION_SOURCE_OBSERVATION", qualification_recomputed=False,
        source_script_sha256=digest(Path(__file__).read_bytes()), audit_sha256=digest(audit_path.read_bytes()),
        archive_manifest_sha256=digest(raw_manifest), new_emu_runs=0, rows=rows,
        limits="Same literal AVL/vtype observed with no intervening explicit configuration write. Removal needs separate vstart/normal-completion/compiled-model checks and a fresh fair full-call experiment including equally optimized RVV; no cycle-saving claim.")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(status=result["status"], reuse=[{k: v for k, v in r.items() if k not in ("inputs", "repetitions")}
        for r in rows if r["software"] == "reuse"]), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "audit", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    inspect(args.archive.resolve(), args.audit.resolve(), args.output.resolve())

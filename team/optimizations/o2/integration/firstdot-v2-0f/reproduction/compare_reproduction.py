"""Compare audited current and independently rebuilt firstdot combinations."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import gzip
import json
from pathlib import Path
import struct

CONTRACT = "current-firstdot-clean-comparison-v1"
EXPECTED = {(v, s, d) for v in ("s1", "firstdot") for s in (1, 3, 5, 7) for d in range(3)}
AUDIT_PASS = "CURRENT_FIRSTDOT_RAW_RECOMPUTATION_AND_ARCHIVE_PASS"
MATRIX_CONTRACT = "zjhwork-0f-firstdot-v2-integration-v1"
RESUMED_MATRIX_CONTRACT = "zjhwork-0f-firstdot-v2-continuation-v1"
RESUMED_MATRIX_PASS = "CURRENT_FIRSTDOT_RESUMED_PAIRED_C_ABI_PASS"
AUDIT_CONTRACT = "zjhwork-0f-firstdot-raw-audit-archive-v1"
RESUMED_AUDIT_CONTRACT = "zjhwork-0f-firstdot-continuation-raw-audit-v1"
RESUMED_AUDIT_PASS = "CURRENT_FIRSTDOT_CONTINUATION_RAW_AUDIT_AND_ARCHIVE_PASS"
LIMITED_AUDIT_CONTRACT = "zjhwork-0f-firstdot-continuation-raw-audit-v2-wall-clock-limited"
LIMITED_AUDIT_PASS = "CURRENT_FIRSTDOT_CONTINUATION_FUNCTIONAL_CYCLES_AUDIT_PASS_WALL_CLOCK_LIMITED"
CHRONOLOGY_CONTRACT = "zjhwork-firstdot-causal-order-wall-clock-limited-v1"
KNOWN_ANOMALY = dict(
    before_label="formal-performance-s1-d0-s01",after_label="formal-performance-s1-d1-s01",
    before_record_sha256="bdca4b1645c29b71bece59985ffe01284e8c69af5abb8f8e6f046609040c582b",
    after_record_sha256="e578b7a006286be7d9e5d916a7f16a55a8c3baafe67e310959869eac42cd2a49",
    before_finished="2026-10-26T07:07:55.796377+00:00",
    after_started="2026-10-26T07:07:55.252896+00:00",backward_microseconds=543481)

C_CONTRACT = "r2-s1-firstdot-c-application-v1"
RESUMED_C_CONTRACT = "current-firstdot-c-continuation-v1"
RESUMED_C_PASS = "CURRENT_FIRSTDOT_C_CONTINUATION_PASS"

def require(ok, message):
    if not ok:
        raise ValueError(message)

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()

def loads(path):
    data = Path(path).read_bytes()
    require(data[:6] == bytes.fromhex("7f454c460201"), "ELF must be 64-bit little endian")
    require(len(data) >= 64, "truncated ELF")
    header = struct.unpack_from("<HHIQQQIHHHHHH", data, 16)
    require(header[1] == 243 and header[8] == 56, "ELF machine/program-header format")
    entry, offset, count = header[3], header[4], header[9]
    require(offset + count * 56 <= len(data), "truncated program headers")
    result = []
    for i in range(count):
        kind, flags, off, va, pa, size, memory, align = struct.unpack_from("<IIQQQQQQ", data, offset+i*56)
        if kind != 1:
            continue
        require(size <= memory and off + size <= len(data), "truncated load segment")
        result.append(dict(flags=flags, vaddr=va, paddr=pa, filesz=size, memsz=memory,
                           align=align, sha256=hashlib.sha256(data[off:off+size]).hexdigest()))
    require(result, "ELF contains no load segment")
    return dict(entry=entry, segments=result)

def images(build):
    rows = read(build / "images.json")["images"]
    mapped = {}
    for row in rows:
        key = tuple(row[k] for k in ("variant", "shard", "dataset"))
        require(key not in mapped and row["suite"] == "performance", "duplicate/invalid image")
        path = Path(row["path"])
        require(path.is_relative_to(build), "image escapes selected build")
        require(sha(path / "vdot-perf.bin") == row["image_sha256"], "image byte drift")
        mapped[key] = row
    require(set(mapped) == EXPECTED, "requires all 24 images")
    return mapped

def compare_images(current_build, clean_build, current_c, clean_c):
    left, right = images(current_build), images(clean_build)
    checks = []
    for key in sorted(EXPECTED):
        a, b = left[key], right[key]
        ap, bp = Path(a["path"]), Path(b["path"])
        require(a["name"] == b["name"], "image selection name mismatch")
        require(a["image_sha256"] == b["image_sha256"], "rebuilt BIN differs: " + a["name"])
        la, lb = loads(ap / "vdot-perf.elf"), loads(bp / "vdot-perf.elf")
        require(la == lb, "rebuilt ELF load segments differ: " + a["name"])
        checks.append(dict(name=a["name"], image_sha256=a["image_sha256"], load=la,
                           full_elf_equal=sha(ap/"vdot-perf.elf")==sha(bp/"vdot-perf.elf")))
    require(sha(current_c/"vdot-perf.bin") == sha(clean_c/"vdot-perf.bin"), "C BIN differs")
    require(loads(current_c/"vdot-perf.elf") == loads(clean_c/"vdot-perf.elf"), "C loaded ELF differs")
    return dict(status="CURRENT_CLEAN_PROGRAM_BYTES_EQUAL", matrix_images=24, c_images=1,
                images=checks, c_image_sha256=sha(current_c/"vdot-perf.bin"),
                full_elf_equality_required=False, elf_debug_path_changes_allowed=True)

def windows(result, allow_resumed=False):
    if result["status"] == RESUMED_MATRIX_PASS:
        counts = dict(new_emu_runs=21, inherited_started=13, inherited_qualified_processes=12,
                      interrupted_runs=1, total_processes_started=34, qualified_processes=33)
        require(allow_resumed and result.get("contract") == RESUMED_MATRIX_CONTRACT
                and result.get("underlying_contract") == MATRIX_CONTRACT
                and result.get("historical_pass_reused") is False
                and all(type(result.get("continuation", {}).get(k)) is int
                        and result["continuation"][k] == v for k, v in counts.items()),
                "explicit current matrix continuation contract/counts required")
    else:
        require(result["status"] == "CURRENT_FIRSTDOT_PAIRED_C_ABI_PASS"
                and result.get("contract") == MATRIX_CONTRACT, "matrix not qualified")
    selected = {}
    for row in result["runs"]:
        require(row["status"] == "R2_DIFFTEST_WINDOWS_AND_O2_PROTOCOL_PASS", "non-normal matrix record")
        key = tuple(row[k] for k in ("variant", "shard", "dataset", "replay", "name"))
        require(key not in selected and len(row["samples"]) == 24, "duplicate run or incomplete windows")
        entries = {}
        for sample in row["samples"]:
            sk = tuple(sample[k] for k in ("seq", "phase", "method", "software", "repeat"))
            require(sk not in entries, "duplicate window")
            require(all(sample[k] == row[k] for k in ("variant", "shard", "dataset", "image_sha256")),
                    "window/run selection mismatch")
            entries[sk] = sample
        selected[key] = entries
    require(len(selected) == 32 and sum(len(s) for s in selected.values()) == 768, "matrix window inventory")
    normal = {(k[0],k[1],k[2]) for k in selected if k[3] == 0}
    replay = {(k[0],k[1],k[2]) for k in selected if k[3] == 1}
    require(normal == EXPECTED and replay == {k for k in EXPECTED if k[2] == 0}, "matrix run selection")
    return selected

def compare_windows(current, clean):
    left, right = windows(current, allow_resumed=True), windows(clean)
    require(left.keys() == right.keys(), "run identities differ")
    differences = []
    for rk in left:
        require(left[rk].keys() == right[rk].keys(), "window identities differ")
        for sk in left[rk]:
            a,b = left[rk][sk], right[rk][sk]
            if a != b:
                differences.append(dict(run=list(rk), window=list(sk),
                    fields={k: [a.get(k),b.get(k)] for k in a.keys() | b.keys() if a.get(k)!=b.get(k)}))
    require(not differences, "window differences: " + json.dumps(differences[:5]))
    return dict(status="CURRENT_CLEAN_ALL_WINDOWS_IDENTICAL", compared_windows=768,
                formal_windows=384, retained_first_warmup_and_replay=True,
                comparison="complete samples, including cycles/instructions/raw counters/ticks")

def verify_audit(directory, allow_resumed=False):
    state = read(directory / "state.json")
    limited = state["status"] == LIMITED_AUDIT_PASS
    if state["status"] in (RESUMED_AUDIT_PASS,LIMITED_AUDIT_PASS):
        expected_contract = LIMITED_AUDIT_CONTRACT if limited else RESUMED_AUDIT_CONTRACT
        counts = dict(qualified_processes=36, actual_launched_processes=38, interrupted_processes=2,
                      continuation_new_emu_processes=23, inherited_launched_processes=15,
                      new_emu_runs=0, new_nemu_runs=0)
        require(allow_resumed and state.get("contract") == expected_contract
                and state.get("interrupted_results_counted_as_pass") is False
                and all(type(state.get(k)) is int and state[k] == v for k, v in counts.items()),
                "explicit current continuation audit contract/counts required")
    else:
        expected_contract = AUDIT_CONTRACT
        require(state["status"] == AUDIT_PASS and state.get("contract") == expected_contract
                and type(state.get("original_emu_processes")) is int and state["original_emu_processes"] == 36,
                "completed 36-process raw audit required")
    require(state["formal_windows"] == 384 and state["c_normal_case_executions"] == 96,
            "audit coverage differs")
    archive=directory/"archive"
    require(state["archive"]["manifest_sha256"]==sha(archive/"manifest.json"),"archive receipt drift")
    manifest=read(archive/"manifest.json")
    require(manifest.get("contract") == expected_contract, "archive contract differs from audit mode")
    sealed={row["logical"]:row for row in manifest["files"]}
    require(len(sealed)==len(manifest["files"]),"duplicate archive logical path")
    paths = {}
    for name in ("evidence-inputs.json", "external-inputs.json"):
        member=sealed["raw-audit/"+name]
        source=directory/name
        payload=Path(member["payload"])
        require(not payload.is_absolute() and ".." not in payload.parts
                and payload.parts[0]=="payload","unsafe audit inventory payload")
        stored=archive/payload
        require(member["original"]==str(source) and member["raw_sha256"]==sha(source)
                and member["raw_bytes"]==source.stat().st_size,"audit inventory detached from sealed archive")
        require(not stored.is_symlink() and sha(stored)==member["stored_sha256"]
                and stored.stat().st_size==member["stored_bytes"],"sealed audit inventory payload differs")
        require(gzip.decompress(stored.read_bytes())==source.read_bytes(),"audit inventory payload differs")
        rows=read(source)
        require(rows, "empty audit input inventory")
        for filename,digest in rows.items():
            require(sha(filename)==digest, "audited input changed: "+filename)
        paths.update(rows)
    require(state["archive"]["manifest_sha256"]==sha(directory/"archive/manifest.json"), "archive receipt drift")
    if limited:
        verify_limited_chronology(directory,state,sealed,paths)
    return paths

def verify_limited_chronology(directory,state,sealed,paths):
    expected=dict(functional_validation="PASS",target_cycle_validation="PASS",
                  wall_clock_chronology="FAIL",causal_serial_order="PASS")
    require(all(state.get(k)==v for k,v in expected.items()),"limited audit must disclose failed wall chronology")
    source=directory/"chronology-proof.json"
    require(state.get("chronology_proof_sha256")==sha(source),"chronology proof state binding differs")
    member=sealed["raw-audit/chronology-proof.json"]
    payload=Path(member["payload"])
    require(not payload.is_absolute() and ".." not in payload.parts and payload.parts[0]=="payload",
            "unsafe chronology proof payload")
    stored=directory/"archive"/payload
    require(member["original"]==str(source) and member["raw_sha256"]==sha(source)
            and member["raw_bytes"]==source.stat().st_size and not stored.is_symlink()
            and sha(stored)==member["stored_sha256"] and stored.stat().st_size==member["stored_bytes"]
            and gzip.decompress(stored.read_bytes())==source.read_bytes(),"chronology proof detached from archive")
    proof=read(source)
    exact=dict(contract=CHRONOLOGY_CONTRACT,wall_clock_chronology="FAIL",causal_serial_order="PASS",
               clock_cause="UNCONFIRMED",ordering="frozen_controller_dispatch_sequence")
    require(all(proof.get(k)==v for k,v in exact.items())
            and proof.get("monotonic_timestamps_recorded") is False
            and proof.get("timestamp_values_modified") is False
            and proof.get("records_reordered") is False
            and type(proof.get("new_emu_runs")) is int and proof["new_emu_runs"]==0,
            "explicit causal-order/clock limitation contract required")
    anomalies=proof.get("anomalies")
    require(isinstance(anomalies,list) and len(anomalies)==1
            and all(anomalies[0].get(k)==v and type(anomalies[0].get(k)) is type(v)
                    for k,v in KNOWN_ANOMALY.items()),"unrecognized wall-clock anomaly")
    for field in ("source_files","receipt_files"):
        rows=proof.get(field)
        require(isinstance(rows,dict) and rows,"missing causal proof input closure")
        for filename,digest in rows.items():
            require(paths.get(filename)==digest and sha(filename)==digest,"causal proof input not audited")
    # The original record hashes are already checked by the raw auditor. Ensure
    # those exact byte identities remain inside the sealed comparison inputs.
    require(all(h in paths.values() for h in (KNOWN_ANOMALY["before_record_sha256"],
                KNOWN_ANOMALY["after_record_sha256"])),"anomalous records absent from audited inputs")
    return proof

def c_outputs(build, run, audited, allow_resumed=False):
    def bound(path):
        require(str(path) in audited and audited[str(path)]==sha(path),"C comparison input not audited: "+str(path))
        return read(path)
    state=bound(run/"state.json")
    if state["status"] == RESUMED_C_PASS:
        counts = dict(new_emu_runs=2, total_launched_processes=4, interrupted_processes=1,
                      logical_completed_processes=3, normal_case_executions=96, distinct_cases=48,
                      public_functions=16, expected_negative_runs=1, normal_runs=2)
        require(allow_resumed and state.get("contract") == RESUMED_C_CONTRACT
                and state.get("performance_measured") is False
                and all(type(state.get(k)) is int and state[k] == v for k, v in counts.items()),
                "explicit current C continuation contract/counts required")
        locations = state["record_locations"]
        require(set(locations) == {"negative", "recovery", "replay"}
                and all(locations[label] == str(run/"runs"/label) for label in ("recovery", "replay")),
                "C continuation normal record locations differ")
        negative = bound(Path(locations["negative"])/"result.json")
        require(negative["status"] == "EXPECTED_VDOT_HIGHBIT_REJECTION"
                and negative["negative"] is True, "C inherited negative is not audited")
    else:
        require(state["status"]=="R4_C_APPLICATION_CALLS_PASS" and state.get("contract") == C_CONTRACT
                and state["normal_case_executions"]==96, "C target calls incomplete")
    manifest=bound(build/"source/manifest.json")
    cases=manifest["cases"]
    require(len(cases)==48 and len({(c["api_symbol"],c["dataset"]) for c in cases})==48, "C case inventory")
    # Both independently audited logs must contain the exact ordered case hashes.
    rows=[]
    for label in ("recovery","replay"):
        record=bound(run/"runs"/label/"result.json")
        require(record["status"]=="R4_C_APPLICATION_DIFFTEST_PASS", "C case run unqualified")
        validation=bound(run/"runs"/label/"validation.json")
        expected=dict(status="R4_C_APPLICATION_DIFFTEST_PASS",case_count=48,public_functions=16,
                      output_hashes=[c["expected_hash"] for c in cases],performance_measured=False)
        require(validation==record["validation"]==expected,"C actual audited outputs differ")
        rows.append(dict(label=label,output_hashes=validation["output_hashes"]))
    return dict(cases=cases, outputs=rows, normal_runs=2, normal_case_executions=96,
                image_sha256=sha(build/"vdot-perf.bin"))

def main(args):
    inputs={k:Path(v).resolve() for k,v in vars(args).items() if k!="output" and v}
    out=args.output.resolve()
    require(not out.exists() and not any(out.is_relative_to(p) or p.is_relative_to(out) for p in inputs.values()),
            "fresh separate output required")
    out.parent.mkdir(parents=True,exist_ok=True)
    result=dict(contract=CONTRACT,status="RUNNING",started=datetime.now(timezone.utc).isoformat(),
                tool_sha256=sha(__file__),inputs={k:str(v) for k,v in inputs.items()},new_emu_runs=0)
    try:
        result["programs"]=compare_images(inputs["current_build"],inputs["clean_build"],
                                           inputs["current_c_build"],inputs["clean_c_build"])
        if args.current_audit or args.clean_audit:
            require(args.current_audit and args.clean_audit and args.current_run and args.clean_run
                    and args.current_c_run and args.clean_c_run,"both complete audited combinations required")
            sealed=[]
            audit_inputs={}
            for tag in ("current","clean"):
                mapped=verify_audit(inputs[tag+"_audit"], allow_resumed=tag=="current")
                audit_inputs[tag]=mapped
                for suffix,filename in (("run","results.json"),("c_run","results.json"),
                                        ("build","combination-build.json"),("c_build","build.json")):
                    p=inputs[tag+"_"+suffix]/filename
                    require(str(p) in mapped and mapped[str(p)]==sha(p),"selected input is not the audited input")
                audit_state=read(inputs[tag+"_audit"]/"state.json")
                sealed.append(dict(audit_sha256=sha(inputs[tag+"_audit"]/"state.json"),
                    contract=audit_state["contract"],status=audit_state["status"],
                    wall_clock_chronology=audit_state.get("wall_clock_chronology","PASS"),
                    performance_time_domain="target simulator cycles; host wall time excluded"))
            for tag in ("current", "clean"):
                path=inputs[tag+"_run"]/"parent-identity.json"
                require(str(path) in audit_inputs[tag] and audit_inputs[tag][str(path)]==sha(path),
                        "comparison identity is not the audited identity")
            ia=read(inputs["current_run"]/"parent-identity.json")
            ib=read(inputs["clean_run"]/"parent-identity.json")
            baseline="0f12df675378556670afd0dd2153f47fcb330610"
            require(ia["contract"]=="current-o2-h1-div-cancel-hardware-v1"
                    and ia["source_commit"]==baseline,"current identity differs")
            require(ib["contract"]=="zjhwork-0f-firstdot-v2-clean-identity-v1"
                    and ib["selected_hardware_commit"]==baseline and ib["new_source_build"] is True,
                    "independently built clean identity required")
            for field in ("hardware_source","build_record","reference","am_home"):
                require(ia["configuration"][field]!=ib["configuration"][field],"clean input reuses original "+field)
            require(ia["flash_sha256"]==ib["flash_sha256"],"flash differs")
            result["identities"]=dict(selected_hardware_commit=baseline,
                current=sha(inputs["current_run"]/"parent-identity.json"),
                clean=sha(inputs["clean_run"]/"parent-identity.json"),
                current_emu=ia["hardware_profile"]["emu_sha256"],clean_emu=ib["hardware_profile"]["emu_sha256"],
                emu_binary_equal=ia["hardware_profile"]["emu_sha256"]==ib["hardware_profile"]["emu_sha256"],
                scope="same host independent sources and builds; installed tools/cache retained")
            result["windows"]=compare_windows(read(inputs["current_run"]/"results.json"),
                                               read(inputs["clean_run"]/"results.json"))
            a=c_outputs(inputs["current_c_build"],inputs["current_c_run"],audit_inputs["current"], allow_resumed=True)
            b=c_outputs(inputs["clean_c_build"],inputs["clean_c_run"],audit_inputs["clean"])
            require(a==b,"C cases/outputs differ")
            result.update(status="CURRENT_CLEAN_PROGRAMS_AND_ALL_WINDOWS_EQUAL",ordinary_c=a,audits=sealed)
        else:
            result["status"]="CURRENT_CLEAN_PROGRAM_BYTES_EQUAL_RUNTIME_NOT_COMPARED"
    except BaseException as exc:
        result.update(status="FAILED",error=repr(exc))
        raise
    finally:
        result["finished"]=datetime.now(timezone.utc).isoformat()
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(result["status"])

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for tag in ("current","clean"):
        for suffix in ("build","c-build","audit","run","c-run"):
            parser.add_argument("--"+tag+"-"+suffix,type=Path,required=suffix in ("build","c-build"))
    parser.add_argument("--output",type=Path,required=True)
    main(parser.parse_args())

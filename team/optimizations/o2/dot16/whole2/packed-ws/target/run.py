#!/usr/bin/env python3
"""Freeze and run one bounded packed-Ws eight-window target screen."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import struct
import subprocess
import sys
import time

CONTRACT = 'r3-packed-ws-eight-window-target-v1'
REF_CONTRACT = 'r3-packed-ws-eight-window-reference-v2'
PRIOR_REF_SHA = 'cec287cff44cdda1070539515a3d426fd81e6a4025e0a84ac6bcb632ef7f1f5a'
REF_SCREEN_SHA = '41907943f78825afb3accde2ead8f9952e01b60770fe76cec8e2b6436b4ea76e'
REF_MAIN_SHA = '6933f5a75a9b61b4b6ee96cdaae1f2e4649312ef0ef726272c7d521c08bc2b4d'
REF_RESULT_SHA = '65de4aca20b86d7faaed7c11863297930d571ee2c97b2ad54bb15bdd4c72e4d0'
MODEL_SHA = '703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82'
ORDER = [1,2,3,4,4,3,2,1]
HARDWARE_RESULT_SHA = "e825fff45feb5afa9952140d9832ec8afe9393c02ebd1ab1558ddcfb4a63ae8f"
EMU_SHA = "f14918658fcd2f19c9fb6c1d493025d98f727ac985ea73129edc58270fa6977d"
REF_SHA = "cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae"
FLASH_SHA = "a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994"
GATE_SHA = "172551fb537e93f33937819b1a7625e39986726c039266750adadb73e8ccc05c"
HELPER_SHA = "db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3"
FLAGS = dict(VDOT_DOT16="1", VDOT_O2_ELASTIC="1", VDOT_T14_FUSED_INPUT="1",
             VDOT_O1_HANDOFF="0", VDOT_O1_TRACE="0", VDOT_O2_TRACE="0",
             VDOT_T12_TRACE="0", VDOT_T13_TRACE="0")
ABI = dict(bytes=1400, regs_int=0, regs_fp=256, csr=512, pc=656,
           hcsr=664, regs_vec=800, vcsr=1312, fcsr=1368, triggercsr=1376)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for raw in iter(lambda: f.read(1024 * 1024), b""):
            h.update(raw)
    return h.hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def read(path):
    return json.loads(Path(path).read_bytes())


def module(path, name, pin):
    need(digest(path) == pin, "module identity: " + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def check_pins(pins):
    for path, pin in pins.items():
        need(digest(path) == pin, "input changed: " + path)


def preflight(args):
    os.sched_setaffinity(0,{1});os.setpriority(os.PRIO_PROCESS,0,5)
    need(args.cpu==1 and os.sched_getaffinity(0)=={1} and os.getpriority(os.PRIO_PROCESS,0)==5,'CPU1 absolute nice5')
    build,out=args.reference_build.resolve(),args.output.resolve()
    need(args.output.is_absolute() and not out.exists() and out!=build and not out.is_relative_to(build)
         and not build.is_relative_to(out),'fresh disjoint preflight output')
    need(args.k in (288,768) and 0<args.max_cycles<=6000000 and 60<=args.budget_seconds<=14400
         and args.stream_limit==16777216,'explicit finite one-case limits')
    need(re.fullmatch('[0-9a-f]{64}',args.reference_result_sha256) is not None
         and digest(build/'result.json')==args.reference_result_sha256==REF_RESULT_SHA,'reviewed closed reference result')
    r=read(build/'result.json')
    need(r['contract']==REF_CONTRACT and r['status']=='PACKED_WS_EIGHT_WINDOWS_REFERENCE_PASS'
         and r['reference_qualified'] and r['all_inputs_unchanged'] and r['all_children_reaped']
         and r['reference_runs']==10 and r['target_emu_runs']==0 and not r['performance_qualified'],
         'actual complete new eight-window reference')
    need(r['prior_reference_result_sha256']==PRIOR_REF_SHA,'original complete scalar crossing')
    need(len(r['commands'])==21 and all(c['direct_child_reaped'] and c['process_group_absent_after_exit']
         and c['exit_code']==(2 if c['label'].endswith('-negative') else 0) for c in r['commands']),
         'all actual reference commands and expected negative exits')
    pins={}
    def pin(path,expected=None):
        path=Path(path).absolute();h=digest(path)
        need(expected is None or h==expected,'preflight input '+str(path))
        need(str(path) not in pins or pins[str(path)]==h,'consistent preflight input pin')
        pins[str(path)]=h;return path
    for mapping in (r['original_inputs'],r['snapshots'],r['generated_inputs']):
        for path,h in mapping.items():pin(path,h)
    pin(build/'result.json',args.reference_result_sha256)
    source=pin(build/'inputs/screen.py',REF_SCREEN_SHA)
    pin(build/'inputs/main.c',REF_MAIN_SHA)
    screen=module(source,'packed_eight_frozen_screen',REF_SCREEN_SHA)
    modelpath=pin(build/'inputs/model.py',MODEL_SHA)
    model=module(modelpath,'packed_eight_frozen_elf',MODEL_SHA)
    k=str(args.k);kind='normal-0' if args.k==288 else 'normal';work=build/('k'+k)
    st=read(pin(work/'static.json',r['campaigns'][k]['static_sha256']))
    need(st['contract']==REF_CONTRACT and st['k']==args.k
         and st['status']=='PACKED_WS_FOUR_ARM_STATIC_PASS_NOT_RUNTIME','same fixed geometry static record')
    elfpath=pin(work/'packed-screen.elf',r['generated_inputs'][str(work/'packed-screen.elf')])
    image=pin(work/'images'/kind/'real-w2.bin',r['generated_inputs'][str(work/'images'/kind/'real-w2.bin')])
    raw=image.read_bytes();elf=model.ELF(elfpath.read_bytes())
    kernels={name:(v['bytes'],v['sha256']) for name,v in st['inspection']['kernels'].items()}
    need(len(kernels)==4 and screen.ORDER==ORDER,'four full frozen kernels and exact eight-window order')
    actual=screen.inspect(elf,raw,kernels,'q288_oracle' if args.k==288 else 'w2_scalar')
    need(actual==st['inspection']==r['campaigns'][k]['inspection'],'actual complete ELF/BIN and static inspection')
    record=st['records'][kind];control=record['control_offset']
    need(raw[control:control+8]==struct.pack('<2I',0,1),'target normal/UART controls only')
    v=r['campaigns'][k]['validations'][kind]
    need(v==r['campaigns'][k]['validations']['replay'] and v['status']=='PACKED_WS_REFERENCE_PASS'
         and not v['negative'] and v['prepared_all_bytes'] and v['packed_slots_all_bytes']
         and len(v['samples'])==8 and [row[0] for row in v['samples']]==ORDER,'closed complete normal and replay')
    need(all(row[5]==record['expected_flags'] and row[6]==int(record['golden_fnv'],16) and row[7]==0 for row in v['samples'])
         and v['final_fcsr']==record['expected_flags'],'complete independently crossed values and flags')
    ref_image=pin(work/'reference'/kind/'image.bin')
    expected=bytearray(raw);expected[control:control+8]=struct.pack('<2I',0,0)
    need(ref_image.read_bytes()==expected,'target image differs from reference only in UART control')
    report_path=pin(args.hardware_result.resolve(),HARDWARE_RESULT_SHA);hardware=read(report_path)
    need(hardware['status']=='DOT16_FULLCORE_SMOKE_PASS'
         and hardware['qualification']['fixed_six_legal_case_fullcore_difftest'] is True
         and hardware['abi']['actual_dynamic_difftest_passed'] is True and hardware['abi']['layout']==ABI
         and hardware['source_identity']['flags']==FLAGS,'original actual hardware and DiffTest ABI identity')
    for path,h in hardware['runtime_inputs'].items():pin(path,h)
    def unique(h):
        paths=[p for p,value in hardware['runtime_inputs'].items() if value==h]
        need(len(paths)==1,'one physical runtime input');return paths[0]
    emu,reference,flash,gate=(unique(h) for h in (EMU_SHA,REF_SHA,FLASH_SHA,GATE_SHA))
    need(hardware['emu']['path']==emu and hardware['emu']['sha256']==EMU_SHA,'physical original EMU')
    helper=pin(build/'inputs/process_helper.py',HELPER_SHA)
    runtime=pin(Path(__file__).resolve());contract=pin(Path(__file__).resolve().with_name('TARGET_CONTRACT.md'))
    check_pins(pins)
    out.mkdir(parents=True);snap=out/'inputs';snap.mkdir()
    for path,name in ((runtime,'run.py'),(contract,'TARGET_CONTRACT.md'),(Path(gate),'runtime_gate.py'),
                      (helper,'process_helper.py'),(report_path,'hardware-result.json')):
        shutil.copyfile(path,snap/name);pin(snap/name,pins[str(path)])
    profile=dict(schema=1,contract=CONTRACT,status='FROZEN_BEFORE_EMU',k=args.k,fixture_kind=kind,
        reference_build=str(build),reference_result_sha256=args.reference_result_sha256,
        image=str(image),image_sha256=digest(image),elf=str(elfpath),elf_sha256=digest(elfpath),
        control_offset=control,normal_control=[0,1],success_pc=actual['success_pc'],
        expected_flags=record['expected_flags'],golden_fnv=record['golden_fnv'],order=ORDER,
        expected_window_instret=[row[3]-row[2] for row in v['samples']],reference_retired=v['retired'],
        kernels=st['inspection']['kernels'],sample_count=8,warm_calls=8,complete_calls=16,
        prepared_payload_bytes=288*(args.k//32)*4,prepare_inside_measurement=False,
        emu=emu,reference=reference,flash=flash,cpu=1,nice=5,max_cycles=args.max_cycles,
        budget_seconds=args.budget_seconds,stream_limit_bytes=args.stream_limit,ram_size='128MB',seed=1,
        pins=pins,gate=str(snap/'runtime_gate.py'),helper=str(snap/'process_helper.py'),
        runtime_source=str(snap/'run.py'),runtime_sha256=digest(snap/'run.py'),hardware_flags=FLAGS,existing_abi=ABI,
        new_emu_runs=0,target_runtime_qualified=False,performance_qualified=False,
        application_performance_qualified=False,full_retirement_window_audited=False,asic_ppa_qualified=False,
        automatic_retry=False,automatic_budget_extension=False,
        qualification='Fixed eight-window reference and full machine identities; no target execution yet')
    check_pins(pins);save(out/'profile.json',profile)
    result=dict(status='PACKED_WS_EIGHT_WINDOW_PREFLIGHT_PASS',profile=str(out/'profile.json'),
        profile_sha256=digest(out/'profile.json'),k=args.k,input_files=len(pins),new_emu_runs=0,
        new_builds=0,new_abi_probes=0)
    save(out/'result.json',result);print(json.dumps(result));return result


def guest_check(raw,reference,profile,gate):
    text=raw.decode('utf-8',errors='strict');gate.validate_failure_markers(text);plain=gate.normalize_console(text)
    need(re.search(r'CRITICAL ERROR|double trap|PMA check failed|PWS_REJECT',plain,re.I) is None,
         'additional runtime/guest failure marker')
    need(plain.count('The first instruction of core 0 has commited. Difftest enabled.')==1,
         'actual original DiffTest enabled banner')
    loaded=[v.strip() for v in re.findall(r'The reference model is ([^\r\n]+)',plain)]
    images=[v.strip() for v in re.findall(r'The image is ([^\r\n]+)',plain)]
    need(loaded==[reference] and images==[profile['image']],'exact loaded reference and frozen image')
    traps=re.findall(r'^Core 0: HIT GOOD TRAP at pc = (0x[0-9a-fA-F]+)[ \t]*$',plain,re.M)
    need(len(traps)==plain.count('HIT GOOD TRAP')==1 and int(traps[0],16)==profile['success_pc'],
         'one actual good trap at frozen ELF success symbol')
    k=profile['k'];lines=[line for line in plain.splitlines() if line.startswith('PWS_')]
    need(len(lines)==10 and lines[0]==f'PWS_BEGIN k={k} rows=288 groups={k//32} control=0'
         and lines[-1]==f'PWS_PASS k={k} samples=8 full_comparisons=16 prepared_bytes={profile["prepared_payload_bytes"]}',
         'complete ordered eight-window guest protocol')
    samples=[]
    for index,line in enumerate(lines[1:-1]):
        m=re.fullmatch(r'PWS_SAMPLE (\d+) (\d+) (\d+) (\d+) (\d+) ([0-9a-f]{16})',line)
        need(m is not None,'complete unambiguous sample record')
        slot,method,cycles,instructions,flags=map(int,m.groups()[:5]);fnv=m[6]
        need(slot==index and method==profile['order'][index] and 0<cycles<(1<<32)-1
             and instructions==profile['expected_window_instret'][index]>0
             and flags==profile['expected_flags'] and fnv==profile['golden_fnv'],
             'method/order/complete value hash/exact flags/actual expected window instret')
        samples.append(dict(index=index,method=method,cycles=cycles,instructions=instructions,flags=flags,golden_fnv=fnv))
    by_method={method:[s['cycles'] for s in samples if s['method']==method] for method in (1,2,3,4)}
    need(all(len(v)==2 for v in by_method.values()),'two opposite-order observations per method')
    means={str(method):sum(values)/2 for method,values in by_method.items()}
    comparisons=dict(original_n_over_packed_n=means['2']/means['4'],original_p_over_packed_p=means['1']/means['3'],
        original_p_over_original_n=means['1']/means['2'],packed_p_over_packed_n=means['3']/means['4'],
        fastest_observed_rvv_over_fastest_observed_custom=min(means['1'],means['3'])/min(means['2'],means['4']))
    aggregates=re.findall(r'^Core-0 instrCnt = (\d+), cycleCnt = (\d+), IPC = ([0-9.]+)[ \t]*$',plain,re.M)
    need(len(aggregates)==1 and all(int(x)>0 for x in aggregates[0][:2]),'one finite aggregate diagnostic')
    return dict(k=k,fixture_kind=profile['fixture_kind'],samples=samples,mean_cycles=means,ratios_from_means=comparisons,
        complete_guest_sequence=True,guest_full_output_comparisons=16,outputs_checked=4608,
        guest_all_slots_guards_csrs_checked=True,prepared_all_bytes_checked_by_guest=True,
        full_target_memory_dump=False,prepare_inside_measurement=False,loaded_reference=reference,
        success_pc=profile['success_pc'],aggregate_diagnostic=dict(instrCnt=int(aggregates[0][0]),cycleCnt=int(aggregates[0][1])),
        aggregate_is_kernel_or_application_metric=False,reference_window_instret_matched=True,
        local_cycle_observations=True,retired_custom_count_verified=False,full_retirement_window_audited=False,
        target_replay_performed=False,target_negative_performed=False,performance_qualified=False,
        application_performance_qualified=False)



def run(args):
    profile_path = args.profile.resolve()
    need(digest(profile_path) == args.profile_sha256, "reviewed profile identity")
    profile = read(profile_path)
    need(profile["contract"] == CONTRACT and profile["status"] == "FROZEN_BEFORE_EMU",
         "frozen profile required")
    need(digest(__file__) == profile["runtime_sha256"], "run source differs from reviewed snapshot")
    check_pins(profile["pins"])
    out = args.output.resolve()
    need(args.output.is_absolute() and not out.exists(), "fresh absolute runtime output")
    need(not any(Path(p).is_relative_to(out) for p in profile["pins"]), "output contains input")
    need(profile["cpu"] == 1 and profile["nice"] == 5, "fixed shared CPU policy")
    os.sched_setaffinity(0, {1})
    os.setpriority(os.PRIO_PROCESS, 0, 5)
    need(os.sched_getaffinity(0) == {1} and os.getpriority(os.PRIO_PROCESS, 0) == 5, "actual CPU1 absolute nice5")
    util = module(profile["helper"], "dot16_q288_runtime_helper", HELPER_SHA)
    gate = module(profile["gate"], "dot16_q288_runtime_gate", GATE_SHA)
    out.mkdir(parents=True)
    cwd = out / "cwd"
    cwd.mkdir()
    argv = [profile["emu"], "-i", profile["image"], "--flash=" + profile["flash"],
            "--ram-size=128MB", "--diff=" + profile["reference"],
            "--max-cycles=" + str(profile["max_cycles"]), "--seed=1"]
    receipt = dict(schema=1, contract=CONTRACT, status="RUNNING", started=util.stamp(),
        profile=str(profile_path), profile_sha256=args.profile_sha256, command=argv, cwd=str(cwd),
        cpu_affinity=sorted(os.sched_getaffinity(0)), nice=os.getpriority(os.PRIO_PROCESS, 0), k=profile["k"],
        budget_seconds=profile["budget_seconds"],
        stream_limit_bytes=profile["stream_limit_bytes"], process_started=False,
        target_runtime_qualified=False, performance_qualified=False,
        full_retirement_window_audited=False, asic_ppa_qualified=False,
        application_performance_qualified=False, full_target_memory_dump=False)
    proc = None
    signals = dict(first=None, count=0)
    def interrupt(signum, frame):
        if signals["first"] is None:
            signals["first"] = signum
        signals["count"] += 1
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    def child_limits():
        limit = profile["stream_limit_bytes"]
        resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
    env = {k: os.environ[k] for k in ("HOME", "PATH") if k in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE="1", LANG="C.UTF-8", LC_ALL="C.UTF-8", TZ="UTC",
               OMP_NUM_THREADS="1")
    save(out / "status.json", receipt)
    try:
        with (out / "stdout.log").open("wb") as stdout, (out / "stderr.log").open("wb") as stderr:
            need(signals["count"] == 0, "cancelled before child launch")
            deadline = time.monotonic() + profile["budget_seconds"]
            proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr,
                                    start_new_session=True, preexec_fn=child_limits)
            receipt.update(process_started=True, pid=proc.pid, pgid=proc.pid)
            save(out / "status.json", receipt)
            print(json.dumps(dict(event="PACKED_WS_EIGHT_WINDOW_PROCESS_STARTED", pid=proc.pid, pgid=proc.pid,
                                  cpu=profile["cpu"], output=str(out))), flush=True)
            while True:
                if signals["count"]:
                    receipt["cancelled"] = True
                    raise InterruptedError("latched runtime signal " + str(signals["first"]))
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    receipt["timed_out"] = True
                    raise TimeoutError("fixed runtime budget exhausted")
                receipt["exit_code"] = proc.poll()
                if receipt["exit_code"] is not None:
                    break
                time.sleep(min(0.25, remaining))
        need(receipt["exit_code"] == 0 and not util.group_exists(proc.pid), "EMU exit/group gate")
        raw = (out / "stderr.log").read_bytes() + (out / "stdout.log").read_bytes()
        checked = guest_check(raw, profile["reference"], profile, gate)
        check_pins(profile["pins"])
        need(digest(profile_path) == args.profile_sha256, "profile changed during run")
        save(out / "checks.json", checked)
        receipt.update(status="PACKED_WS_EIGHT_WINDOW_TARGET_PASS", target_runtime_qualified=True,
            input_identities_unchanged=True, checks_sha256=digest(out / "checks.json"),
            qualification="this fixed packed-Ws eight-window complete-call correctness and CSR observations only")
    except BaseException as exc:
        receipt.update(status="FAILED", error=repr(exc), target_runtime_qualified=False)
        raise
    finally:
        if proc is not None:
            try:
                if util.group_exists(proc.pid):
                    receipt["cleanup_requested"] = True
                    receipt["cleanup_complete"] = util.stop_group(proc)
            except BaseException as exc:
                receipt.update(status="FAILED", target_runtime_qualified=False,
                               cleanup_error=repr(exc))
            receipt["exit_code"] = proc.poll()
            receipt["process_reaped"] = proc.returncode is not None
            receipt["process_group_absent"] = not util.group_exists(proc.pid)
            if not receipt["process_reaped"] or not receipt["process_group_absent"]:
                receipt.update(status="FAILED", target_runtime_qualified=False,
                               cleanup_incomplete=True)
        changes = []
        for path, pin in {**profile["pins"], str(profile_path): args.profile_sha256}.items():
            try:
                actual = digest(path)
                if actual != pin:
                    changes.append(dict(path=path, expected=pin, actual=actual))
            except OSError as exc:
                changes.append(dict(path=path, error=repr(exc)))
        receipt["changed_inputs"] = changes
        receipt["input_identities_unchanged"] = not changes
        if changes:
            receipt.update(status="FAILED", target_runtime_qualified=False,
                           input_identity_error="input changed or unreadable after run")
        receipt["raw_logs"] = {n: dict(bytes=(out / n).stat().st_size, sha256=digest(out / n))
                               for n in ("stdout.log", "stderr.log") if (out / n).exists()}
        receipt["signals"] = dict(signals)
        if signals["count"]:
            receipt.update(status="FAILED", target_runtime_qualified=False, cancelled=True)
        receipt["finished"] = util.stamp()
        save(out / "status.json", receipt)
    need(receipt["status"] == "PACKED_WS_EIGHT_WINDOW_TARGET_PASS", "runtime failed after final checks")
    print(json.dumps(receipt))
    return receipt

if __name__ == '__main__':
    sys.dont_write_bytecode=True
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='mode',required=True)
    a=s.add_parser('preflight')
    for name in ('reference-build','hardware-result','output'):a.add_argument('--'+name,type=Path,required=True)
    a.add_argument('--reference-result-sha256',required=True)
    a.add_argument('--k',type=int,choices=(288,768),required=True)
    a.add_argument('--cpu',type=int,choices=(1,),required=True)
    for name in ('max-cycles','budget-seconds','stream-limit'):a.add_argument('--'+name,type=int,required=True)
    a=s.add_parser('run');a.add_argument('--profile',type=Path,required=True)
    a.add_argument('--profile-sha256',required=True);a.add_argument('--output',type=Path,required=True)
    args=p.parse_args();(preflight if args.mode=='preflight' else run)(args)

#!/usr/bin/env python3
"""Prepare bounded, reversible derivatives of the existing Q288 builder/runner.

No build or guest is launched by this preparer. Existing process ownership,
cleanup, fixture checks and guest parser are retained in the frozen derivatives.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

CONTRACT = 'r3-dot16-whole8-narrow-q288-v1'
BUILDER_SHA = '211e35d232bc941950e20dee1633a1bea90148ba3b02e90ae3e540e0cf4e4d0d'
RUNNER_SHA = 'ed585cfa849358b4ee28eae0cd46afeb56ca089a77c09acdc359b36e765fb55e'
NARROW_SHA = 'e0b36908072fa22d3f6c17ec60807a87750d97af58e5c1d01ba7cee9e5bf6ce3'
WHOLE8_SHA = 'd02068b6714fb268faa526a751c53f601c7e6c46d20a8f20400334906425e448'
MODEL_SHA = '703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82'
WHOLE2_ELF_SHA = '9f7978f3d4be2b8793d979c2e6b84636476fc3547bd7da17441e2076ca9ffde0'
NEW = 'q288_dot16_whole8_narrow'
N_MACHINE_SHA = '050bc3db3e2a70bd6e5409cbf9c139868008e8ccb18776b7e0e7104e6a554b75'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, pin):
    raw = path.read_bytes()
    need(sha(raw) == pin, 'input identity: '+str(path))
    return raw


def module(path, pin, name):
    read(path,pin)
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


class Derivative:
    def __init__(self, raw):
        self.raw=raw
        self.text=raw.decode()
        self.edits=[]

    def replace(self, before, after, count=1):
        actual=self.text.count(before)
        need(actual == count, f'anchor count {actual}!={count}: {before[:120]}')
        self.text=self.text.replace(before,after)
        self.edits.append(dict(before=before,after=after,count=count))

    def finish(self):
        text=self.text
        for edit in reversed(self.edits):
            need(text.count(edit['after']) == edit['count'], 'inverse anchor count')
            text=text.replace(edit['after'],edit['before'])
        need(text.encode() == self.raw, 'whole source inverse')
        compile(self.text,'derived_source','exec')
        return self.text.encode(),dict(original_sha256=sha(self.raw),
            derived_sha256=sha(self.text.encode()), original_reconstructed_byte_exact=True,
            edits=self.edits)


def derive_builder(raw, expected):
    d=Derivative(raw)
    d.replace('Derive one fixed P/whole2/plain-D/FR complete-Q288 image. No EMU.',
              'Derive one fixed P/whole2/whole8-narrow/FR Q288 image. No EMU.')
    d.replace('r3-dot16-whole2-q288-v1',CONTRACT)
    d.replace('WRAPPERS = ("q288_paired16_rvv", "q288_dot16_whole2", "q288_dot16_vdot", "q288_fused_rvv4")',
              'WRAPPERS = ("q288_paired16_rvv", "q288_dot16_whole2", "'+NEW+'", "q288_fused_rvv4")')
    d.replace('ee92c07b7803b04c5340ba4412cb36326b8f5ed42fbf0677fc2f210bcd6711bb',N_MACHINE_SHA)
    d.replace('ORDER = (3, 0, 1, 2, 3, 3, 2, 1, 0, 3)',
              'NARROW_SHA = '+repr(NARROW_SHA)+'\nWHOLE8_SHA = '+repr(WHOLE8_SHA)
              +'\nEXPECTED_N_MACHINE = bytes.fromhex('+repr(expected.hex())+')\n'
              +'ORDER = (3, 0, 1, 2, 3, 3, 2, 1, 0, 3)')
    d.replace('rows.append(dict(stage=0, arm=1, dataset=3))',
              'rows.append(dict(stage=0, arm=2, dataset=3))')
    d.replace('        if index != 1:\n',
              '        if index == 2:\n            need(data == EXPECTED_N_MACHINE, "independent complete N machine proof")\n        elif index != 1:\n')
    d.replace('d_function_bytes=484','d_function_bytes=312')
    d.replace('Path(__file__).resolve(), Path(__file__).with_name("CONTRACT.md").resolve()]',
              'Path(__file__).resolve(), Path(__file__).with_name("CONTRACT.md").resolve(),\n'
              '             args.narrow_generator.resolve(), args.whole8_generator.resolve()]')
    d.replace('    before = {str(p): digest(p) for p in paths}',
              '    need(digest(paths[5]) == NARROW_SHA and digest(paths[6]) == WHOLE8_SHA, "candidate generator identities")\n'
              '    before = {str(p): digest(p) for p in paths}')
    d.replace('("base.zip", "whole2.zip", "process_helper.py", "image.py", "CONTRACT.md")',
              '("base.zip", "whole2.zip", "process_helper.py", "image.py", "CONTRACT.md", "narrow.py", "whole8.py")')
    d.replace('        (source / "fused.S").write_bytes(base_sources["fused.S"] + append.encode())',
              '        narrow = module(inputs / "narrow.py", "narrow_candidate")\n'
              '        _, candidate, candidate_proof = narrow.derive(whole2_raw, narrow.load_whole8(inputs / "whole8.py"))\n'
              '        append += "\\n" + candidate.decode()\n'
              '        (source / "fused.S").write_bytes(base_sources["fused.S"] + append.encode())')
    d.replace('        edits_main = [\n'
              '            ("    q_wrappers[2](&q_context);", "    q_wrappers[1](&q_context);"),\n'
              '            ("    record(0,2,3);", "    record(0,1,3);")]','        edits_main = []')
    d.replace('extern void q288_dot16_whole2(struct q288_context *);"),',
              'extern void q288_dot16_whole2(struct q288_context *);\\nextern void '+NEW+'(struct q288_context *);"),')
    d.replace('q_wrapper const q_wrappers[4] = {q288_paired16_rvv,q288_dot16_whole2,q288_dot16_vdot,q288_fused_rvv4};',
              'q_wrapper const q_wrappers[4] = {q288_paired16_rvv,q288_dot16_whole2,'+NEW+',q288_fused_rvv4};')
    d.replace('original_reconstructed_byte_exact=True, only_existing_whole2_appended=True)',
              'original_reconstructed_byte_exact=True, whole2_and_narrow_appended=True)\n'
              '        proofs["candidate"] = candidate_proof')
    d.replace('enumerate(("P", "W", "D", "FR"))','enumerate(("P", "W", "N", "FR"))')
    d.replace('fullmin=dict(dataset=3, arm=1, kind=0','fullmin=dict(dataset=3, arm=2, kind=0')
    d.replace('DOT16_WHOLE2_Q288_IMAGE_STATIC_PASS','DOT16_WHOLE8_NARROW_Q288_IMAGE_STATIC_PASS')
    d.replace('    p.add_argument("--helper", required=True, type=Path)',
              '    p.add_argument("--helper", required=True, type=Path)\n'
              '    p.add_argument("--narrow-generator", required=True, type=Path)\n'
              '    p.add_argument("--whole8-generator", required=True, type=Path)')
    return d.finish()


def derive_runner(raw, builder_sha, elf_sha, binary_sha):
    d=Derivative(raw)
    d.replace('P/whole2/plain-D/FR','P/whole2/whole8-narrow/FR')
    d.replace('r3-dot16-whole2-q288-v1',CONTRACT)
    for old,new in ((BUILDER_SHA,builder_sha),(WHOLE2_ELF_SHA,elf_sha),
        ('ec900613377b8a023435a4eb88b9d3134e0da011675fc0dc4a45aae57d3149eb',binary_sha)):
        d.replace(old,new)
    d.replace('DOT16_WHOLE2_Q288','DOT16_WHOLE8_NARROW_Q288',5)
    d.replace('dict(P=6, W=7, D=6, FR=10)','dict(P=6, W=6, N=7, FR=10)')
    d.replace('fullmin_arm=1','fullmin_arm=2')
    d.replace('emu=emu, reference=ref, flash=flash, cpu=args.cpu,',
              'emu=emu, reference=ref, flash=flash, cpu=args.cpu, nice=4,\n'
              '        shared_cpu_policy="one extra instance on CPU0; existing four-arm inputs and policy unchanged",')
    d.replace('    os.sched_setaffinity(0, {profile["cpu"]})',
              '    need(profile["cpu"] == 0 and profile["nice"] == 4, "fixed shared CPU policy")\n'
              '    os.sched_setaffinity(0, {profile["cpu"]})\n'
              '    os.setpriority(os.PRIO_PROCESS, 0, profile["nice"])\n'
              '    need(os.getpriority(os.PRIO_PROCESS, 0) == 4, "actual nice=4")')
    d.replace('cpu_affinity=sorted(os.sched_getaffinity(0)), budget_seconds=profile["budget_seconds"],',
              'cpu_affinity=sorted(os.sched_getaffinity(0)), nice=os.getpriority(os.PRIO_PROCESS,0),\n'
              '        budget_seconds=profile["budget_seconds"],')
    return d.finish()


def prepare(a):
    need(a.output.is_absolute() and not a.output.exists(), 'fresh absolute output')
    files={a.builder:BUILDER_SHA,a.runner:RUNNER_SHA,a.narrow_generator:NARROW_SHA,
           a.whole8_generator:WHOLE8_SHA,a.model:MODEL_SHA,a.whole2_elf:WHOLE2_ELF_SHA}
    raws={p:read(p,pin) for p,pin in files.items()}
    n=module(a.narrow_generator,NARROW_SHA,'narrow_derive')
    model=module(a.model,MODEL_SHA,'narrow_elf')
    old=model.ELF(raws[a.whole2_elf]).symbol_data('q288_dot16_whole2')
    expected=n.expected_machine(old)
    need(sha(expected)==N_MACHINE_SHA,'independently expected N machine identity')
    image,proof=derive_builder(raws[a.builder],expected)
    contract=a.contract.read_bytes()
    need(CONTRACT in contract.decode(),'new contract identity')
    a.output.mkdir(parents=True)
    for path,name in ((a.builder,'old-image.py'),(a.runner,'old-run.py'),
                      (a.narrow_generator,'narrow.py'),(a.whole8_generator,'whole8.py')):
        (a.output/name).write_bytes(raws[path])
    (a.output/'image.py').write_bytes(image)
    (a.output/'CONTRACT.md').write_bytes(contract)
    (a.output/'whole2-machine.bin').write_bytes(old)
    (a.output/'expected-machine.bin').write_bytes(expected)
    proof.update(contract=CONTRACT,expected_function_sha256=sha(expected),
        inputs={str(p):pin for p,pin in files.items()},contract_sha256=sha(contract),
        preparer_sha256=sha(Path(__file__).read_bytes()),new_builds=0,new_emu_runs=0)
    (a.output/'builder-derivation.json').write_text(json.dumps(proof,indent=2)+'\n')
    need(all(sha(p.read_bytes())==pin for p,pin in files.items()),'inputs stable')
    print(json.dumps(dict(status='NARROW_Q288_SOURCE_PREPARED',image_builder_sha256=sha(image),
                         expected_function_sha256=sha(expected),output=str(a.output))))


def runner(a):
    need(a.output.is_absolute() and not a.output.exists(),'fresh runner output')
    status=json.loads((a.build/'status.json').read_bytes())
    need(status['status']=='DOT16_WHOLE8_NARROW_Q288_IMAGE_STATIC_PASS'
         and status['contract']==CONTRACT and status['inputs_unchanged']
         and status['generated_inputs_unchanged'] and status['last_process_reaped']
         and status['last_process_group_absent'],'actual completed GNU build')
    bsha=sha((a.build/'inputs/image.py').read_bytes())
    read(a.build/'paired16-target.elf',status['elf_sha256'])
    read(a.build/'paired16-target.bin',status['binary_sha256'])
    raw=read(a.old_runner,RUNNER_SHA)
    new,proof=derive_runner(raw,bsha,status['elf_sha256'],status['binary_sha256'])
    a.output.mkdir(parents=True)
    (a.output/'run.py').write_bytes(new)
    proof.update(contract=CONTRACT,image_builder_sha256=bsha,elf_sha256=status['elf_sha256'],
        binary_sha256=status['binary_sha256'],new_emu_runs=0,
        resource_policy=dict(cpu=0,nice=4,max_cycles=4000000,budget_seconds=9000,
            stream_limit_bytes=16777216,outer_budget_seconds=9600,automatic_retry=False))
    (a.output/'derivation.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(dict(status='NARROW_Q288_RUNNER_PREPARED',runner_sha256=sha(new),
                         output=str(a.output))))


def main():
    sys.dont_write_bytecode=True
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='mode',required=True)
    q=sub.add_parser('prepare')
    for name in ('builder','runner','narrow-generator','whole8-generator','model','whole2-elf','contract','output'):
        q.add_argument('--'+name,required=True,type=Path)
    q=sub.add_parser('runner')
    for name in ('old-runner','build','output'):
        q.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    (prepare if a.mode=='prepare' else runner)(a)


if __name__=='__main__':
    main()

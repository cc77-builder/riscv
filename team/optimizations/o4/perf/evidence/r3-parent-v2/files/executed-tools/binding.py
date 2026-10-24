import pathlib,json,hashlib,re,os
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:4]))
root=pathlib.Path('/home/lizufan/riscv-lab/r3-perf-20261025-0001')
base=pathlib.Path('/home/lizufan/riscv-lab/t17-clean-20261024-0854')
old=base/'clean-02/source'
manifest_raw=(base/'build-01/generated-artifacts.json').read_bytes()
manifest={e['path']:e for e in json.loads(manifest_raw)}
selected={}
for name in ['VDotElastic.sv','ExeUnit_17.sv','WbDataPath.sv','CtrlBlock.sv','Rob.sv']:
 rel='build/rtl/'+name;raw=(old/rel).read_bytes()
 assert hashlib.sha256(raw).hexdigest()==manifest[rel]['sha256'] and len(raw)==manifest[rel]['bytes'],rel
 selected[rel]=manifest[rel]
text=(old/'build/rtl/VDotElastic.sv').read_text()
declarations={}
for prefix in ['pPerf_','rPacket_perfDebugInfo_']:
 found=re.findall(r'(?m)^\s*reg\s+(?:\[(\d+):0\]\s+)?('+prefix+r'\w+);',text)
 fields={name:int(high)+1 if high else 1 for high,name in found}
 assert len(fields)==10 and sum(fields.values())==577,fields
 declarations[prefix]=fields
rob=(old/'build/rtl/Rob.sv').read_text()
latency_names=sorted(set(re.findall(r'\w*[vV][dD][oO][tT]_latency_\w+',rob)))
build=json.loads((base/'build-01/build-state.json').read_text())
records={name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in ['build-01/build-state.json','build-01/hardware-inputs.json','build-01/generated-artifacts.json','build-01/effective-environment.json']}
util=root/'source/utility/src/main/scala/utility/PerfCounterUtils.scala'
lines=util.read_text().splitlines()
report=dict(status='R3_T17_GENERATED_BINDING_PASS',scope='existing observe-profile generated RTL, not new build or ASIC mapping',original_records=records,source_commit=build['source_commit'],flags=build['flags'],cpu_affinity=build['cpu_affinity'],selected_generated=selected,perf_register_declarations=declarations,rob_vdot_latency_names=latency_names,insttable_generated_paths=[name for name in manifest if 'InstTable' in name],perf_counter_utility=dict(sha256=hashlib.sha256(util.read_bytes()).hexdigest(),first=65,last=85,text='\n'.join(lines[64:85])))
out=root/'t17-binding-v1.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
print('T17_ARTIFACT_MATCH',len(selected),'P_R_BITS',[sum(x.values()) for x in declarations.values()])
print('VDOT_COUNTERS',latency_names[:30],'COUNT',len(latency_names))
run=root/'run-02'
commands=json.loads((run/'commands.json').read_text())
faults={p['log'][7:-4]:p['exit_code'] for p in commands if p['log'].startswith('inject-')}
assert len(faults)==20 and set(faults.values())=={1}
assert all(p['exit_code']==0 for p in commands if not p['log'].startswith('inject-'))
inputs=json.loads((run/'source.json').read_text())
assert all(x in inputs for x in ['team/optimizations/o4/perf/audit.py','team/optimizations/o2/parent/check_trace.py','team/optimizations/o2/parent/test_trace.py'])
for name,sha in inputs.items():assert hashlib.sha256((root/'source'/name).read_bytes()).hexdigest()==sha,name
assert (run/'source-after.status').read_text()=='SOURCE_AND_DEPENDENCIES_UNCHANGED\n'
summary=dict(status='R3_RUN_IDENTITY_PASS',source_files=len(inputs),dependencies=len(json.loads((run/'dependencies.json').read_text())),generated_files=len(json.loads((run/'generated-files.json').read_text())),commands=len(commands),negative_cases=faults,original_audit_sha256=inputs['team/optimizations/o4/perf/audit.py'],published_audit_sha256='780f8daa1801fa378d3fa097029e2ddc393d9e906cf4f8a64e27023854326abe',post_change='CLI gzip transport and contract-marker wording; replay algorithm unchanged; raw/gzip both rechecked')
out=root/'run-identity-v1.json';assert not out.exists();out.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))

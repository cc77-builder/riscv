#!/usr/bin/env python3
"""Read-only C2-G0 reset/identity audit. No RTL writes or hardware runs."""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import re
import subprocess
from datetime import datetime, timezone, timedelta

ROOT = Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
OLD = Path('/home/riscv/riscv-lab/o2-r3-div-gate-fullcore-20261024/build-01')
COST = Path('/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025/parent-cost-01/rtl')
OUT = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(rel): return (ROOT / rel).read_text()
def dump(name, value): (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def git(*args): return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
def must(text, pattern): assert re.search(pattern,text,re.S), pattern

def main():
    refs = [
        'AGENTS.md', 'team/docs/collaboration-current.md',
        'src/main/scala/xiangshan/backend/exu/ExeUnit.scala',
        'src/main/scala/xiangshan/backend/Backend.scala',
        'src/main/scala/xiangshan/XSCore.scala',
        'src/main/scala/top/Top.scala',
        'src/test/scala/top/SimTop.scala',
        'src/main/scala/xiangshan/backend/rob/RobBundles.scala',
        'src/main/scala/xiangshan/backend/fu/wrapper/VIDiv.scala',
        'src/main/scala/xiangshan/backend/fu/wrapper/VFDivSqrt.scala',
        'src/main/scala/xiangshan/backend/fu/vector/VecNonPipedFuncUnit.scala',
        'utility/src/main/scala/utility/Hold.scala',
        'utility/src/main/scala/utility/CircularQueuePtr.scala',
        'utility/src/main/scala/utility/ClockGate.scala',
        'utility/src/main/scala/utility/ResetGen.scala',
        'yunsuan/src/main/scala/yunsuan/vector/VectorIdiv/VectorIdiv.scala',
    ]
    generated = [
        'build/emu', 'build/rtl/Backend.sv','build/rtl/ExuBlock_2.sv',
        'build/rtl/ExeUnit_17.sv', 'build/rtl/VIDiv.sv',
        'build/rtl/VFDivSqrt.sv','build/rtl/VectorIdiv.sv',
        'build/rtl/VectorFloatDivider.sv','build/rtl/VectorFloatDividerR64.sv',
        'build/rtl/fpsqrt_vector_r16.sv','build/rtl/ClockGate.sv',
    ]
    extras=[OLD/'generated-artifacts.json',OLD/'hardware-inputs.json',
            COST/'VectorIdiv.sv',COST/'ClockGate.sv',Path(__file__).resolve()]
    paths=[ROOT/r for r in refs+generated]+extras
    before={str(p):sha(p) for p in paths}
    baseline=git('rev-parse','HEAD')
    assert baseline=='0f12df675378556670afd0dd2153f47fcb330610'
    assert not git('diff','HEAD','--','src')
    manifest={r['path']:r for r in json.loads((OLD/'generated-artifacts.json').read_text())}
    generated_results=[]
    for rel in generated:
        assert sha(ROOT/rel)==manifest[rel]['sha256'], rel
        generated_results.append(dict(path=rel,sha256=sha(ROOT/rel),matches_frozen_build=True))
    hw=json.loads((OLD/'hardware-inputs.json').read_text())
    assert hw['source_commit']==baseline
    assert sha(ROOT/'src/main/scala/xiangshan/backend/exu/ExeUnit.scala')==hw['files']['src/main/scala/xiangshan/backend/exu/ExeUnit.scala']
    assert generated_results[0]['sha256']=='2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8'
    # Bind actual reset/control semantics, not parent-fixture assumptions.
    parent=read('build/rtl/ExeUnit_17.sv')
    must(parent, r'always @\(posedge clock or posedge reset\) begin\s+if \(reset\) begin\s+uncer_en_reg <= 1.h0;\s+uncer_en_reg_1 <= 1.h0;\s+elasticDivOccupied_divBusy <= 1.h0;')
    reset_cells=[('VectorIdiv','stateReg',"3'h1"),('VectorFloatDividerR64','fsm_q',"6'h1"),('fpsqrt_vector_r16','fsm_q',"4'h1")]
    for mod,reg,idle in reset_cells:
        t=read('build/rtl/'+mod+'.sv')
        must(t,rf'always @\(posedge clock or posedge reset\) begin\s+if \(reset\)\s+{reg} <= {re.escape(idle)};')
        must(t,rf'assign (?:io_div_in_ready_0|io_start_ready_o|start_ready_o) = {reg}\[0\];')
    must(read('build/rtl/Backend.sv'),r'wire\s+inner_cg_cgen = 1.h0;')
    must(read('build/rtl/Backend.sv'),r'ExuBlock_2 inner_vfExuBlock \(\s+\.clock\s+\(clock\),\s+\.reset\s+\(reset\),')
    must(read('build/rtl/ExuBlock_2.sv'),r'ExeUnit_17 exus_4 \(\s+\.clock\s+\(clock\),\s+\.reset\s+\(reset\),')
    for typ,inst,clock in [('VFDivSqrt','Vfdiv','_ClockGate_Q'),('VIDiv','Vidiv','_ClockGate_1_Q')]:
        must(parent,rf'{typ} {inst} \(\s+\.clock\s+\({clock}\),\s+\.reset\s+\(reset\),')
    must(read('build/rtl/VIDiv.sv'),r'VectorIdiv vidiv \(\s+\.clock\s+\(clock\),\s+\.reset\s+\(reset\),')
    fp=read('build/rtl/VFDivSqrt.sv')
    for lane in [0,1]:
        must(fp,rf'VectorFloatDivider vfdivs_{lane} \(\s+\.clock\s+\(clock\),\s+\.reset\s+\(reset\),')
    vf=read('build/rtl/VectorFloatDivider.sv')
    for typ,inst in [('VectorFloatDividerR64','u_vector_float_divider_r64'),('fpsqrt_vector_r16','u_vector_float_sqrt_r16')]:
        must(vf,rf'{typ} {inst} \(\s+\.clock\s+\(clock\),\s+\.reset\s+\(reset\),')
    must(vf,r'assign io_start_ready_o =\s+_u_vector_float_divider_r64_io_start_ready_o & _u_vector_float_sqrt_r16_start_ready_o;')
    must(fp,r'assign io_in_ready_0 = _vfdivs_0_io_start_ready_o & _vfdivs_1_io_start_ready_o;')
    must(fp,r'assign io_out_valid_0 = _vfdivs_0_io_finish_valid_o & _vfdivs_1_io_finish_valid_o;')
    assert 'always @(posedge clock or posedge reset)' not in (COST/'VectorIdiv.sv').read_text()
    must((COST/'VectorIdiv.sv').read_text(),r'always @\(posedge clock\) begin\s+if \(reset\)\s+stateReg <= 3.h1;')
    gate=read('build/rtl/ClockGate.sv')
    must(gate,r'if\(!CK\) EN = TE \| E;')
    must(gate,r'assign Q = CK & EN;')
    # Verify the exact TE chain for VFEX4; no accidental selection of another EXU.
    bblock=re.search(r'  ExuBlock_2 inner_vfExuBlock \((.*?)\n  \);',read('build/rtl/Backend.sv'),re.S).group()
    eblock=re.search(r'  ExeUnit_17 exus_4 \((.*?)\n  \);',read('build/rtl/ExuBlock_2.sv'),re.S).group()
    for idx in [10,11,12]:
        must(bblock,rf'\.cg_bore_{idx}_cgen\s+\(inner_cg_cgen\)')
    for port,idx in [('cg_bore_cgen',10),('cg_bore_1_cgen',11),('cg_bore_2_cgen',12)]:
        must(eblock,rf'\.{port}\s+\(cg_bore_{idx}_cgen\)')
    for signal,port in [('Vfdiv_clock_te_cgen','cg_bore_cgen'),('Vidiv_clock_te_cgen','cg_bore_1_cgen')]:
        must(parent,rf'wire\s+{signal} = {port};')
        must(parent,rf'\.TE \({signal}\)')
    # Source-bound capture/dispatch/flush obligations.
    ex=read('src/main/scala/xiangshan/backend/exu/ExeUnit.scala')
    for needle in [
        'val divAccept = io.in.fire && io.in.bits.fuType =/= FuType.vdot.U',
        'val divRobIdx = RegEnable(io.in.bits.robIdx, divAccept)',
        'val divCancelled = divBusy && divRobIdx.needFlush(io.flush)',
        'fu.io.out.fire || elasticDivCancelled.get',
        'fu.io.flush <> io.flush',
        'val allowInput = !elasticDivOccupied.get &&',
        '!io.flush.valid && !reset.asBool',
        'sink.bits.ctrl.robIdx      := source.bits.robIdx']:
        assert needle in ex,needle
    must(read('src/main/scala/xiangshan/backend/fu/vector/VecNonPipedFuncUnit.scala'),r'outCtrl\s+= DataHoldBypass\(io.in.bits.ctrl, io.in.fire\)')
    must(read('utility/src/main/scala/utility/Hold.scala'),r'Mux\(valid, data, RegEnable\(data, valid\)\)')
    for wrapper in ['VIDiv','VFDivSqrt']:
        t=read('src/main/scala/xiangshan/backend/fu/wrapper/'+wrapper+'.scala')
        must(t,r'when\(io.in.ready\)\{\s+thisRobIdx := io.in.bits.ctrl.robIdx\s+\}.otherwise\{\s+thisRobIdx := outCtrl.robIdx')
        assert 'thisRobIdx.needFlush(io.flush)' in t
    # Independent circular-ROB spellings, all 128 encoded pointers in MinimalConfig.
    def parent_flush(p,r,valid,self_):
        pf,pv=divmod(p,64);rf,rv=divmod(r,64)
        return bool(valid and ((self_ and p==r) or (bool(pf^rf)^bool(pv>rv))))
    def child_flush(p,r,valid,self_):
        if not valid:return False
        pf,pv=divmod(p,64);rf,rv=divmod(r,64)
        older_redirect = (pv>rv) if pf==rf else (pv<=rv)
        return older_redirect or (self_ and pf==rf and pv==rv)
    comparisons=0; kills=0; equality_self=0;wrap_cases=0
    for p,r,valid,self_ in itertools.product(range(128),range(128),(0,1),(0,1)):
        a=parent_flush(p,r,valid,self_);b=child_flush(p,r,valid,self_)
        assert a==b
        comparisons+=1;kills+=a
        equality_self += bool(valid and self_ and p==r and a)
        wrap_cases += bool(valid and (p//64 != r//64) and a)
    # Mutation rejects lost ROB identity; no assertion assumes all redirects kill.
    mutation=None
    for p,stale,r,self_ in itertools.product(range(128),range(128),range(128),(0,1)):
        if p!=stale and parent_flush(p,r,1,self_)!=child_flush(stale,r,1,self_):
            mutation={'parent_rob':p,'stale_child_rob':stale,'redirect':r,'self':self_,
                      'parent_kill':parent_flush(p,r,1,self_),'child_kill':child_flush(stale,r,1,self_)}
            break
    assert mutation is not None
    # For an accepted current DIV, both parent and child capture the same input.
    # Combinational parent valid is disabled while B=1, so no intervening recapture.
    # Child clock is open on acceptance (E=fire|hold), then hold supplies cancel edge.
    gate_cases=[]
    for fire,hold,kill,outfire in itertools.product((0,1),repeat=4):
        old_e=bool(fire or hold)
        next_h=bool(fire or (hold and not(kill or outfire)))
        if hold and (kill or outfire) and not fire:
            assert old_e and not next_h
            gate_cases.append({'fire':fire,'old_hold':hold,'cancel':kill,
                               'outfire':outfire,'cancel_edge_open':old_e,'next_hold':next_h})
    # Two-state illustrative event examples; these are not gate-level simulations.
    probes={
      'real_async_cold_reset_TE0': {'before':{'B':1,'HI':1,'HF':1,'int_state':2,'div0':8,'sqrt0':4,'div1':32,'sqrt1':8,'EN_I':0,'EN_F':0,'TE':0},
        'event':'shared posedge reset, no clock edge',
        'after':{'B':0,'HI':0,'HF':0,'int_state':1,'div0':1,'sqrt0':1,'div1':1,'sqrt1':1,'RI':1,'RF':1},
        'explanation':'Async state blocks assign IDLE directly; gate EN/TE is irrelevant to reset.'},
      'sync_fixture_TE0_uninitialized_negative_control':{
        'before':{'B':0,'HI':0,'HF':0,'int_state':0,'EN_I':0,'TE':0,'valid':0},
        'events':['assert reset','parent clock posedge','deassert reset'],
        'after':{'B':0,'HI':0,'int_state':0,'RI':0,'gate_edges':0},
        'interpretation':'An uninitialized synchronous gated child cannot be initialized with a closed clock. This is not the verified full-core AsyncReset configuration.'}}
    assert probes['real_async_cold_reset_TE0']['after']['RI']==1
    assert probes['sync_fixture_TE0_uninitialized_negative_control']['after']['RI']==0
    dump('rob-exhaustive.json',dict(status='PASS',pointer_values=128,comparisons=comparisons,
         kill_rows=kills,equality_self_rows=equality_self,wrap_kill_rows=wrap_cases,
         stale_identity_mutation_detected=mutation,scope='Boolean needFlush equivalence under proven common captured ROB; not independent whole RTL equivalence'))
    dump('reset-edge-probes.json',probes)
    dump('hold-edge-check.json',dict(status='PASS',all_truth_table_rows=16,release_examples=gate_cases,
         scope='Latch-low-phase/next-rising-edge model; cancel sampled synchronously, no analog timing proof'))
    after={str(p):sha(p) for p in paths}
    assert before==after
    dump('inputs.json',{'files':[{'path':p,'sha256':s,'bytes':Path(p).stat().st_size} for p,s in before.items()]})
    dump('generated-identity.json',{'frozen_manifest':str(OLD/'generated-artifacts.json'),
          'manifest_sha256':sha(OLD/'generated-artifacts.json'),'source_commit':baseline,
          'config':hw['config'],'profile':hw['profile'],'artifacts':generated_results})
    summary={'status':'C2_G0_RESET_IDENTITY_REVIEW_PASS','time':datetime.now(timezone(timedelta(hours=8))).isoformat(),
             'source_commit':baseline,'input_files':len(before),'inputs_unchanged':True,
             'frozen_generated_files_verified':len(generated),'ROB_comparisons':comparisons,
             'actual_fullcore_reset':'shared asynchronous active-high reset, all ready-producing FSMs reset to IDLE',
             'TE':'actual MinimalConfig constant zero; not required for async reset',
             'fixture_reset':'synchronous; requires reset clock edge. Negative control is out of fullcore domain.',
             'RTL_mutations':0,'GitHub_writes':0,'hardware_or_EDA_runs':0,
             'proof_boundary':'Static reset connectivity/control audit and finite helper checks. Overall reachable-state invariant is main-agent model obligation.'}
    dump('summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

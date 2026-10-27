from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,shutil,subprocess,zipfile
R=Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
W=Path('/home/riscv/riscv-lab/software-import-20261026')
OUT=W/'c8-package-01'
REVIEW=W/'reviews/c8-package-root-01'
P=R/'team/optimizations/o2/integration/firstdot-v2-0f/package/c8'
WIN=Path('/mnt/d/yanyi/riscv大赛/doc/firstdotV2选择性集成_20261026')
now=lambda:datetime.now(timezone(timedelta(hours=8))).isoformat()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def save(p,j):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def identity(p):
    return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
report=read(OUT/'report.json')
assert report['status']=='CURRENT_C8_MINIMAL_PACKAGE_STATIC_PASS'
assert read(REVIEW/'pipeline.command.json')['exit_code']==0
base=read(REVIEW/'baseline.json')
for rel,digest in base['src'].items():assert sha(R/rel)==digest,rel
for file,digest in base['old'].items():assert sha(file)==digest,file
assert not subprocess.check_output(['git','diff','HEAD','--','src'],cwd=R)
design=read(P.parent/'c8-design-inputs.json')
for file,item in design['protected_files'].items():assert sha(file)==item['sha256'],file
for file,digest in read(OUT/'source-inputs.json').items():assert sha(file)==digest,file
for file,digest in read(REVIEW/'source-v1.json').items():assert sha(P/file)==digest,file
# Preserve complete local output/commands and trial snapshots; do not copy old target logs.
archive=W/'reviews/c8-package-final-archive-01'
archive.mkdir()
members=[]
with zipfile.ZipFile(archive/'evidence.zip','x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    roots={'validation':OUT,'root-review':REVIEW,
           'public-smoke-v1':W/'reviews/c8-public-agent-01',
           'public-guards-v2':W/'reviews/c8-public-agent-02'}
    for role,root in roots.items():
        for f in sorted(root.rglob('*')):
            if not f.is_file():continue
            assert not f.is_symlink(),f
            raw=f.read_bytes();name=role+'/'+str(f.relative_to(root))
            z.writestr(name,raw)
            members.append({'member':name,'source':str(f),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
with zipfile.ZipFile(archive/'evidence.zip') as z:
    assert len(z.namelist())==len(members)
    for item in members:assert hashlib.sha256(z.read(item['member'])).hexdigest()==item['sha256']
save(archive/'manifest.json',{'status':'LOCAL_C8_PACKAGE_ARCHIVE_READBACK_PASS','created':now(),
    'archive':identity(archive/'evidence.zip'),'members':members,
    'scope':'Static evidence plus original trial/command logs; historical runtime archives referenced, not duplicated.'})
sdkzip=WIN/'8x32最小软件包.zip'
assert not sdkzip.exists()
with zipfile.ZipFile(sdkzip,'x',zipfile.ZIP_DEFLATED) as z:
    for f in sorted((OUT/'sdk').rglob('*')):
        if f.is_file():z.write(f,'c8-sdk/'+str(f.relative_to(OUT/'sdk')))
with zipfile.ZipFile(sdkzip) as z:
    for f in (OUT/'sdk').rglob('*'):
        if f.is_file():assert z.read('c8-sdk/'+str(f.relative_to(OUT/'sdk')))==f.read_bytes()
e=P/'evidence';e.mkdir()
for n in ['report.json','state.json','tools.json','source-inputs.json']:
    shutil.copyfile(OUT/n,e/n)
for n in ['qualification.json','matrix-raw-audit.json','c8-raw-audit.json']:
    shutil.copyfile(OUT/'qualification'/n,e/n)
for n in ['pipeline.command.json','pipeline.command.stdout.log','pipeline.command.stderr.log',
          'host-tests.command.json','host-tests.stdout.log','host-tests.stderr.log']:
    shutil.copyfile(REVIEW/n,e/n)
# Text command receipts/logs; exclude ar-p binary stdout from daily source materials.
for f in sorted(OUT.rglob('*.command.json')):
    rel=f.relative_to(OUT)
    for suffix in ['.command.json','.stdout.log','.stderr.log']:
        sibling=Path(str(f).replace('.command.json',suffix))
        if not sibling.exists() or rel.as_posix()=='archive/extract.command.json' and suffix=='.stdout.log':continue
        dst=e/'commands'/sibling.relative_to(OUT);dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(sibling,dst)
shutil.copyfile(OUT/'sdk/manifest.json',e/'sdk-manifest.json')
save(e/'archive-reference.json',{'manifest':identity(archive/'manifest.json'),
    'archive':identity(archive/'evidence.zip'),'members':len(members),'windows_sdk':identity(sdkzip)})
record_id='C8-PACKAGE-DIVFIX0F-CLEAN02-20261027-01'
record={'record_id':record_id,'status':report['status'],'recorded_at':now(),
    'scope':'Independent opt-in C8 source aliases, complete single-member static library and relocatable-link qualification',
    'contract':report['contract'],'source_commit':base['head'],
    'selected_hardware_commit':report['qualification']['current_identity']['selected_hardware_commit'],
    'hardware_identity':report['qualification']['current_identity'],
    'configuration':{'hardware':'MinimalConfig, one core, VLEN exactly128, existing0f O2+H1+DIV cancel hold fix',
        'target_abi':'RV64 lp64d / Nexus-AM bare metal, VS enabled',
        'assembly_flags':['-march=rv64gcv','-mabi=lp64d','-mno-relax'],
        'link_flags':['-r','--no-relax'],'toolchain':report['toolchain']},
    'input_identities':{'binding':identity(OUT/'qualification/qualification.json'),
        'sdk_manifest':identity(OUT/'sdk/manifest.json'),'sources':identity(OUT/'source-inputs.json'),
        'object':report['independent_object'],'prior_c_bin_sha256':'56805506eb98b68269c73a3645d8f75dff73b697e30dec5f93ccc4716089ad34'},
    'comparison':{'authority':'Independently assembled full object equals qualified C8 object; full caller.o/linked.o versus explicit expected callees',
        'modes':report['alias_modes'],'cycles':'NOT_TESTED'},
    'execution':{'pipeline':read(REVIEW/'pipeline.command.json'),'new_emu_runs':0,'new_nemu_runs':0,
        'command_receipts':115,'host_unit_tests':22,'python_optimization_guard_negatives':3},
    'metrics':{'object_bytes':27160,'library_bytes':(OUT/'sdk/libxs_gemv_c8.a').stat().st_size,
        'defined_functions':16,'new_runtime_wrapper_symbols':0,'alias_modes':4,
        'required_force_modes':3,'extra_expanded_literal_mode':1,'integration_negative_controls':17,
        'coexistence_cases':16,'moved_examples':2,
        'historical_matrix_processes_reaudited':33,'historical_c_processes_reaudited':3,'leaf_anchors':48},
    'verification':{'static_package':'PASS','full_object_equality':'PASS','caller_and_link_equality':'PASS',
        'exact_symbol_relocations':'PASS','all_linked_undefined_empty':'PASS',
        'negative_controls':'PASS','moved_sdk':'PASS','host_tests':'PASS',
        'historical_raw_evidence':'REVALIDATED','new_example_runtime':'NOT_TESTED',
        'new_final_elf':'NOT_TESTED','new_cycles':'NOT_TESTED','new_area_sta_power':'NOT_TESTED'},
    'prior_performance':{'source_record':'CONFIG-REUSE-MATRIX-DIVFIX0F-CLEAN02-20261027-01',
        'reused_not_remeasured':True,'shape':'8x32','firstdot_cycles':282.25,'config_reuse_cycles':273,
        'fastest_same_window_rvv_cycles':299,'speedup':299/273,'formal_samples_per_cell':12},
    'prior_functional_record':'CONFIG-REUSE-C8-DIVFIX0F-CLEAN02-20261027-02',
    'decision':{'current':'ACCEPT_EXPLICIT_OPT_IN_C8_STATIC_PACKAGE','default_changed':False,
        'hardware_changed':False,'github_uploaded':False,
        'next':'Use explicit C8 package; new real application/final image requires scoped runtime contract; separately attribute4x8/16x64 control drift.'},
    'preserved_development':{'public_smoke_01':'Passed before replacing optimization-bypassable assert guards',
        'public_guards_02':'Fixed explicit checks; rejected wrongsource/reusedoutput/inside-repo output with Python optimization',
        'integrated_pipeline_01':'PASS first attempt; no rerun/selective data removal'},
    'evidence':{'archive_manifest':identity(archive/'manifest.json'),'archive_members':len(members),
        'report':identity(OUT/'report.json'),'pipeline':identity(REVIEW/'pipeline.command.json'),
        'sdk_zip':identity(sdkzip),'new_package_source_pins':read(REVIEW/'source-v1.json')},
    'limitations':['No new target execution or end-to-end performance claim.',
        'Complete object/archive and tested relocatable callers are equal; no claim of arbitrary final application layout equivalence.',
        'VLEN exactly128, full128-bit output slots and existing CSR clobber contract remain mandatory.',
        'FORCE_RVV changes call target only; complete archive still contains unused customvdot.',
        'Agent audit and local byte archive are not human signoff or a new independent machine reproduction.']}
save(P/'record.json',record)
result=r"""# 8×32 最小 C8 软件包验收

**结果：PASS，可作为独立、显式选用的 C8 静态软件包使用。** 当前软件源码基点 c823a8786e052c6e26f6915563c42b6d730dd8e3，硬件保持 0f12df675378556670afd0dd2153f47fcb330610（O2＋H1＋DIV取消保持修复）。

本轮实现 §selected_gemv_c8.h§、完整单对象库构建、调用示例、当前身份验证器和主机测试。未切换旧四尺寸默认入口，未修改生产 RTL，未提交或上传 GitHub。执行者 @cc77-builder / Agent；本地包验收不是成员人工验收。

## 实际结果

| 验收项 | 本轮结果 |
| --- | --- |
| GNU 构建 | 固定 rv64gcv/lp64d/mno-relax，独立重建完整对象与原 C8 已验证对象全字节相同 |
| 完整对象 | 27,160 bytes；SHA256 f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3 |
| 静态库 | libxs_gemv_c8.a，仅一个完整 gemv.o；ar t/p、独立归档、确定性字节一致 |
| 符号与节 | 16 个原公共函数；单一16字节对齐.text；原对象无重定位；新增运行时别名/包装函数为0 |
| 别名与链接 | 缺省、0、1及宏展开为1共4模式；两个别名的 caller.o/linked.o 与直接调用逐字节相同 |
| 实际引用 | 每模式核对2个有序指针重定位、2个调用重定位；GNU可重定位链接后未解析符号为空 |
| 错误配置拒绝 | 17项集成负控：10种非法宏、4种错误别名、错误对象、错误库、缺失头文件 |
| 旧入口共存 | V1/V2分别与C8，两个包含顺序×旧新开关0/1，共16组，选择与版本保持 |
| 搬移 | SDK移到仓库外含空格目录；默认vdot及强制RVV示例均按文档flags编译/链接通过 |
| 主机检查 | 22项unittest通过，包括错误硬件/NEMU、混合配置、缺失数据集、伪造历史C资格及改哈希后错选择拒绝 |
| 构建门禁 | 额外3项Python优化模式负控通过：旧输出、仓库内输出、错误源码仍被拒绝 |
| 原始资格 | 当前0f身份及完整输入闭包复核；原33个矩阵进程＋3个C进程重审，48次叶函数锚点通过 |
| 新目标运行 | 0 EMU、0 NEMU；新示例运行、新最终ELF、新周期、面积/STA/功耗均为NOT_TESTED |

完整验收流水线：2026-10-27T21:36:30.342114+08:00 至 2026-10-27T21:38:56.981151+08:00，exit0；115份命令回执。新包首次集成验收即通过，原始输出与预期失败负控全部保留。

## 如何选用

使用 [构建与调用说明](README.md) 和 [完整 ABI 合同](CONTRACT.md)。头文件提供：

~~~c
#include "selected_gemv_c8.h"
xs_c8_gemv_8x32(packed_ax, slots);      /* configuration reuse vdot */
xs_c8_gemv_8x32_rvv(packed_ax, slots);  /* explicit reuse RVV */
~~~

§XS_C8_GEMV_FORCE_RVV=1§ 将默认入口也选为 RVV；缺省或0为vdot。仅接受最终展开为字面量0或1，切换后重编相关翻译单元。

必须是 **VLEN恰好128**、VS已启用和已验证的RV64/lp64d平台。输入为16字节对齐的288字节有符号INT8 A[8][32]||x[32]；输出是16字节对齐的8×16字节槽，共128字节，输入输出不重叠。每槽低32位为结果、高96位清零。输出不能当作紧密的 int32_t[8]。原向量状态/CSR效果保持，详见合同。

完整库仍有16个函数及未调用vdot代码；显式RVV不等于纯RVV镜像或跨平台自动检测。旧 firstdot 包与四尺寸默认均保持。

## 性能含义与下一步

本轮证明新编译期入口在被测试的调用对象和可重定位链接中没有新增包装代码，并正确复用了已验证的同一完整对象。它不是新的性能测试，也不证明任意最终应用的布局或周期都相同。

此前第25条矩阵数据继续有效：8×32配置复用273.00 cycles，firstdot282.25，最快同场RVV299.00，加速比1.095238×；每格12正式样本。本轮没有把这些数值重新标成新实测。

最小包目标已完成。下一步若接入实际应用或产生新的最终ELF，先固定新调用布局/窗口合同，再做受影响路径的全128位正确性、差分拒错/恢复与重放；性能比较须用同路径firstdot/RVV对照。纯宏别名不需要新增wrapper。如果新增wrapper、dispatcher或CSR保护，需新的控制流检查，不能借用旧唯一jal/ret门禁。其他尺寸的4×8/16×64控制漂移仍可独立只读归因，4×13保留RVV。

## 证据与工程记录

- [机器可读记录](record.json)；[GNU与静态结果](evidence/report.json)；[当前资格绑定](evidence/qualification.json)。
- [固定输入](INPUTS.json)；[原文审计/构建工具](verify_c8_package.py)；[主机测试](test_c8_package.py)。
- [矩阵原文重审](evidence/matrix-raw-audit.json)；[C调用原文重审](evidence/c8-raw-audit.json)。
- [归档索引](evidence/archive-reference.json)；§evidence/commands/§保留115份命令及文本日志，ar提取的二进制stdout保留在完整外部归档。
- 原始输出：/home/riscv/riscv-lab/software-import-20261026/c8-package-01。
- 外部完整归档：/home/riscv/riscv-lab/software-import-20261026/reviews/c8-package-final-archive-01。
- 记录ID：C8-PACKAGE-DIVFIX0F-CLEAN02-20261027-01，统一版本档案第27条。

初版Makefile烟雾测试通过后，审查发现assert可能被Python优化模式跳过，改为显式退出并验证三项门禁；修正前后材料均保留。没有降低旧运行门禁、更新旧对象哈希或覆盖历史失败。
"""
result=result.replace('§',chr(96))
(P/'RESULT.md').write_text(result)
ledgerp=R/'team/docs/version-data-ledger.json'
ledger=read(ledgerp);assert len(ledger['records'])==26
old_records=json.loads(json.dumps(ledger['records']))
ledger['records'].append(record);ledger['last_append_at']=now();ledger['last_append_note']=record_id
save(ledgerp,ledger)
assert read(ledgerp)['records'][:26]==old_records
mdp=R/'team/docs/version-data-ledger.md'
old_md=mdp.read_text()
mdp.write_text(old_md+'\n\n## 17. 独立8×32 C8最小软件包（第27条）\n\n'+result.replace('# 8×32 最小 C8 软件包验收\n\n','',1).replace('## ','### '))
assert mdp.read_text().startswith(old_md)
route=R/'team/docs/development-route-current.md'
txt=route.read_text()
old=next(line for line in txt.splitlines() if line.startswith('> 8×32稳定入口评审'))
new='> 8×32稳定入口最小C8包已实现并验收：独立显式入口、两个编译期别名和完整单对象库；GNU整对象/调用/链接等价、17项集成负控、16组头文件共存及含空格目录搬移通过，22主机测试通过。见[结果](../optimizations/o2/integration/firstdot-v2-0f/package/c8/RESULT.md)。当前0f原33+3进程已重新审计，0新EMU/NEMU；记录27为静态包资格，新应用/最终ELF/性能/PPA仍NOT_TESTED。下一步按需要接入实际应用并固定受影响路径合同；4×8/16×64控制漂移可独立只读归因，4×13保留RVV。旧入口和默认保持，未上传。'
route.write_text(txt.replace(old,new))
readme=R/'team/README.md'
txt=readme.read_text()
txt+='\n- [独立8×32 C8软件包：构建、选用与验收](optimizations/o2/integration/firstdot-v2-0f/package/c8/RESULT.md)。\n'
readme.write_text(txt)
board=R/'开发计分板.md'
with board.open('a') as f:
    f.write(f'\n\n## 2026-10-27 独立8×32 C8最小软件包\n\n- 执行者：@cc77-builder / Agent；操作ID：20261027-cc77-builder-c8-package；开发区间：{base["started"]} 至 {now()}（UTC+08:00）；主机自动验证与等待不计成员人工投入。\n'
        '- 成果：新增独立C8头、完整27160-byte单对象库构建、示例、当前资格适配及测试；默认/0/1及展开1调用/链接全字节等价，17集成负控、16共存、2搬移模式和22主机检查通过。构建门禁另覆盖3项Python优化模式拒错。\n'
        '- 验证：首次完整流水线21:36:30至21:38:56+08 exit0，115命令回执；当前0f与原33矩阵+3C进程重审、48叶锚通过。0新EMU/NEMU；新应用运行、最终ELF、周期、面积/STA/功耗均NOT_TESTED。完整对象/宏别名证据不扩大到任意最终应用布局。\n'
        '- 身份与证据：[包结果](team/optimizations/o2/integration/firstdot-v2-0f/package/c8/RESULT.md)、[数据档案](team/docs/version-data-ledger.md)第27条；源码c823a/硬件0f。旧149项设计输入和398生产源码文件未变。局部烟雾测试原件及assert门禁修正前后均留档。\n'
        '- 接续：最小包完成，可显式选用；若接入真实应用，先固定新最终映像/路径合同并按影响验证，需性能时同路径公平比较。另可继续4×8/16×64控制差异只读归因，4×13保留RVV。旧默认及RTL保持，未提交/推送GitHub，未发布Issue消息。\n')
# Windows mirrors are delivery copies; repository remains authoritative.
for src,name in [(P/'RESULT.md','8x32最小软件包_验收结果.md'),(P/'record.json','8x32最小软件包_数据.json'),
                 (P/'README.md','8x32最小软件包_使用说明.md'),(P/'CONTRACT.md','8x32最小软件包_调用合同.md'),
                 (ledgerp,'各版本运行数据档案.json'),(mdp,'各版本运行数据档案.md')]:
    shutil.copyfile(src,WIN/name)
# Standalone result mirror must not expose broken repo-relative evidence hyperlinks.
win_text=result.replace('(README.md)','(8x32最小软件包_使用说明.md)').replace('(CONTRACT.md)','(8x32最小软件包_调用合同.md)')
# Remaining evidence links point to the actual WSL authority.
import re
win_text=re.sub(r'\]\(([^)]+)\)',lambda m: m.group(0) if m.group(1).startswith('8x32') else
    ']('+str(P/m.group(1))+')',win_text)
(WIN/'8x32最小软件包_验收结果.md').write_text(win_text)
(WIN/'当前进度.md').write_text('# 当前进度\n\n8×32独立C8最小软件包已经实现并通过GNU、整对象、别名与可重定位链接等价、拒错和搬移验收。\n\n'
    '详见[验收结果](8x32最小软件包_验收结果.md)、[使用说明](8x32最小软件包_使用说明.md)、[软件包](8x32最小软件包.zip)。\n\n'
    '版本档案追加第27条。硬件仍是O2＋H1＋DIV取消保持修复（0f），旧默认保持。原33+3进程已重审，0新EMU/NEMU，新示例运行/最终ELF/周期/PPA为NOT_TESTED；旧1.095238×不是本轮新测。未上传GitHub。\n\n'
    '下一步按需要接入真实应用，先固定新路径/最终映像合同再验证；其他尺寸控制差异可独立只读归因。\n')
save(REVIEW/'delivery.json',{'time':now(),'record_id':record_id,'archive_manifest':identity(archive/'manifest.json'),
    'sdk_zip':identity(sdkzip),'source_unchanged':398,'design_inputs_unchanged':len(design['protected_files']),
    'ledger_records':27,'prior_records_preserved':True,'result':str(P/'RESULT.md')})
print(json.dumps({'record_id':record_id,'archive_members':len(members),'ledger_records':27,
    'sdk_zip':str(sdkzip),'evidence_bytes':sum(f.stat().st_size for f in e.rglob('*') if f.is_file())}))

from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,shutil,subprocess,zipfile,re
R=Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
W=Path('/home/riscv/riscv-lab/software-import-20261026')
OUT=W/'c8-relink-01'; REVIEW=W/'reviews/c8-relink-root-01'
P=R/'team/optimizations/o2/integration/firstdot-v2-0f/package/c8/relink'
WIN=Path('/mnt/d/yanyi/riscv大赛/doc/firstdotV2选择性集成_20261026')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
now=lambda:datetime.now(timezone(timedelta(hours=8))).isoformat()
def save(p,j):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def ident(p):
    return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
report=read(OUT/'report.json');base=read(REVIEW/'baseline.json')
assert report['status']=='C8_EXISTING_C_FINAL_IMAGE_EQUIVALENCE_PASS'
assert read(REVIEW/'pipeline.command.json')['exit_code']==0
assert read(REVIEW/'postcheck/result.json')['status']=='GNU_STRIP_DEBUG_THREE_WAY_FULL_ELF_EQUAL'
for rel,h in base['src'].items():assert sha(R/rel)==h
for path,h in base['old_package'].items():assert sha(path)==h
for path,h in read(OUT/'source-inputs.json').items():assert sha(path)==h
assert not subprocess.check_output(['git','diff','HEAD','--','src'],cwd=R)
ledgerp=R/'team/docs/version-data-ledger.json'
assert sha(ledgerp)==sha(REVIEW/'before-version-data-ledger.json')
assert sha(R/'team/docs/version-data-ledger.md')==sha(REVIEW/'before-version-data-ledger.md')
archive=W/'reviews/c8-relink-final-archive-01';archive.mkdir()
members=[]
with zipfile.ZipFile(archive/'evidence.zip','x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for role,root in [('validation',OUT),('review',REVIEW)]:
        for f in sorted(root.rglob('*')):
            if not f.is_file():continue
            assert not f.is_symlink()
            name=role+'/'+str(f.relative_to(root));raw=f.read_bytes();z.writestr(name,raw)
            members.append({'member':name,'source':str(f),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
with zipfile.ZipFile(archive/'evidence.zip') as z:
    for item in members:assert hashlib.sha256(z.read(item['member'])).hexdigest()==item['sha256']
save(archive/'manifest.json',{'status':'C8_RELINK_LOCAL_ARCHIVE_READBACK_PASS','created':now(),
    'archive':ident(archive/'evidence.zip'),'members':members,
    'scope':'Local static builds and exact-image reuse evidence; not a new target run or independent machine reproduction.'})
shutil.copytree(OUT/'integrated/source',P/'source')
e=P/'evidence';e.mkdir()
for n in ['report.json','state.json','build-dependencies.json','source-inputs.json','control-vs-integrated.json','nonload-positive.json']:
    shutil.copyfile(OUT/n,e/n)
shutil.copytree(OUT/'qualification',e/'qualification')
for name in ['control','integrated']:
    (e/name).mkdir()
    for file in ['equivalence.json','link.map']:
        shutil.copyfile(OUT/name/file,e/name/file)
    shutil.copytree(OUT/name/'commands',e/name/'commands')
shutil.copytree(OUT/'negative/wrong-library',e/'wrong-library',ignore=shutil.ignore_patterns('*.a','*.elf'))
for name in ['pipeline.command.json','pipeline.command.stdout.log','pipeline.command.stderr.log']:
    shutil.copyfile(REVIEW/name,e/name)
shutil.copytree(REVIEW/'postcheck',e/'postcheck',ignore=shutil.ignore_patterns('*.elf'))
record_id='C8-RELINK-DIVFIX0F-CLEAN02-20261027-01'
record={'record_id':record_id,'status':report['status'],'recorded_at':now(),
    'scope':'Qualified C8 SDK reconnected to original ordinary C fixture; complete loaded image and input plan equivalence',
    'contract':report['contract'],'source_commit':base['head'],
    'selected_hardware_commit':report['binding']['identity']['selected_hardware_commit'],
    'hardware_identity':report['binding']['identity'],
    'parent_records':[report['prior_functional_record'],report['prior_package_record']],
    'configuration':{'hardware':'Current0f O2+H1+DIV cancel hold fix, MinimalConfig, one core, VLEN128',
        'platform':'Existing Nexus-AM riscv64-xs, GNU rv64gcv/lp64d',
        'selection':'Default C8 reusevdot, explicit C8 reuseRVV; other14 public functions retained',
        'am_libraries':'Frozen existing AM/klib reused read-only',
        'toolchain':report['toolchain']},
    'input_identities':{'fixed_roles':ident(P/'INPUTS.json'),
        'protected_inputs':ident(OUT/'qualification/protected-inputs.json'),
        'protected_files':report['binding']['protected_files'],
        'build_dependencies':ident(OUT/'build-dependencies.json'),
        'original_bin_sha256':report['comparisons']['integrated']['bin_sha256'],
        'original_elf_sha256':report['comparisons']['integrated']['original_elf_sha256'],
        'integrated_elf_sha256':report['comparisons']['integrated']['candidate_elf_sha256'],
        'integrated_sources':report['builds']['integrated']['sources']},
    'comparison':{'original_vs_control':report['comparisons']['control'],
                  'original_vs_integrated':report['comparisons']['integrated'],
                  'control_vs_integrated':report['comparisons']['control_vs_integrated'],
                  'gnu_strip_debug':read(REVIEW/'postcheck/result.json')},
    'execution':{'pipeline':read(REVIEW/'pipeline.command.json'),'gnu_builds':2,
                 'primary_command_receipts':8,'postcheck_command_receipts':3,
                 'new_emu_runs':0,'new_nemu_runs':0,'new_fullcore_runs':0},
    'metrics':{'final_bin_bytes':31440,'load_file_bytes':30024,'load_memory_bytes':31440,
               'zero_fill_bytes':1416,'public_functions':16,'call_table_cases':48,'input_arrays':12,
               'aliased_table_entries':6,'actual_image_mutation_negatives':5,'input_plan_negative':1,
               'wrong_library_negative':1,'debug_only_positive':1},
    'verification':{'source_and_archive_provenance':'PASS','final_loaded_image_and_BIN':'PASS',
        'entry_and_ABI_flags':'PASS','function_addresses_and_bytes':'PASS',
        'call_table_and_inputs':'PASS','ISA_attributes':'PASS','BSS_and_permissions':'PASS',
        'whole_ELF_original_bytes':'DIFFERENT_NONLOAD_DEBUG_ONLY',
        'whole_ELF_after_GNU_strip_debug':'PASS_EQUAL',
        'original_runtime_qualification':'REUSED_SAME_IMAGE_AND_PLAN_RECORD26',
        'new_target_execution':'NOT_RUN_NOT_REQUIRED_BY_EQUIVALENCE',
        'new_performance':'NOT_TESTED','new_area_sta_power':'NOT_TESTED'},
    'negative_controls':report['negative_controls'],
    'prior_performance':{'source_record':'CONFIG-REUSE-MATRIX-DIVFIX0F-CLEAN02-20261027-01',
        'reused_as_historical_context_only':True,'firstdot_cycles':282.25,'config_reuse_cycles':273,
        'fastest_same_window_rvv_cycles':299,'speedup':299/273,
        'scope':'Historical matrix window, not this ordinary C fixture or new package measurement'},
    'decision':{'current':'ACCEPT_C8_SDK_RELINK_WITH_EXISTING_FUNCTIONAL_EVIDENCE',
        'default_changed':False,'production_RTL_changed':False,'github_uploaded':False,
        'next':'C8 minimal package integration complete; choose a concrete application before a new image contract, or readonly4x8/16x64 control attribution; retain4x13 RVV.'},
    'evidence':{'archive_manifest':ident(archive/'manifest.json'),'archive_members':len(members),
        'report':ident(OUT/'report.json'),'map':ident(OUT/'integrated/link.map'),
        'pipeline':ident(REVIEW/'pipeline.command.json')},
    'limitations':['New ELF byte identity differs only in debug sections; actual loaded image and plan exactly preserved.',
        'Reused26th record includes ordinaryC full128/NEMU/O2,bit100 negative,recovery/replay; no fresh target results claimed.',
        'This is the existing48-case fixture, not a new end-to-end LLM or Linux application.',
        'Changing forceRVV, source, data, ABI, toolchain or final layout requires renewed affected-path qualification.',
        'No new performance, PPA or human signoff. All planned negative artifacts remain local evidence.']}
save(P/'record.json',record)
text=r"""# C8 软件包接回普通 C 程序：最终镜像等价结果

**PASS：C8 软件包已真实接入原普通 C 夹具，最终可执行内容完全等价。** 依照事先约定，复用第26条同镜像的功能、NEMU/O2、bit100拒错、恢复与重放证据；本轮无需新增全核仿真。

执行者 @cc77-builder / Agent；操作ID 20261027-cc77-builder-c8-relink。生产RTL保持0f，旧四尺寸默认不变；未提交或上传GitHub。

## 接入内容

- 原主程序只把底层头的包含改为 §selected_gemv_c8.h§。
- 8×32 reuse vdot/RVV × 三数据集，共6个函数表项改用 §xs_c8_gemv_8x32§ / §xs_c8_gemv_8x32_rvv§。其余42项、数据、期望值、顺序和校验不变，没有重新生成测试向量。
- 真正从 §libxs_gemv_c8.a(gemv.o)§ 链入完整合格对象；SDK程序源目录没有gemv.S，对象目录没有绕过库的gemv.o。GNU依赖文件和link map确认实际包含SDK头、实际抽取库成员。
- 在全新输出中分别构建原源码复制对照和SDK接入程序，保留原AM/klib和链接次序；只有输出路径和记录链接来源的选项不同。

源码见 [source](source/)，重建和完整核验见 [README](README.md)。

## 三方等价结果

比较对象：原已通过全核的C8镜像 → 本轮原源码复制对照 → 本轮SDK接入版。

| 项目 | 结果 |
| --- | --- |
| 完整BIN | 三者全字节一致，均31,440字节 |
| BIN SHA256 | 56805506eb98b68269c73a3645d8f75dff73b697e30dec5f93ccc4716089ad34 |
| 入口 | 均0x80000000；ABI flags及ISA属性一致 |
| PT_LOAD | 同地址、权限、对齐及完整内容；file30,024B，memory31,440B，零填充1,416B |
| 装载节 | 所有SHF_ALLOC节的位置、大小、权限、对齐及内容一致，包括BSS |
| 函数 | 16个公共函数及启动/主程序等5个函数的地址、大小和机器码一致 |
| 测试表与数据 | 48条64字节调用记录与原计划逐项匹配；12组输入数组地址及内容一致 |
| GNU链接 | 无未解析符号；map与实际子命令证明使用SDK库成员 |
| 完整ELF原字节 | 不同；差异仅在.debug_info、.debug_line、.debug_line_str |
| 独立GNU复核 | 分别objcopy --strip-debug后，三份完整ELF全字节一致 |
| 去调试ELF SHA256 | 7e26e295fb020a63334026f768ed4825372266465b4e6008973de966fefc04ab |

调试节保存源文件/头文件路径及行号等信息，构建目录与头文件发生变化会改变这些记录。保留原ELF，没有通过删除调试信息来掩盖装载差异：主检查器已先完整比较装载内容和计划，去调试检查是独立补充证据。

原ELF SHA256：02159c7ef78cb31eb24cf706bf2974eadea313710563f235f2b11a7bb922de56。  
复制对照ELF SHA256：cfad14278ee4a3590de9bcbe7589b808fd91959156cef93ba92a78a90db0d99b。  
SDK接入ELF SHA256：f0ddf1167c961101e70f58cfd012ae788d2965324ad057aa4ade5af1de5bc42e。

## 检查器拒错与输入保护

7项负控全部被拒绝：实际ELF代码字节改坏、调用表改坏、启动入口改变、BSS大小改变、ISA属性改变、输入计划改变，以及真实GNU链接错误空库。另有只改调试字节的正控，确认不会将纯调试变化判为行为改变。错误镜像只用于主机检查，没有送入全核。

627项完整输入与封存运行证据绑定当前0f、EMU/NEMU及GNU工具。原33个矩阵进程和3个C进程的审计关系及全部封存输出树保持；本轮没有重复解析相同原始日志或伪造新PASS。当前操作保存了真实新GNU构建和最终镜像等价证据。

成功流水线：2026-10-27T21:59:40.771873+08:00 至 2026-10-27T21:59:43.182911+08:00，exit0。两次GNU构建，8份主流水线命令回执，另3份去调试GNU检查回执。流程首次通过，负控和原始文件全部保留。

## 已完成与未新增的结论

当前C8包已从“对象/可重定位链接合格”推进到“接回原可运行C程序、完整镜像等价”。原16函数、48例/两轮96正常调用（8×32占12例/24调用）的功能资格可明确复用；不是本轮重新执行这些调用。

新增EMU/NEMU/全核运行均为0。当前验证的是原测试夹具的包化接入，不是新的实际应用或LLM推理。没有新的周期、面积、STA或功耗测量。原273 cycles与1.095238×属于第25条性能矩阵，不是本C程序新测数据。

最小软件包接入闭环已完成。后续选择具体应用后再固定新的输入/调用路径/最终镜像合同；需要新性能结论时使用同路径firstdot/RVV及必要的集成前对照。另可继续4×8、16×64控制差异只读归因；4×13保留RVV。生产RTL和旧默认均不因本次接入改变。

## 证据

- [完整数据记录](record.json)，统一版本档案第28条：C8-RELINK-DIVFIX0F-CLEAN02-20261027-01。
- [比较与负控结果](evidence/report.json)、[实际接入link map](evidence/integrated/link.map)、[GNU独立复核](evidence/postcheck/result.json)。
- [原图/新图比较](evidence/integrated/equivalence.json)、[输入身份](evidence/qualification/report.json)、[执行回执](evidence/pipeline.command.json)。
- 原始输出：/home/riscv/riscv-lab/software-import-20261026/c8-relink-01。
- 完整本地归档：/home/riscv/riscv-lab/software-import-20261026/reviews/c8-relink-final-archive-01。
- 软件基点c823a8786e052c6e26f6915563c42b6d730dd8e3；硬件0f12df675378556670afd0dd2153f47fcb330610。当前状态为本地未提交材料，不能把基点SHA当作已包含本次修改的提交。
"""
text=text.replace('§',chr(96));(P/'RESULT.md').write_text(text)
save(e/'archive-reference.json',{'manifest':ident(archive/'manifest.json'),'archive':ident(archive/'evidence.zip'),'members':len(members)})
ledger=read(ledgerp);old_records=read(REVIEW/'before-version-data-ledger.json')['records']
assert len(ledger['records'])==27 and ledger['records']==old_records
ledger['records'].append(record);ledger['last_append_at']=now();ledger['last_append_note']=record_id
save(ledgerp,ledger)
assert read(ledgerp)['records'][:27]==old_records
md=R/'team/docs/version-data-ledger.md'
old=md.read_text()
entry=text.replace('# C8 软件包接回普通 C 程序：最终镜像等价结果\n\n','',1).replace('## ','### ')
entry=re.sub(r'\]\(([^)]+)\)',lambda m:'](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/'+m.group(1)+')',entry)
md.write_text(old+'\n\n## 18. C8接回普通C最终镜像等价（第28条）\n\n'+entry)
assert md.read_text().startswith(old)
route=R/'team/docs/development-route-current.md';t=route.read_text()
oldline=next(x for x in t.splitlines() if x.startswith('> 8×32稳定入口最小C8包'))
newline='> 8×32最小C8包及接回原普通C程序已闭合：包级GNU/别名/拒错/搬移通过；新接入程序与原合格镜像的完整BIN、PT_LOAD、入口、16函数、48项表和12组输入全部一致，ELF仅三个调试节变化，GNU去调试后三份ELF全字节相同。见[接入结果](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/RESULT.md)。记录28明确复用第26条同镜像功能，0新EMU/NEMU，无新性能/PPA。下一步选定具体应用再定义新路径合同；也可先只读归因4×8/16×64控制漂移，4×13保留RVV。旧默认和RTL保持，未上传。'
route.write_text(t.replace(oldline,newline))
readme=R/'team/README.md'
with readme.open('a') as f:f.write('\n- [C8接回普通C：最终镜像等价与原回归复用](optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/RESULT.md)。\n')
with (R/'开发计分板.md').open('a') as f:
    f.write(f'\n\n## 2026-10-27 C8回接普通C最终镜像等价\n\n- 执行者：@cc77-builder / Agent；操作ID：20261027-cc77-builder-c8-relink；工作区间{base["started"]}至{now()}（UTC+08:00），包含自动检查，不计成员人工投入。\n'
        '- 实现：原main只换选用头，48项表仅6项改用C8别名，真实链接完整SDK库；原数据/校验/次序保持。独立GNU构建原源码对照和接入版。\n'
        '- 结果：三份BIN均31440B、SHA56805506…；PT_LOAD/全部装载节/入口/21函数锚/48表项/12输入一致。ELF差异仅debug_info/line/line_str；GNU去调试后三份完整ELF一致。7负控及调试字节正控通过，627固定输入/原文封存身份保持；8主命令+3GNU补充回执。\n'
        '- 运行边界：符合预先约定，同BIN同计划明确复用第26条全128/NEMU/O2及负控恢复重放；0新EMU/NEMU，未跑新周期/PPA。首次接入流水线21:59:40至21:59:43+08 exit0。无生产RTL修改、默认切换、提交或GitHub写入。\n'
        '- 证据：[接入结果](team/optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/RESULT.md)、[版本档案](team/docs/version-data-ledger.md)第28条；原始输出software-import-20261026/c8-relink-01，归档reviews/c8-relink-final-archive-01。\n'
        '- 接续：C8最小包与既有C程序接入闭环完成；下一步选定实际应用才增加新镜像/调用合同，或继续4×8/16×64控制漂移只读归因，4×13保留RVV。新应用不得仅凭本次等价借用原周期与功能。\n')
for src,name in [(P/'RESULT.md','C8回接普通C_最终镜像等价结果.md'),(P/'record.json','C8回接普通C_运行数据.json'),
                 (P/'README.md','C8回接普通C_使用说明.md'),(P/'CONTRACT.md','C8回接普通C_验证合同.md'),
                 (ledgerp,'各版本运行数据档案.json'),(md,'各版本运行数据档案.md')]:
    shutil.copyfile(src,WIN/name)
# Make Windows navigation resolve to the actual authoritative files.
for name,origin in [('C8回接普通C_最终镜像等价结果.md',P/'RESULT.md'),('C8回接普通C_使用说明.md',P/'README.md')]:
    t=origin.read_text()
    t=re.sub(r'\]\(([^)]+)\)',lambda m:']('+str(origin.parent/m.group(1))+')',t)
    (WIN/name).write_text(t)
bundle=WIN/'C8回接普通C_程序与镜像.zip'
with zipfile.ZipFile(bundle,'x',zipfile.ZIP_DEFLATED) as z:
    for role,root in [('source',P/'source'),('sdk',OUT/'sdk'),('evidence',P/'evidence')]:
        for f in sorted(root.rglob('*')):
            if f.is_file():z.write(f,role+'/'+str(f.relative_to(root)))
    for f in ['vdot-perf.elf','vdot-perf.bin','link.map']:
        z.write(OUT/'integrated'/f,'image/'+f)
    z.write(P/'README.md','README.md');z.write(P/'CONTRACT.md','CONTRACT.md')
    z.write(P/'RESULT.md','RESULT.md');z.write(P/'record.json','record.json')
with zipfile.ZipFile(bundle) as z:
    assert z.read('image/vdot-perf.bin')==(OUT/'integrated/vdot-perf.bin').read_bytes()
(WIN/'当前进度.md').write_text('# 当前进度\n\nC8最小软件包已接回原普通C程序，最终镜像等价检查通过。\n\n'
    '三份完整BIN全字节相同；最终ELF仅三个调试信息节有差异，GNU去调试后三份完整ELF也一致。按事先条件复用原全核证据，0新EMU/NEMU。\n\n'
    '详见[等价结果](C8回接普通C_最终镜像等价结果.md)、[使用说明](C8回接普通C_使用说明.md)、[程序与镜像](C8回接普通C_程序与镜像.zip)。版本档案已追加第28条，硬件0f与旧默认保持，无新性能/PPA，未上传GitHub。\n\n'
    '下一步选定具体应用再定义新输入/调用/最终镜像合同；也可先只读分析4×8/16×64控制差异，4×13保留RVV。\n')
save(REVIEW/'delivery.json',{'status':'C8_RELINK_RECORDED','time':now(),'record_id':record_id,
    'archive_manifest':ident(archive/'manifest.json'),'bundle':ident(bundle),
    'ledger_records':28,'prior27_preserved':True,'old_package_pins_preserved':True})
print(json.dumps({'record_id':record_id,'archive_members':len(members),'bundle':str(bundle),'ledger_records':28},ensure_ascii=False))

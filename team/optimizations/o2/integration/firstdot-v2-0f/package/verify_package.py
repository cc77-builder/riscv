#!/usr/bin/env python3
"""Current V2 package static qualification; no EMU or historical runtime claims."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SHAPES = ((4,8),(8,32),(16,64),(4,13))
PUBLIC = Path('team/optimizations/o2/r2-select/public/firstdot')
FIRSTDOT = Path('team/optimizations/o2/r2-vector-accum/firstdot/public')
CONTRACT = 'current-firstdot-v2-package-static-v1'

def require(ok, message):
    if not ok: raise ValueError(message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def sha(path):
    return digest(Path(path).read_bytes())

def read(path):
    return json.loads(Path(path).read_text())

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def now():
    return datetime.now(timezone.utc).isoformat()

def caller(force, aliases):
    lines = ['#include <stdint.h>', '#include "selected_gemv.h"',
             '_Static_assert(XS_GEMV_STABLE_API_VERSION == 2, "V2 required");']
    for m,k in SHAPES:
        for fallback in (False,True):
            method='rvv' if force or fallback or (m,k)==(4,13) else 'vdot'
            target=f'firstdot_gemv_{m}x{k}_reuse_{method}'
            name=f'xs_gemv_{m}x{k}'+('_rvv' if fallback else '') if aliases else target
            suffix='rvv' if fallback else 'default'
            lines.append(f'void call_{m}x{k}_{suffix}(const int8_t *a, void *b) {{ {name}(a,b); }}')
    return '\n'.join(lines)+'\n'

def check_archive(lib, expected, library):
    actual=library.archive_member(Path(lib).read_bytes())
    require(actual==expected, 'archive member differs from independently rebuilt object')
    return dict(member='gemv.o',bytes=len(actual),sha256=digest(actual))

def validate_sources(repo, package):
    manifest_path=repo/'team/optimizations/o2/integration/firstdot-v2-0f/import-manifest.json'
    manifest=read(manifest_path)
    require(manifest['upstream_ref']=='fcf4a11fc569cb2a8fcb4e18d96ec2764b228557','wrong imported source revision')
    selected={}
    for row in manifest['files']:
        rel=Path(row['path'])
        require(not rel.is_absolute() and '..' not in rel.parts,'unsafe imported path')
        p=repo/rel
        require(p.is_file() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'imported source drift: '+str(rel))
        selected[str(p)]=row['sha256']
    require(len(selected)==45,'imported source inventory')
    source_manifest=read(repo/FIRSTDOT/'manifest.json')
    require(source_manifest['files']=={n:sha(repo/FIRSTDOT/n) for n in ('gemv.S','gemv.h')},'public source manifest bytes differ')
    require((package/'include/selected_gemv.h').read_bytes()==(repo/PUBLIC/'selected_gemv.h').read_bytes(),'selected header differs from imported source')
    require((package/'include/firstdot_gemv.h').read_bytes()==(repo/FIRSTDOT/'gemv.h').read_bytes(),'public header differs from imported source')
    selected[str(manifest_path)]=sha(manifest_path)
    return selected

def main(args):
    repo, package, matrix, out = [p.resolve() for p in (args.repo,args.package,args.matrix,args.output)]
    require(not out.exists(),'new output required')
    for protected in (repo,package,matrix):
        require(not out.is_relative_to(protected) and not protected.is_relative_to(out),'output overlaps inputs')
    if os.name=='posix': os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    sys.path.insert(0,str(repo/'team/optimizations/o2/r2-vector-accum'))
    import firstdot_gate as g
    import firstdot_library as library
    g.bind(repo)
    out.mkdir(parents=True)
    state=dict(contract=CONTRACT,status='RUNNING',started=now(),new_emu_runs=0,
        current_matrix_runtime_qualified=False,current_c_runtime_qualified=False,
        historical_pass_reused=False,stable_default_changed=False)
    save(out/'state.json',state)
    commands=[]
    def run(folder,label,argv,success=True):
        folder.mkdir(parents=True,exist_ok=True)
        env=dict(os.environ)
        for key in ('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','GCC_EXEC_PREFIX','COMPILER_PATH'):
            env.pop(key,None)
        before=now()
        proc=subprocess.run([str(x) for x in argv],cwd=repo,env=env,capture_output=True,timeout=180)
        receipt=dict(command=[str(x) for x in argv],cwd=str(repo),started=before,finished=now(),
            exit_code=proc.returncode,expected_success=success,
            stdout_sha256=digest(proc.stdout),stderr_sha256=digest(proc.stderr))
        (folder/(label+'.stdout.log')).write_bytes(proc.stdout)
        (folder/(label+'.stderr.log')).write_bytes(proc.stderr)
        save(folder/(label+'.command.json'),receipt)
        commands.append(str((folder/(label+'.command.json')).relative_to(out)))
        require((proc.returncode==0)==success,'unexpected command result: '+label)
        return proc.stdout
    try:
        inputs=validate_sources(repo,package)
        sources={str(Path(__file__).resolve()):sha(__file__)}
        for module in list(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path and Path(path).is_file() and Path(path).resolve().is_relative_to(repo):
                sources[str(Path(path).resolve())]=sha(path)
        for n in ('gemv.o','libxs_gemv_firstdot.a','include/selected_gemv.h','include/firstdot_gemv.h'):
            inputs[str(package/n)]=sha(package/n)
        for n in ('images.json','state.json','combination-build.json'):
            inputs[str(matrix/n)]=sha(matrix/n)
        tools={n:shutil.which(args.cross_prefix+n) for n in ('gcc','ld','ar','nm','readelf')}
        require(all(tools.values()),'missing GNU tool')
        versions={}
        for name,path in tools.items():
            versions[name]=dict(path=path,sha256=sha(path),
                version=run(out/'tools',name,[path,'--version']).decode().splitlines()[0])
        save(out/'tools.json',versions)
        flags=['-std=c11','-march=rv64gcv','-mabi=lp64d','-mno-relax','-ffreestanding','-O2']
        authority=out/'authority'
        run(authority,'assemble',[tools['gcc'],'-march=rv64gcv','-mabi=lp64d','-mno-relax',
             '-c',repo/FIRSTDOT/'gemv.S','-o',authority/'gemv.o'])
        authoritative=(authority/'gemv.o').read_bytes()
        require(authoritative==(package/'gemv.o').read_bytes(),'packaged object differs from independent assembly')
        member=check_archive(package/'libxs_gemv_firstdot.a',authoritative,library)
        public=g.ELF(authoritative)
        names={f'firstdot_gemv_{m}x{k}_{sw}_{method}' for m,k in SHAPES for sw in ('basic','reuse') for method in ('vdot','rvv')}
        defined={n for n,(_,size,index,_) in public.symbols.items() if size>0 and index>0}
        require(defined==names,'package defines unexpected public code')
        require(not any(n.startswith('xs_gemv_') for n in public.symbols),'runtime wrapper exported')
        images=read(matrix/'images.json')['images']
        require(len(images)==24 and len({i['name'] for i in images})==24,'matrix inventory')
        require(read(matrix/'state.json')['status']=='CURRENT_FIRSTDOT_STATIC_PASS_RUNTIME_NOT_RUN','matrix build incomplete')
        closure,anchors=[],[]
        seen=set()
        for image in images:
            if image['variant']!='firstdot':continue
            key=image['shard'],image['dataset']
            require(key not in seen,'duplicate matrix object');seen.add(key)
            root=Path(image['path'])
            require(root==matrix/'images'/image['name'],'matrix image path')
            g.verify_build(root,repo)
            require(sha(root/'vdot-perf.bin')==image['image_sha256'],'matrix payload changed')
            original=g.ELF((root/'gemv-reference.o').read_bytes())
            for row in read(root/'data/manifest.json')['rows']:
                target=row['api_symbol'].replace('r4_gemv_','firstdot_gemv_',1)
                raw=public.symbol_data(target)
                require(raw==original.symbol_data(row['api_symbol']),'package leaf differs from current matrix')
                anchors.append(dict(image=image['name'],symbol=target,bytes=len(raw),sha256=digest(raw)))
            for n in ('gemv-reference.o','build.json','data/manifest.json','vdot-perf.bin'):
                inputs[str(root/n)]=sha(root/n)
        require(seen=={(s,d) for s in (1,3,5,7) for d in range(3)} and len(anchors)==48,'matrix cross-dataset anchors incomplete')
        save(out/'leaf-anchors.json',dict(scope='current freshly built matrix objects; runtime not inferred',comparisons=anchors))
        def compile_one(folder,source,include,defines=(),success=True):
            folder.mkdir(parents=True,exist_ok=True)
            path=folder/'caller.c';path.write_text(source)
            run(folder,'compile',[tools['gcc'],*flags,*defines,'-I'+str(include),'-c',path,'-o',folder/'caller.o'],success)
            return folder/'caller.o'
        def link_one(folder,obj,lib):
            target=folder/'linked.o'
            run(folder,'link',[tools['ld'],'-r','--no-relax',obj,lib,'-o',target])
            undefined=run(folder,'undefined',[tools['nm'],'-u',target])
            require(not undefined.strip(),'unresolved symbols after relocatable link')
            return target
        mode_checks=[]
        for label,force,defines in [('default',False,()),('zero',False,('-DXS_GEMV_FORCE_RVV=0',)),('one',True,('-DXS_GEMV_FORCE_RVV=1',))]:
            folder=out/'modes'/label
            alias=compile_one(folder/'alias',caller(force,True),package/'include',defines)
            explicit=compile_one(folder/'explicit',caller(force,False),package/'include',defines)
            require(alias.read_bytes()==explicit.read_bytes(),'aliases resolve wrong callees: '+label)
            al=link_one(folder/'alias',alias,package/'libxs_gemv_firstdot.a')
            ex=link_one(folder/'explicit',explicit,package/'libxs_gemv_firstdot.a')
            require(al.read_bytes()==ex.read_bytes(),'alias linked object differs: '+label)
            linked=g.ELF(al.read_bytes())
            require(all(linked.symbol_data(n)==public.symbol_data(n) for n in names),'link changed package leaf')
            require(not any(n.startswith('xs_gemv_') for n in linked.symbols),'new wrapper symbol')
            mode_checks.append(dict(mode=label,aliases=8,caller_sha256=sha(alias),linked_sha256=sha(al),undefined_symbols=0))
        # A moved SDK carries no repository-relative header dependency.
        moved=out/'moved-sdk'
        shutil.copytree(package/'include',moved/'include')
        shutil.copyfile(package/'libxs_gemv_firstdot.a',moved/'libxs_gemv_firstdot.a')
        example=(repo/PUBLIC/'example.c').read_text()
        ex=compile_one(out/'moved-example',example,moved/'include')
        link_one(out/'moved-example',ex,moved/'libxs_gemv_firstdot.a')
        negatives=[]
        def rejected(label,operation,paths):
            try: operation()
            except ValueError as exc:
                negatives.append(dict(case=label,reason=str(exc),mutated_sha256={str(p):sha(p) for p in paths if Path(p).is_file()}))
            else: raise ValueError('corruption accepted: '+label)
        for value in ('2','-1','(1)','true'):
            compile_one(out/'negative'/('macro-'+str(len(negatives))),
                caller(False,True),package/'include',('-DXS_GEMV_FORCE_RVV='+value,),False)
            negatives.append(dict(case='invalid-macro-'+value,compiler_rejected=True))
        for label,old,new in [
            ('wrong-default-alias','#define xs_gemv_4x8 firstdot_gemv_4x8_reuse_vdot','#define xs_gemv_4x8 firstdot_gemv_4x8_reuse_rvv'),
            ('wrong-k13-choice','#define xs_gemv_4x13 xs_gemv_4x13_rvv','#define xs_gemv_4x13 firstdot_gemv_4x13_reuse_vdot')]:
            directory=out/'negative'/label
            shutil.copytree(package/'include',directory/'include')
            header=directory/'include/selected_gemv.h'
            text=header.read_text();require(text.count(old)==1,'negative alias target missing')
            header.write_text(text.replace(old,new))
            broken=compile_one(directory,caller(False,True),directory/'include')
            good=out/'modes/default/explicit/caller.o'
            rejected(label,lambda:require(broken.read_bytes()==good.read_bytes(),'semantic alias/caller mismatch despite refreshed digest'),[header,broken])
        corrupt=out/'negative/wrong-object'
        corrupt.mkdir(parents=True)
        raw=bytearray(authoritative)
        # Modify an actual text byte while preserving valid ELF metadata.
        raw[public.named['.text'][4]+8]^=1
        (corrupt/'gemv.o').write_bytes(raw)
        run(corrupt,'archive',[tools['ar'],'rcsD',corrupt/'wrong.a',corrupt/'gemv.o'])
        rejected('rehash-wrong-object',lambda:check_archive(corrupt/'wrong.a',authoritative,library),[corrupt/'gemv.o',corrupt/'wrong.a'])
        empty=out/'negative/wrong-library';empty.mkdir(parents=True)
        run(empty,'archive',[tools['ar'],'rcsD',empty/'empty.a'])
        rejected('wrong-library-unresolved',lambda:link_one(empty,out/'modes/default/alias/caller.o',empty/'empty.a'),[empty/'empty.a'])
        missing=out/'negative/missing-header';(missing/'include').mkdir(parents=True)
        shutil.copyfile(package/'include/selected_gemv.h',missing/'include/selected_gemv.h')
        compile_one(missing,example,missing/'include',success=False)
        negatives.append(dict(case='missing-header',compiler_rejected=True))
        v1=repo/'team/optimizations/o2/r2-select/public/selected_gemv.h'
        compile_one(out/'negative/v1-before-v2','#include "'+str(v1)+'"\n'+caller(False,True),
                    package/'include',success=False)
        negatives.append(dict(case='v1-before-v2',compiler_rejected=True))
        reverse=compile_one(out/'v2-before-v1','#include "selected_gemv.h"\n#include "'+str(v1)+'"\n'+caller(False,True),
                    package/'include')
        require(reverse.read_bytes()==(out/'modes/default/explicit/caller.o').read_bytes(),'V1 inclusion downgraded V2 aliases')
        for p,d in inputs.items():require(sha(p)==d,'input drift after validation: '+p)
        for p,d in sources.items():require(sha(p)==d,'checker drift after validation: '+p)
        save(out/'inputs.json',dict(inputs=inputs,checker_sources=sources))
        report=dict(contract=CONTRACT,status='CURRENT_FIRSTDOT_V2_PACKAGE_STATIC_PASS',started=state['started'],finished=now(),
            package=str(package),matrix=str(matrix),independent_object=member,defined_functions=16,
            new_wrapper_symbols=0,matrix_leaf_comparisons=48,alias_modes=mode_checks,
            moved_sdk_example_compiled_and_linked=True,v2_before_v1_preserves_v2=True,
            negative_controls=negatives,toolchain=versions,command_receipts=commands,
            source_manifest_sha256=sha(repo/FIRSTDOT/'manifest.json'),import_manifest_sha256=sha(repo/'team/optimizations/o2/integration/firstdot-v2-0f/import-manifest.json'),
            input_manifest_sha256=sha(out/'inputs.json'),new_emu_runs=0,new_nemu_runs=0,
            current_matrix_runtime_qualified=False,current_c_runtime_qualified=False,
            historical_pass_reused=False,stable_default_changed=False,
            limits='Static package/source and newly built matrix leaf identity only. Full-core and C runtime qualification must be attached separately.')
        save(out/'report.json',report)
        state.update(status=report['status'],finished=report['finished'],report_sha256=sha(out/'report.json'))
        save(out/'state.json',state)
        print(json.dumps({k:v for k,v in report.items() if k not in ('negative_controls','toolchain','command_receipts','alias_modes')},indent=2))
        return report
    except BaseException as exc:
        state.update(status='FAILED',error=repr(exc),finished=now())
        save(out/'state.json',state)
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('repo','package','matrix','output'):parser.add_argument('--'+flag,type=Path,required=True)
    parser.add_argument('--cross-prefix',default='riscv64-linux-gnu-')
    main(parser.parse_args())

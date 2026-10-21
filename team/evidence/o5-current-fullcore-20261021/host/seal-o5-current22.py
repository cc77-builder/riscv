"""Seal raw current-source evidence after actual run and recheck completion."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
workspace=Path('/mnt/c/Code/RVInno/riscv')
sealer=Path(__file__).resolve()
sealer_sha=hashlib.sha256(sealer.read_bytes()).hexdigest()
target=workspace/'team/evidence/o5-current-fullcore-20261021'
if target.exists():raise ValueError('existing evidence must be retained')
state=json.loads((base/'build-06/build-state.json').read_text())
if state['status']!='O2_FULLCORE_BUILD_PASS':raise ValueError('actual build did not pass')
launches=json.loads((base/'runs/launches.json').read_text())
if [(row['name'],row.get('exit_code')) for row in launches] != [('core-01',1),('supplements-01',0)]:
    raise ValueError('unexpected original campaign outcomes')
core=json.loads((base/'runs/core-01/result.json').read_text())
supplements=json.loads((base/'runs/supplements-01/result.json').read_text())
if core.get('status')!='O2_CORE_REGRESSION_FAILED' or supplements.get('status')!='O2_SUPPLEMENTS_PASS':
    raise ValueError('unexpected original final verdicts')
negative=json.loads((base/'runs/core-01/negative-vdot/result.json').read_text())
if negative.get('status')!='FAILED' or negative.get('error')!="ValueError('negative mismatch must bind injected PC and vector register')":
    raise ValueError('original negative is not the reviewed false rejection')
for path in (base/'runs/core-01').glob('*/result.json'):
    if path.parent.name!='negative-vdot' and json.loads(path.read_text()).get('status')=='FAILED':
        raise ValueError('another core job failed: '+path.parent.name)
review=json.loads((base/'runs/recheck-03/result.json').read_text())
if review.get('status') not in ('O2_G3_OFFLINE_RECHECK_PASS','O2_G3_OFFLINE_RECHECK_INCOMPLETE') or review.get('error'):
    raise ValueError('strict audit verdict missing')
if not all(review.get(k) is True for k in ('core_regression_pass','supplements_pass','original_evidence_unchanged')):
    raise ValueError('jobs or input integrity failed')
if review.get('g3_complete') != (review['status']=='O2_G3_OFFLINE_RECHECK_PASS'):
    raise ValueError('inconsistent completion verdict')
audit_commit='2b6c5d6c1d29cc4a933f73853ce2ccbfc449f2fa'
if review.get('runtime_gate_audit',{}).get('source_commit')!=audit_commit:
    raise ValueError('wrong runtime-gate audit revision')
if review.get('build_source_commit')!=state['source_commit'] or review.get('emu_sha256')!=state['emu_sha256']:
    raise ValueError('audit/build identity mismatch')
if review.get('original_evidence_unchanged') is not True:
    raise ValueError('original evidence changed')
summary=json.loads((base/'current-g3-summary.json').read_text())
if summary.get('status')!=review['status'] or summary.get('source_sha256')!=hashlib.sha256((base/'runs/recheck-03/result.json').read_bytes()).hexdigest():
    raise ValueError('derived summary is missing or stale')
launch=json.loads((base/'recheck-launch-03.json').read_text())
seeded=json.loads((base/'runs/supplements-02/result.json').read_text())
seed_launch=json.loads((base/'seed-supplement-launch-02.json').read_text())
if launch.get('native_head')!='afe589bffc1fe98785784100187d45e953b421e9' or seed_launch.get('source_commit')!=launch['native_head']:
    raise ValueError('wrong seeded driver source')
if seed_launch.get('status')!='PASS' or seed_launch.get('emu_seed')!=1 or seeded.get('status')!='O2_SUPPLEMENTS_PASS':
    raise ValueError('seeded experiment did not pass')
if [len(x['runs']) for x in (core,supplements,seeded)] != [12,2,2]:
    raise ValueError('unexpected actual launch count')
if summary.get('actual_launches')!=16 or summary.get('selected_jobs')!=14:
    raise ValueError('derived launch counts differ')
expected_exit=0 if review['g3_complete'] else 1
if launch.get('exit_code')!=expected_exit or not all(launch.get(k) is True for k in
    ('original_files_unchanged','shared_drivers_unchanged','launcher_unchanged','native_head_unchanged')):
    raise ValueError('corrected audit launcher integrity or exit failed')
cleanup=json.loads((base/'temporary-swap-cleanup.json').read_text())
if cleanup.get('removed') is not True or (base/'temporary-build.swap').exists():
    raise ValueError('temporary swap not cleaned up')
audited=dict(launch['original_files'])
audited[str(sealer)]=sealer_sha
audited[launch['launcher_path']]=launch['launcher_sha256']
archive=json.loads((base/'prepared-inputs-v4.json').read_text())
if archive.get('status')!='PREPARED_INPUT_ARCHIVE_VERIFIED' or archive.get('sha256')!='cf899b8b72d5b8c719e9aefad7ada88198416ce1a0b00edd13708c0b343ee28f':
    raise ValueError('unexpected prepared archive receipt')
if (base/'prepared-inputs-v4.zip').stat().st_size!=archive['bytes']:
    raise ValueError('prepared archive length changed')
audited[str(base/'prepared-inputs-v4.zip')]=archive['sha256']
if not launch.get('audit_output_files'):raise ValueError('missing completed audit output inventory')
for path,digest in launch['audit_output_files'].items():
    if path in audited and audited[path]!=digest:raise ValueError('conflicting audit output identity: '+path)
    audited[path]=digest
input_audit=json.loads((base/'runs/recheck-03/input-audit.json').read_text())
for path,digest in input_audit['original_evidence_and_inputs'].items():
    if path in audited and audited[path]!=digest:raise ValueError('conflicting audited identity: '+path)
    audited[path]=digest
for path in (base/'build-06/build-state.json',base/'runs/recheck-03/result.json',
             base/'recheck-launch-03.json',base/'runs/recheck-03/input-audit.json',
             base/'current-g3-summary.json',base/'seed-supplement-launch-02.json',
             base/'temporary-swap-cleanup.json'):
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if str(path) in audited and audited[str(path)]!=digest:raise ValueError('sealed receipt differs from audit')
    audited[str(path)]=digest

def verify_audited():
    for path,digest in audited.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:
            raise ValueError('post-audit drift: '+path)
verify_audited()
target.mkdir(parents=True)
files={}
def copy(source,relative):
    destination=target/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if hashlib.sha256(destination.read_bytes()).hexdigest()!=digest:raise ValueError('copy drift')
    if str(source) in audited and digest!=audited[str(source)]:raise ValueError('copied audited identity drift')
    files[str(relative)]=dict(sha256=digest,bytes=destination.stat().st_size,source=str(source))
for source in sorted(base.iterdir()):
    if source.is_file() and source.suffix in ('.json','.jsonl','.log','.exit'):
        copy(source,Path('native')/source.name)
copy(base/'prepared-inputs-v4.zip',Path('native/prepared-inputs-v4.zip'))
copy(base/'repo/build/time.log',Path('native/build-06/root-make-time.log'))
for name in ('build-01','build-02','build-03','build-04','build-05','build-06','native-clang-probe-05',
             'native-clang-link-probe-06','native-clang-link-probe-07','native-clang-link-probe-08','input-negatives-01','runs'):
    for source in sorted((base/name).rglob('*')):
        relative=source.relative_to(base)
        if not source.is_file() or any(part in ('failed-products','interrupted-products') for part in relative.parts):continue
        if source.suffix in ('.json','.jsonl','.log','.txt','.sh','.exit','.patch','.py','.stdout','.stderr') or name in ('runs','native-clang-probe-05') or (name.startswith('native-clang-link-probe-') and source.parent==base/name):
            copy(source,Path('native')/relative)
for source in sorted((workspace/'team/out').iterdir()):
    if source.is_file() and (source.name.startswith('o5-') and source.suffix in ('.log','.json') or
                            'o5' in source.name and source.suffix=='.py' or source.name=='prepare-lf21.py'):
        copy(source,Path('host')/source.name)
readme=workspace/'team/out/o5-final-evidence-README.md'
with readme.open('x',encoding='utf-8') as stream:
    stream.write(f'''# Current-source O2 G3 evidence — 2026-10-21

Final independently recomputed verdict: **{review['status']}**.

- Hardware build: `{state['source_commit']}`; explicit `split-clang-v2`.
- EMU SHA-256: `{state['emu_sha256']}`.
- Explicit corrected gate/auditor commit: `{audit_commit}`.
- Actual launches: 16, including two retained original supplements and two seed=1 supplements. Selected audit jobs: 14; one intentional bit100 rejection, remaining normal jobs pass. G3 complete: {review['g3_complete']}; missing coverage: {review['suite_coverage']['missing']}.
- Original core verdict `{core['status']}` is preserved. Its sole failed job was the old gate's commit-group PC false rejection. No original log, result or launch ledger was rewritten.

Start with [selected audit](native/runs/recheck-03/result.json), [original core](native/runs/core-01/result.json), [seed=1 supplements](native/runs/supplements-02/result.json), and [deployment receipt](native/recheck-launch-03.json). Original supplements-01 and recheck-02 INCOMPLETE are retained. Seed runner commit: afe589bffc1fe98785784100187d45e953b421e9; shared core drivers remain byte-identical to the build revision.
The [derived summary](native/current-g3-summary.json) exposes exact counts and qualified coverage sources. [Build06](native/build-06/build-state.json) and attempts01–05 retain separate identities and failures.

`manifest.json` records payload hashes, sizes and original source paths. Selected prepared inputs are preserved in `native/prepared-inputs-v4.zip`; its previously verified hash is rechecked while sealing. Audit-bound inputs and evidence are rechecked before and after copies. The temporary swap cleanup receipt is included.

This is audit evidence and a selected-input archive, not a portable complete rebuild environment. EMU, all native tools and every hardware dependency are not bundled. Absolute-path strict replay still requires the prepared native workspace or a separately rebuilt contract. No new performance/PPA, independent T17 or human ACK claim. O1/O2 remain default-off in production.
''')
copy(readme,Path('README.md'))
verify_audited()
manifest=dict(schema_version=1,sealed_utc=datetime.now(timezone.utc).isoformat(),
    sealer_path=str(sealer),sealer_sha256=sealer_sha,
    tested_build_commit=state['source_commit'],emu_sha256=state['emu_sha256'],
    runtime_gate_audit_commit=audit_commit,original_core_status=core['status'],
    corrected_audit_status=review['status'],g3_complete=review['g3_complete'],
    audited_source_files_reverified=len(audited),
    scope='current-source O2 G3 audit evidence; not a portable rebuild environment, performance/PPA/independent T17 or human ACK',files=files)
(target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('EVIDENCE_SEALED',len(files),sum(row['bytes'] for row in files.values()),flush=True)

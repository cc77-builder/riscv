from pathlib import Path
import io,tarfile,subprocess,json
repo=Path.cwd();out=repo/'team/out/james-sync-20261017'
root=Path('/home/amesotten/.cache/codex-rvinno/sync-t14-frozen-20261017')
root.mkdir(exist_ok=False)
data=subprocess.check_output(['git','archive','a877e0575','team/scripts','team/workloads/vdot-perf','team/models/vdot'])
with tarfile.open(fileobj=io.BytesIO(data)) as archive:archive.extractall(root,filter='data')
(root/'team/evidence').symlink_to(repo/'team/evidence',target_is_directory=True)
result=subprocess.run(['python3','-OO','-B',str(root/'team/scripts/verify-t14-archive.py'),'--archive',str(repo/'team/evidence/t14-optimization-20261016'),'--output',str(out/'t14-frozen-replay')])
(out/'t14-frozen-status.json').write_text(json.dumps(dict(exit_code=result.returncode,source='a877e0575ea91392edc7816637e51ae8d1689b36',historical=True,hardware_rerun=False))+'\n')
raise SystemExit(result.returncode)

import hashlib, json, pathlib, subprocess, sys
root=pathlib.Path(__file__).resolve().parents[2]
folder=root/'team/optimizations/o1/evidence/20261018-fu-validation'
manifest=json.loads((folder/'manifest.json').read_text())
for name, expected in manifest['files'].items():
    data=(folder/name).read_bytes()
    if len(data)!=expected['bytes'] or hashlib.sha256(data).hexdigest()!=expected['sha256']:
        raise SystemExit('manifest mismatch '+name)
sys.path.insert(0,str(root/'team/optimizations/o1'))
from check_negative import check_negative
for fault in ('identity','wen','high','cancel'):
    check_negative(fault,1,(folder/f'fu-02/inject-{fault}.log').read_text())
print('UPSTREAM_EVIDENCE_PASS files='+str(len(manifest['files']))+' four_actual_fault_logs=pass')

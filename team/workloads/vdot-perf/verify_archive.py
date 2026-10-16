"""Offline byte, source, ELF, trace and result replay. Does not rerun hardware."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import analyze
import check as c


def main(a):
    root=a.archive.resolve()
    files=json.loads((root/'archive-files.json').read_text())['files']
    for item in files:
        path=(root/item['path']).resolve();c.require(path.is_relative_to(root),'archive path escape')
        data=path.read_bytes();c.require(hashlib.sha256(data).hexdigest()==item['sha256'],'archive byte mismatch '+item['path'])
        raw=gzip.decompress(data) if path.suffix=='.gz' else data
        c.require(len(raw)==item['raw_bytes'] and hashlib.sha256(raw).hexdigest()==item['raw_sha256'],'raw archive byte mismatch')
    seal=root/'file-manifest.json'
    if seal.exists():
        for name,digest in json.loads(seal.read_text())['files'].items():
            c.require(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'final archive file mismatch '+name)
    external=json.loads((root/'external-artifacts.json').read_text())
    pins=json.loads((root/'hardware-build/hardware-inputs.json').read_text())
    c.require(set(external.values())=={pins['emu_sha256'],'efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4','a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994'},'external build pins')
    calibration=c.verify(root/'support/smoke-build-02',root/'support/calibration-02',external)
    c.require(len(calibration['samples'])==13,'calibration cardinality')
    result=analyze.analyze(root/'images-v3',root/'campaign-v3',root/'images-stream-v4',root/'campaign-stream-v4',a.output,external)
    previous=json.loads((root/'support/analysis-v1/result.json').read_text())
    c.require(result==previous,'offline recomputation changed accepted result')
    receipt=dict(status='T13_OFFLINE_REPLAY_PASS',archive_files=len(files),calibration_windows=13,accepted_runs=126,performance_windows=1404,full_core_functional_calls=108,recomputed_result_identical=True,hardware_rerun=False)
    (a.output/'offline-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);main(p.parse_args())

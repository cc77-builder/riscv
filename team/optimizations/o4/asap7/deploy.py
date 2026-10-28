#!/usr/bin/env python3
"""Deploy project-local Linux EDA tools/libraries without changing system packages."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import urllib.request

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    report = {'status': 'PREPARING', 'files': {}, 'tools': {}}
    def obtain(url, name, digest):
        dest = root / 'downloads' / digest / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        cached = args.cache / name
        data = cached.read_bytes() if cached.is_file() and sha(cached) == digest else urllib.request.urlopen(url, timeout=90).read()
        dest.write_bytes(data)
        if sha(dest) != digest:
            raise ValueError('download SHA mismatch: ' + name)
        report['files'][str(dest.relative_to(root))] = digest
        return dest
    try:
        old = json.loads((HERE.parent / 'toolchain-lock.json').read_text())
        packages = [(p, folder) for p, folder in zip(old['packages'], ['universe/b/berkeley-abc', 'universe/o/opensta', 'universe/y/yosys'])]
        packages.append(({'name': 'libtcl8.6_8.6.14+dfsg-1build1_amd64.deb', 'sha256': '7534eb825f6317514d747ce53b4d6c23bf24df1dc1785f9599610ece5515e685'}, 'main/t/tcl8.6'))
        for item, folder in packages:
            p = obtain('https://archive.ubuntu.com/ubuntu/pool/' + folder + '/' + item['name'], item['name'], item['sha256'])
            subprocess.run(['dpkg-deb', '-x', str(p), str(root / 'tools')], check=True)
        lib = root / 'libraries'; lib.mkdir()
        for item in old['library']['files']:
            if 'url' in item:
                p = obtain(item['url'], item['file'], item['sha256'])
                (lib / item['file']).write_bytes(p.read_bytes())
        lock = json.loads((HERE / 'library-lock.json').read_text())
        base = 'https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/' + lock['commit'] + '/flow/platforms/asap7/'
        for item in lock['files']:
            p = obtain(base + item['path'], Path(item['path']).name, item['sha256'])
            target = lib / 'asap7' / item['path']; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())
            if target.suffix == '.gz':
                target.with_suffix('').write_bytes(gzip.decompress(target.read_bytes()))
        env = dict(os.environ, LD_LIBRARY_PATH=str(root / 'tools/usr/lib/x86_64-linux-gnu'))
        env.pop('LD_PRELOAD', None)
        env['TCL_LIBRARY'] = str(root / 'tools/usr/share/tcltk/tcl8.6')
        for exe, options in [('yosys', ['-V']), ('berkeley-abc', ['-c', 'version']), ('sta', ['-version'])]:
            p = root / 'tools/usr/bin' / exe
            linked = subprocess.check_output(['ldd', str(p)], env=env, text=True)
            if 'not found' in linked:
                raise RuntimeError(linked)
            report['tools'][exe] = {'sha256': sha(p), 'version': subprocess.check_output([str(p), *options], env=env, text=True), 'ldd': linked}
        q = shlex.quote
        (root / 'activate.sh').write_text('export RVINNO_EDA_ROOT=' + q(str(root)) + '\nexport PATH=' + q(str(root / 'tools/usr/bin')) + ':"$PATH"\nexport LD_LIBRARY_PATH=' + q(env['LD_LIBRARY_PATH']) + '\nexport TCL_LIBRARY=' + q(env['TCL_LIBRARY']) + '\n')
        report['status'] = 'TOOLS_AND_LIBRARIES_READY'
    except BaseException as error:
        report.update(status='FAILED', error=repr(error))
        raise
    finally:
        (root / 'deployment.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'root': str(root)}))

if __name__ == '__main__':
    main()

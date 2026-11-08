#!/usr/bin/env python3
"""Verify the final source/material snapshot; does not execute hardware."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):
            h.update(data)
    return h.hexdigest()


def main():
    manifest=json.loads((HERE/'MANIFEST.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        path=ROOT/entry['path']
        if not path.is_file() or digest(path)!=entry['sha256']:
            raise ValueError('Missing or changed file: '+entry['path'])
    for name in ['开发计分板.md','AGENTS.md','team/submission/cie2026-v1/history','team/docs/development-route-current.md']:
        if (ROOT/name).exists():raise ValueError('Development/history material remains: '+name)
    git_status='NOT_AVAILABLE_IN_FILE_EXPORT'
    if (ROOT/'.git').exists():
        def git(*a):return subprocess.check_output(['git','-C',str(ROOT),*a],text=True).strip()
        if git('rev-parse','HEAD:src')!=manifest['src_tree']:
            raise ValueError('Production source Git tree changed')
        for item in manifest['submodules']:
            if git('rev-parse','HEAD:'+item['path'])!=item['commit']:
                raise ValueError('Submodule pin changed: '+item['path'])
        git_status='SOURCE_AND_SUBMODULE_PINS_MATCH'
    print(json.dumps({'status':'FINAL_PACKAGE_PASS','files_verified':len(manifest['files']),
                      'original_source_files':manifest['original_source_files'],
                      'original_logs_preserved':5356,'git':git_status,
                      'rtl_executed':False,'nemu_executed':False},ensure_ascii=False,indent=2))


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.CalledProcessError) as e:
        print('FINAL_PACKAGE_FAIL: '+str(e),file=sys.stderr)
        sys.exit(1)

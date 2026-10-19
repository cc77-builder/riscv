"""Shared live-build dependency gate; frozen evidence uses its own checkers."""
from pathlib import Path
import hashlib
import runpy
import subprocess

HARDWARE = ['src', 'macros', 'scripts', 'build.sc', 'Makefile', 'Makefile.test',
            'team/scripts/activate.sh', 'team/scripts/prepare-core-baseline.py',
            'team/optimizations/o1/build_inputs.py']


def hardware_files(root):
    """Complete current compiler inventory, including added nonignored files."""
    root = Path(root)
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z',
        '--cached', '--others', '--exclude-standard', '--', *HARDWARE]).split(b'\0')
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in sorted({raw.decode() for raw in names if raw})
            if (root / name).is_file()}


def verify_hardware_files(root, expected):
    verify_dependencies(root)
    if hardware_files(root) != expected:
        raise RuntimeError('Hardware compiler inventory changed')


def verify_dependencies(root):
    root = Path(root)
    helper = runpy.run_path(str(root / 'team/scripts/prepare-core-baseline.py'))
    # Root Scala/macros are compiler inputs too, including ignored directories.
    helper['root_inputs'](root)
    pins = helper['modules'](root)
    helper['verify_dependencies'](root, pins)
    return pins

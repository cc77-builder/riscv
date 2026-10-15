#!/usr/bin/env python3
"""Assemble isolated RVV research candidates; do not execute the object.

Requires Python 3.10+, Clang with RISC-V support, and llvm-readelf or readelf.
Writes only the requested JSON and optional symbol listing. Object is temporary.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--symbols-output', type=Path)
    parser.add_argument('--clang', default='clang')
    parser.add_argument('--readelf')
    args = parser.parse_args()
    source = Path(__file__).with_name('rvv_candidates.S')
    if not source.is_file():
        raise RuntimeError('rvv_candidates.S must be next to this script')
    clang = shutil.which(args.clang)
    readelf = shutil.which(args.readelf) if args.readelf else (
        shutil.which('llvm-readelf') or shutil.which('readelf'))
    if not clang or not readelf:
        raise RuntimeError('Install Clang and llvm-readelf/readelf or pass their paths')

    def run(argv: list[str]) -> str:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError('Assembly check failed: ' + result.stderr.strip())
        return result.stdout

    flags = ['--target=riscv64', '-march=rv64gcv', '-mabi=lp64d', '-c']
    with tempfile.TemporaryDirectory(prefix='vdot-assembly-probe-') as directory:
        obj = Path(directory) / 'rvv_candidates.o'
        run([clang, *flags, str(source), '-o', str(obj)])
        raw = obj.read_bytes()
        if (len(raw) < 64 or raw[:6] != b'\x7fELF\x02\x01'
                or struct.unpack_from('<H', raw, 18)[0] != 243):
            raise AssertionError('Expected little-endian ELF64 for RISC-V')
        listing = run([readelf, '-sW', str(obj)])
        symbols = {}
        for line in listing.splitlines():
            columns = line.split()
            if len(columns) >= 8 and columns[0].endswith(':'):
                try:
                    symbols[columns[7]] = dict(value=int(columns[1], 16), size=int(columns[2]))
                except ValueError:
                    continue
        results = {}
        for name in ('b5_tumu', 'b5_tuma', 'b5_tamu', 'b5_tama'):
            size = symbols[name + '_end']['value'] - symbols[name + '_begin']['value']
            if size != 20:
                raise AssertionError(name + ' is not a 20-byte norvc core')
            results[name] = dict(core_bytes=size, core_instructions=size // 4,
                                 entry_policy_must_match_variant=True)
        kernel = symbols['rvv_delayed_reduce_k8']
        if kernel['size'] <= 0 or kernel['size'] % 4:
            raise AssertionError('Unexpected kernel symbol size')
        object_hash = hashlib.sha256(raw).hexdigest()
    output = dict(schema=1, scope='assembler/ELF check only; no instruction execution',
                  ran_at_utc=datetime.now(timezone.utc).isoformat(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  clang_version=run([clang, '--version']).splitlines()[0],
                  readelf_version=run([readelf, '--version']).splitlines()[0],
                  command=['clang', *flags, 'rvv_candidates.S', '-o', '<temporary-object>'],
                  variants=results, kernel_static_bytes=kernel['size'],
                  object_sha256=object_hash, passed=True,
                  not_proved=['runtime ISA behavior', 'latency or throughput',
                              'correctness for invalid kernel lengths', 'RTL/PPA'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    if args.symbols_output:
        args.symbols_output.parent.mkdir(parents=True, exist_ok=True)
        args.symbols_output.write_text(listing, encoding='utf-8')
    print(json.dumps(dict(passed=True, b5_variants=len(results), core_bytes_each=20,
                         kernel_static_bytes=kernel['size'])))


if __name__ == '__main__':
    main()

"""Run an evidence auditor from a checkout without original build products.

This is a Python audit-hook dependency probe, not an OS security sandbox. It
rejects Python filesystem access to specified original roots and subprocess
arguments/cwd that name them. Installed GNU tools and temporary extraction are
still allowed. No source or raw-auditor rule is patched.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import traceback

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--checkout', type=Path, required=True)
parser.add_argument('--script', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
parser.add_argument('--deny-root', type=Path, action='append', required=True)
parser.add_argument('--expect', choices=('pass', 'reject'), default='pass')
parser.add_argument('--reject-fragment')
parser.add_argument('arguments', nargs=argparse.REMAINDER)
args = parser.parse_args()
checkout, script, report = (v.resolve() for v in (args.checkout, args.script, args.report))
denied = tuple(p.resolve() for p in args.deny_root)
if report.exists() or not script.is_relative_to(checkout) or (checkout/'build').exists() or (checkout/'out').exists():
    raise ValueError('new report and source-only audit checkout required')
if any(checkout.is_relative_to(p) or report.is_relative_to(p) for p in denied):
    raise ValueError('audit inputs/output overlap denied roots')
argv = args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
script_sha, launcher_sha = sha(script), sha(__file__)
revision = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
os.chdir(checkout)
started = datetime.now(timezone.utc).isoformat()
events, rejected = {}, []


class OriginalTreeAccess(RuntimeError):
    pass


def hook(event, values):
    if event in ('open', 'os.listdir', 'os.scandir'):
        target = values[0]
        if isinstance(target, (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(target)).resolve()
            events[event] = events.get(event, 0) + 1
            if any(path.is_relative_to(root) for root in denied):
                rejected.append(dict(event=event, path=str(path)))
                raise OriginalTreeAccess('original physical tree read: ' + str(path))
    elif event == 'subprocess.Popen':
        executable, command, cwd, _ = values
        command = command if isinstance(command, (tuple, list)) else [command]
        checked = [str(executable), str(cwd or Path.cwd())] + [str(s) for s in command]
        events[event] = events.get(event, 0) + 1
        if any(str(root) in value for root in denied for value in checked):
            rejected.append(dict(event=event, command=checked))
            raise OriginalTreeAccess('subprocess names original physical tree')
    elif event == 'os.system' or event.startswith(('os.exec', 'os.posix_spawn')):
        raise OriginalTreeAccess('unsupported process launch under dependency probe: ' + event)


sys.addaudithook(hook)
self_test = False
try:
    (denied[0] / '__t17_guard_probe__').read_bytes()
except OriginalTreeAccess:
    self_test = True
if not self_test or len(rejected) != 1:
    raise RuntimeError('dependency guard self-test failed')
rejected.clear()
sys.path.insert(0, str(script.parent))
sys.argv = [str(script)] + argv
error, succeeded = None, False
try:
    runpy.run_path(str(script), run_name='__main__')
    succeeded = True
except SystemExit as exc:
    succeeded = exc.code in (None, 0)
    if not succeeded:
        error = 'SystemExit: ' + str(exc.code)
except Exception as exc:
    error = type(exc).__name__ + ': ' + str(exc)
    traceback.print_exc()
qualified = succeeded and not rejected if args.expect == 'pass' else (
    not succeeded and args.reject_fragment is not None and args.reject_fragment in (error or '') and not rejected)
if argv.count('--output') != 1:
    raise ValueError('one explicit auditor output required')
auditor_output = Path(argv[argv.index('--output') + 1]).resolve()
if succeeded and not auditor_output.is_file():
    qualified = False
if (checkout/'build').exists() or (checkout/'out').exists():
    qualified = False
proof = dict(status='T17_DETACHED_AUDIT_PASS' if qualified and succeeded else
             'T17_DETACHED_EXPECTED_REJECTION_PASS' if qualified else 'T17_DETACHED_AUDIT_FAIL',
             started=started, finished=datetime.now(timezone.utc).isoformat(), checkout=str(checkout), revision=revision,
             execution_cwd=str(Path.cwd()),
             build_present=False, out_present=False, script=str(script), script_sha256=script_sha,
             launcher_sha256=launcher_sha, arguments=argv, denied_roots=[str(p) for p in denied],
             auditor_output=dict(path=str(auditor_output), sha256=sha(auditor_output) if auditor_output.is_file() else None),
             guard_self_test=self_test, event_counts=events, rejected_runtime_accesses=rejected,
             auditor_succeeded=succeeded, error=error, new_emu_runs=0, new_nemu_runs=0,
             scope='Python file/enumeration access and explicit subprocess arguments; not an OS sandbox or clean-machine installation')
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof, indent=2))
sys.exit(0 if qualified else 1)

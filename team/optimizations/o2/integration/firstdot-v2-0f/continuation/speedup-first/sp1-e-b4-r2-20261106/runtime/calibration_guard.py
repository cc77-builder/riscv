"""Thin B4 entry using the byte-identical proven R7 guardian; no authorization creation."""
from pathlib import Path
import json,sys
import runner
from watchdog import run_guard

def main():
 runner.validate_authorization()
 package=Path(__file__).resolve().parent.parent
 command=[sys.executable,'-B',str(Path(__file__).resolve().parent/'runner.py'),'run-batch']
 result=run_guard(command,package,package/'external-batch',runner.contract()['budgets']['batch_outer_seconds'],True,'batch')
 print(json.dumps({'status':result['status'],'reason':result['reason'],'elapsed_seconds':result['elapsed_seconds'],'cleanup_ok':result['cleanup_ok']}))
 raise SystemExit(0 if result['status']=='GUARD_PASS' else 1)
if __name__=='__main__':main()

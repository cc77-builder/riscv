"""Future explicit-authorized bounded execution only. Not called by R4 host admission."""
from pathlib import Path
import sys,json
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N/'runtime'))
import runner
from watchdog import require_batch_guard
if __name__=='__main__':
    require_batch_guard(N);runner.verify();runner.validate_auth()
    outcome=runner.execute()
    print(json.dumps({'status':outcome['status']}))
    sys.exit(0 if outcome['status']=='CALIBRATION_TRIGGER_HIT_ONLY' else 1)

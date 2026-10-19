"""Fail closed: injected checker-observation corruption must be detected exactly."""
import argparse
from pathlib import Path

FAULTS = ("identity", "wen", "high", "cancel")
def check(fault, rc, text):
    if fault not in FAULTS or rc != 1:
        raise ValueError("wrong fault or return code")
    if text.splitlines() != [f"O2_FU_INJECT {fault}", f"O2_FU_FAIL {fault}"]:
        raise ValueError("wrong, missing, duplicate, unexpected, or escaped fault marker")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fault",choices=FAULTS,required=True)
    p.add_argument("--return-code",type=int,required=True)
    p.add_argument("--log",type=Path,required=True)
    a=p.parse_args()
    check(a.fault,a.return_code,a.log.read_text())
    print("O2_FU_NEGATIVE_GATE_PASS "+a.fault)
if __name__=="__main__": main()

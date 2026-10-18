"""Executable O1 interface specification, NOT Chisel/RTL simulation.

Division latency below is an arbitrary stimulus parameter; it is not a hardware
claim. The model validates intended transaction ordering, not ExeUnit circuitry.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    serial: int
    kind: str = 'vdot'
    v0: bool = False
    illegal: bool = False


class Contract:
    def __init__(self, *, handoff=True, latency=2):
        if latency not in (2, 3) or (handoff and latency != 2):
            raise ValueError('invalid mode')
        self.handoff, self.latency = handoff, latency
        self.cycle = 0
        self.pending = None
        self.accepted = self.responded = self.killed = self.reset_dropped = 0

    def step(self, incoming=None, *, ready=True, redirect=False, cancel=False, reset=False):
        if cancel and not redirect:
            raise ValueError('cancellation requires redirect')
        if incoming is not None and incoming.kind not in ('vdot', 'div'):
            raise ValueError('unknown request kind')
        old, due = self.pending if self.pending else (None, 0)
        output_valid = old is not None and self.cycle >= due and not cancel and not reset
        response = old if output_valid and ready else None
        overlap_allowed = bool(self.handoff and response and response.kind == 'vdot'
                               and incoming and incoming.kind == 'vdot')
        accept = incoming if (old is None or overlap_allowed) and not redirect and not reset else None
        visible = None if not output_valid else {
            'serial': old.serial, 'v0_wen': old.v0 and not old.illegal,
            'vec_wen': not old.v0 and not old.illegal, 'illegal': old.illegal}
        if reset:
            self.reset_dropped += int(old is not None)
            self.pending = None
        elif cancel and old:
            self.killed += 1
            self.pending = None
        elif response:
            self.responded += 1
            self.pending = None
        if accept:
            assert self.pending is None
            self.pending = (accept, self.cycle + (self.latency if accept.kind == 'vdot' else 5))
            self.accepted += 1
        assert self.accepted == self.responded + self.killed + self.reset_dropped + int(self.pending is not None)
        result = {'cycle': self.cycle, 'accepted': accept, 'response': response,
                  'visible': visible, 'busy_after': self.pending is not None}
        self.cycle += 1
        return result


def next_busy(*, busy, input_fire, output_fire, kill_old, kill_input, enabled):
    """Parent next-state equations under test (contract only)."""
    if input_fire and kill_input or busy and kill_old:
        return False
    if enabled:
        if input_fire:
            return True
        if output_fire:
            return False
    else:
        if output_fire:
            return False
        if input_fire:
            return True
    return busy

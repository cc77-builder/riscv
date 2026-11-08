"""Synthetic trace mutation tests. These exercise the checker, not RTL."""
import copy
import itertools
import random
import unittest
from o2_cancel_selector import base as a


class Fixture:
    def __init__(self):
        self.header = ('SP1_SCHEMA version=1 clock=global mode=p4_one_cycle min_latency=1 slots=2 rob_size=48 '
                       'ftq_size=8 vlen=128 vpu_width=195 perf_width=577')
        self.rows, self.entries = [], {}
        self.p = self.r = self.div = self.last_div = None
        self.seq, self.cycle = 0, 1

    def add(self, kind, /, **f):
        self.rows.append('SP1_' + kind + ' ' + ' '.join(
            k + '=' + (hex(v) if k in a.HEXES else str(v)) for k, v in f.items()))

    def enqueue(self, rob='0:5', pdest=7, vd=10, ftq='0:1'):
        e = dict(rob=rob, pdest=pdest, vd=vd, ftq=ftq, pc=0x80000000 + len(self.entries)*4)
        self.entries[rob] = e
        self.add('ENQUEUE', cycle=self.cycle - 1, rob=rob, pc=e['pc'], ftq=ftq,
                 word=(0x0294050b & ~(31 << 7)) | (vd << 7))
        return rob

    def request(self, rob, illegal=0, vl=8, vs1=0x807f01ff01020304, vs2=0xfe8001ff02040506):
        e = self.entries[rob]
        return dict(cycle=self.cycle, seq=self.seq, rob=rob, pdest=e['pdest'], vl=vl,
                    illegal=illegal, vecwen=int(e['vd'] != 0), v0wen=int(e['vd'] == 0),
                    vpu=1 << 178, perf=0xabc000 + self.seq, vs1=vs1, vs2=vs2)

    def packet(self, kind, t):
        f = {k:t[k] for k in ('seq','rob','pdest','illegal')}
        if True:
            f['data'] = 0 if t['illegal'] else a.dot_result(t['vs1'], t['vs2'])
        f.update(vecwen=0 if t['illegal'] else t['vecwen'],
                 v0wen=0 if t['illegal'] else t['v0wen'],
                 exception=4 if t['illegal'] else 0, vpu=t['vpu'], perf=t['perf'])
        self.add(kind, cycle=self.cycle, **f)

    def commit(self, t, cycle=None):
        e = self.entries[t['rob']]
        self.add('COMMIT', cycle=self.cycle + 1 if cycle is None else cycle,
                 rob=t['rob'], pc=e['pc'], ftq=e['ftq'])

    def tick(self, rob=None, *, ready=1, flush=None, wait=None, illegal=0, vl=8,
             div_fu=None, div_done=False, div_tail=False, auto_commit=True):
        c, p, r, d = self.cycle, self.p, self.r, self.div
        kp = bool(p and flush and a.flushed(p['rob'], *flush))
        kr = bool(r and flush and a.flushed(r['rob'], *flush))
        lp, lr = p is not None and not kp, r is not None and not kr
        move, out = bool(lp and (not lr or ready)), bool(lr)
        vready = int((not lp or not lr or ready) and not flush)
        divoccupied = int(d is not None or div_tail)
        accepted = rob is not None
        assert not (accepted and wait)
        request = self.request(rob, illegal, vl) if rob and not div_fu else None
        div_request = dict(cycle=c, seq=self.seq, rob=rob, fu=div_fu,
                           pdest=11) if div_fu else None
        if request or div_request:
            assert not flush and not divoccupied
            if request:
                assert vready
            else:
                assert not p and not r
        direct = bool(request and not lp and (not lr or ready))
        enqueue_p = bool(request and not direct)
        occupancy = int(p is not None) + int(r is not None)
        busy = int(bool(occupancy or divoccupied))
        self.add('STATE', cycle=c, pvalid=int(p is not None), pseq=p['seq'] if p else 0,
                 prob=p['rob'] if p else '0:0', ppdest=p['pdest'] if p else 0,
                 rvalid=int(r is not None), rseq=r['seq'] if r else 0,
                 rrob=r['rob'] if r else '0:0', rpdest=r['pdest'] if r else 0,
                 occupancy=occupancy, invalid=int(accepted or wait is not None),
                 inready=int(accepted), vready=vready, outvalid=int(out), outready=ready,
                 move=int(move), directr=int(direct), enqueuep=int(enqueue_p), killp=int(kp), killr=int(kr),
                 divactive=int(d is not None), divseq=d['seq'] if d else 0,
                 divoccupied=divoccupied, busy=busy)
        if flush:
            origin, self_flush = flush
            self.add('REDIRECT', cycle=c-1, rob=origin, ftq='0:1', self=self_flush)
            self.add('VFEX4_REDIRECT', cycle=c, rob=origin, self=self_flush)
        if accepted:
            t = request or div_request
            self.add('VFEX4_ACCEPT', cycle=c, seq=t['seq'], rob=rob,
                     fu=a.VDOT if request else div_fu, pdest=t['pdest'])
            self.add('ACCEPT' if request else 'DIV_ACCEPT', **t)
            self.seq += 1
        if wait:
            self.add('VFEX4_WAIT', cycle=c, rob=wait, fu=a.VDOT, busy=busy)
        for slot, t, killed in (('P',p,kp),('R',r,kr)):
            if killed:
                self.add('KILL', cycle=c, seq=t['seq'], slot=slot, rob=t['rob'],
                         pdest=t['pdest'], redirect=flush[0], self=flush[1])
        if request:
            self.packet('DIRECT_R' if direct else 'ENQUEUE_P', request)
        if move:
            self.packet('MOVE', p)
        if out:
            self.packet('RESPONSE' if ready else 'STALL', r)
            if ready and auto_commit and not r['illegal']:
                self.commit(r)
        dk = d and flush and a.flushed(d['rob'], *flush)
        if dk:
            self.add('DIV_KILL', cycle=c, **{k:d[k] for k in ('seq','rob','fu','pdest')},
                     redirect=flush[0], self=flush[1])
            d['cancelled'] = True
            self.div = None
        if div_done or div_tail:
            t = self.last_div
            self.add('DIV_OUTPUT', cycle=c, **{k:t[k] for k in ('seq','rob','fu','pdest')},
                     ready=1, cancelled=int(t.get('cancelled', False)))
            if not t.get('cancelled'):
                self.div = None
        if div_request:
            self.div = self.last_div = div_request
        self.p = request if enqueue_p else p if lp and not move else None
        self.r = p if move else request if direct else r if lr and not ready else None
        self.cycle += 1
        return request

    def drain(self):
        while self.p or self.r:
            self.tick()
        self.tick()

    def text(self):
        rows = sorted(self.rows, key=lambda line:int(line.split('cycle=')[1].split()[0]))
        return self.header + '\n' + '\n'.join(rows) + ('\n' if rows else '')


def basic():
    f=Fixture()
    f.enqueue()
    f.tick('0:5')
    f.drain()
    return f


def stream():
    f=Fixture()
    for i in range(5,9):
        f.enqueue(f'0:{i}', pdest=i+2, vd=0 if i == 6 else 10)
    for i in range(5,9):
        f.tick(f'0:{i}')
    f.drain()
    return f


def blocked():
    f=Fixture()
    f.enqueue(); f.enqueue('0:6',8)
    f.tick('0:5'); f.tick('0:6',ready=0)
    f.tick(ready=0,wait='0:7'); f.tick(ready=0,wait='0:7')
    f.drain()
    return f


def killed(reverse=False, both=False, wrap=False):
    f=Fixture()
    older,newer=('0:47','1:0') if wrap else ('0:5','0:6')
    first,second=(newer,older) if reverse else (older,newer)
    f.enqueue(first); f.enqueue(second,8)
    f.tick(first); f.tick(second,ready=0)
    f.tick(ready=0,flush=(older,int(both)),auto_commit=False)
    f.drain()
    return f


def change(text, prefix, old, new):
    rows=text.splitlines(keepends=True)
    for i,row in enumerate(rows):
        if row.startswith(prefix):
            assert old in row,(row,old)
            rows[i]=row.replace(old,new,1)
            return ''.join(rows)
    raise AssertionError(prefix)


def drop(text,prefix):
    rows=text.splitlines(keepends=True)
    for i,row in enumerate(rows):
        if row.startswith(prefix):
            return ''.join(rows[:i]+rows[i+1:])
    raise AssertionError(prefix)


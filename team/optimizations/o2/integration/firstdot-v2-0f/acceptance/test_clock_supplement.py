import copy
import unittest
import clock_supplement as c

class ClockContractTests(unittest.TestCase):
    def setUp(self):
        self.raw=dict(pid=123,command=["emu"],cwd="/tmp/private",exit_code=0,raw_logs_sha256={"stdout.log":"sha"})
        self.clock=dict(self.raw)
        for index,key in enumerate(("before_popen","after_popen","before_wait","after_wait")):
            self.clock[key]=dict(utc=f"2026-10-27T00:00:0{index}+00:00",monotonic_ns=(index+1)*1000000000,boot_id="boot-a")
    def test_valid(self):
        self.assertEqual(c.clock_check(self.clock,self.raw)["status"],"PASS")
    def test_pid(self):
        self.clock["pid"]=124
        with self.assertRaises(RuntimeError): c.clock_check(self.clock,self.raw)
    def test_boot(self):
        self.clock["after_wait"]["boot_id"]="boot-b"
        with self.assertRaises(RuntimeError): c.clock_check(self.clock,self.raw)
    def test_monotonic_reverse(self):
        self.clock["after_wait"]["monotonic_ns"]=1
        with self.assertRaises(RuntimeError): c.clock_check(self.clock,self.raw)
    def test_receipt_binding(self):
        self.clock["command"]=["other"]
        with self.assertRaises(RuntimeError): c.clock_check(self.clock,self.raw)
    def test_wall_clock_backwards_reported(self):
        self.clock["after_wait"]["utc"]="2026-10-26T23:59:59+00:00"
        result=c.clock_check(self.clock,self.raw)
        self.assertFalse(result["utc_nondecreasing"])
        self.assertEqual(result["status"],"PASS")
    def test_capacity_overflow(self):
        rows=[dict(name=str(i),started="2026-10-27T00:00:00+00:00",finished="2026-10-27T00:00:01+00:00") for i in range(4)]
        self.assertEqual(c.capacity(rows,3)["status"],"FAIL")
        self.assertEqual(c.capacity(rows[:3],3)["status"],"PASS")
    def test_duplicate(self):
        r=dict(name="a",started="2026-10-27T00:00:00+00:00",finished="2026-10-27T00:00:01+00:00")
        with self.assertRaises(RuntimeError): c.capacity([r,r],3)
    def test_inverted_utc(self):
        with self.assertRaises(RuntimeError):
            c.capacity([dict(name="a",started="2026-10-27T00:00:02+00:00",finished="2026-10-27T00:00:01+00:00")],3)
    def test_old_missing_timeout(self):
        runtime=dict(name="a",process_started=True,pid=123,exit_code=0,actual_new_execution=True,performance_measured=False)
        c.binding(runtime,runtime)
        runtime["timed_out"]=True
        with self.assertRaises(RuntimeError): c.binding(runtime,runtime)
    def test_spawn_mismatch(self):
        runtime=dict(name="a",process_started=True,pid=123,exit_code=0,timed_out=False,terminated_returncode=None,actual_new_execution=True,performance_measured=False)
        c.binding(runtime,runtime)
        result=dict(runtime,pid=124)
        with self.assertRaises(RuntimeError): c.binding(runtime,result)

if __name__=="__main__": unittest.main()

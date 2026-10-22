import unittest
import check as c
class CheckerTests(unittest.TestCase):
    def words(self):
        return dict(enumerate([]))
    def window(self,extra):
        values=[c.base.START,*c.base.COUNTERS[:2],*extra,*c.base.COUNTERS[2:],c.base.STOP]
        return {0x1000+4*i:w for i,w in enumerate(values)}
    def test_pointer_write_to_t6_is_not_a_loop(self):
        self.assertEqual(len(c.walk(self.window([0x00060f93]))),7)
    def test_control_flow_rejected(self):
        for word in (0x00000063,0x0000006f,0x00008067):
            with self.assertRaisesRegex(ValueError,"branch"):c.walk(self.window([word]))
    def test_missing_counter_rejected(self):
        data=self.window([]);del data[0x1004]
        with self.assertRaises(ValueError):c.walk(data)
    def test_counter_order_rejected(self):
        data=self.window([]);data[0x1004],data[0x1008]=data[0x1008],data[0x1004]
        with self.assertRaises(ValueError):c.walk(data)

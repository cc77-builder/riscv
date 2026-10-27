"""Exercise semantic input comparison without weakening the sealed byte hashes."""
import unittest

from merged_regression_evidence import compare_json_inputs


class SealedInputComparisonTests(unittest.TestCase):
    def check(self, left, right):
        compare_json_inputs(left, right, 'runtime-inputs.json')

    def test_only_object_order_and_whitespace_may_differ(self):
        self.check(b'{"a": "sha-a", "b": {"x": 1, "y": [2,3]}}\n',
                   b'{\n "b": {"y": [2, 3], "x": 1}, "a": "sha-a"\n}')

    def test_missing_added_changed_and_reordered_values_are_rejected(self):
        original = b'{"a": "sha-a", "b": [1,2]}'
        for changed in (b'{"a": "sha-a"}', b'{"a": "sha-a", "b": [1,2], "c": null}',
                        b'{"a": "sha-b", "b": [1,2]}', b'{"a": "sha-a", "b": [2,1]}'):
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, 'input differs'):
                self.check(original, changed)

    def test_boolean_integer_and_float_substitutions_are_rejected(self):
        for changed in (b'{"a":true}', b'{"a":1.0}'):
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, 'input differs'):
                self.check(b'{"a":1}', changed)

    def test_duplicate_keys_are_rejected_even_when_effective_values_match(self):
        with self.assertRaisesRegex(ValueError, 'duplicate JSON'):
            self.check(b'{"a":1}', b'{"a":0,"a":1}')

    def test_nonstandard_json_constants_are_rejected(self):
        for value in (b'NaN', b'Infinity', b'-Infinity'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'non-standard JSON'):
                self.check(b'{"a":'+value+b'}', b'{"a":'+value+b'}')


if __name__ == '__main__':
    unittest.main()

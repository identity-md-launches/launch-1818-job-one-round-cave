import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('window_diff_test', HERE / 'window_diff.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.raw = (HERE.parent / 'settlement-window/demo-plan.json').read_bytes()
        self.plan = json.loads(self.raw)
        self.pin = hashlib.sha256(self.raw).hexdigest()

    def check(self, plan=None):
        return m.compare(self.raw, json.dumps(self.plan if plan is None else plan).encode(), self.pin)

    def test_unchanged_real_plan_and_no_evidence_reads(self):
        with patch.object(m.w.b.k, 'review_file', side_effect=AssertionError('evidence opened')):
            with patch.object(m.d.b.k, 'review_file', side_effect=AssertionError('evidence opened')):
                self.assertTrue(self.check()['planCompatible'])
                self.assertEqual(m.compare(self.raw, self.raw, self.pin)['windowChanges'], [])

    def test_each_widened_edge_rejects(self):
        for field, delta in (('notBeforeBlock', -1), ('notAfterBlock', 1)):
            plan = copy.deepcopy(self.plan)
            plan['windows'][0][field] += delta
            result = self.check(plan)
            self.assertFalse(result['planCompatible'])
            self.assertEqual(result['windowChanges'][0]['kind'], 'window_widened')

    def test_narrower_edge_cannot_offset_wider_edge(self):
        self.plan['windows'][0]['notBeforeBlock'] += 1
        self.plan['windows'][0]['notAfterBlock'] += 1
        result = self.check()
        self.assertFalse(result['planCompatible'])
        self.assertEqual(len(result['windowChanges']), 2)

    def test_narrowing_and_reordering_and_case_alias(self):
        for row in self.plan['windows']:
            if row['notAfterBlock'] - row['notBeforeBlock'] >= 2:
                row['notBeforeBlock'] += 1
                row['notAfterBlock'] -= 1
            row['transactionHash'] = '0x' + row['transactionHash'][2:].upper()
        self.plan['windows'].reverse()
        self.plan['batch']['items'].reverse()
        result = self.check()
        self.assertTrue(result['planCompatible'])
        self.assertTrue(result['windowOrderChanged'])
        self.assertTrue(result['batchComparison']['orderChanged'])

    def test_policy_weakening_reference_and_transaction_changes(self):
        for kind in ('confirmations', 'finality', 'evidence', 'sha256', 'remove'):
            p = copy.deepcopy(self.plan)
            item = p['batch']['items'][0]
            if kind == 'confirmations':
                item['policy']['minimumConfirmations'] -= 1
            elif kind == 'finality':
                item['policy']['requireFinalized'] = False
            elif kind == 'evidence':
                item['evidence'] = 'line-3/nonexistent.json'
            elif kind == 'sha256':
                item['sha256'] = 'a'*64
            else:
                tx = item['policy']['transactionHash']
                p['batch']['items'].pop(0)
                p['windows'] = [r for r in p['windows'] if r['transactionHash'] != tx]
            with self.subTest(kind=kind):
                self.assertFalse(self.check(p)['planCompatible'])

    def test_pin_mismatch_precedes_parsing(self):
        with patch.object(m.w.b.k.p.s, 'strict_json', side_effect=AssertionError('parsed')):
            result = m.compare(b'not json', b'also invalid', self.pin)
        self.assertEqual(result['state'], 'baseline_pin_mismatch')

    def test_strict_full_validation(self):
        for value in (True, -1, 2**64, '12', 2.5):
            p = copy.deepcopy(self.plan)
            p['windows'][1]['notBeforeBlock'] = value
            with self.subTest(value=value), self.assertRaises(m.Error):
                self.check(p)
        for raw in (b'{"version":1,"version":1}', b'{"x":NaN}', b' ' * 90001):
            with self.assertRaises(m.Error):
                m.compare(raw, self.raw, hashlib.sha256(raw).hexdigest())
        self.plan['windows'][1]['memo'] = 'unreviewed'
        with self.assertRaises(m.Error):
            self.check()

    def test_cli_and_path_refusals(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(m.main(['--demo']), 0)
        self.assertFalse(json.loads(out.getvalue())['evidenceChecked'])
        for args in (['--demo', '--baseline', 'x'], [],
                     ['--baseline', '../outside', '--proposed', 'x', '--baseline-sha256', self.pin]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(m.main(args), 2)

    def test_inputs_not_mutated_and_changes_after_first_failure(self):
        self.plan['windows'][0]['notBeforeBlock'] -= 1
        self.plan['windows'][1]['notAfterBlock'] += 1
        saved = copy.deepcopy(self.plan)
        self.assertEqual(len(self.check()['windowChanges']), 2)
        self.assertEqual(self.plan, saved)

    def test_cli_widening_exits_one_and_reports_both_hashes(self):
        folder = Path('test/scratch/window-plan-diff')
        folder.mkdir(parents=True, exist_ok=True)
        baseline, proposed = folder / 'baseline.json', folder / 'proposed.json'
        baseline.write_bytes(self.raw)
        self.plan['windows'][1]['notAfterBlock'] += 1
        proposed.write_text(json.dumps(self.plan))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = m.main(['--baseline', str(baseline), '--proposed', str(proposed),
                           '--baseline-sha256', self.pin])
        self.assertEqual(code, 1)
        result = json.loads(out.getvalue())
        self.assertEqual(result['baselineSha256'], self.pin)
        self.assertEqual(result['proposedSha256'], hashlib.sha256(proposed.read_bytes()).hexdigest())
        self.assertEqual(result['state'], 'plan_review_required')

    def test_added_transaction_requires_review(self):
        old = copy.deepcopy(self.plan)
        tx = old['batch']['items'].pop()['policy']['transactionHash']
        old['windows'] = [r for r in old['windows'] if r['transactionHash'] != tx]
        raw = json.dumps(old).encode()
        self.assertFalse(m.compare(raw, self.raw, hashlib.sha256(raw).hexdigest())['planCompatible'])

    def test_all_windows_validate_before_comparison(self):
        for kind in ('duplicate', 'missing', 'unknown', 'reversed'):
            p = copy.deepcopy(self.plan)
            if kind == 'duplicate':
                p['windows'][1] = copy.deepcopy(p['windows'][0])
            elif kind == 'missing':
                p['windows'].pop()
            elif kind == 'unknown':
                p['extra'] = True
            else:
                p['windows'][1]['notBeforeBlock'] = p['windows'][1]['notAfterBlock'] + 1
            with self.subTest(kind=kind), self.assertRaises(m.Error):
                self.check(p)

    def test_stronger_policy_and_single_block_window(self):
        self.plan['batch']['items'][0]['policy']['minimumConfirmations'] += 1
        row = self.plan['windows'][1]
        row['notBeforeBlock'] = row['notAfterBlock']
        result = self.check()
        self.assertTrue(result['planCompatible'])
        self.assertEqual(result['windowChanges'][0]['kind'], 'window_narrowed')


if __name__ == '__main__':
    unittest.main()

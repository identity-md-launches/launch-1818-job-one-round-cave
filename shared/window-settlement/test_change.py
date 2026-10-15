"""Non-weakening plans still need real retained ZTO evidence to settle."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tested_window_change', HERE / 'change.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ChangeTests(unittest.TestCase):
    def setUp(self):
        self.raw = (HERE / 'plan.json').read_bytes()
        self.pin = hashlib.sha256(self.raw).hexdigest()
        self.plan = json.loads(self.raw)

    def review(self, plan=None):
        raw = (json.dumps(self.plan if plan is None else plan) + '\n').encode()
        return m.review(self.raw, raw, self.pin, hashlib.sha256(raw).hexdigest())

    def test_historical_real_zto_replay(self):
        result = self.review()
        self.assertTrue(result['accepted'])
        self.assertTrue(result['planComparison']['planCompatible'])
        self.assertTrue(result['evidenceChecked'])
        self.assertEqual([r['inclusionBlock'] for r in
            result['settlementReview']['windowReview']['comparisons']], [26190898, 26194715])

    def test_narrowing_accepts_only_if_actual_inclusion_remains(self):
        self.plan['windows'][1].update(notBeforeBlock=26194715, notAfterBlock=26194715)
        self.assertTrue(self.review()['accepted'])
        self.plan['windows'][1].update(notBeforeBlock=26194716, notAfterBlock=26194716)
        result = self.review()
        self.assertTrue(result['planComparison']['planCompatible'])
        self.assertFalse(result['accepted'])
        self.assertTrue(result['windowChecked'])
        self.assertEqual(result['state'], 'window_review_required')

    def test_each_widened_edge_refuses_before_evidence(self):
        for field, delta in (('notBeforeBlock', -1), ('notAfterBlock', 1)):
            p = copy.deepcopy(self.plan)
            p['windows'][1][field] += delta
            with self.subTest(field=field), patch.object(m.gate, 'review',
                    side_effect=AssertionError('evidence opened')):
                result = self.review(p)
            self.assertEqual(result['state'], 'plan_review_required')
            self.assertFalse(result['evidenceChecked'])

    def test_policy_weakening_and_changed_evidence_refuse(self):
        for kind in ('confirmations', 'finality', 'path', 'pin'):
            p = copy.deepcopy(self.plan)
            item = p['batch']['items'][0]
            if kind == 'confirmations': item['policy']['minimumConfirmations'] -= 1
            elif kind == 'finality': item['policy']['requireFinalized'] = False
            elif kind == 'path': item['evidence'] = 'missing-evidence.json'
            else: item['sha256'] = p['batch']['items'][1]['sha256']
            with self.subTest(kind=kind), patch.object(m.gate, 'review',
                    side_effect=AssertionError('evidence opened')):
                self.assertEqual(self.review(p)['state'], 'plan_review_required')

    def test_stronger_unmet_confirmations_never_accept(self):
        self.plan['batch']['items'][0]['policy']['minimumConfirmations'] = 1000000
        result = self.review()
        self.assertTrue(result['planComparison']['planCompatible'])
        self.assertFalse(result['accepted'])
        self.assertFalse(result['windowChecked'])

    def test_baseline_pin_before_either_parse(self):
        with patch.object(m.gate.window.b.k.p.s, 'strict_json',
                side_effect=AssertionError('parsed')):
            r = m.review(b'bad', b'also bad', self.pin, self.pin)
        self.assertEqual(r['state'], 'baseline_pin_mismatch')

    def test_proposed_pin_before_either_parse(self):
        with patch.object(m.gate.window.b.k.p.s, 'strict_json',
                side_effect=AssertionError('parsed')):
            r = m.review(self.raw, b'bad', self.pin, self.pin)
        self.assertEqual(r['state'], 'proposed_pin_mismatch')

    def test_structural_diagnostic_before_comparison(self):
        self.plan['windows'][1]['notAfterBlock'] = '26194720'
        with patch.object(m.diff, 'compare', side_effect=AssertionError('compared')):
            r = self.review()
        self.assertEqual(r['state'], 'structural_review_required')
        self.assertEqual(r['structure']['proposed']['diagnostics'][0]['path'],
                         '/windows/1/notAfterBlock')
        self.assertFalse(r['evidenceChecked'])

    def test_baseline_structure_also_required(self):
        p = copy.deepcopy(self.plan)
        p['accepted'] = True
        raw = json.dumps(p).encode()
        r = m.review(raw, self.raw, hashlib.sha256(raw).hexdigest(), self.pin)
        self.assertEqual(r['state'], 'structural_review_required')
        self.assertFalse(r['structure']['baseline']['valid'])

    def test_reordered_storage_and_case_aliases(self):
        self.plan['batch']['items'].reverse()
        self.plan['windows'].reverse()
        for row in self.plan['windows']:
            row['transactionHash'] = '0x' + row['transactionHash'][2:].upper()
        self.assertTrue(self.review()['accepted'])

    def test_semantic_error_before_evidence(self):
        self.plan['windows'][1]['notBeforeBlock'] = self.plan['windows'][1]['notAfterBlock'] + 1
        with patch.object(m.gate, 'review', side_effect=AssertionError('opened')):
            with self.assertRaises(m.diff.Error):
                self.review()

    def test_missing_evidence_is_not_compatible_plan_acceptance(self):
        with patch.object(m.gate.window.b.k, 'review_file',
                          side_effect=FileNotFoundError('missing')):
            r = self.review()
        self.assertFalse(r['accepted'])
        self.assertTrue(r['planComparison']['planCompatible'])

    def test_strict_bytes_bounds_and_complete_output(self):
        for raw in (b'{"version":1,"version":1}', b'{"x":NaN}', b'\xff', b' ' * 90001):
            with self.subTest(raw=raw[:20]), self.assertRaises(m.ERRORS):
                m.review(self.raw, raw, self.pin, hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ValueError):
            m.review(bytearray(self.raw), self.raw, self.pin, self.pin)
        with self.assertRaises(ValueError):
            m.gate.render({'accepted': True, 'tooLarge': 'x' * 100000})

    def test_same_cli_path_captured_once_and_exact_proposed_replayed(self):
        path = str((HERE / 'plan.json').relative_to(Path.cwd()))
        original = m.gate.window.b.k.load_bytes
        def capture(name):
            return self.raw if str(name) == path else original(name)
        with patch.object(m.gate.window.b.k, 'load_bytes', side_effect=capture) as reader:
            with patch.object(m.gate, 'review', wraps=m.gate.review) as replay:
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    status = m.main([path, path, '--baseline-sha256', self.pin,
                                     '--proposed-sha256', self.pin])
        self.assertEqual(status, 0)
        self.assertEqual(sum(str(c.args[0]) == path for c in reader.call_args_list), 1)
        replay.assert_called_once_with(self.raw, self.pin)
        self.assertTrue(json.loads(out.getvalue())['accepted'])

    def test_bad_pin_before_io_and_no_partial_output(self):
        with patch.object(m.gate.window.b.k, 'load_bytes', side_effect=AssertionError('opened')):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                status = m.main(['x', 'y', '--baseline-sha256', 'bad',
                                 '--proposed-sha256', self.pin])
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(out.getvalue())['state'], 'input_error')

    def test_no_network_and_no_mutation(self):
        files = [HERE / 'plan.json', HERE / 'plan.sha256'] + [
            Path(i['evidence']) for i in self.plan['batch']['items']]
        before = [p.read_bytes() for p in files]
        with patch.object(m.gate.window.b.k.p.s.RPC, 'call', side_effect=AssertionError('network')):
            self.assertTrue(self.review()['accepted'])
        self.assertEqual(before, [p.read_bytes() for p in files])


if __name__ == '__main__':
    unittest.main(verbosity=2)

import copy
import io
import json
from pathlib import Path
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

import digest_inventory as inv
from typed_digest import load_workspace_json, TypedDataError

FOLDER = Path(__file__).absolute().parent
EXPECTED = '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774'


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.source = load_workspace_json(FOLDER / 'zto-payment.json')
        self.manifest = {'requests': [
            {'id': 'first', 'path': 'a', 'expect': EXPECTED},
            {'id': 'second', 'path': 'b'},
            {'id': 'third', 'path': 'c'},
        ]}
        self.data = {key: copy.deepcopy(self.source) for key in 'abc'}
        self.data['b']['domain']['chainId'] = '0x1'
        self.data['b']['message']['confirmations'] = '12'
        self.data['c']['message']['minimumRaw'] = str(int(self.source['message']['minimumRaw']) + 1)

    def run_report(self):
        return inv.inventory(self.manifest, self.data.__getitem__)

    def test_equivalent_encoding_and_one_unit_change(self):
        report = self.run_report()
        self.assertTrue(report['complete'])
        self.assertEqual(report['items'][0]['digest'], EXPECTED)
        self.assertEqual(report['repeatedDigests'], [{'hash': EXPECTED, 'ids': ['first', 'second']}])
        self.assertEqual(report['sharedDomainSeparators'][0]['ids'], ['first', 'second', 'third'])
        self.assertFalse(report['allEntriesPinned'])
        self.assertTrue(report['allSuppliedExpectationsMatch'])

    def test_different_chain_separates_groups(self):
        self.data['b']['domain']['chainId'] = 2
        report = self.run_report()
        self.assertEqual(report['repeatedDigests'], [])
        self.assertEqual(report['sharedDomainSeparators'][0]['ids'], ['first', 'third'])

    def test_mismatch_retains_complete_inventory(self):
        self.manifest['requests'][2]['expect'] = EXPECTED
        report = self.run_report()
        self.assertFalse(report['allSuppliedExpectationsMatch'])
        self.assertEqual(len(report['items']), 3)
        self.assertFalse(report['items'][2]['matchesExpectedDigest'])

    def test_all_pins_and_case_normalization(self):
        self.manifest['requests'] = self.manifest['requests'][:2]
        self.manifest['requests'][1]['expect'] = '0x' + EXPECTED[2:].upper()
        report = self.run_report()
        self.assertTrue(report['allEntriesPinned'])
        self.assertTrue(report['allSuppliedExpectationsMatch'])

    def test_manifest_rejected_before_any_request_read(self):
        malformed = [None, {}, {'requests': []}, {'requests': [None]},
                     {'requests': self.manifest['requests'] * 6}]
        for field, value in [('id', 'first'), ('id', 'bad label'), ('path', None),
                             ('expect', EXPECTED[:-2]), ('extra', True)]:
            manifest = copy.deepcopy(self.manifest)
            manifest['requests'][-1][field] = value
            malformed.append(manifest)
        for manifest in malformed:
            with self.subTest(manifest=manifest):
                with patch.object(inv, 'digest') as calculate:
                    with self.assertRaises(ValueError):
                        inv.inventory(manifest, lambda _: self.fail('unexpected read'))
                    calculate.assert_not_called()

    def test_unselected_invalid_entry_cannot_be_hidden(self):
        self.data['c']['message']['confirmations'] = -1
        with self.assertRaises(ValueError):
            self.run_report()

    def test_each_entry_captured_once_and_inputs_unchanged(self):
        before = copy.deepcopy((self.manifest, self.data))
        calls = []
        def loader(name):
            calls.append(name)
            return self.data[name]
        inv.inventory(self.manifest, loader)
        self.assertEqual(calls, ['a', 'b', 'c'])
        self.assertEqual((self.manifest, self.data), before)

    def test_missing_input_aborts(self):
        def loader(name):
            if name == 'c':
                raise FileNotFoundError('missing input')
            return self.data[name]
        with self.assertRaises(FileNotFoundError):
            inv.inventory(self.manifest, loader)

    def test_no_pins_is_explicit(self):
        for item in self.manifest['requests']:
            item.pop('expect', None)
        report = self.run_report()
        self.assertFalse(report['allEntriesPinned'])
        self.assertTrue(all(r['matchesExpectedDigest'] is None for r in report['items']))

    def test_order_is_manifest_order(self):
        self.manifest['requests'].reverse()
        report = self.run_report()
        self.assertEqual([r['id'] for r in report['items']], ['third', 'second', 'first'])
        self.assertEqual(report['repeatedDigests'][0]['ids'], ['second', 'first'])

    def test_output_bound_fails_closed(self):
        with patch.object(inv, 'MAX_REPORT_BYTES', 10):
            with self.assertRaises(TypedDataError):
                self.run_report()

    def test_path_refusal_without_opening_outside_workspace(self):
        for path in ('../outside.json', '.hidden/input.json', '/outside/input.json'):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    inv.inventory({'requests': [{'id': 'bad', 'path': path}]})

    def test_cli_success_mismatch_and_invalid_no_success_output(self):
        for mode, expected_code in [('match', 0), ('mismatch', 1), ('invalid', 2)]:
            manifest = copy.deepcopy(self.manifest)
            if mode == 'mismatch':
                manifest['requests'][2]['expect'] = EXPECTED
            if mode == 'invalid':
                self.data['c']['message']['confirmations'] = -1
            def loader(name):
                return manifest if name == 'manifest' else self.data[name]
            out, err = io.StringIO(), io.StringIO()
            with patch.object(inv, 'load_workspace_json', loader):
                # The injected inventory loader makes the CLI transport-free.
                original = inv.inventory
                with patch.object(inv, 'inventory', lambda data: original(data, loader)):
                    with redirect_stdout(out), redirect_stderr(err):
                        code = inv.main(['manifest'])
            self.assertEqual(code, expected_code)
            if mode == 'invalid':
                self.assertEqual(out.getvalue(), '')
                self.assertIn('digest-inventory:', err.getvalue())
            else:
                self.assertTrue(json.loads(out.getvalue())['complete'])


if __name__ == '__main__':
    unittest.main()

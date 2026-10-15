#!/usr/bin/env python3
"""Review window-plan changes against an independently retained baseline hash."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def sibling(name, filename):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'),
        Path(__file__).resolve().parent.parent / name / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


w = sibling('settlement-window', 'window.py')
d = sibling('settlement-plan-diff', 'plan_diff.py')
Error = w.Error
# Both inherited module trees define the same exception class by separate loads.
INPUT_ERRORS = (Error, d.Error, ValueError, TypeError, KeyError, OSError, RecursionError)
LIMITATIONS = ('Plan comparison only; no evidence is opened and no settlement is asserted. '
    'A narrower window can still exclude the actual inclusion. Replay the proposed plan '
    'with settlement-window after review. Retain the baseline hash independently; '
    'replacing both defeats this check. No payment authorization or current freshness.')


def compare(old_raw, new_raw, baseline_sha256):
    expected = w.b.k.pin(baseline_sha256)
    for raw in (old_raw, new_raw):
        if type(raw) is not bytes or len(raw) > w.b.k.LIMIT:
            raise Error('bounded exact plan bytes required')
    actual = hashlib.sha256(old_raw).hexdigest()
    proposed = hashlib.sha256(new_raw).hexdigest()
    result = dict(planCompatible=False, state='baseline_pin_mismatch',
        baselineSha256=actual, expectedBaselineSha256=expected,
        proposedSha256=proposed, evidenceChecked=False, limitations=LIMITATIONS)
    if actual != expected:
        return result
    old = w.b.k.p.s.strict_json(old_raw)
    new = w.b.k.p.s.strict_json(new_raw)
    before, after = w.validate(old), w.validate(new)
    # Reuse all transaction, policy and evidence-reference comparison rules.
    a = json.dumps(old['batch'], ensure_ascii=True).encode('ascii')
    z = json.dumps(new['batch'], ensure_ascii=True).encode('ascii')
    batch = d.compare(a, z, hashlib.sha256(a).hexdigest())
    changes = []
    for tx in sorted(before.keys() & after.keys()):
        for i, field in enumerate(('notBeforeBlock', 'notAfterBlock')):
            left, right = before[tx][i], after[tx][i]
            if left == right:
                continue
            wider = right < left if i == 0 else right > left
            changes.append(dict(transactionHash=tx, field=field, before=left,
                after=right, kind='window_widened' if wider else 'window_narrowed',
                blocking=wider))
    compatible = batch['planCompatible'] and not any(c['blocking'] for c in changes)
    result.update(planCompatible=compatible,
        state='plan_unchanged_or_stricter' if compatible else 'plan_review_required',
        batchComparison=batch, windowChanges=changes,
        windowOrderChanged=[r['transactionHash'].lower() for r in old['windows']] !=
                           [r['transactionHash'].lower() for r in new['windows']])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--baseline')
    parser.add_argument('--proposed')
    parser.add_argument('--baseline-sha256')
    args = parser.parse_args(argv)
    try:
        if args.demo:
            if any(x is not None for x in (args.baseline, args.proposed, args.baseline_sha256)):
                raise Error('demo refuses overrides')
            folder = (Path(__file__).resolve().parent.parent /
                      'settlement-window').relative_to(Path.cwd())
            old = w.b.k.load_bytes(folder / 'demo-plan.json')
            expected = w.b.k.load_bytes(folder / 'demo-plan.sha256').decode('ascii').strip()
            result = compare(old, old, expected)
            result['demoNote'] = 'Unchanged window plan for two historical real ZTO transactions.'
        else:
            if any(x is None for x in (args.baseline, args.proposed, args.baseline_sha256)):
                raise Error('baseline, proposed and retained baseline pin required')
            expected = w.b.k.pin(args.baseline_sha256)
            result = compare(w.b.k.load_bytes(args.baseline),
                             w.b.k.load_bytes(args.proposed), expected)
        encoded = json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False) + '\n'
        if len(encoded.encode('ascii')) > 100000:
            raise Error('report exceeds 100 KB')
        print(encoded, end='')
        return 0 if result['planCompatible'] else 1
    except INPUT_ERRORS:
        print(json.dumps(dict(planCompatible=False, state='input_error',
            reason='Invalid bounded window plans, paths or baseline pin')))
        return 2


if __name__ == '__main__':
    sys.exit(main())

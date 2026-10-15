#!/usr/bin/env python3
"""Require a non-weakened window plan and successful replay of its exact bytes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, HERE / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load('change_window_gate', 'review.py')
diff = load('change_window_diff', 'vendor/window-plan-diff/window_diff.py')
ERRORS = (*diff.INPUT_ERRORS, gate.window.Error)
LIMITATIONS = ('Historical provider observations, not current chain truth or a state proof. '
    'A non-weakened plan is not settlement; both gates must pass. '
    'Keep baseline and proposed hashes independently. Replacing bytes and pins together '
    'defeats retention. No payment amount, authorization, signing or deployment.')


def review(baseline_raw, proposed_raw, baseline_pin, proposed_pin):
    """Use each captured plan exactly once; never promote a baseline or pin."""
    for pin in (baseline_pin, proposed_pin):
        gate.window.b.k.pin(pin)
    for raw in (baseline_raw, proposed_raw):
        if type(raw) is not bytes or len(raw) > gate.window.b.k.LIMIT:
            raise ValueError('bounded exact plan bytes required')
    result = dict(accepted=False, state='baseline_pin_mismatch',
        baselineSha256=hashlib.sha256(baseline_raw).hexdigest(),
        proposedSha256=hashlib.sha256(proposed_raw).hexdigest(),
        expectedBaselineSha256=baseline_pin, expectedProposedSha256=proposed_pin,
        evidenceChecked=False, windowChecked=False, limitations=LIMITATIONS)
    if result['baselineSha256'] != baseline_pin:
        return result
    if result['proposedSha256'] != proposed_pin:
        result['state'] = 'proposed_pin_mismatch'
        return result
    # Structural diagnostics come before semantics or evidence reads.
    structure = {}
    for role, raw in (('baseline', baseline_raw), ('proposed', proposed_raw)):
        value = gate.window.b.k.p.s.strict_json(raw)
        errors = gate.contracts.validate(value, gate.CONTRACT)
        structure[role] = dict(valid=not errors, diagnostics=errors)
    result['structure'] = structure
    if not all(row['valid'] for row in structure.values()):
        result['state'] = 'structural_review_required'
        gate.render(result)
        return result
    comparison = diff.compare(baseline_raw, proposed_raw, baseline_pin)
    result['planComparison'] = comparison
    if not comparison['planCompatible']:
        result['state'] = 'plan_review_required'
        gate.render(result)
        return result
    # Replay the SAME captured proposed bytes, with the caller's retained pin.
    settlement = gate.review(proposed_raw, proposed_pin)
    result.update(accepted=settlement['accepted'], state=settlement['state'],
        evidenceChecked=settlement['evidenceChecked'],
        windowChecked=settlement['windowChecked'], settlementReview=settlement)
    gate.render(result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline')
    parser.add_argument('proposed')
    parser.add_argument('--baseline-sha256', required=True)
    parser.add_argument('--proposed-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        for pin in (args.baseline_sha256, args.proposed_sha256):
            gate.window.b.k.pin(pin)
        # Reusing one path must not capture two potentially different versions.
        captured = {}
        for name in (args.baseline, args.proposed):
            if name not in captured:
                captured[name] = gate.window.b.k.load_bytes(name)
        result = review(captured[args.baseline], captured[args.proposed],
                        args.baseline_sha256, args.proposed_sha256)
        sys.stdout.write(gate.render(result))
        return 0 if result['accepted'] else 2 if result['state'] == 'input_error' else 1
    except ERRORS:
        print(json.dumps(dict(accepted=False, state='input_error', evidenceChecked=False,
            windowChecked=False, reason='Invalid bounded plans, pins, evidence or report')))
        return 2


if __name__ == '__main__':
    sys.exit(main())

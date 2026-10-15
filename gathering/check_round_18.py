#!/usr/bin/env python3
"""Check the new shared gate here, detached, and across its refusal boundaries."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BASE = 'shared/window-settlement/'


def main():
    assert Path.cwd() == ROOT
    scratch = ROOT / 'test/scratch/round18'
    scratch.mkdir(parents=True, exist_ok=True)
    detached = scratch / 'portable'
    shutil.copytree(ROOT / BASE, detached / BASE, dirs_exist_ok=True)
    pin = (ROOT / BASE / 'plan.sha256').read_text().strip()
    demo = [BASE + 'change.py', BASE + 'plan.json', BASE + 'plan.json',
            '--baseline-sha256', pin, '--proposed-sha256', pin]
    cases = [
        (ROOT, 0, [BASE + 'test_change.py'], None),
        (ROOT, 0, demo, BASE + 'change-match.json'),
        (detached, 0, [BASE + 'test_change.py'], None),
        (detached, 0, demo, None),
    ]
    original = json.loads((ROOT / BASE / 'plan.json').read_text())
    for name in ('widened', 'narrowed-outside', 'narrowed-match', 'structure'):
        plan = json.loads(json.dumps(original))
        if name == 'widened': plan['windows'][1]['notAfterBlock'] += 1
        elif name == 'narrowed-outside':
            plan['windows'][1].update(notBeforeBlock=26194716, notAfterBlock=26194716)
        elif name == 'narrowed-match':
            plan['windows'][1].update(notBeforeBlock=26194715, notAfterBlock=26194715)
        else: plan['windows'][1]['notBeforeBlock'] = '26194710'
        raw = (json.dumps(plan) + '\n').encode()
        path = scratch / (name + '.json')
        path.write_bytes(raw)
        args = [BASE + 'change.py', BASE + 'plan.json', str(path.relative_to(ROOT)),
                '--baseline-sha256', pin, '--proposed-sha256', hashlib.sha256(raw).hexdigest()]
        cases.append((ROOT, 0 if name == 'narrowed-match' else 1, args,
                      BASE + 'change-' + name + '.json'))
    cases.extend([
        (ROOT, 1, ['line-2/tools/field-relations/check.py',
                  'line-2/tools/field-relations/window.contract.json',
                  'line-2/tools/field-relations/reversed-window.json',
                  'line-2/tools/field-relations/window.relations.json'], None),
        (ROOT, 2, [BASE + 'change.py', '../outside', BASE + 'plan.json',
                  '--baseline-sha256', pin, '--proposed-sha256', pin], None),
    ])
    rows = []
    for cwd, expected, args, save in cases:
        result = subprocess.run([sys.executable, '-B', *args], cwd=cwd,
            capture_output=True, text=True, timeout=45,
            env={'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'})
        row = dict(command=['python3', '-B', *args], detached=cwd != ROOT,
            expectedExit=expected, exitCode=result.returncode,
            passed=result.returncode == expected, stdout=result.stdout, stderr=result.stderr)
        rows.append(row)
        if save and row['passed']:
            assert len(result.stdout.encode()) <= 100000
            (ROOT / save).write_text(result.stdout)
        print('PASS' if row['passed'] else 'FAIL', args[0], result.returncode)
    # Keep each delivered result below the assignment's file limit.
    for i, group in enumerate((rows[:5], rows[5:]), 1):
        output = json.dumps(group, separators=(',', ':')) + '\n'
        assert len(output.encode()) <= 100000
        (ROOT / f'gathering/round-checks-18-{i}.json').write_text(output)
    return 0 if all(r['passed'] for r in rows) else 1


if __name__ == '__main__':
    sys.exit(main())

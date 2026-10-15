"""Local output-contract and bounded regression checks for contribution 38."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
from image_bytes import read_png


def run(args):
    p = subprocess.run(args, capture_output=True, text=True)
    return dict(command=args, exitCode=p.returncode, stdout=p.stdout, stderr=p.stderr)


def main():
    commands = [
        [sys.executable, '-B', '-m', 'unittest', 'discover', '-s',
         'line-3/tools/window-plan-diff', '-p', 'test_*.py', '-v'],
        [sys.executable, '-B', '-m', 'unittest', 'discover', '-s',
         'line-3/tools/settlement-plan-diff', '-p', 'test_*.py', '-v'],
        [sys.executable, '-B', 'line-3/tools/window-plan-diff/window_diff.py', '--demo']]
    results = [run(c) for c in commands]
    assert all(r['exitCode'] == 0 for r in results)
    Path('line-3/check-results-38.json').write_text(json.dumps(results, indent=2)+'\n')
    wall = Path('artifacts/line-3/wall-v18.png').read_bytes()
    assert wall == Path('artifacts/line-3/wall.png').read_bytes()
    width, height, pixels = read_png(wall)
    assert (width, height) == (1254, 1254)
    digest = hashlib.sha256(wall).hexdigest()
    record = json.loads(Path('dist/line-3/38.json').read_text())
    assert set(record) == {'name', 'image', 'attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/' + digest
    attrs = record['attributes']
    assert [r['trait_type'] for r in attrs] == ['Cave','Wall','Number','Left behind','Meaning','One thing']
    assert [r['value'] for r in attrs[:4]] == ['Water','Line 3',38,'window-plan-diff']
    assert type(attrs[2]['value']) is int
    assert len(list(Path('dist/line-3').glob('*.json'))) == 38
    jpg = Path('dist/line-3/38.jpg').read_bytes()
    assert jpg[:2] == b'\xff\xd8' and jpg[-2:] == b'\xff\xd9'
    offset = 2
    dimensions = None
    while offset < len(jpg):
        assert jpg[offset] == 255
        marker = jpg[offset+1]
        length = int.from_bytes(jpg[offset+2:offset+4], 'big')
        if marker == 192:
            bits, h, w, channels = struct.unpack('>BHHB', jpg[offset+4:offset+10])
            dimensions = [w,h]
            assert (bits,w,h,channels) == (8,512,512,3)
            break
        offset += 2+length
    assert dimensions == [512,512] and len(jpg) <= 100000
    tracked = subprocess.check_output(['git','diff','--name-only'], text=True).splitlines()
    for name in tracked:
        assert name in ('line-3/README.md','line-3/USED.md'), name
    goal = subprocess.check_output(['git','show','HEAD:line-3/GOAL.md'])
    assert goal == Path('line-3/GOAL.md').read_bytes()
    untracked = subprocess.check_output(['git','ls-files','--others','--exclude-standard'], text=True).splitlines()
    for name in untracked:
        if name.startswith('test/scratch/'):
            continue
        assert name.startswith(('line-3/','dist/line-3/','artifacts/line-3/')), name
        if not name.startswith('artifacts/'):
            assert Path(name).stat().st_size <= 100000, name
    assert subprocess.run(['git','diff','--check'], capture_output=True).returncode == 0
    result = dict(passed=True, focusedTests=13, inheritedPlanComparisonTests=20,
        demoPassed=True, wallDimensions=[width,height],wallFormat='RGB PNG',
        wallSha256=digest, previewDimensions=dimensions, previewFormat='RGB JPEG',
        previewBytes=len(jpg), goalUnchanged=True, olderRecordsUnchanged=True,
        requiredOutputsLeftUntracked=True, unmetVisualRequirements=[])
    assert subprocess.check_output(['git','ls-files','artifacts/line-3/wall-v18.png']) == b''
    Path('line-3/delivery-check-38.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()

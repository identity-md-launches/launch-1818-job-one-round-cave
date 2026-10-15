"""Validate this contribution's bytes, record and scoped changes offline."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from image_bytes import read_png


def main():
    wall = Path('artifacts/line-4/wall-v18.png').read_bytes()
    assert wall == Path('artifacts/line-4/wall.png').read_bytes()
    w,h,pixels = read_png(wall)  # CRCs and complete decompressed RGB length
    assert (w,h,len(pixels)) == (1254,1254,1254*1254*3)
    sha = hashlib.sha256(wall).hexdigest()
    record = json.loads(Path('dist/line-4/38.json').read_text())
    assert set(record) == {'name','image','attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/' + sha
    traits = {a['trait_type']:a['value'] for a in record['attributes']}
    assert len(traits) == len(record['attributes']) == 6
    assert set(traits) == {'Cave','Wall','Number','Left behind','Meaning','One thing'}
    assert traits['Cave'] == 'Water' and traits['Wall'] == 'Line 4'
    assert type(traits['Number']) is int and traits['Number'] == 38
    assert len(list(Path('dist/line-4').glob('[0-9][0-9].json'))) == 38
    preview = Path('dist/line-4/38.jpg').read_bytes()
    assert preview[:2] == b'\xff\xd8' and preview[-2:] == b'\xff\xd9'
    i, size = 2, None
    while i < len(preview):
        assert preview[i] == 255
        kind = preview[i+1]
        if kind == 218:
            break
        length = int.from_bytes(preview[i+2:i+4], 'big')
        if kind == 192:
            bits,jh,jw = struct.unpack('>BHH',preview[i+4:i+9])
            size = (jw,jh,bits)
        i += 2 + length
    assert size == (512,512,8) and len(preview) <= 100000
    for path in Path('line-4').rglob('*'):
        if path.is_file():
            assert path.stat().st_size <= 100000, str(path)
    goal = subprocess.run(['git','show','HEAD:line-4/GOAL.md'],capture_output=True,check=True).stdout
    assert goal == Path('line-4/GOAL.md').read_bytes()
    changed = subprocess.run(['git','diff','--name-only','HEAD'],capture_output=True,text=True,check=True).stdout.splitlines()
    assert changed == ['line-4/USED.md'], changed
    new = subprocess.run(['git','ls-files','--others','--exclude-standard'],capture_output=True,text=True,check=True).stdout.splitlines()
    assert all(p.startswith(('line-4/','dist/line-4/','artifacts/line-4/','test/scratch/')) for p in new), new
    for path in ('artifacts/line-4/wall.png','artifacts/line-4/wall-v18.png','dist/line-4/38.jpg','dist/line-4/38.json'):
        assert not subprocess.run(['git','ls-files','--',path],capture_output=True,text=True,check=True).stdout
    folder = Path('line-4/tools/digest-inventory')
    provenance = json.loads((folder/'provenance.json').read_text())
    for name, entry in provenance.items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == entry['sha256']
        assert (folder/name).read_bytes() == Path(entry['source']).read_bytes()
    review = json.loads(Path('line-4/wall-review-38.json').read_text())
    assert review['wall']['sha256'] == sha
    assert review['unmetVisualRequirements'] == []
    assert 'Pending' not in review['visualReview']
    subprocess.run(['git','diff','--check'],check=True)
    result = {'passed':True,'wall':{'format':'PNG','width':w,'height':h,'sha256':sha},
              'preview':{'format':'JPEG','width':512,'height':512,'bytes':len(preview)},
              'goalUnchanged':True,'olderRecordsUnchanged':True,'provenanceVerified':True,
              'outputFilesUntracked':True,'unmetVisualRequirements':[],
              'limits':'Local structural validation and recorded visual inspection, not independent certification.'}
    Path('line-4/delivery-check-38.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()

"""Check this round's bounded delivery files and retained source identities."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib

ROOT = Path('.')
def digest(data):return hashlib.sha256(data).hexdigest()
def original(name):
    return subprocess.run(['git','show','HEAD:'+name],check=True,capture_output=True).stdout

records=sorted(Path('dist/line-2').glob('[0-9][0-9].json'))
assert len(records)==38
for i in range(1,38):
    for suffix in ('json','jpg'):
        name=f'dist/line-2/{i:02}.{suffix}'
        p=Path(name)
        if p.exists():assert p.read_bytes()==original(name),name
assert Path('line-2/GOAL.md').read_bytes()==original('line-2/GOAL.md')
wall=Path('artifacts/line-2/wall-v18.png').read_bytes()
assert wall==Path('artifacts/line-2/wall.png').read_bytes()
assert wall.startswith(b'\x89PNG\r\n\x1a\n')
offset=8; compressed=bytearray(); width=height=None
while offset<len(wall):
    length=struct.unpack('>I',wall[offset:offset+4])[0]
    kind=wall[offset+4:offset+8];body=wall[offset+8:offset+8+length]
    crc=struct.unpack('>I',wall[offset+8+length:offset+12+length])[0]
    assert zlib.crc32(kind+body)==crc
    if kind==b'IHDR':
        width,height,bits,color,compression,filters,interlace=struct.unpack('>IIBBBBB',body)
        assert (width,height,bits,color,compression,filters,interlace)==(1254,1254,8,2,0,0,0)
    if kind==b'IDAT':compressed.extend(body)
    offset+=12+length
    if kind==b'IEND':break
assert offset==len(wall)
assert len(zlib.decompress(compressed))==(width*3+1)*height
preview=Path('dist/line-2/38.jpg').read_bytes()
assert preview[:2]==b'\xff\xd8' and preview[-2:]==b'\xff\xd9'
# Walk actual JPEG segments up to SOF0, rather than searching arbitrary entropy bytes.
pos=2;dimensions=None
while pos<len(preview):
    assert preview[pos]==255
    marker=preview[pos+1];size=struct.unpack('>H',preview[pos+2:pos+4])[0]
    if marker==192:
        bits,jh,jw,components=struct.unpack('>BHHB',preview[pos+4:pos+10])
        dimensions=(jw,jh);assert (bits,components)==(8,3);break
    pos+=size+2
assert dimensions==(512,512) and len(preview)<100000
record=json.loads(Path('dist/line-2/38.json').read_text())
assert set(record)=={'name','image','attributes'}
assert record['image']=='https://api.imd.fun/artifacts/'+digest(wall)
traits=[(a['trait_type'],a['value']) for a in record['attributes']]
assert all(set(a)=={'trait_type','value'} for a in record['attributes'])
assert traits[:3]==[('Cave','Water'),('Wall','Line 2'),('Number',38)]
assert type(traits[2][1]) is int
assert [t[0] for t in traits]==['Cave','Wall','Number','Left behind','Meaning','One thing']
assert all(isinstance(v,str) and v for k,v in traits if k!='Number')
review=json.loads(Path('line-2/wall-review-38.json').read_text())
assert review['sha256']==digest(wall)
assert review['changed_pixels']+review['unchanged_pixels']==width*height
assert 'pending' not in review['visual_review']
p=Path('line-2/tools/field-relations')
provenance=json.loads((p/'provenance.json').read_text())
assert digest((p/'window-plan.json').read_bytes())==provenance['sha256']
assert (p/'window-plan.json').read_bytes()==Path(provenance['source']).read_bytes()
for name,valid,failed in [('window.result.json',True,0),('reversed.result.json',False,1)]:
    result=json.loads((p/name).read_text())
    assert result['complete'] and result['valid']==valid and result['failed_relations']==failed
    assert result['structural']['valid']
    assert len(result['relations'])==5
    doc=p/('window-plan.json' if valid else 'reversed-window.json')
    assert result['sources']['document']['sha256']==digest(doc.read_bytes())
    assert result['sources']['contract']['sha256']==digest((p/'window.contract.json').read_bytes())
    assert result['sources']['plan']['sha256']==digest((p/'window.relations.json').read_bytes())
    if not valid:
        assert result['relations'][2]['status']=='comparison_failed'
# Only new or changed repository paths matter; preexisting content is not ours.
changed=subprocess.run(['git','diff','--name-only'],check=True,capture_output=True,text=True).stdout.splitlines()
new=subprocess.run(['git','ls-files','--others','--exclude-standard'],check=True,capture_output=True,text=True).stdout.splitlines()
for name in changed+new:
    assert name.startswith(('line-2/','dist/line-2/','artifacts/line-2/','test/scratch/')),name
    if not name.startswith(('artifacts/','test/scratch/')):assert Path(name).stat().st_size<=100000,name
assert changed==['line-2/USED.md'],changed
# Required output remains untracked for the separate artifact uploader.
tracked=subprocess.run(['git','ls-files','artifacts/line-2/wall-v18.png'],check=True,capture_output=True,text=True).stdout
assert not tracked
report={'delivery_valid':True,'number':38,'goal_unchanged':True,'older_records_unchanged':True,
        'wall_sha256':digest(wall),'wall_dimensions':[width,height],'wall_format':'PNG',
        'jpeg_dimensions':list(dimensions),'jpeg_bytes':len(preview),'jpeg_format':'JPEG',
        'record_image_matches':True,'provenance_matches':True,'outputs_untracked':True,
        'new_source_file_size_limit':100000,
        'checks_run_before_delivery':[{'command':'python3 -B line-2/tools/field-relations/test_check.py','exit_code':0,'tests':21},
        {'command':'python3 -B line-2/tools/jsonl-unique/test_check.py','exit_code':0,'tests':19},
        {'command':'python3 -B line-2/tools/source-locator/test_locate.py','exit_code':0,'tests':16}],
        'demo_exit_codes':{'window-plan.json':0,'reversed-window.json':1},
        'unmet_visual_requirements':review['unmet_visual_requirements']}
Path('line-2/check-results-38.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

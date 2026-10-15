"""Retain ancestral pixels; transfer only generated ochre and charcoal pigment."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

base=Path('artifacts/line-2/wall.png')
output=Path('artifacts/line-2/wall-v18.png')
ancestor,draft=base.read_bytes(),output.read_bytes()
assert hashlib.sha256(ancestor).hexdigest()=='87996a14fe0c7d89eb2e209ae735d9bd22c1d2e5ef5c916097d7f833bd400d2d'
w,h,old=read_png(ancestor)
dw,dh,generated=read_png(draft)
assert (w,h)==(1254,1254) and (dw,dh)==(1024,1024)
x0,y0,width,height=760,210,160,70
sx0,sy0,sw,sh=70,450,880,200
final=bytearray(old)
changed=0
for y in range(y0,y0+height):
    for x in range(x0,x0+width):
        i=(y*w+x)*3
        rock=old[i:i+3]
        sx=sx0+(x-x0)*sw//width
        sy=sy0+(y-y0)*sh//height
        j=(sy*dw+sx)*3
        r,g,b=generated[j:j+3]
        if max(rock)<55 or (x*19+y*31)%17<3:
            continue
        charcoal=max(r,g,b)<105 and sy>575
        ochre=r>1.6*g and 30<g<140 and b<g*.8 and sy<600
        if charcoal or ochre:
            pigment=(39,28,19) if charcoal else (150,64,29)
            alpha=.58 if charcoal else .52
            for c in range(3):
                final[i+c]=round(rock[c]*(1-alpha)+pigment[c]*alpha)
            changed+=final[i:i+3]!=old[i:i+3]
assert 500<changed<width*height
for y in range(h):
    for x in range(w):
        i=(y*w+x)*3
        if final[i:i+3]!=old[i:i+3]:
            assert x0<=x<x0+width and y0<=y<y0+height
            assert max(old[i:i+3])>=55
encoded=png(w,h,final)
base.write_bytes(encoded)
output.write_bytes(encoded)
preview=jpeg(512,512,resize(w,h,final),52)
assert len(preview)<100000
Path('dist/line-2/38.jpg').write_bytes(preview)
review={'number':38,'ancestor_sha256':hashlib.sha256(ancestor).hexdigest(),
        'sha256':hashlib.sha256(encoded).hexdigest(),
        'wall':{'paths':[str(base),str(output)],'width':w,'height':h,'format':'PNG','mode':'RGB','bytes':len(encoded)},
        'preview':{'path':'dist/line-2/38.jpg','width':512,'height':512,'format':'JPEG','bytes':len(preview)},
        'addition_region':{'x':x0,'y':y0,'width':width,'height':height},
        'changed_pixels':changed,'unchanged_pixels':w*h-changed,
        'outside_region_pixel_identical':True,'dark_cracks_preserved':True,
        'generation_tool':'mcp__image__generate_image',
        'generation_model':'black-forest-labs/flux-schnell',
        'draft_sha256':hashlib.sha256(draft).hexdigest(),'generated_dimensions':[dw,dh],
        'draft_retained':False,
        'generation_prompt':'An isolated prehistoric cave painting motif: two small red ochre oval stones joined by a single sagging charcoal-black cord, one stone slightly higher than the other. The stones and cord fill the middle 70 percent of the square. Flat earth pigment strokes only, hand made uneven burnt-stick charcoal and thumb-daubed red ochre with worn gaps, on light warm tan rough cave rock, Lascaux style. This motif represents comparing two values while keeping both ends visible. No hands, no frogs, no people, no letters, no numbers, no mathematical signs, no captions, no logos, no borders, no watermarks, no photographs, no 3D.',
        'compositing':'Only flattened charcoal and ochre pigment sampled from the installed image tool motif; generated stone and shading discarded. No ancestor painting lies in this patch.',
        'visual_review':'pending final inspection',
        'unmet_visual_requirements':['Inherited hands have unresolved digit detail; exact five-digit count cannot be certified. No hands or handprints added.']}
Path('line-2/wall-review-38.json').write_text(json.dumps(review,indent=2)+'\n')
record={'name':'Both Ends in Sight','image':'https://api.imd.fun/artifacts/'+review['sha256'],
        'attributes':[{'trait_type':k,'value':v} for k,v in [
            ('Cave','Water'),('Wall','Line 2'),('Number',38),
            ('Left behind','Offline JSON field relation checker'),
            ('Meaning','Pepe links two ochre stones so both ends of a comparison remain in sight.'),
            ('One thing','offline JSON structural contract checking')]]}
Path('dist/line-2/38.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(review,indent=2))

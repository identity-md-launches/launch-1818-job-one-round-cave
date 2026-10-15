"""Keep only new image-editor pigment; retain ancestral pixels everywhere else."""
import hashlib
import json
from pathlib import Path

from image_bytes import read_png, png, jpeg, resize


def main():
    folder = Path('artifacts/line-4')
    ancestor = (folder / 'wall.png').read_bytes()
    draft = (folder / 'wall-v18.png').read_bytes()
    old_sha = '6199e3620b645212b17dbb911bf17b902519bdeaa5c4640440fa27cc1d9d4cca'
    assert hashlib.sha256(ancestor).hexdigest() == old_sha
    w, h, old = read_png(ancestor)
    dw, dh, generated = read_png(draft)
    assert (w, h, dw, dh) == (1254, 1254, 1254, 1254)
    final = bytearray(old)
    changes = []
    for y in range(963, 1020):
        for x in range(990, 1078):
            i = (y*w+x)*3
            r, g, b = generated[i:i+3]
            seed = any(((x-cx)/16)**2 + ((y-cy)/13)**2 < 1
                       for cx, cy in ((1012, 980), (1049, 982)))
            red = seed and 45 < r < 190 and r-g > 20 and r > 1.45*g
            # Restrict charcoal selection to the shallow cradle's actual band.
            curve_y = 1014 - .009*(x-1031)**2
            charcoal = 998 < x < 1070 and abs(y-curve_y) < 5 and max(r,g,b) < 76
            if not (red or charcoal) or sum(old[i:i+3]) < 75:
                continue
            original = old[i:i+3]
            pigment = bytes(round(a*.25 + p*.75) for a, p in zip(original, (r,g,b)))
            final[i:i+3] = pigment
            if pigment != original:
                changes.append((x,y))
    assert 400 < len(changes) < 2600
    wall = png(w,h,final)
    preview = jpeg(512,512,resize(w,h,final),52)
    assert len(preview) < 100000
    sha = hashlib.sha256(wall).hexdigest()
    for name in ('wall.png', 'wall-v18.png'):
        (folder/name).write_bytes(wall)
    Path('dist/line-4/38.jpg').write_bytes(preview)
    record = {
        'name': 'The Paired Seeds',
        'image': 'https://api.imd.fun/artifacts/' + sha,
        'attributes': [
            {'trait_type':'Cave','value':'Water'},
            {'trait_type':'Wall','value':'Line 4'},
            {'trait_type':'Number','value':38},
            {'trait_type':'Left behind','value':'offline EIP-712 digest inventory'},
            {'trait_type':'Meaning','value':'Two ochre seeds in one cradle mark requests that encode the same digest.'},
            {'trait_type':'One thing','value':'offline EIP-712 typed-data digest checking'},
        ],
    }
    Path('dist/line-4/38.json').write_text(json.dumps(record,indent=2)+'\n')
    review = {
        'wall': {'paths':['artifacts/line-4/wall.png','artifacts/line-4/wall-v18.png'],
                 'width':w,'height':h,'format':'PNG','mode':'RGB','bytes':len(wall),'sha256':sha},
        'preview': {'path':'dist/line-4/38.jpg','width':512,'height':512,'format':'JPEG','bytes':len(preview)},
        'ancestorSha256': old_sha,
        'generatedDraftSha256':hashlib.sha256(draft).hexdigest(),
        'imageTool':'installed image edit_image; explicit workspace output',
        'promptSummary':'Preserve entire ancestral cave and Pepe; add only two matching red ochre seeds in a shallow charcoal cradle on vacant lower-right stone, no writing or new hands.',
        'changedPixels':len(changes),'unchangedPixels':w*h-len(changes),
        'additionBoundsExclusive':[min(x for x,y in changes),min(y for x,y in changes),max(x for x,y in changes)+1,max(y for x,y in changes)+1],
        'preservation':'Only editor-generated seed and cradle pigment retained. Every pixel outside selected pigment and deep original cracks is exactly ancestral.',
        'visualReview':'Pending final wall and preview inspection.',
        'unmetVisualRequirements':[],
        'limitations':['Local review is not independent visual certification.',
                       'Small mark is subtle at thumbnail size.',
                       'Generated draft changed surrounding stone, so only selected new pigment was retained.'],
    }
    Path('line-4/wall-review-38.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()

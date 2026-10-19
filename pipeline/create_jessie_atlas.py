"""Pack original Jessie diffuse + a documented temporary eye texture into one sheet."""
import json,sys
from pathlib import Path
from PIL import Image
import numpy as np
src,out=map(Path,sys.argv[1:]);out.mkdir(exist_ok=False)
source=Image.open(src).convert('RGBA');assert source.size==(2048,2048)
y,x=np.mgrid[0:1024,0:1024];x=(x-511.5)/512;y=(511.5-y)/512;r=np.hypot(x,y);angle=np.arctan2(y,x)
eye=np.full((1024,1024,4),255,dtype='u1');eye[:,:,:3]=[245,245,238]
mask=r<.36;variation=(10*np.sin(angle*43)+7*np.sin(angle*67+r*70)).astype(int)
for k,base in enumerate([72,116,68]):eye[:,:,k][mask]=np.clip(base+variation[mask],0,255)
eye[:,:,:3][r<.15]=[12,18,12];eye[:,:,:3][(r>.335)&(r<.36)]=[30,55,32]
eye[:,:,:3][((x+.12)**2+(y-.13)**2)<.045**2]=255
im=Image.fromarray(eye);im.save(out/'Jessie-temporary-eyes.png')
atlas=Image.new('RGBA',(4096,4096),(245,245,238,255));atlas.paste(source.resize((3040,3040),Image.Resampling.LANCZOS),(16,16));atlas.paste(im.resize((992,992),Image.Resampling.LANCZOS),(3088,16));atlas.save(out/'Jessie-basecolor-atlas.png')
(out/'atlas-layout.json').write_text(json.dumps({'size':4096,'body':[16,16,3040,3040],'eyes':[3088,16,992,992],'eye_method':'Temporary procedural green irises/white sclera; original eye texture not supplied','original_diffuse_preserved':str(src)},indent=2)+'\n')

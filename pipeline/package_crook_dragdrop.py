"""File-only crook test ZIP: no installers, README, mods.txt or working skin packages."""
from pathlib import Path
import argparse,hashlib,json,zipfile
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--output',type=Path,default=root/'BoPeep-Crook-Test-v0.1.3.zip');a=p.parse_args()
files={'BoPeepCrook/Scripts/main.lua':(root/'runtime/BoPeepCrook/Scripts/main.lua').read_bytes()}
for ext in ('pak','utoc','ucas'):
 name='zBoCrookAsset_P.'+ext;files['Paks/'+name]=(a.assets/name).read_bytes()
with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as z:
 for name,data in sorted(files.items()):
  i=zipfile.ZipInfo(name,date_time=(2026,10,19,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;z.writestr(i,data)
with zipfile.ZipFile(a.output) as z:
 assert z.testzip() is None;assert {n:z.read(n) for n in z.namelist()}==files
r={'file':a.output.name,'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'bytes':a.output.stat().st_size,'files':{n:hashlib.sha256(d).hexdigest() for n,d in files.items()},'status':'WINDOWS_PENDING','checks':'14 carry Lua mock regression groups pass; no registry-only LoadAsset call; package files unchanged from v0.1; ZIP byte-readback verified'}
(root/'docs/crook-carry-v0.1.3-download.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

"""Deterministic file-only combined test; no installers, README or mods.txt."""
import argparse,hashlib,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=root/'ToyStory-Buzz-BoPeep-Test-v0.3.zip');a=p.parse_args();assert not a.output.exists()
stage=Path('/workspace/mod-work/refinement-next');folders=[stage/'buzz-arms-v1/package/mod',Path('/workspace/mod-work/wings-stage/proven-package-v2/mod'),stage/'bopeep-cape-v4h/package/mod',stage/'crook-package-v3/package/mod'];files={}
for folder in folders:
 for ext in ['pak','utoc','ucas']:
  matches=list(folder.glob('*.'+ext));assert len(matches)==1;f=matches[0];name='Paks/'+f.name;assert name not in files;files[name]=f.read_bytes()
for mod in ['BuzzWings','BoPeepCrook']:
 files[mod+'/Scripts/main.lua']=(root/'runtime'/mod/'Scripts/main.lua').read_bytes();files[mod+'/enabled.txt']=b''
files['BuzzWings/Scripts/wing_config.lua']=(root/'runtime/BuzzWings/Scripts/wing_config.lua').read_bytes()
with zipfile.ZipFile(a.output,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,data in sorted(files.items()):
  info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data,compresslevel=6)
with zipfile.ZipFile(a.output) as z:
 assert z.testzip() is None;assert {n:z.read(n) for n in z.namelist()}==files
report={'file':a.output.name,'bytes':a.output.stat().st_size,'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'status':'OFFLINE_VALIDATED_WINDOWS_PENDING','file_only':True,'automatic_accessory_startup':True,'debug_keys':'F6/F9 suspend/resume; not required','manual_wing_key':'Unassigned; user-configurable in wing_config.lua','native_spear_animation_substituted':False,'forward_flight_pose_implemented':False,'cape_status':'Incremental upper repair; small collar artifact remains','current_runtime_accessories':'Local client only','files':{n:hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())}}
(root/'docs/playtest-v03-download.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['file','bytes','sha256','status']},indent=2))

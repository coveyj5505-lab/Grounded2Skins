"""Publish independent drag/drop tests only after the corrected assets pass readback."""
import json,hashlib,zipfile
from pathlib import Path
r=Path('/workspace/mod-work/anatomy-corrections');repo=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
frozen=json.loads((r/'frozen.json').read_text())
for name,h in frozen.items():assert sha((repo/name).read_bytes())==h,name
assert json.loads((r/'woody-validation-v1.json').read_text())['status']=='PASS_OFFLINE_ONLY'
assert json.loads((r/'cooked-source-material-validation.json').read_text())['status']=='PASS_OFFLINE'
assert json.loads((r/'woody-cooked-previews-v1/scope.json').read_text())['runtime']=='NOT TESTED'
assert json.loads((r/'buzz-flight-native-v1/validation.json').read_text())['status']=='PASS_OFFLINE_CANDIDATE_ONLY'
for kind in ['controller','adapter']:assert json.loads((repo/f'docs/buzz-flight-{kind}-regressions.json').read_text())['status']=='PASS_MOCKED_LUA_NOT_UNREAL'
packages=[]
for filename,folder,stem,flight in [('Woody-Pelvis-V3-Test.zip','woody-package-v1','zWoodyAnatomyV3_P',False),('Buzz-Flight-Pose-V1-Test.zip','buzz-flight-package-v1','zBuzzFlightTest_P',True)]:
 files={}
 for suffix in ['pak','utoc','ucas']:
  p=r/folder/'mod'/(stem+'.'+suffix);files['Paks/'+p.name]=p.read_bytes()
 if flight:
  for p in sorted((repo/'experiments/BuzzFlightVisual/Scripts').glob('*.lua')):
   b=p.read_bytes()
   if p.name=='flight_config.lua':b=b'-- Isolated Windows flight-pose test; remove this mod to return to v0.3.\nreturn {Enabled=true,DebugToggleKey=nil}\n'
   files['Mods/BuzzFlightVisual/Scripts/'+p.name]=b
 target=repo/filename;assert not target.exists()
 with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name,b in sorted(files.items()):
   info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b,compresslevel=6)
 with zipfile.ZipFile(target) as z:assert z.testzip() is None;assert {name:z.read(name) for name in z.namelist()}==files
 packages.append({'file':filename,'bytes':target.stat().st_size,'sha256':sha(target.read_bytes()),'files':{name:sha(b) for name,b in sorted(files.items())},'status':'OFFLINE_VALIDATED_WINDOWS_PENDING','requires_UE4SS':flight,'install':('Copy Paks files into Augusta/Content/Paks and Mods/BuzzFlightVisual into the UE4SS Mods folder; add BuzzFlightVisual : 1 to existing mods.txt. Keep v0.3 character and wing/crook files unchanged.' if flight else 'Close game, move active older Woody/Pete replacement trio outside Paks, copy these three Paks files into Augusta/Content/Paks. Other characters/accessories unchanged.'),'rollback':('Remove BuzzFlightVisual entry/folder and zBuzzFlightTest_P trio; v0.3 remains untouched.' if flight else 'Remove zWoodyAnatomyV3_P trio and restore previous Woody trio.'),'scope':('Automatic third-person flight visual only during confirmed IsGliding. First-person/landing restore native render presentation. Static limb pose, original tuft remains, local-client cosmetic only. New runtime paths need Windows validation.' if flight else 'Pelvis geometry/weights corrected; V2 boots/ring retained; native 188-bone skeleton, head/body sections, all textures/materials retained. Synthetic pose checks do not replace gameplay confirmation.')})
(repo/'docs/anatomy-update-downloads.json').write_text(json.dumps({'packages':packages,'frozen_inputs_sha256':frozen},indent=2)+'\n');print(json.dumps([{k:p[k] for k in ['file','bytes','sha256','status']} for p in packages],indent=2))

"""One drag/drop test bundle; never overwrite a released artifact."""
import hashlib,json,zipfile
from pathlib import Path
repo=Path(__file__).resolve().parents[1];r=Path('/tmp/toystory-feedback-v3');docs=repo/'docs/feedback-v3';target=repo/'ToyStory-All-Fixes-V3-UE57-Test.zip';assert not target.exists();sha=lambda b:hashlib.sha256(b).hexdigest()
for p,h in json.load(open('/workspace/mod-work/anatomy-corrections/frozen.json')).items():assert sha((repo/p).read_bytes())==h,p
for item in json.load(open(repo/'docs/skin-fixes-next/downloads.json'))['packages']:assert sha((repo/item['file']).read_bytes())==item['sha256'],item['file']
files={};stages={'Buzz':r/'Buzz-final','Woody':r/'Woody-final','BoPeep':r/'BoPeep-complete','Jessie':r/'Jessie-build','Crook':r/'CrookAll-final'}
for name,stage in stages.items():
 report=json.load(open(stage/'validation.json'));assert report['status'] in ['PASS_OFFLINE_WINDOWS_PENDING','PASS_ALL_THREE_VIEWS_OFFLINE_WINDOWS_PENDING']
 for f in (stage/'package/mod').iterdir():files['Paks/'+f.name]=f.read_bytes()
 files['Validation/'+name+'.json']=(stage/'validation.json').read_bytes()
# The already-working forward visual's asset is reused byte-for-byte.
for f in Path('/workspace/mod-work/ue57-migration/flight-package-v1/mod').iterdir():files['Paks/'+f.name]=f.read_bytes()
for folder in ['BoPeepCrook','BuzzFlightVisual']:
 for f in (repo/'runtime-feedback-v3'/folder/'Scripts').glob('*.lua'):
  b=f.read_bytes()
  if folder=='BuzzFlightVisual' and f.name=='flight_config.lua':b=b'-- Combined V3 Windows feature test; stable wing control is unchanged.\nreturn {Enabled=true,DebugToggleKey=nil}\n'
  files['Mods/'+folder+'/Scripts/'+f.name]=b
for f in (docs/'previews').iterdir():
 if f.suffix.lower() in ['.png','.jpg']:files['Previews/'+f.name]=f.read_bytes()
files['Validation/local-regressions.json']=(r/'regressions.json').read_bytes()
files['MOVE-OLD-TRIOS-OUTSIDE-PAKS.txt']=b'''Close the game completely. Move all active older Buzz/BoPeep/Woody/Jessie skin trios OUTSIDE Paks, plus old zBoCrookUE57_P or zBoCrookHandV2UE57_P trios. A trio is .pak/.utoc/.ucas with the same stem. Keep those backups.
Copy all18 files from this Paks folder into Augusta/Content/Paks. The four new skins and crook use z*V3UE57_99_P names. zBuzzFlightUE57_P is the same forward-flight asset as before.
Replace/merge ONLY the two included Mods folders' Scripts files, including build_receipt.lua. Keep the working BuzzWings folder/config/F1 binding and zBuzzWingsUE57_P trio unchanged.
Keep existing mods.txt entries BoPeepCrook : 1, BuzzWings : 1, BuzzFlightVisual : 1. Do not replace the whole mods.txt.
TEST: Jessie first (does Hoops appear as Jessie?), then all skins in both views. BoPeep: auto empty-hand crook, thicker shaft, right-edge flat hand, camera switches, occupied main/off hand hiding. Woody: badge and shorter holster. Buzz: F1 standing, actual Shift-opened tuft glide in TP, landing, manual wings preference restoration, FP/TP during glide if safe. Check duplicate body/wings/gripping hands/tuft.
Send UE4SS.log and screenshots. BUILD RECEIPT lines report installed header/sizes and known old trios; presence alone does not prove mounting.
ROLLBACK: remove the four new V3 skin trios and new V3 crook trio, restore your previous trios and previous BoPeepCrook/BuzzFlightVisual Scripts from their frozen ZIPs. F1 wings are unchanged.
Offline readback/render/Lua checks passed. Windows appearance/functionality is pending. Minor collar/vest seams remain. Native spear montage substitution is not included; unarmed gameplay remains untouched. No install/update executables are included.
'''
assert len([n for n in files if n.startswith('Paks/')])==18
main=files['Mods/BoPeepCrook/Scripts/main.lua'].decode();toc=files['Paks/zBoCrookHandV3UE57_99_P.utoc'];assert toc[:64].hex() in main
receipt=files['Mods/BuzzFlightVisual/Scripts/build_receipt.lua'].decode()
for name,stage in stages.items():
 toc=next((stage/'package/mod').glob('*.utoc'));assert toc.stem in receipt and toc.read_bytes()[:64].hex() in receipt
assert not any('/BuzzWings/' in n for n in files)
with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,b in sorted(files.items()):
  info=zipfile.ZipInfo(n,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b,compresslevel=6)
with zipfile.ZipFile(target) as z:assert z.testzip() is None;assert {n:z.read(n) for n in z.namelist()}==files
record={'file':target.name,'bytes':target.stat().st_size,'sha256':sha(target.read_bytes()),'status':'OFFLINE_VALIDATED_WINDOWS_PENDING','paks_trios':6,'wing_runtime_and_assets':'Existing F1 implementation preserved; not replaced','all_previous_releases_unchanged':True,'members':{n:{'bytes':len(b),'sha256':sha(b)} for n,b in sorted(files.items())}}
(docs/'download.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k] for k in ['file','bytes','sha256','status']},indent=2))

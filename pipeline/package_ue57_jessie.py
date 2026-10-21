"""Package only the current-build Jessie candidate after independent checks."""
from pathlib import Path
import json,hashlib,zipfile,shutil
repo=Path(__file__).resolve().parents[1];stage=Path('/workspace/mod-work/ue57-migration');validation=json.loads((stage/'jessie-final-validation-v1.json').read_text());assert validation['status']=='PASS_OFFLINE_WINDOWS_PENDING';container=json.loads((stage/'jessie-package-v1/repackage-validation.json').read_text());assert container['packages_recognized']==11 and container['chunks_verified']==16
# Revalidate received originals; building the mod may not change any input chunk.
for name,item in json.loads((stage/'extraction-report.json').read_text())['characters'].items():
 for e in item['chunks']:assert hashlib.sha256((stage/name/'chunks'/e['id']).read_bytes()).hexdigest()==e['sha256']
for e in json.loads((stage/'textures/texture-report.json').read_text())['chunks']:assert hashlib.sha256((stage/'textures/chunks'/e['id']).read_bytes()).hexdigest()==e['sha256']
frozen=json.loads(Path('/workspace/mod-work/anatomy-corrections/frozen.json').read_text())
for name,h in frozen.items():assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==h,name
files={}
for suffix in ['pak','utoc','ucas']:
 p=stage/'jessie-package-v1/mod'/('zJessieUE57_P.'+suffix);files['Paks/'+p.name]=p.read_bytes()
p=repo/'Jessie-UE57-Compatibility-Test.zip';assert not p.exists()
with zipfile.ZipFile(p,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,b in sorted(files.items()):
  i=zipfile.ZipInfo(name,(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;z.writestr(i,b,compresslevel=6)
with zipfile.ZipFile(p) as z:assert z.testzip() is None;assert {name:z.read(name) for name in z.namelist()}==files
out=repo/'docs/ue57-migration'
for src,dest in [('jessie-final-validation-v1.json','jessie-final-validation.json'),('jessie-package-v1/repackage-validation.json','jessie-container-validation.json'),('jessie-check-v1/previews/Jessie-UE57-cooked.png','Jessie-UE57-cooked.png'),('jessie-check-v1/previews/Jessie-UE57-front.png','Jessie-UE57-front.png')]:shutil.copyfile(stage/src,out/dest)
r={'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'OFFLINE_VALIDATED_WINDOWS_PENDING','files':{name:hashlib.sha256(b).hexdigest() for name,b in files.items()},'game_build':'UE5.7.4 Augusta-CL-3207493','scope':'Jessie/Hoops replacement only. No UE4SS script, accessory, other character or third-party-mod repair.','preserved':'Accepted geometry, weights, UVs and native FP head/body section split exact. Full head retained.','changed':'Current-build object templates, post-LOD tails, material and texture templates; private2048BC1 atlas resampled from preserved original4096RGBA image.','test':'Keep other mod Paks out and UE4SS disabled for this asset-only check. Copy three Paks files into Augusta/Content/Paks. Launch to menu, exit, relaunch. If both clean, play as Hoops and check first/third-person views and movement.','rollback':'Remove only zJessieUE57_P trio. Do not restore old incompatible character trios while testing this build.','frozen_previous_releases_and_runtime_verified_unchanged':True,'user_input_chunks_verified_unchanged':True,'limitations':'No full mapped UObject deserialization and no Windows engine load test yet. Container/native readback is offline evidence only.'};(out/'jessie-test-download.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['file','bytes','sha256','status']},indent=2))

"""Make an independent Woody-only, drag/drop test ZIP after read-back passes."""
import hashlib,json,zipfile,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];stage=Path('/workspace/mod-work/woody-polish-next');report=json.loads((stage/'validation-v2.json').read_text());assert report['status']=='PASS_OFFLINE_ONLY';assert json.loads((stage/'cooked-source-material-validation.json').read_text())['status']=='PASS_OFFLINE';assert json.loads((stage/'cooked-previews-v2/pose-validation.json').read_text())['status']=='PASS_OFFLINE'
frozen=json.loads((stage/'frozen-v03.json').read_text())
for name,digest in frozen.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
files={}
for suffix in ['pak','utoc','ucas']:
 p=stage/'package-v2/mod'/('zWoodyPolishV2_P.'+suffix);files['Paks/'+p.name]=p.read_bytes()
out=root/'Woody-Boots-Ring-V2-Test.zip';assert not out.exists()
with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,b in sorted(files.items()):
  info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b,compresslevel=6)
with zipfile.ZipFile(out) as z:assert z.testzip() is None;assert {n:z.read(n) for n in z.namelist()}==files
r={'file':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'status':'OFFLINE_VALIDATED_WINDOWS_PENDING','files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()},'changes':'Woody main/backpack boot-tabs and pull-string ring only','original_FP_head_body_sections_preserved':True,'other_characters_or_runtime_changes':False,'frozen_v03_verified':frozen,'install':'Game closed: move previous zWoodyFP_P trio outside Paks; copy new three files into Augusta/Content/Paks. Keep other characters and v0.3 accessories. Do not leave other Pete replacement trios enabled. Roll back by removing new trio and restoring old one.','limitations':['Windows validation pending','Character-select mesh retains previous geometry','Original animation, rigid hand policy, cloth and material limitations unchanged']};(root/'docs/woody-polish-v2-download.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['file','bytes','sha256','status']},indent=2))

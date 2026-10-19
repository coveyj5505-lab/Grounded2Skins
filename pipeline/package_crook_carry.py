"""Build the isolated Windows carry-test archive; doesn't alter installed skins."""
from pathlib import Path
import argparse,hashlib,json,zipfile
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--output',type=Path,default=root/'BoPeep-Crook-Carry-Test-v0.1.zip');a=p.parse_args()
files={}
for ext in ('pak','utoc','ucas'):
 path=a.assets/f'zBoCrookAsset_P.{ext}';files['Paks/'+path.name]=path.read_bytes()
for path in (root/'runtime/BoPeepCrook').rglob('*'):
 if path.is_file():files['UE4SS/Mods/BoPeepCrook/'+path.relative_to(root/'runtime/BoPeepCrook').as_posix()]=path.read_bytes()
for path in (root/'pipeline/windows/crook').iterdir():
 if path.is_file():files[path.name]=path.read_bytes()
with zipfile.ZipFile(a.output,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for name,data in sorted(files.items()):
  info=zipfile.ZipInfo(name,date_time=(2026,10,19,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
with zipfile.ZipFile(a.output) as z:
 assert z.testzip() is None
 assert {n:z.read(n) for n in z.namelist()}==files
manifest=root/'docs/crook-carry-download.json';m=json.loads(manifest.read_text());m.update(filename=a.output.name,bytes=a.output.stat().st_size,sha256=hashlib.sha256(a.output.read_bytes()).hexdigest())
manifest.write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(m,indent=2))

"""Read eight exact current-build baseline packages; never install/modify game files."""
import argparse,hashlib,json,subprocess,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'support'))
from extract_selected import listing,canonical,DATA_TYPES,DLL_HASH
from discover_pete import header
TARGETS=(
 '/Game/Blueprints/Player/BP_SurvivalPlayerController',
 '/Game/UI/Map/UI_Map',
 '/Game/_Dev/Art/Buildings/Proto/BP_Teleporter',
 '/Game/Art/World/ZN10_Labs/Lab_Props/Teleporter/BP_Teleporter_Door',
 '/Game/UI/Map/UI_MapPanel',
 '/Game/Blueprints/Attacks/CreatureAttacks',
 '/Game/Blueprints/Attacks/ItemAttacks',
 '/Game/Art/Items/Weapons/Spear02/Spear02',
)
MAX_BYTES=64*1024*1024

def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def collect(retoc,source,out):
 retoc,source,out=(Path(x).resolve() for x in (retoc,source,out))
 if source.name.casefold()!='augusta-wingdk.utoc' or not source.is_file() or not source.with_suffix('.ucas').is_file():raise ValueError('Select original Augusta-WinGDK.utoc and matching UCAS')
 if out.exists() or out.is_relative_to(source.parent):raise ValueError('New output directory outside game Paks required')
 if subprocess.check_output([str(retoc),'--version'],text=True).strip()!='retoc_cli 0.1.5':raise ValueError('retoc 0.1.5 required')
 for name,expected in DLL_HASH.items():
  dll=retoc.with_name(name)
  if dll.exists() and digest(dll)!=expected:raise ValueError('Unexpected decoder checksum '+name)
 source_files=[source,source.with_suffix('.ucas')];before=[(p.stat().st_size,p.stat().st_mtime_ns) for p in source_files]
 out.mkdir(parents=True);(out/'chunks').mkdir()
 report=dict(status='INCOMPLETE',targets=list(TARGETS),selection='Eight exact known baseline packages only; no dependency traversal or textures',max_decoded_bytes=MAX_BYTES,decoded_bytes=0,packages=[],chunks=[],missing=[],errors=[],source_metadata_unchanged=False)
 try:
  rows=listing(retoc,source,out/'source-index.log');index={}
  for row in rows:
   if row['type']=='ExportBundleData':
    key=canonical(row['path'])
    if key in index:raise ValueError('Duplicate indexed package path '+key)
    index[key]=row
  for target in TARGETS:
   key=canonical(target);entry=index.get(key)
   if not entry:report['missing'].append(key);continue
   chunks=[r for r in rows if r['id'][:16]==entry['id'][:16] and r['type'] in DATA_TYPES]
   size=sum(r['size'] for r in chunks)
   if report['decoded_bytes']+size>MAX_BYTES:raise ValueError('64 MiB budget reached; retaining partial output')
   for chunk in chunks:
    path=out/'chunks'/chunk['id']
    with (out/'extract.log').open('a') as log:subprocess.run([str(retoc),'get',str(source),chunk['id'],str(path)],check=True,stdout=log,stderr=subprocess.STDOUT)
    if path.stat().st_size!=chunk['size']:raise ValueError('Decoded chunk size mismatch')
    report['chunks'].append(dict(chunk,sha256=digest(path)));report['decoded_bytes']+=chunk['size']
   info=header((out/'chunks'/entry['id']).read_bytes())
   report['packages'].append(dict(path=key,chunk=entry['id'],imported_packages=info['imported_packages'],name_map=info['name_map']))
  if not report['missing']:report['status']='EXTRACTED_READ_ONLY'
 except Exception as error:report['errors'].append(str(error))
 finally:
  after=[(p.stat().st_size,p.stat().st_mtime_ns) for p in source_files];report['source_metadata_unchanged']=before==after
  if before!=after:report['status']='INCOMPLETE';report['errors'].append('Source metadata changed during collection')
  (out/'native-baselines-report.json').write_text(json.dumps(report,indent=2)+'\n')
  with zipfile.ZipFile(out.with_suffix('.zip'),'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for f in sorted(out.rglob('*')):
    if f.is_file() and f.name!='source-index.log':z.write(f,f.relative_to(out))
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--retoc',required=True);p.add_argument('--utoc',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 r=collect(a.retoc,a.utoc,a.output);print('UPLOAD ONE ZIP: '+str(Path(a.output).with_suffix('.zip')));print(r['status'],len(r['packages']),'packages',r['decoded_bytes'],'bytes',r['missing'],r['errors']);raise SystemExit(0 if r['status']=='EXTRACTED_READ_ONLY' else 2)

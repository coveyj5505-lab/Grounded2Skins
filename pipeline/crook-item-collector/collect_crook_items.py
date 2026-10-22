"""Read current native item tables so the crook row can be cooked offline.
No UE4SS struct copying, gameplay actions or changes to source game files.
"""
import argparse, hashlib, json, struct, subprocess, sys, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'support'))
from extract_selected import listing,canonical,DLL_HASH
from discover_pete import header
ROOT='/Game/Blueprints/Items/Table_AllItems'
TABLE_CLASSES={0x4834f6301fd65d7d,0x71e24a29987bd1ed}
MAX_BYTES=64*1024*1024
MAX_PACKAGES=128
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def collect(retoc,source,out):
 retoc,source,out=(Path(p).resolve() for p in (retoc,source,out))
 if source.name.casefold()!='augusta-wingdk.utoc' or not source.is_file() or not source.with_suffix('.ucas').is_file():raise ValueError('Select original Augusta-WinGDK.utoc and matching UCAS')
 if out.exists() or out.is_relative_to(source.parent):raise ValueError('New output folder outside game Paks required')
 if subprocess.check_output([str(retoc),'--version'],text=True).strip()!='retoc_cli 0.1.5':raise ValueError('retoc 0.1.5 required')
 for name,expected in DLL_HASH.items():
  dll=retoc.with_name(name)
  if dll.exists() and digest(dll)!=expected:raise ValueError('Unexpected decoder checksum '+name)
 pair=[source,source.with_suffix('.ucas')];before=[(p.stat().st_size,p.stat().st_mtime_ns) for p in pair]
 out.mkdir(parents=True);(out/'chunks').mkdir()
 report=dict(status='INCOMPLETE',root=ROOT,selection='Table_AllItems and actual imported item-table dependencies only; table class checked against current global IDs',max_decoded_bytes=MAX_BYTES,max_packages=MAX_PACKAGES,decoded_bytes=0,packages=[],chunks=[],skipped=[],missing=[],errors=[],source_metadata_unchanged=False)
 try:
  rows=listing(retoc,source,out/'source-index.log');index={}
  for row in rows:
   if row['type']=='ExportBundleData':
    key=canonical(row['path'])
    if key in index:raise ValueError('Duplicate native package path '+key)
    index[key]=row
  queue=[canonical(ROOT)];seen=set()
  while queue:
   key=queue.pop(0)
   if key in seen:continue
   if len(seen)>=MAX_PACKAGES:raise ValueError('128-package inspection limit reached')
   seen.add(key);entry=index.get(key)
   if entry is None:report['missing'].append(key);continue
   if report['decoded_bytes']+entry['size']>MAX_BYTES:raise ValueError('64 MiB read budget reached; partial output retained')
   path=out/'chunks'/entry['id']
   with (out/'extract.log').open('a') as log:subprocess.run([str(retoc),'get',str(source),entry['id'],str(path)],check=True,stdout=log,stderr=subprocess.STDOUT)
   if path.stat().st_size!=entry['size']:raise ValueError('Chunk size mismatch')
   report['decoded_bytes']+=entry['size'];raw=path.read_bytes();s=struct.unpack_from('<15I',raw)
   if s[0]!=0 or not (s[8]<s[9]<=s[1]<=len(raw)) or (s[9]-s[8])%72:raise ValueError('Unexpected current native Zen export layout')
   classes=[struct.unpack_from('<Q',raw,p+32)[0] for p in range(s[8],s[9],72)]
   if not any(c in TABLE_CLASSES for c in classes):
    report['skipped'].append(dict(path=key,reason='Not a current native DataTable/CompositeDataTable'));path.unlink();continue
   info=header(raw)
   report['chunks'].append(dict(entry,sha256=digest(path)))
   report['packages'].append(dict(path=key,chunk=entry['id'],imported_packages=info['imported_packages'],name_map=info['name_map'],export_classes=[hex(c) for c in classes]))
   # Composite tables import their parent tables. Follow their actual imports
   # regardless of folder/name; stop at ordinary DataTables so references in
   # weapon rows never expand into attacks, effects, textures or other assets.
   if 0x4834f6301fd65d7d in classes:
    queue.extend(canonical(dep) for dep in info['imported_packages'])
  if report['packages'] and not report['missing']:report['status']='EXTRACTED_READ_ONLY'
 except Exception as err:report['errors'].append(str(err))
 finally:
  report['source_metadata_unchanged']=before==[(p.stat().st_size,p.stat().st_mtime_ns) for p in pair]
  if not report['source_metadata_unchanged']:report['status']='INCOMPLETE';report['errors'].append('Source metadata changed')
  (out/'crook-items-report.json').write_text(json.dumps(report,indent=2)+'\n')
  with zipfile.ZipFile(out.with_suffix('.zip'),'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in sorted(out.rglob('*')):
    if p.is_file() and p.name!='source-index.log':z.write(p,p.relative_to(out))
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--retoc',required=True);p.add_argument('--utoc',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 r=collect(a.retoc,a.utoc,a.output);print('UPLOAD ONE ZIP: '+str(Path(a.output).with_suffix('.zip')));print(r['status'],len(r['packages']),'tables',r['decoded_bytes'],'bytes',r['missing'],r['errors']);raise SystemExit(0 if r['status']=='EXTRACTED_READ_ONLY' else 2)

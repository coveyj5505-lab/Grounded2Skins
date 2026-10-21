"""Read only original container; collect all four characters without UE4SS/gameplay.
Raw extraction deliberately does not assume UE5.6 Zen or skeletal serialization.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
from extract_selected import listing,canonical,DATA_TYPES
CHARACTERS={'Max':'Player_Male01','Willow':'Player_Female01','Pete':'Player_Male02','Hoops':'Player_Female02'}
MAX_CHARACTER=192*1024*1024

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def metadata(p):
 s=p.stat();return {'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
def select(rows):
 groups={}
 for name,folder in CHARACTERS.items():
  prefix=canonical('/Game/_Augusta/Art/Characters/'+folder)+'/';all_assets=[e for e in rows if e['type']=='ExportBundleData' and canonical(e['path']).startswith(prefix)];chosen=[]
  for e in all_assets:
   leaf=canonical(e['path']).rsplit('/',1)[-1]
   # Includes body/backpack/hair meshes, skeletons and physics by actual index.
   if leaf.startswith(('sk_','phat_','pa_','mi_')) or 'physicsasset' in leaf or 'skeleton' in leaf:chosen.append(e)
  groups[name]={'folder':folder,'candidates':all_assets,'selected':chosen}
 # Physics packages imported from the older Art/ directory are also included.
 shared=[e for e in rows if e['type']=='ExportBundleData' and any(canonical(e['path']).startswith(canonical('/Game/Art/Characters/'+f)+'/') for f in CHARACTERS.values()) and any(t in canonical(e['path']).rsplit('/',1)[-1] for t in ['physics','skeleton'])]
 shared += [e for e in rows if e['type']=='ExportBundleData' and canonical(e['path'])==canonical('/Game/_Augusta/Art/Characters/Materials/MM_Character')]
 groups['Shared']={'folder':'Shared physics/material baseline','candidates':shared,'selected':shared};return groups

def write_report(out,report):
 (out/'extraction-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
def collect(retoc,source,out):
 retoc,source,out=map(lambda p:Path(p).resolve(),(retoc,source,out))
 if source.name.casefold()!='augusta-wingdk.utoc':raise ValueError('Select original Augusta-WinGDK.utoc, not a mod container')
 if out.exists():raise ValueError('Output already exists; nothing overwritten')
 if out.is_relative_to(source.parent):raise ValueError('Output must be outside the game Paks folder')
 if not source.with_suffix('.ucas').is_file():raise ValueError('Adjacent original Augusta-WinGDK.ucas is required')
 out.mkdir(parents=True);report={'status':'started','scope':'All four original installed characters; no running game, UE4SS, save or mod writes','source':str(source),'source_files':{},'characters':{},'errors':[],'source_metadata_unchanged':False,'archives':[]}
 sources=[source,source.with_suffix('.ucas')]
 for name in ['global.utoc','global.ucas']:
  q=source.with_name(name)
  if q.is_file():sources.append(q)
 before={str(p):metadata(p) for p in sources};report['source_files']=before
 env=dict(os.environ,RAYON_NUM_THREADS='2')
 try:
  version=subprocess.check_output([str(retoc),'--version'],text=True,env=env).strip();report['retoc_version']=version;report['retoc_exe_sha256']=digest(retoc)
  if version!='retoc_cli 0.1.5':raise ValueError('Use the previously tested retoc.exe0.1.5; current tool reports '+version)
  for name in ['oo2core_9_win64.dll','liboo2corelinux64.so.9']:
   q=retoc.with_name(name)
   if q.exists():report.setdefault('decoder_sha256',{})[name]=digest(q)
  with (out/'container-info.log').open('w',encoding='utf-8') as f:subprocess.run([str(retoc),'info',str(source)],stdout=f,stderr=subprocess.STDOUT,env=env,check=True)
  print('Reading original container index once...',flush=True);rows=listing(retoc,source,out/'source-index.log');groups=select(rows)
  (out/'selected-index.json').write_text(json.dumps(groups,indent=2)+'\n',encoding='utf-8')
  # Snapshot the original small global pair for version/script-object metadata.
  shared=out/'Shared';shared.mkdir();report['global_files']=[]
  for q in sources[2:]:
   if q.stat().st_size>64*1024*1024:report['errors'].append('Global file exceeds64MiB budget; retained path/metadata only: '+q.name);continue
   target=shared/q.name;shutil.copyfile(q,target);report['global_files'].append({'file':q.name,'sha256':digest(target),'bytes':target.stat().st_size})
  for name,group in groups.items():
   folder=out/name;folder.mkdir(exist_ok=True);chunks=folder/'chunks';chunks.mkdir();prefixes={e['id'][:16] for e in group['selected']};entries=[e for e in rows if e['type'] in DATA_TYPES and e['id'][:16] in prefixes];total=sum(e['size'] for e in entries);r={'character':name,'directory':group['folder'],'packages':group['selected'],'chunks':[],'decoded_bytes_planned':total,'errors':[],'status':'started'};report['characters'][name]=r;write_report(out,report)
   print(f'{name}: {len(group["selected"])} packages, {total/1024/1024:.1f} MiB selected.',flush=True)
   if total>MAX_CHARACTER:r['errors'].append('Selection exceeds192MiB safety budget; inspect selected-index.json');r['status']='partial';continue
   if not group['selected']:r['errors'].append('No matching original packages; directory may have changed');r['status']='partial';continue
   for i,e in enumerate(entries,1):
    dest=chunks/e['id']
    try:
     print(f'  {name} {i}/{len(entries)}: {Path(e["path"]).name}',flush=True)
     with (folder/'extract.log').open('a',encoding='utf-8') as log:subprocess.run([str(retoc),'get',str(source),e['id'],str(dest)],stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
     if dest.stat().st_size!=e['size']:raise ValueError('Chunk size differs from original index')
     r['chunks'].append(dict(e,sha256=digest(dest)))
    except Exception as ex:r['errors'].append(e['id']+': '+str(ex))
   r['status']='complete' if not r['errors'] else 'partial';(folder/'character-report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');write_report(out,report)
 except Exception as ex:report['errors'].append(str(ex));print('Collection issue: '+str(ex),flush=True)
 finally:
  report['source_metadata_unchanged']=before=={str(p):metadata(p) for p in sources};report['status']='complete' if not report['errors'] and report['characters'] and all(v['status']=='complete' for v in report['characters'].values()) and report['source_metadata_unchanged'] else 'partial-share-available-output';write_report(out,report)
  # Separate per-character archives; the metadata archive includes index/errors
  # even if listing or decoding fails on the updated container version.
  for name in ['Max','Willow','Pete','Hoops','Shared']:
   folder=out/name
   if not folder.exists():continue
   zpath=out.parent/(out.name+'-'+name+'.zip')
   with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for q in sorted(folder.rglob('*')):
     if q.is_file():z.write(q,q.relative_to(out))
   report['archives'].append({'file':zpath.name,'bytes':zpath.stat().st_size,'sha256':digest(zpath)})
  write_report(out,report);zpath=out.parent/(out.name+'-Report.zip')
  with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for q in sorted(out.iterdir()):
    if q.is_file():z.write(q,q.name)
  print('\nFINISHED: '+report['status'],flush=True);print('Upload all '+out.name+'-*.zip files beside this output folder. No server/character switching needed.',flush=True)
 return 0 if report['status']=='complete' else 2
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--retoc',required=True,type=Path);p.add_argument('--utoc',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 try:sys.exit(collect(a.retoc,a.utoc,a.output))
 except Exception as e:print('ERROR: '+str(e),file=sys.stderr);sys.exit(1)

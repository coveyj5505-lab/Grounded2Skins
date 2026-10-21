"""Read four current-build Max atlas texture templates (shared by all skin builders)."""
import argparse,json,hashlib,subprocess,zipfile,sys
from pathlib import Path
from extract_selected import listing,canonical,DATA_TYPES
TARGETS=['/Game/_Augusta/Art/Characters/Player_Male01/Textures/T_Max_Apparel_01_'+s for s in ['C','N','RMA','SSS']]
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def collect(retoc,source,out):
 retoc,source,out=[Path(x).resolve() for x in [retoc,source,out]]
 if source.name.casefold()!='augusta-wingdk.utoc' or not source.with_suffix('.ucas').is_file():raise ValueError('Select original Augusta-WinGDK.utoc with its adjacent UCAS')
 if out.exists() or out.is_relative_to(source.parent):raise ValueError('New output folder outside Paks required')
 out.mkdir(parents=True);(out/'chunks').mkdir();pair=[source,source.with_suffix('.ucas')];before=[(p.stat().st_size,p.stat().st_mtime_ns) for p in pair];r={'scope':'Four current-build texture templates; character models not extracted again','source':str(source),'requested':TARGETS,'packages':[],'chunks':[],'errors':[],'status':'started'}
 try:
  r['retoc_version']=subprocess.check_output([str(retoc),'--version'],text=True).strip()
  if r['retoc_version']!='retoc_cli 0.1.5':raise ValueError('Use existing retoc0.1.5')
  rows=listing(retoc,source,out/'index.log');keys={canonical(p) for p in TARGETS};packs=[e for e in rows if e['type']=='ExportBundleData' and canonical(e['path']) in keys];r['packages']=packs;missing=keys-{canonical(e['path']) for e in packs}
  if missing:r['errors'].append('Missing textures: '+str(sorted(missing)))
  prefixes={e['id'][:16] for e in packs};entries=[e for e in rows if e['type'] in DATA_TYPES and e['id'][:16] in prefixes]
  if sum(e['size'] for e in entries)>128*1024*1024:raise ValueError('Four textures exceed128MiB; share report')
  for i,e in enumerate(entries,1):
   print(f'Texture data {i}/{len(entries)}: {e["path"]}',flush=True);dest=out/'chunks'/e['id']
   with (out/'extract.log').open('a',encoding='utf-8') as log:subprocess.run([str(retoc),'get',str(source),e['id'],str(dest)],stdout=log,stderr=subprocess.STDOUT,check=True)
   assert dest.stat().st_size==e['size'];r['chunks'].append(dict(e,sha256=digest(dest)))
 except Exception as e:r['errors'].append(str(e));print('Partial collection: '+str(e),flush=True)
 finally:
  r['source_size_and_mtime_unchanged']=before==[(p.stat().st_size,p.stat().st_mtime_ns) for p in pair];r['status']='complete' if not r['errors'] and len(r['packages'])==4 and r['source_size_and_mtime_unchanged'] else 'partial';(out/'texture-report.json').write_text(json.dumps(r,indent=2)+'\n')
  zpath=out.with_suffix('.zip')
  with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for q in sorted(out.rglob('*')):
    if q.is_file() and (q.name!='index.log' or r['status']!='complete'):z.write(q,q.relative_to(out))
  print('UPLOAD: '+str(zpath)+'; '+r['status'],flush=True)
 return 0 if r['status']=='complete' else 2
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--retoc',required=True);p.add_argument('--utoc',required=True);p.add_argument('--output',required=True);a=p.parse_args();sys.exit(collect(a.retoc,a.utoc,a.output))

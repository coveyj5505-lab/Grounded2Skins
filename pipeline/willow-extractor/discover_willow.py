#!/usr/bin/env python3
"""Discover actual character mesh paths and follow their skeleton/physics imports.
Read-only input; no full UCAS copy, material download or guessed mesh filenames.
"""
import argparse,hashlib,json,struct,subprocess,sys
from pathlib import Path
from extract_selected import listing,canonical,DATA_TYPES,DLL_HASH
CLASSES={0x42d93e6acfce1861:'SkeletalMesh',0x6300bfd362d4e28b:'Skeleton',0x6ce65259da8a872c:'PhysicsAsset'}

def names(b,pos):
 count=struct.unpack_from('<I',b,pos)[0];pos+=4
 if count==0:return [],pos
 assert 0<count<100000;size=struct.unpack_from('<I',b,pos)[0];pos+=12+count*8;lengths=struct.unpack_from('>'+str(count)+'H',b,pos);pos+=count*2;start=pos;result=[]
 for x in lengths:
  length=(x&32767)*(2 if x&32768 else 1);result.append(b[pos:pos+length].decode('utf-16-le' if x&32768 else 'utf-8'));pos+=length
 assert pos-start==size;return result,pos

def header(b):
 s=struct.unpack_from('<15I',b);assert s[0]==0,'Versioned Zen header retained for cloud inspection; no guessed decoding'
 local,_=names(b,60);imp,pos=names(b,s[12]);nums=struct.unpack_from('<'+'i'*len(imp),b,pos);imp=[n if v==0 else n+'_'+str(v-1) for n,v in zip(imp,nums)]
 assert s[8]<=s[9]<=s[1]<=len(b) and (s[9]-s[8])%72==0
 return {'name_map':local,'imported_packages':imp,'export_classes':[CLASSES.get(struct.unpack_from('<Q',b,i+32)[0],hex(struct.unpack_from('<Q',b,i+32)[0])) for i in range(s[8],s[9],72)]}

def extract(retoc,source,out,character_root='/Game/_Augusta/Art/Characters/Player_Female01'):
 retoc,source,out=map(Path,(retoc,source,out));assert not out.exists(),'Output must be new'
 assert not out.resolve().is_relative_to(source.resolve().parent),'Output must be outside source Paks directory'
 version=subprocess.check_output([str(retoc),'--version'],text=True).strip();assert version=='retoc_cli 0.1.5',version
 for name,digest in DLL_HASH.items():
  lib=retoc.with_name(name)
  if lib.exists():assert hashlib.file_digest(lib.open('rb'),'sha256').hexdigest()==digest,'Unexpected decoder checksum'
 pair=[source,source.with_suffix('.ucas')];before=[(p.stat().st_size,p.stat().st_mtime_ns) for p in pair];out.mkdir(parents=True);(out/'chunks').mkdir();rows=listing(retoc,source,out/'source-index.log');index={canonical(e['path']):e for e in rows if e['type']=='ExportBundleData'};prefix=canonical(character_root).rstrip('/')+'/'
 candidates=[e for e in rows if e['type']=='ExportBundleData' and canonical(e['path']).startswith(prefix)];selected=[e for e in candidates if e['path'].replace('\\','/').split('/')[-1].casefold().startswith('sk_') and not any(s in e['path'].split('/')[-1].casefold() for s in ['physicsasset','skeleton'])];queue=[canonical(e['path']) for e in selected];seen=set();report={'retoc_version':version,'source':str(source),'character_root':character_root,'selection':'Actual indexed SK meshes under character directory, including hair; skeleton/physics targets followed from actual Zen imported package names','requested':[],'missing_targets':[],'chunks':[],'packages':[],'header_warnings':[],'errors':[],'package_count':0,'selected_payload_bytes':0,'discovered_paths':[e['path'] for e in candidates],'legacy':{'status':'not requested'},'source_size_and_mtime_unchanged':False}
 try:
  import blake3
 except ImportError:blake3=None
 try:
  while queue:
   key=queue.pop(0)
   if key in seen:continue
   seen.add(key);report['requested'].append(key)
   if key not in index:report['missing_targets'].append(key);continue
   entry=index[key];chunks=[e for e in rows if e['id'][:16]==entry['id'][:16] and e['type'] in DATA_TYPES]
   if report['package_count']>=48 or report['selected_payload_bytes']+sum(e['size'] for e in chunks)>128*1024*1024:raise RuntimeError('Selected extraction exceeded48packages/128MiB decoded budget; upload current report for review')
   for e in chunks:
    dest=out/'chunks'/e['id']
    with (out/'extract.log').open('a',encoding='utf-8') as log:subprocess.run([str(retoc),'get',str(source),e['id'],str(dest)],check=True,stdout=log,stderr=subprocess.STDOUT)
    assert dest.stat().st_size==e['size'];e=dict(e,sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest(),toc_hash_checked=False)
    if blake3:assert blake3.blake3(dest.read_bytes()).hexdigest()[:40]==e['toc_blake3_20'];e['toc_hash_checked']=True
    report['chunks'].append(e);report['selected_payload_bytes']+=e['size']
   report['package_count']+=1
   try:
    meta=header((out/'chunks'/entry['id']).read_bytes());report['packages'].append(dict(path=entry['path'],chunk_id=entry['id'],**meta))
    for dep in meta['imported_packages']:
     leaf=dep.split('/')[-1].casefold()
     if 'skeleton' in leaf or 'physicsasset' in leaf:queue.append(canonical(dep))
   except (ValueError,AssertionError,struct.error,UnicodeError) as err:report['header_warnings'].append({'path':entry['path'],'error':str(err)})
 except Exception as err:report['errors'].append(str(err))
 finally:
  report['source_size_and_mtime_unchanged']=before==[(p.stat().st_size,p.stat().st_mtime_ns) for p in pair]
  report['status']='complete' if report['package_count'] and not any(report[k] for k in ['missing_targets','header_warnings','errors']) and report['source_size_and_mtime_unchanged'] else 'partial_or_needs_review'
  (out/'extraction-report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'packages':report['package_count'],'decoded_bytes':report['selected_payload_bytes'],'missing_dependencies':report['missing_targets'],'output':str(out)}),flush=True)
 return 0 if report['status']=='complete' else 2
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--retoc',type=Path,required=True);p.add_argument('--utoc',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.utoc.name.casefold()!='augusta-wingdk.utoc':p.error('Choose ORIGINAL Augusta-WinGDK.utoc, not a mod index')
 sys.exit(extract(a.retoc,a.utoc,a.output))

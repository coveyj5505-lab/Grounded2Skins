"""Read only one known animation package and its actual indexed dependencies.

Reuses the already-tested retoc0.1.5 listing/canonicalization/Zen-header readers.
No SDK offsets, game process, guessed sequence names, or full-container copy.
Output is an independent evidence archive, not a mod or runtime test.
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'pete-extractor'))
from extract_selected import listing,canonical,DATA_TYPES,DLL_HASH
from discover_pete import header
DEFAULT='/Game/_Augusta/Art/Characters/Player_Male01/Animation/Combat/AM_Player_Character_Attack_Spear_01_Augusta'
def extract(retoc,source,out,target=DEFAULT,roots=None,max_packages=32,max_bytes=64*1024*1024):
 retoc,source,out=map(lambda p:Path(p).resolve(),[retoc,source,out]);assert source.suffix=='.utoc' and source.is_file() and source.with_suffix('.ucas').is_file();assert not out.exists(),'New output directory required';assert not out.is_relative_to(source.parent),'Output must be outside original Paks directory';assert subprocess.check_output([str(retoc),'--version'],text=True).strip()=='retoc_cli 0.1.5'
 for name,digest in DLL_HASH.items():
  lib=retoc.with_name(name)
  if lib.exists():assert hashlib.file_digest(lib.open('rb'),'sha256').hexdigest()==digest,'Unexpected decoder checksum'
 roots=roots or ['/Game/_Augusta/Art/Characters/Player_Male01/Animation/','/Game/_Augusta/Art/Animation/'];roots=[canonical(r).rstrip('/')+'/' for r in roots];target=canonical(target);pair=[source,source.with_suffix('.ucas')];before=[(p.stat().st_size,p.stat().st_mtime_ns) for p in pair];out.mkdir(parents=True);(out/'chunks').mkdir();rows=listing(retoc,source,out/'source-index.log');index={}
 for row in rows:
  if row['type']=='ExportBundleData':
   key=canonical(row['path']);assert key not in index,'Duplicate package path in selected container';index[key]=row
 report={'status':'INCOMPLETE','source':str(source),'target':target,'selection':'Exact known montage, then only actual Zen imported animation packages or imported skeletons present in the original container index','allowed_animation_roots':roots,'max_packages':max_packages,'max_decoded_bytes':max_bytes,'package_count':0,'decoded_bytes':0,'packages':[],'chunks':[],'missing':[],'excluded_imports':[],'errors':[],'original_source_size_and_mtime_unchanged':False};queue=[target];seen=set()
 try:
  while queue:
   key=queue.pop(0)
   if key in seen:continue
   seen.add(key)
   if key not in index:report['missing'].append(key);continue
   entry=index[key];chunks=[e for e in rows if e['id'][:16]==entry['id'][:16] and e['type'] in DATA_TYPES];total=sum(e['size'] for e in chunks)
   if report['package_count']>=max_packages or report['decoded_bytes']+total>max_bytes:raise RuntimeError('Targeted budget exceeded; retained partial report/chunks. Do not increase automatically.')
   for e in chunks:
    dest=out/'chunks'/e['id']
    with (out/'extract.log').open('a') as log:subprocess.run([str(retoc),'get',str(source),e['id'],str(dest)],check=True,stdout=log,stderr=subprocess.STDOUT)
    assert dest.stat().st_size==e['size'];report['chunks'].append(dict(e,sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest()));report['decoded_bytes']+=e['size']
   h=header((out/'chunks'/entry['id']).read_bytes());imports=h['imported_packages'];report['packages'].append({'path':key,'chunk':entry['id'],'imported_packages':imports,'name_map':h['name_map']});report['package_count']+=1
   for imported in imports:
    child=canonical(imported);allowed=any(child.startswith(prefix) for prefix in roots) or child.casefold().endswith('_skeleton')
    if allowed:
     if child not in seen and child not in queue:queue.append(child)
    else:report['excluded_imports'].append(child)
  if report['missing']:raise RuntimeError('One or more exact package paths not found; inspect missing list instead of guessing replacements.')
  report['status']='EXTRACTED_READ_ONLY'
 except Exception as exc:report['errors'].append(str(exc))
 finally:
  after=[(p.stat().st_size,p.stat().st_mtime_ns) for p in pair];report['original_source_size_and_mtime_unchanged']=before==after;assert before==after,'Source metadata changed';report['excluded_imports']=sorted(set(report['excluded_imports']));(out/'animation-extraction-report.json').write_text(json.dumps(report,indent=2)+'\n')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--retoc',required=True,type=Path);p.add_argument('--utoc',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--target',default=DEFAULT);p.add_argument('--animation-root',action='append');a=p.parse_args();r=extract(a.retoc,a.utoc,a.output,a.target,a.animation_root);print(json.dumps({k:r[k] for k in ['status','package_count','decoded_bytes','missing','errors','original_source_size_and_mtime_unchanged']},indent=2));raise SystemExit(0 if r['status']=='EXTRACTED_READ_ONLY' else 1)

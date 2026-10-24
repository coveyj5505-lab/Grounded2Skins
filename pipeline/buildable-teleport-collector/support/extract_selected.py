#!/usr/bin/env python3
"""Targeted read-only retoc extraction. Reads the index, then selected chunks.
Never unpacks or copies the full UCAS. Output must be outside the game directory.
"""
import argparse,hashlib,json,os,re,subprocess,sys
from pathlib import Path
LINE=re.compile(r'^(.+?)\s+([0-9a-fA-F]{24})\s+([0-9a-fA-F]{64})\s+(\w+)\s+(\d+)\s+(.+)$')
DATA_TYPES={'ExportBundleData','BulkData','OptionalBulkData','MemoryMappedBulkData'}
DLL_HASH={'oo2core_9_win64.dll':'6f5d41a7892ea6b2db420f2458dad2f84a63901c9a93ce9497337b16c195f457','liboo2corelinux64.so.9':'ed7e98f70be1254a80644efd3ae442ff61f854a2fe9debb0b978b95289884e9c'}
def canonical(path):
 p=path.replace('\\','/').removeprefix('../../../')
 for prefix,mount in [('Augusta/Content/','/Game/'),('Engine/Content/','/Engine/')]:
  if p.startswith(prefix):p=mount+p[len(prefix):];break
 if p.endswith('.uasset'):p=p[:-7]
 return p.casefold()
def listing(retoc,source,log,all_entries=False):
 cmd=[str(retoc),'list',str(source),'--hash','--size','--path']+(['--all'] if all_entries else [])
 entries=[]
 with log.open('w',encoding='utf-8') as out:
  proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=out,text=True,encoding='utf-8',errors='replace')
  for line in proc.stdout:
   out.write(line);match=LINE.match(line.rstrip())
   if match:
    owner,cid,h,kind,size,path=match.groups();entries.append(dict(owner=owner.strip(),id=cid.lower(),toc_blake3_20=h[:40].lower(),type=kind,size=int(size),path=path))
  proc.stdout.close()
  code=proc.wait()
 if code:raise RuntimeError(f'retoc list failed ({code}); see {log}')
 if not entries:raise RuntimeError('No recognizable retoc list entries; refusing an empty extraction')
 return entries

def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--retoc',required=True,type=Path);a.add_argument('--utoc',required=True,type=Path);a.add_argument('--output',required=True,type=Path);a.add_argument('--targets',type=Path,default=Path(__file__).with_name('targets.json'));a.add_argument('--legacy-context',type=Path,help='Optional read-only Paks directory containing original archive AND global pair; duplicate selected paths are rejected');args=a.parse_args()
 retoc=args.retoc.resolve();source=args.utoc.resolve();output=args.output.resolve()
 if output.is_relative_to(source.parent):raise RuntimeError('Choose output outside the game/Paks directory')
 if not source.is_file() or not source.with_suffix('.ucas').is_file():raise RuntimeError('Both original UTOC and adjacent same-name UCAS are required')
 if output.exists():raise RuntimeError('Output must be a NEW directory; existing files will not be overwritten')
 version=subprocess.check_output([str(retoc),'--version'],text=True).strip()
 if version!='retoc_cli 0.1.5':raise RuntimeError('This helper was tested with retoc_cli 0.1.5; use that pinned version')
 for name,expected in DLL_HASH.items():
  lib=retoc.with_name(name)
  if lib.exists() and hashlib.file_digest(lib.open('rb'),'sha256').hexdigest()!=expected:raise RuntimeError('Existing decoder has an unexpected checksum: '+str(lib))
 targets=json.loads(args.targets.read_text(encoding='utf-8-sig'));requested={canonical(p):p for p in targets}
 if not requested:raise RuntimeError('Empty target list')
 output.mkdir(parents=True);(output/'chunks').mkdir();before={str(p):[p.stat().st_size,p.stat().st_mtime_ns] for p in [source,source.with_suffix('.ucas')]}
 rows=listing(retoc,source,output/'source-index.log');packages={canonical(e['path']):e for e in rows if e['type']=='ExportBundleData' and canonical(e['path']) in requested};missing=[requested[k] for k in requested if k not in packages];prefixes={e['id'][:16] for e in packages.values()};selected=[e for e in rows if e['id'][:16] in prefixes and e['type'] in DATA_TYPES]
 print(f'Index scanned. Extracting {len(packages)} requested packages and {len(selected)-len(packages)} associated bulk chunks. Missing targets: {len(missing)}',flush=True)
 report={'retoc_version':version,'source':str(source),'requested':targets,'missing_targets':missing,'package_count':len(packages),'chunks':[],'content_hash_note':'SHA256 recorded for transport. Original TOC BLAKE3-160 values recorded; validated when the optional Python blake3 module is available.','legacy':{'status':'not requested'}}
 try:
  import blake3
 except ImportError:blake3=None
 for entry in selected:
  dest=output/'chunks'/entry['id'];cmd=[str(retoc),'get',str(source),entry['id'],str(dest)]
  with (output/'extract.log').open('a',encoding='utf-8') as log:subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT)
  if dest.stat().st_size!=entry['size']:raise RuntimeError('Extracted size mismatch for '+entry['id'])
  entry['sha256']=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest();entry['toc_hash_checked']=False
  if blake3:
   if blake3.blake3(dest.read_bytes()).hexdigest()[:40]!=entry['toc_blake3_20']:raise RuntimeError('TOC content hash mismatch')
   entry['toc_hash_checked']=True
  report['chunks'].append(entry)
 if args.legacy_context and packages:
  context=args.legacy_context.resolve();full=listing(retoc,context,output/'context-index.log',all_entries=True)
  for key,entry in packages.items():
   alternatives=[e for e in full if e['type']=='ExportBundleData' and canonical(e['path'])==key]
   if len(alternatives)!=1 or alternatives[0]['owner']!=source.stem:raise RuntimeError('Legacy context has a missing, overridden or duplicate selected path: '+entry['path'])
  cmd=[str(retoc),'to-legacy',str(context),str(output/'legacy'),'--no-shaders','--no-script-objects']
  for entry in packages.values():cmd+=['--filter',entry['path']]
  with (output/'legacy.log').open('w',encoding='utf-8') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  text=(output/'legacy.log').read_text();match=re.search(r'Extracted (\d+) \((\d+) failed\)',text);files=list((output/'legacy').rglob('*.uasset')) if (output/'legacy').exists() else []
  passed=bool(p.returncode==0 and match and int(match[1])==len(packages) and int(match[2])==0 and len(files)==len(packages))
  report['legacy']={'status':'passed' if passed else 'failed','exit_code':p.returncode,'uasset_count':len(files),'runner_summary':match[0] if match else None,'command':cmd}
 after={str(p):[p.stat().st_size,p.stat().st_mtime_ns] for p in [source,source.with_suffix('.ucas')]};assert before==after,'source file metadata changed during extraction'
 report['source_size_and_mtime_unchanged']=True;report['selected_payload_bytes']=sum(e['size'] for e in selected);(output/'extraction-report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Finished:',output,'Selected decoded bytes:',report['selected_payload_bytes'],flush=True)
 if missing or report['legacy']['status']=='failed':return 2
 return 0
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as ex:print('ERROR:',ex,file=sys.stderr);sys.exit(1)

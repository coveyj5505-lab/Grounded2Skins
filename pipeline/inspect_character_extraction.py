#!/usr/bin/env python3
"""Validate a targeted stock extraction ZIP, including Windows path separators.
Never executes uploaded files. Writes a new normalized stage, verifies all chunk
sizes/SHA256 and parses native skeleton structures using existing readers.
"""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
from extract_reference_skeleton import extract

def inspect(archive,out,body_stem):
 assert not out.exists(),'Output must be new';out.mkdir(parents=True)
 with zipfile.ZipFile(archive) as z:
  assert sum(f.file_size for f in z.infolist())<=256*1024*1024,'Oversized targeted extraction'
  for f in z.infolist():
   dest=out/f.filename.replace('\\','/');assert dest.resolve().is_relative_to(out.resolve()),'Unsafe ZIP path'
   if f.is_dir():dest.mkdir(parents=True,exist_ok=True)
   else:
    assert not dest.exists(),'Duplicate normalized ZIP path';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(f))
 report=json.loads((out/'extraction-report.json').read_text(encoding='utf-8-sig'))
 assert report['source'].replace('\\','/').split('/')[-1].casefold()=='augusta-wingdk.utoc'
 assert report['source_size_and_mtime_unchanged']
 assert not any(report[k] for k in ['missing_targets','errors','header_warnings']),'Inspect partial report before proceeding'
 for c in report['chunks']:
  assert re.fullmatch('[0-9a-f]{24}',c['id']);raw=(out/'chunks'/c['id']).read_bytes();assert len(raw)==c['size'] and hashlib.sha256(raw).hexdigest()==c['sha256']
 meta=report['packages'];skeletons=[]
 for m in meta:
  assert re.fullmatch('[0-9a-f]{24}',m['chunk_id']);raw=(out/'chunks'/m['chunk_id']).read_bytes();m['sha256']=hashlib.sha256(raw).hexdigest()
  if 'SkeletalMesh' in m['export_classes'] or 'Skeleton' in m['export_classes']:
   sk=extract(raw,m['name_map']);sk.update(package=m['path'],chunk_sha256=m['sha256']);skeletons.append(sk)
 body=next(s for s in skeletons if s['package'].endswith('/'+body_stem+'.uasset'))
 (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');(out/'reference-skeletons.json').write_text(json.dumps({'meshes':skeletons},indent=2)+'\n');(out/'rig-reference.json').write_text(json.dumps({'meshes':[body]},indent=2)+'\n')
 result={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'packages':report['package_count'],'decoded_bytes':report['selected_payload_bytes'],'all_chunk_sizes_and_sha256_valid':True,'source_unchanged_as_reported':True,'body_bones':body['bone_count'],'body_package':body['package']};(out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('new_output',type=Path);p.add_argument('body_stem');a=p.parse_args();inspect(a.archive,a.new_output,a.body_stem)

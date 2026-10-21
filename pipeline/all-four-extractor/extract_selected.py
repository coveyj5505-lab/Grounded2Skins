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

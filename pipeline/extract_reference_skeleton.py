#!/usr/bin/env python3
"""Locate and validate the documented native UE5 FReferenceSkeleton structure.
This does not deserialize UObject properties, render buffers or skin weights.
"""
import argparse,hashlib,json,math,struct
from pathlib import Path

def extract(data,names):
 candidates=[]
 for ni,name in enumerate(names):
  if name!='Root_NSK':continue
  pat=struct.pack('<IIi',ni,0,-1);start=0
  while True:
   pos=data.find(pat,start)
   if pos<0:break
   start=pos+1
   if pos<4:continue
   n=struct.unpack_from('<i',data,pos-4)[0]
   if not 1<=n<=2000 or pos+n*12+4+n*80+4+n*12>len(data):continue
   bones=[]
   for i in range(n):
    idx,num,parent=struct.unpack_from('<IIi',data,pos+12*i)
    if idx>=len(names) or num!=0 or (parent!=-1 if i==0 else not 0<=parent<i):break
    bones.append({'index':i,'name':names[idx],'parent':parent})
   if len(bones)!=n or len({b['name'] for b in bones})!=n:continue
   p=pos+n*12
   if struct.unpack_from('<i',data,p)[0]!=n:continue
   p+=4;valid=True
   for i in range(n):
    t=struct.unpack_from('<10d',data,p+i*80)
    if not all(math.isfinite(v) for v in t) or abs(sum(v*v for v in t[:4])-1)>.001 or max(abs(v) for v in t[4:7])>100000 or any(abs(v)>1000 for v in t[7:]):valid=False;break
    bones[i].update(rotation_xyzw=t[:4],translation_cm=t[4:7],scale_xyz=t[7:])
   if not valid:continue
   end=p+n*80
   if struct.unpack_from('<i',data,end)[0]!=n:continue
   end+=4;map_entries={}
   for i in range(n):
    idx,num,bone=struct.unpack_from('<IIi',data,end+i*12)
    if idx>=len(names) or num!=0 or not 0<=bone<n or names[idx]!=bones[bone]['name']:valid=False;break
    map_entries[names[idx]]=bone
   if not valid or len(map_entries)!=n:continue
   candidates.append({'offset':pos-4,'end':end+n*12,'bone_count':n,'bones':bones,'validation':{'parent_before_child':True,'names_unique':True,'all_pose_quaternions_normalized':True,'bone_pose_counts_equal':True,'name_to_index_map_exact':True},'source_structure':'CUE4Parse FReferenceSkeleton/FMeshBoneInfo and UE5 double FTransform; located structurally, not via mapped UObject deserialization'})
 if len(candidates)!=1:raise ValueError(f'expected one fully validated skeleton, found {len(candidates)}')
 return candidates[0]
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('metadata',type=Path);a.add_argument('chunks',type=Path);a.add_argument('output',type=Path);x=a.parse_args();meta=json.loads(x.metadata.read_text());results=[]
 for m in meta:
  if m['path'].endswith(('/SK_Male_Teen_01.uasset','/SK_Male_Teen_01_w_BackPack.uasset')):
   p=x.chunks/m['chunk_id'];s=extract(p.read_bytes(),m['name_map']);s.update(package=m['path'],chunk_sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest());results.append(s)
 assert len(results)==2 and results[0]['bones']==results[1]['bones'],'body and backpack skeleton differ'
 if x.output.exists():raise FileExistsError(x.output)
 x.output.write_text(json.dumps({'coordinate_system':'Unreal left-handed Z-up, centimeters; rotations stored xyzw, parent-local transforms','body_backpack_skeletons_identical':True,'meshes':results},indent=2)+'\n');print('Verified two identical reference skeletons:',results[0]['bone_count'],'bones each')

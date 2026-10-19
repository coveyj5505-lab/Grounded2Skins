#!/usr/bin/env python3
"""Clone Jessie texture templates and MI by checked equal-length Zen header edits.

Preserves native bytes and every unrelated original external dependency. Rebuilds
name hashes, public export/import hashes, chunk IDs and container store entries.
"""
import argparse,json,struct,hashlib,shutil
from pathlib import Path
from cityhash import CityHash64
from compare_stock_max import names
p=argparse.ArgumentParser(description=__doc__);p.add_argument('atlas_raw',type=Path);p.add_argument('stock_mi_chunk',type=Path);p.add_argument('new_output',type=Path);a=p.parse_args();assert not a.new_output.exists();(a.new_output/'chunks').mkdir(parents=True)
base='/Game/_Augusta/Art/Characters/Player_Male01/Textures/';leafs=['MI_Character_Male01_Max_Apparel01']+['T_Max_Apparel_01_'+s for s in ['C','N','RMA','SSS']];paths={base+n:(base+n).replace('/_Augusta/','/_Jessie0/').replace('_Max_','_Jes_') for n in leafs};shorts={n:n.replace('_Max_','_Jes_') for n in leafs};repl={**paths,**shorts}
pkg_hash=lambda s:CityHash64(s.lower().encode('utf-16-le'));obj_hash=lambda s:CityHash64(s.lower().encode('utf-16-le'))
ids={pkg_hash(k):pkg_hash(v) for k,v in paths.items()};hashes={obj_hash(k):obj_hash(v) for k,v in shorts.items()}
def patch_batch(b,pos):
 original,end=names(b,pos)
 if not original:return
 q=pos+16+len(original)*10
 for i,old in enumerate(original):
  enc=old.encode('ascii');assert b[q:q+len(enc)]==enc
  new=old
  for k,v in repl.items():new=new.replace(k,v)
  if new!=old:
   assert len(new)==len(old);assert struct.unpack_from('<Q',b,pos+16+i*8)[0]==CityHash64(old.lower().encode())
   struct.pack_into('<Q',b,pos+16+i*8,CityHash64(new.lower().encode()));b[q:q+len(enc)]=new.encode()
  q+=len(enc)
 assert q==end
manifest=json.loads((a.atlas_raw/'manifest.json').read_text());files=[];result_paths={};records=[]
for cid,path in manifest['chunk_paths'].items():
 if '/T_Max_Head_' in path:continue
 files.append((cid,path,(a.atlas_raw/'chunks'/cid).read_bytes()))
assert hashlib.sha256(a.stock_mi_chunk.read_bytes()).hexdigest()=='ad8ce9e2e08ef67d711ec79ffed15323ab257c579a2708dd2bd31fb5d53c855e'
files.append(('0cfec9856be41dcc00000001','../../../Augusta/Content/_Augusta/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Max_Apparel01.uasset',a.stock_mi_chunk.read_bytes()))
mi_imports=[]
for cid,path,data in files:
 b=bytearray(data);oldpkg=int.from_bytes(bytes.fromhex(cid[:16]),'little');newid=ids.get(oldpkg,oldpkg).to_bytes(8,'little').hex()+cid[16:];newpath=path
 for old,new in paths.items():newpath=newpath.replace(old.replace('/Game/','../../../Augusta/Content/'),new.replace('/Game/','../../../Augusta/Content/'))
 if path.endswith('.uasset'):
  s=struct.unpack_from('<15I',b);assert s[0]==0
  patch_batch(b,60);patch_batch(b,s[12])
  for off in range(s[6],s[7],8):
   h=struct.unpack_from('<Q',b,off)[0]
   if h in hashes:struct.pack_into('<Q',b,off,hashes[h])
  for off in range(s[8],s[9],72):
   h=struct.unpack_from('<Q',b,off+56)[0]
   if h in hashes:struct.pack_into('<Q',b,off+56,hashes[h])
  assert b[s[1]:]==data[s[1]:],'Native/property payload changed'
  if cid=='0cfec9856be41dcc00000001':mi_imports=names(b,s[12])[0]
 assert newid not in result_paths;(a.new_output/'chunks'/newid).write_bytes(b);result_paths[newid]=newpath;records.append({'old_chunk':cid,'new_chunk':newid,'path':newpath,'native_payload_preserved':True,'sha256':hashlib.sha256(b).hexdigest()})
# Read the original v5 StoreEntry buffer; retain shader-hash arrays byte-exact.
header=next((a.atlas_raw/'chunks').glob('*00000006'));old=header.read_bytes();assert struct.unpack_from('<II',old)==(0x496f436e,5);n=struct.unpack_from('<I',old,16)[0];oldids=struct.unpack_from('<'+'Q'*n,old,20);pos=20+n*8;sz=struct.unpack_from('<I',old,pos)[0];buf=old[pos+4:pos+4+sz];entries={};retained={int.from_bytes(bytes.fromhex(c[:16]),'little') for c,p,_ in files}
for i,id in enumerate(oldids):
 if id not in retained:continue
 count,offset,sc,so=struct.unpack_from('<4I',buf,i*16);imp=list(struct.unpack_from('<'+'Q'*count,buf,i*16+offset)) if count else [];sh=buf[i*16+8+so:i*16+8+so+sc*20] if sc else b'';assert len(sh)==sc*20
 entries[ids.get(id,id)]=([ids.get(v,v) for v in imp],sh)
miold=pkg_hash(base+leafs[0]);assert miold==int.from_bytes(bytes.fromhex('0cfec9856be41dcc'),'little');entries[ids[miold]]=([pkg_hash(v) for v in mi_imports],b'')
assert len(entries)==14;entries=dict(sorted(entries.items()));buffer=bytearray(16*len(entries))
for i,(id,(imp,sh)) in enumerate(entries.items()):
 if imp:struct.pack_into('<II',buffer,16*i,len(imp),len(buffer)-16*i);buffer.extend(struct.pack('<'+'Q'*len(imp),*imp))
 if sh:struct.pack_into('<II',buffer,16*i+8,len(sh)//20,len(buffer)-16*i-8);buffer.extend(sh)
h=bytearray(old[:16]+struct.pack('<I',len(entries))+struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(buffer))+buffer+bytes(20));h.extend(struct.pack('<qqI',len(h)+16,4,0));(a.new_output/'chunks'/header.name).write_bytes(h)
(a.new_output/'manifest.json').write_text(json.dumps(dict(manifest,chunk_paths=result_paths),indent=2)+'\n');(a.new_output/'isolation-report.json').write_text(json.dumps({'strategy':'Intermediate Jessie private-template clone; direct equal-length Zen header names/hashes and store dependency edits; original native bytes and unrelated imports unchanged','package_paths':paths,'packages':len(entries),'records':records,'source_header_id':header.name,'original_files_modified':False},indent=2)+'\n');print('Private Zen assets written:',len(entries),'packages')

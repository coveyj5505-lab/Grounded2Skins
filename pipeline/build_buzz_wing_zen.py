"""Cooked native accessory LODs + isolated two-mesh/private-material Zen package store."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
from cityhash import CityHash64
from compare_stock_max import names
from assemble_bopeep_zen import batch,H
from native_buffers import skeleton_signature,require
from write_resized_lod import array16,section,STREAM_TAIL
p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('buzz_baseline',type=Path);p.add_argument('out',type=Path);a=p.parse_args();out=a.out;out.mkdir(exist_ok=False);(out/'chunks').mkdir()
reference=a.buzz_baseline/'reference.json';source=a.buzz_baseline/'package/unpacked/chunks/cd809abc483f179000000001';original=source.read_bytes();profile=json.loads((a.buzz_baseline/'readback-cd809abc483f179000000001/mesh.json').read_text());assert hashlib.sha256(original).hexdigest()==profile['source_sha256'];assert profile['skeleton_bones']==230 and profile['lod_count']==1
paths={};reports=[]
def clone_header(raw,replacements):
 b=bytearray(raw);s=struct.unpack_from('<15I',b)
 for at in [60,s[12]]:
  old,end=names(b,at);new=[]
  for value in old:
   # Exact FName equality is essential: mesh package prefixes also match _Skeleton/_PhysicsAsset.
   new.append(replacements.get(value,value))
  encoded=batch(new);assert len(encoded)==end-at;b[at:end]=encoded
 # Only the renamed private material public object hash changes, not mesh export name.
 oldname='MI_Character_Male01_Buz_Apparel01';newname='MI_Character_Male01_Wng_Apparel01';oh,nh=H(oldname),H(newname)
 for at in range(s[6],s[7],8):
  if struct.unpack_from('<Q',b,at)[0]==oh:struct.pack_into('<Q',b,at,nh)
 assert b[s[1]:]==raw[s[1]:]
 return bytes(b)
oldpkg='/Game/_Augusta/Art/Characters/Player_Male01/SK_Male_Teen_01'
oldmi='/Game/_BuzzMod/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Buz_Apparel01'
newmi=oldmi.replace('/_BuzzMod/','/_BzWing0/').replace('_Buz_','_Wng_')
for state,namespace in [('deployed','_BzWExt0'),('retracted','_BzWRet0')]:
 buffers=a.stage/('buffers-'+state+'-v1');manifest=json.loads((buffers/'manifest.json').read_text());assert manifest['skeleton_signature']==skeleton_signature(reference)
 records=[]
 for filename in ['indices.bin','positions.bin','static-vertices.bin','skin-weights.bin','colors.bin']:
  data=(buffers/filename).read_bytes();assert hashlib.sha256(data).hexdigest()==manifest['files'][filename]['sha256'];records.append(data)
 assert all(sec['palette']==[0] and sec['material']==0 for sec in manifest['sections'])
 stream=b'\x05\x00'+b''.join(records)+STREAM_TAIL
 lod=b'\x05\x00'+struct.pack('<ii',0,1)+array16(range(230))+struct.pack('<i',len(manifest['sections']))+b''.join(section(s) for s in manifest['sections'])+array16([0])+struct.pack('<I',len(stream))+stream
 start,end=profile['lod_start'],profile['all_lods_end'];assert original[end-54:end]==STREAM_TAIL and len(original)-end==100
 s=struct.unpack_from('<15I',original);matches=[]
 for at in range(s[8],s[9],72):
  off,size=struct.unpack_from('<QQ',original,at)
  if s[1]+off<=start and s[1]+off+size==len(original)-4:matches.append((at,size))
 assert len(matches)==1;entry,oldsize=matches[0]
 bulk=[]
 for at in range(60,s[6]-31):
  old,dup,size,flags,cooked=struct.unpack_from('<qqqIB',original,at)
  if old>0 and dup==-1 and size==0 and flags==0 and cooked==0 and original[at+29:at+32]==bytes(3):bulk.append(at)
 assert len(bulk)==1
 delta=len(lod)-(end-start);b=bytearray(original[:start]+lod+original[end:]);struct.pack_into('<Q',b,entry+8,oldsize+delta);struct.pack_into('<q',b,bulk[0],start+len(lod)+4-s[1])
 positions=np.load(buffers/'expected.npz')['positions'];lo,hi=positions.min(0),positions.max(0);center=(lo+hi)/2;extent=(hi-lo)/2
 b[profile['material_start']-56:profile['material_start']]=struct.pack('<7d',*center,*extent,float(np.linalg.norm(extent)))
 assert b[profile['material_start']:start]==original[profile['material_start']:start] and b[start+len(lod):]==original[end:]
 newpkg=oldpkg.replace('/_Augusta/','/'+namespace+'/')
 raw=clone_header(bytes(b),{oldpkg:newpkg,oldmi:newmi,'MI_Character_Male01_Buz_Apparel01':'MI_Character_Male01_Wng_Apparel01'})
 original_imports,_=names(original,s[12]);new_imports,_=names(raw,s[12]);assert new_imports==[newmi if value==oldmi else value for value in original_imports],'Unrelated skeleton/physics/game dependency renamed'
 assert oldpkg+'_Skeleton' in new_imports and oldpkg+'_w_BackPack_PhysicsAsset' in new_imports
 cid=H(newpkg).to_bytes(8,'little').hex()+'00000001';(out/'chunks'/cid).write_bytes(raw);paths[cid]='../../../Augusta/Content/'+newpkg.removeprefix('/Game/')+'.uasset'
 reports.append({'state':state,'asset':newpkg+'.SK_Male_Teen_01','chunk':cid,'vertices':manifest['output_vertices'],'triangles':manifest['triangles'],'root_only':True,'lod_count':1,'skeleton_and_native_tail_preserved':True,'source_sha256':profile['source_sha256'],'sha256':hashlib.sha256(raw).hexdigest()})
# Select ONLY the new private MI + four textures/bulk streams from the proven template clone.
material=a.stage/'material-templates-v1';m=json.loads((material/'manifest.json').read_text());selected={cid:path for cid,path in m['chunk_paths'].items() if '/_BzWing0/' in path};assert len(selected)==9
for cid,path in selected.items():assert cid not in paths;(out/'chunks'/cid).write_bytes((material/'chunks'/cid).read_bytes());paths[cid]=path
# Fresh seven-package store: read every import dependency from its actual renamed header.
entries={}
for cid,path in paths.items():
 if not path.endswith('.uasset'):continue
 b=(out/'chunks'/cid).read_bytes();s=struct.unpack_from('<15I',b);imp,at=names(b,s[12]);assert s[1]-at==4*len(imp);nums=struct.unpack_from('<'+'i'*len(imp),b,at);entries[int.from_bytes(bytes.fromhex(cid[:16]),'little')]=[H(n if number==0 else n+'_'+str(number-1)) for n,number in zip(imp,nums)]
assert len(entries)==7
entries=dict(sorted(entries.items()));store=bytearray(16*len(entries))
for i,imports in enumerate(entries.values()):
 if imports:struct.pack_into('<II',store,i*16,len(imports),len(store)-i*16);store.extend(struct.pack('<'+'Q'*len(imports),*imports))
header=next((material/'chunks').glob('*00000006'));prefix=header.read_bytes()[:16];assert struct.unpack_from('<II',prefix)==(0x496f436e,5)
b=bytearray(prefix+struct.pack('<I',len(entries))+struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(store))+store+bytes(20));b.extend(struct.pack('<qqI',len(b)+16,4,0));(out/'chunks'/header.name).write_bytes(b)
(out/'manifest.json').write_text(json.dumps(dict(m,chunk_paths=paths),indent=2)+'\n')
assert all('/_Augusta/' not in path and '/_BuzzMod/' not in path and '/_BoPeep0/' not in path for path in paths.values())
r={'packages':7,'indexed_chunks':len(paths),'meshes':reports,'private_material':newmi,'original_game_and_body_paths_overridden':False,'runtime':'NOT TESTED; independent component must disable collision, animation and postprocess'};(out/'wing-zen-report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

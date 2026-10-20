"""Use the Windows-loaded crook's stock inline-LOD layout for rigid wing copies.

The Buzz body retains its original 230-bone animation binding. These independent
root-weighted cosmetics use the proven accessory's 192-bone serialization only;
they never run an animation or a leader-pose binding.
"""
import argparse,json,struct,hashlib
from pathlib import Path
import numpy as np
from native_buffers import encode,skeleton_signature
from assemble_bopeep_zen import batch,H
from compare_stock_max import names
from write_resized_lod import array16,section,STREAM_TAIL
p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args();out=a.out;out.mkdir(exist_ok=False);(out/'raw/chunks').mkdir(parents=True)
crook=Path('/workspace/mod-work/crook-stage');wing=Path('/workspace/mod-work/wings-stage');source=crook/'package-v1/unpacked';cid='4d2d88a628acba9400000001';original=(source/'chunks'/cid).read_bytes();profile=json.loads((crook/'native-readback-v1/mesh.json').read_text());assert hashlib.sha256(original).hexdigest()==profile['source_sha256'];assert profile['skeleton_bones']==192 and profile['lod_count']==4
reference=crook/'reference.json';sig=skeleton_signature(reference);paths={};reports=[]
oldpkg='/Game/_BoCrook/Art/Characters/Player_Female01/SK_Female_Teen_01';oldmi='/Game/_BoPeep0/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Bop_Apparel01';newmi=oldmi.replace('_BoPeep0','_BzWing0').replace('_Bop_','_Wng_')
for state,namespace in [('deployed','_BzWExt1'),('retracted','_BzWRet1')]:
 data=dict(np.load(wing/('atlas-'+state+'-v1/Buzz-atlas-SKINNED.npz')))
 assert np.all(data['joints']==0) and np.all(data['weights'][:,0]==1)
 data['skeleton_signature']=np.array(sig);data['skeleton_bone_count']=np.array(192);data['materials']=np.zeros(len(data['indices']),dtype='u2');data['material_count']=np.array(len(profile['materials']))
 np.savez_compressed(out/(state+'.npz'),**data);buffers=out/(state+'-buffers');m=encode(data,sig,buffers)
 records=[(buffers/n).read_bytes() for n in ['indices.bin','positions.bin','static-vertices.bin','skin-weights.bin','colors.bin']];stream=b'\x05\x00'+b''.join(records)+STREAM_TAIL
 lod=b'\x05\x00'+struct.pack('<ii',0,1)+array16(range(192))+struct.pack('<i',len(m['sections']))+b''.join(section(s) for s in m['sections'])+array16([0])+struct.pack('<I',len(stream))+stream
 start,end=profile['lod_start'],profile['all_lods_end'];s=struct.unpack_from('<15I',original);entries=[];bulks=[]
 for at in range(s[8],s[9],72):
  off,size=struct.unpack_from('<QQ',original,at)
  if s[1]+off<=start and s[1]+off+size==len(original)-4:entries.append((at,size))
 for at in range(60,s[6]-31):
  off,dup,size,flags,cooked=struct.unpack_from('<qqqIB',original,at)
  if off>0 and dup==-1 and size==flags==cooked==0 and original[at+29:at+32]==bytes(3):bulks.append(at)
 assert len(entries)==len(bulks)==1 and original[end-54:end]==STREAM_TAIL
 body=lod*4;b=bytearray(original[:start]+body+original[end:]);delta=len(body)-(end-start);struct.pack_into('<Q',b,entries[0][0]+8,entries[0][1]+delta);struct.pack_into('<q',b,bulks[0],start+len(body)+4-s[1])
 pos=np.load(buffers/'expected.npz')['positions'];lo,hi=pos.min(0),pos.max(0);center=(lo+hi)/2;extent=(hi-lo)/2;b[profile['material_start']-56:profile['material_start']]=struct.pack('<7d',*center,*extent,float(np.linalg.norm(extent)))
 assert b[profile['material_start']:start]==original[profile['material_start']:start] and b[start+len(body):]==original[end:]
 newpkg=oldpkg.replace('_BoCrook',namespace);replacements={oldpkg:newpkg,oldmi:newmi,oldmi.rsplit('/',1)[1]:newmi.rsplit('/',1)[1]}
 for at in [60,s[12]]:
  ns,stop=names(b,at);encoded=batch([replacements.get(n,n) for n in ns]);assert len(encoded)==stop-at;b[at:stop]=encoded
 for at in range(s[6],s[7],8):
  if struct.unpack_from('<Q',b,at)[0]==H(oldmi.rsplit('/',1)[1]):struct.pack_into('<Q',b,at,H(newmi.rsplit('/',1)[1]))
 imports,_=names(b,s[12]);original_imports,_=names(original,s[12]);assert imports==[newmi if v==oldmi else v for v in original_imports]
 newcid=H(newpkg).to_bytes(8,'little').hex()+'00000001';(out/'raw/chunks'/newcid).write_bytes(b);paths[newcid]='../../../Augusta/Content/'+newpkg.removeprefix('/Game/')+'.uasset';reports.append({'state':state,'chunk':newcid,'asset':newpkg+'.SK_Female_Teen_01','vertices':m['output_vertices'],'triangles':m['triangles'],'lods':4})
material=wing/'material-templates-v1';manifest=json.loads((material/'manifest.json').read_text())
for cid,path in manifest['chunk_paths'].items():
 if '/_BzWing0/' in path:(out/'raw/chunks'/cid).write_bytes((material/'chunks'/cid).read_bytes());paths[cid]=path
entries={}
for cid,path in paths.items():
 if not path.endswith('.uasset'):continue
 b=(out/'raw/chunks'/cid).read_bytes();s=struct.unpack_from('<15I',b);ns,end=names(b,s[12]);nums=struct.unpack_from('<'+'i'*len(ns),b,end);entries[int.from_bytes(bytes.fromhex(cid[:16]),'little')]=[H(n if v==0 else n+'_'+str(v-1)) for n,v in zip(ns,nums)]
entries=dict(sorted(entries.items()));store=bytearray(16*len(entries))
for i,imports in enumerate(entries.values()):
 if imports:struct.pack_into('<II',store,i*16,len(imports),len(store)-i*16);store.extend(struct.pack('<'+'Q'*len(imports),*imports))
header=next((source/'chunks').glob('*00000006'));b=bytearray(header.read_bytes()[:16]+struct.pack('<I',len(entries))+struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(store))+store+bytes(20));b.extend(struct.pack('<qqI',len(b)+16,4,0));(out/'raw/chunks'/header.name).write_bytes(b)
(out/'raw/manifest.json').write_text(json.dumps(dict(manifest,chunk_paths=paths),indent=2)+'\n');(out/'report.json').write_text(json.dumps({'meshes':reports,'template':'Windows-visible crook native layout','Buzz_body_skeleton_unchanged':True,'component_animation_disabled':True,'runtime':'PENDING'},indent=2)+'\n');print(json.dumps(reports,indent=2))

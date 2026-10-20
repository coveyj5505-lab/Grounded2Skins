"""Independent CUE mesh/mip readbacks, exact private paths, MI links and atlas UV checks."""
import argparse,json,hashlib,struct
from pathlib import Path
import numpy as np
from PIL import Image
import texture2ddecoder
from compare_stock_max import names
p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('reference',type=Path);p.add_argument('report',type=Path);a=p.parse_args();root=a.stage;raw=root/'final-unpacked/chunks';meta=json.loads((root/'final-metadata.json').read_text());by_path={'/Game/'+m['path'].split('/Content/',1)[1][:-7]:m for m in meta};refs=json.loads(a.reference.read_text())['meshes'][0]['bones'];assert all(s['bones']==refs for s in json.loads((root/'final-skeletons.json').read_text())['meshes'])
def resolve(m,index):
 assert index<0;b=(raw/m['chunk_id']).read_bytes();s=struct.unpack_from('<15I',b);v=struct.unpack_from('<Q',b,s[7]+(-index-1)*8)[0];assert v>>62==2;v&=(1<<62)-1;package=m['imported_packages'][v>>32];h=struct.unpack_from('<Q',b,s[6]+(v&0xffffffff)*8)[0]
 if package in by_path:
  target=(raw/by_path[package]['chunk_id']).read_bytes();ts=struct.unpack_from('<15I',target);assert h in [struct.unpack_from('<Q',target,i+56)[0] for i in range(ts[8],ts[9],72)]
 return package
reports=[]
for i,m in enumerate(x for x in meta if '/SK_Male_Teen_01.uasset' in x['path']):
 state='deployed' if '/_BzWExt0/' in m['path'] else 'retracted';d=root/f'final-mesh-readback-{i}';j=json.loads((d/'mesh.json').read_text());expected=np.load(root/f'buffers-{state}-v1/expected.npz');n=len(expected['positions']);read=lambda file,t,c:np.fromfile(d/file,dtype=t).reshape(-1,c)
 assert (j['vertices'],j['triangles'],j['skeleton_bones'],j['lod_count'])==(n,328,230,1)
 assert np.array_equal(read('positions.f32','<f4',3),expected['positions']) and np.array_equal(read('indices.u32','<u4',1).ravel(),expected['indices'])
 assert np.array_equal(read('uv0.f32','<f4',2),expected['uv0'].astype('f2').astype('f4'))
 assert np.max(abs(read('normals.f32','<f4',3)-expected['normals']))<.008
 assert np.all(read('weights.u16','<u2',8)[:,0]==255) and np.all(read('weights.u16','<u2',8)[:,1:]==0) and np.all(read('joints.u16','<u2',8)==0)
 assert j['used_bones']==[0] and np.all(read('triangle-materials.u16','<u2',1)==0)
 baseline_meta=json.loads((a.reference.parent/'metadata.json').read_text());source_meta=next(x for x in baseline_meta if x['chunk_id']=='cd809abc483f179000000001');oldmi='/Game/_BuzzMod/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Buz_Apparel01';newmi='/Game/_BzWing0/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Wng_Apparel01';assert m['imported_packages']==[newmi if value==oldmi else value for value in source_meta['imported_packages']], 'Non-material external dependency changed'
 material=resolve(m,j['materials'][0]['package_index']);assert material=='/Game/_BzWing0/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Wng_Apparel01'
 # Actual serialized self package summary and top-level exported UObject name, not directory-only identity.
 b=(raw/m['chunk_id']).read_bytes();s=struct.unpack_from('<15I',b);nm,_=names(b,60);package=nm[s[2]&0x3fffffff];assert s[3]==0;mesh_names=[]
 for at in range(s[8],s[9],72):
  idx,num=struct.unpack_from('<II',b,at+16);outer=struct.unpack_from('<Q',b,at+24)[0]
  if outer==0xffffffffffffffff:assert num==0;mesh_names.append(nm[idx&0x3fffffff])
 assert mesh_names==['SK_Male_Teen_01']
 # Independently reconstruct affine atlas mapping from original per-face material UVs.
 z=np.load(root/f'atlas-{state}-v1/Buzz-atlas-SKINNED.npz');src=np.load(root/f'export-v2/{state.title()}/Buzz-geometry-SKINNED.npz');ar=json.loads((root/f'atlas-{state}-v1/atlas-report.json').read_text());uv=np.empty_like(z['uv0']);coverage=np.zeros(len(uv),bool)
 for record in ar['materials']:
  ids=np.unique(z['indices'][z['source_materials']==record['material_slot']]);old=z['source_vertices'][ids];source=src['uv0'][old];lo,hi=np.array(record['source_uv_bounds']);x,y,w,h=record['atlas_cell'];g=record['gutter'];uv[ids]=np.c_[(x+g+(source[:,0]-lo[0])/(hi[0]-lo[0])*(w-2*g))/4096,(y+g+(hi[1]-source[:,1])/(hi[1]-lo[1])*(h-2*g))/4096];coverage[ids]=True
 assert coverage.all() and np.max(abs(uv-z['uv0']))<1e-6
 reports.append({'state':state,'vertices':n,'triangles':328,'asset':package+'.'+mesh_names[0],'material':material,'native_positions_indices_weights_UVs':'Exact intended encoding','230_bone_reference_exact':True,'all_external_skeleton_physics_game_dependencies_exact_baseline':True,'atlas_UVs_independently_reconstructed':True})
mi=next(m for m in meta if m['path'].endswith('MI_Character_Male01_Wng_Apparel01.uasset'));b=(raw/mi['chunk_id']).read_bytes();s=struct.unpack_from('<15I',b);needle=struct.pack('<I',4)+b'\x00\x07\x00\x07';hits=[i for i in range(s[1],s[1]+600) if b[i:i+8]==needle];assert len(hits)==1;q=hits[0]+4;bindings=[]
for k in range(4):
 assert b[q:q+4]==b'\x00\x07\x00\x07';name,num=struct.unpack_from('<II',b,q+4);assert num==0;index,tex=struct.unpack_from('<ii',b,q+13);assert index==-1;bindings.append({'parameter':mi['name_map'][name],'texture':resolve(mi,tex)});q+=37
assert [x['parameter'] for x in bindings]==['Albedo','Normal','RMA','SSSMask'];assert all('/_BzWing0/' in x['texture'] for x in bindings)
mips=0
for texture in json.loads((root/'textured-v1/texture-write-report.json').read_text())['textures']:
 leaf=texture['path'].rsplit('/',1)[1][:-7].replace('_Max_','_Wng_');j=json.loads((root/('final-mips-'+leaf)/'texture.json').read_text());assert j['mip_count']==len(texture['mips'])
 for expected,got in zip(texture['mips'],j['mips']):assert all(expected[k]==got[k] for k in ['level','width','height','bytes','sha256']);mips+=1
normal=root/'final-mips-T_Wng_Apparel_01_N'
for record in json.loads((normal/'texture.json').read_text())['mips']:
 data=(normal/f"mip-{record['level']:02}.bin").read_bytes();block=data[:16];assert data==block*(len(data)//16);pixels=np.frombuffer(texture2ddecoder.decode_bc5(block,4,4),dtype='u1').reshape(4,4,4)[:,:,[2,1]];assert np.all(pixels==128)
decoded=np.frombuffer(texture2ddecoder.decode_bc3((root/'final-mips-T_Wng_Apparel_01_C/mip-00.bin').read_bytes(),4096,4096),dtype='u1').reshape(4096,4096,4)[:,:,[2,1,0,3]];atlas=np.asarray(Image.open(root/'atlas-deployed-v1/Buzz-basecolor-atlas.png'));mae=float(np.mean(abs(decoded[:,:,:3].astype(float)-atlas[:,:,:3])));assert mae<5;Image.fromarray(decoded).save(root/'final-decoded-wing-atlas.png')
assert all('/_Augusta/' not in m['path'] and '/_BuzzMod/' not in m['path'] for m in meta)
r={'status':'PASS_OFFLINE_ONLY','meshes':reports,'material_bindings':bindings,'private_packages':len(meta),'texture_mips_readback_hash_checked':mips,'independent_BC3_mean_absolute_error':mae,'flat_normal_map_all_mips':'RG128 constant; no stripe regression','game_body_or_BoPeep_packages_overridden':False,'runtime':'Not yet tested in Windows','retoc_legacy_assets_converted':7};a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

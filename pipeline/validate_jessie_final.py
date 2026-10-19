#!/usr/bin/env python3
"""Validate final native CUE readbacks, private MI links and independent BC decode."""
import argparse,json,struct,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
import texture2ddecoder
p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',type=Path);p.add_argument('reference',type=Path);p.add_argument('new_report',type=Path);p.add_argument('--source-geometry',type=Path);a=p.parse_args();root=a.stage;assert not a.new_report.exists()
meta=json.loads((root/'final-metadata.json').read_text());by_path={'/Game/'+m['path'].split('/Content/',1)[1][:-7]:m for m in meta};raw=root/'final-unpacked/chunks'
def resolve(m,index):
 assert index<0;b=(raw/m['chunk_id']).read_bytes();s=struct.unpack_from('<15I',b);v=struct.unpack_from('<Q',b,s[7]+(-index-1)*8)[0];assert v>>62==2;v&=(1<<62)-1;pkg=m['imported_packages'][v>>32];h=struct.unpack_from('<Q',b,s[6]+(v&0xffffffff)*8)[0]
 if pkg in by_path:
  target=(raw/by_path[pkg]['chunk_id']).read_bytes();ts=struct.unpack_from('<15I',target);assert h in [struct.unpack_from('<Q',target,i+56)[0] for i in range(ts[8],ts[9],72)]
 return pkg
expected=np.load(root/'native-buffers/expected.npz');manifest=json.loads((root/'native-buffers/manifest.json').read_text());refs=json.loads(a.reference.read_text())['meshes'];fresh=json.loads((root/'final-skeletons.json').read_text())['meshes']
original_meta=json.loads((root.parent/'hoops-stock-normalized/metadata.json').read_text())
for mesh in fresh:
 original=next(x for x in refs if x['package']==mesh['package']);assert mesh['bones']==original['bones']
weights=expected['quantized_weights'];joints=np.zeros_like(expected['local_joints'],dtype='u2')
for section in manifest['sections']:
 x,y=section['vertex_start'],section['vertex_start']+section['vertices'];palette=np.array(section['palette']);joints[x:y]=np.where(weights[x:y]>0,palette[expected['local_joints'][x:y]],0)
mesh_reports=[]
for i,m in enumerate([m for m in meta if '/Player_Female02/' in m['path']]):
 d=root/f'final-mesh-readback-{i}';j=json.loads((d/'mesh.json').read_text());n=len(expected['positions']);read=lambda name,t,shape:np.fromfile(d/name,dtype=t).reshape(shape)
 payload=(raw/m['chunk_id']).read_bytes();blocks=[payload[x['start']:x['end']] for x in j['lods']]
 assert len(blocks)==4 and all(block==blocks[0] for block in blocks)
 if '/Hair/' in m['path']:
  assert (j['vertices'],j['triangles'],j['skeleton_bones'])==(3,1,12)
  assert np.all(read('positions.f32','<f4',(3,3))==0)
  assert np.all(read('joints.u16','<u2',(3,8))==0)
  assert np.all(read('weights.u16','<u2',(3,8))[:,0]==255)
  continue
 assert (j['vertices'],j['triangles'],j['skeleton_bones'])==(n,8757,189)
 assert np.array_equal(read('positions.f32','<f4',(n,3)),expected['positions'].astype('f4'))
 assert np.array_equal(read('indices.u32','<u4',(-1,)),expected['indices'])
 assert np.array_equal(read('weights.u16','<u2',(n,8)),weights) and np.array_equal(read('joints.u16','<u2',(n,8)),joints)
 assert np.array_equal(read('uv0.f32','<f4',(n,2)),expected['uv0'].astype('f2').astype('f4'))
 assert np.max(abs(read('normals.f32','<f4',(n,3))-expected['normals']))<.008
 assert np.array_equal(read('colors.rgba8','u1',(n,4)),expected['colors'])
 assert np.all(read('triangle-materials.u16','<u2',(-1,))==0) and j['required_bones']==list(range(189))
 assert all(all(j['sections'][k][key]==value for key,value in sec.items()) for k,sec in enumerate(manifest['sections']))
 original=next(x for x in original_meta if x['chunk_id']==m['chunk_id'])
 changed=[(old,new) for old,new in zip(original['imported_packages'],m['imported_packages']) if old!=new]
 assert len(changed)==1 and '/Player_Female02/Textures/' in changed[0][0] and '/_Jessie0/' in changed[0][1]
 # Every LOD has been read by CUE and must be byte-identical to LOD0.
 payload=(raw/m['chunk_id']).read_bytes();blocks=[payload[x['start']:x['end']] for x in j['lods']]
 assert len(blocks)==4 and all(block==blocks[0] for block in blocks)
 assert all(x['vertices']==n and x['triangles']==8757 for x in j['lods'])
 material=resolve(m,j['materials'][0]['package_index']);assert '/_Jessie0/' in material
 mesh_reports.append({'mesh':m['path'],'vertices':n,'triangles':8757,'LOD_positions_weights_joints_indices_colors_materials_UVs':'exact intended encoding','skeleton':'189 original recovered bones and rest transforms exact','material':material})
mi=next(m for m in meta if m['path'].endswith('MI_Character_Male01_Jes_Apparel01.uasset'));b=(raw/mi['chunk_id']).read_bytes();s=struct.unpack_from('<15I',b);needle=struct.pack('<I',4)+b'\x00\x07\x00\x07';offsets=[i for i in range(s[1],s[1]+600) if b[i:i+8]==needle];assert len(offsets)==1;q=offsets[0]+4;bindings=[]
for k in range(4):
 assert b[q:q+4]==b'\x00\x07\x00\x07';name,num=struct.unpack_from('<II',b,q+4);assoc=b[q+12];idx,tex=struct.unpack_from('<ii',b,q+13);assert num==0 and assoc==2 and idx==-1
 bindings.append({'parameter':mi['name_map'][name],'texture':resolve(mi,tex),'serialized_offset':q,'structure':'Unversioned TextureParameterValue fragment(3), ParameterInfo fragment(3), FName, association, index, FPackageIndex, GUID'});q+=37
assert [b['parameter'] for b in bindings]==['Albedo','Normal','RMA','SSSMask'];assert all('/_Jessie0/' in b['texture'] for b in bindings);assert bindings[0]['texture'].endswith('T_Jes_Apparel_01_C')
assert '/Game/_Augusta/Art/Characters/Materials/MM_Character' in mi['imported_packages']
assert all('/_Jessie0/' in m['path'] for m in meta if '/Textures/' in m['path'])
# Independent conversion readback of the actual final container, including cached
# original MI shader payload and each native stream. All legacy payloads exact.
legacy_matches=0
for m in meta:
 payload=(raw/m['chunk_id']).read_bytes();header=struct.unpack_from('<I',payload,4)[0]
 legacy=root/'final-readback-legacy'/m['path'].replace('../../../','');legacy=legacy.with_suffix('.uexp')
 assert legacy.read_bytes()==payload[header:];legacy_matches+=1
for cid,path in json.loads((root/'final-unpacked/manifest.json').read_text())['chunk_paths'].items():
 if path.endswith('.ubulk'):
  assert (raw/cid).read_bytes()==(root/'final-readback-legacy'/path.replace('../../../','')).read_bytes();legacy_matches+=1
original_mi=(root.parent.parent/'stock-max-stage/chunks/0cfec9856be41dcc00000001').read_bytes();original_header=struct.unpack_from('<I',original_mi,4)[0]
cloned_mi=(raw/mi['chunk_id']).read_bytes();cloned_header=struct.unpack_from('<I',cloned_mi,4)[0]
assert original_mi[original_header:]==cloned_mi[cloned_header:]
texture_report=json.loads((root/'textured/texture-write-report.json').read_text());mips=0
for t in texture_report['textures']:
 leaf=Path(t['path']).stem.replace('T_Max','T_Jes');d=root/('final-mips-'+leaf);j=json.loads((d/'texture.json').read_text());assert j['mip_count']==len(t['mips']) and j['pixel_format']==t['format']
 for e,got in zip(t['mips'],j['mips']):assert all(e[k]==got[k] for k in ['level','width','height','bytes','sha256']);mips+=1
# Independently verify the flat BC5 normal's PIXELS, not merely encoded hashes.
normal_dir=root/'final-mips-T_Jes_Apparel_01_N'
for record in json.loads((normal_dir/'texture.json').read_text())['mips']:
 payload=(normal_dir/f"mip-{record['level']:02}.bin").read_bytes();block=payload[:16]
 assert payload==block*(len(payload)//16),'Normal map is not constant block-by-block'
 normal_rg=np.frombuffer(texture2ddecoder.decode_bc5(block,4,4),dtype='u1').reshape(4,4,4)[:,:,[2,1]]
 assert np.all(normal_rg==128),'Flat-normal regression: alternating channels/columns'
# Independent BC decoder returns BGRA; explicitly convert to RGBA.
d=root/'final-mips-T_Jes_Apparel_01_C';decoded=np.frombuffer(texture2ddecoder.decode_bc3((d/'mip-00.bin').read_bytes(),4096,4096),dtype='u1').reshape(4096,4096,4)[:,:,[2,1,0,3]];atlas=np.asarray(Image.open(root.parent/'atlas-v1/Jessie-basecolor-atlas.png').convert('RGBA'));mae=float(np.mean(abs(decoded[:,:,:3].astype(float)-atlas[:,:,:3])));assert mae<5 and np.all(decoded[:,:,3]==255)
Image.fromarray(decoded).save(root/'final-decoded-atlas.png')
# The single source sheet needs only V reversal, no atlas cell packing.
src=np.load(a.source_geometry or root.parent/'geometry-v1/Jessie-geometry-SKINNED.npz')
assert np.array_equal(expected['uv0'],src['uv0'][expected['source_vertices']])
assert np.all((src['uv0']>=-1e-5)&(src['uv0']<=1+1e-5))
report={'status':'passed_offline','mesh_readbacks':mesh_reports,'material_texture_bindings':bindings,'material_parent':'Original MM_Character; cached MI shader/native payload preserved byte-exact','flat_BC5_normal_pixels_all_mips':'independently decoded RG128 constant; no alternating columns','private_texture_and_MI_paths':True,'original_game_texture_or_MI_paths_overridden':False,'legacy_export_and_bulk_payloads_roundtrip_exact':legacy_matches,'texture_mips_read_by_CUE4Parse_and_hash_checked':mips,'independent_BC3_RGBA_mean_absolute_error':mae,'atlas_UVs':'Body sheet plus temporary eye region; explicit V reversal and exact independent CUE half-float UV readback','physics':'Original Hoops game physics/skeleton/animation references preserved; no replacements bundled','native_bone_binding':'No native bone/rest transform edits','runtime':'NOT TESTED: user Windows gameplay test required','limitations':['One opaque character material; eyes/face share simplified suit shading','Atlas downsampling and distant mip color bleed possible','Flat normal map, temporary matte RMA and black SSS','Original voices/portrait remain; no new facial animation','Hat and braid follow head; no cloth or braid physics; original source preserved','No input, movement, collision capsule or gliding mechanic changes']}
a.new_report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','texture_mips_read_by_CUE4Parse_and_hash_checked','independent_BC3_RGBA_mean_absolute_error']}))

#!/usr/bin/env python3
"""Validate final native CUE readbacks, private MI links and independent BC decode."""
import argparse,json,struct,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
import texture2ddecoder
p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',type=Path);p.add_argument('reference',type=Path);p.add_argument('new_report',type=Path);a=p.parse_args();root=a.stage;assert not a.new_report.exists()
meta=json.loads((root/'final-metadata.json').read_text());by_path={'/Game/'+m['path'].split('/Content/',1)[1][:-7]:m for m in meta};raw=root/'final-unpacked/chunks'
def resolve(m,index):
 assert index<0;b=(raw/m['chunk_id']).read_bytes();s=struct.unpack_from('<15I',b);v=struct.unpack_from('<Q',b,s[7]+(-index-1)*8)[0];assert v>>62==2;v&=(1<<62)-1;pkg=m['imported_packages'][v>>32];h=struct.unpack_from('<Q',b,s[6]+(v&0xffffffff)*8)[0]
 if pkg in by_path:
  target=(raw/by_path[pkg]['chunk_id']).read_bytes();ts=struct.unpack_from('<15I',target);assert h in [struct.unpack_from('<Q',target,i+56)[0] for i in range(ts[8],ts[9],72)]
 return pkg
expected=np.load(root/'native-buffers/expected.npz');manifest=json.loads((root/'native-buffers/manifest.json').read_text());refs=json.loads(a.reference.read_text())['meshes'][0]['bones'];fresh=json.loads((root/'final-skeletons.json').read_text())['meshes'];assert all(s['bones']==refs for s in fresh)
weights=expected['quantized_weights'];joints=np.zeros_like(expected['local_joints'],dtype='u2')
for section in manifest['sections']:
 x,y=section['vertex_start'],section['vertex_start']+section['vertices'];palette=np.array(section['palette']);joints[x:y]=np.where(weights[x:y]>0,palette[expected['local_joints'][x:y]],0)
mesh_reports=[]
for i,m in enumerate([m for m in meta if m['path'].endswith(('SK_Male_Teen_01.uasset','SK_Male_Teen_01_w_BackPack.uasset'))]):
 d=root/f'final-mesh-readback-{i}';j=json.loads((d/'mesh.json').read_text());n=len(expected['positions']);read=lambda name,t,shape:np.fromfile(d/name,dtype=t).reshape(shape)
 assert (j['vertices'],j['triangles'],j['skeleton_bones'])==(n,20124,230)
 assert np.array_equal(read('positions.f32','<f4',(n,3)),expected['positions'].astype('f4'))
 assert np.array_equal(read('indices.u32','<u4',(-1,)),expected['indices'])
 assert np.array_equal(read('weights.u16','<u2',(n,8)),weights) and np.array_equal(read('joints.u16','<u2',(n,8)),joints)
 assert np.array_equal(read('uv0.f32','<f4',(n,2)),expected['uv0'].astype('f2').astype('f4'))
 assert np.max(abs(read('normals.f32','<f4',(n,3))-expected['normals']))<.008
 assert np.array_equal(read('colors.rgba8','u1',(n,4)),expected['colors'])
 assert np.all(read('triangle-materials.u16','<u2',(-1,))==0) and len(j['sections'])==1 and j['required_bones']==list(range(230))
 assert all(all(j['sections'][k][key]==value for key,value in sec.items()) for k,sec in enumerate(manifest['sections']))
 original=next(x for x in json.loads((root.parent/'reports/commander-packages.json').read_text()) if x['chunk_id']==m['chunk_id'])
 expected_imports=[v.replace('/_Augusta/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Max_Apparel01','/_BuzzMod/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Buz_Apparel01') for v in original['imported_packages']]
 assert m['imported_packages']==expected_imports,'Unrelated original game dependency changed'
 material=resolve(m,j['materials'][0]['package_index']);assert '/_BuzzMod/' in material
 mesh_reports.append({'mesh':m['path'],'vertices':n,'triangles':20124,'LOD_positions_weights_joints_indices_colors_materials_UVs':'exact intended encoding','skeleton':'230 original recovered bones and rest transforms exact','material':material})
mi=next(m for m in meta if m['path'].endswith('MI_Character_Male01_Buz_Apparel01.uasset'));b=(raw/mi['chunk_id']).read_bytes();s=struct.unpack_from('<15I',b);needle=struct.pack('<I',4)+b'\x00\x07\x00\x07';offsets=[i for i in range(s[1],s[1]+600) if b[i:i+8]==needle];assert len(offsets)==1;q=offsets[0]+4;bindings=[]
for k in range(4):
 assert b[q:q+4]==b'\x00\x07\x00\x07';name,num=struct.unpack_from('<II',b,q+4);assoc=b[q+12];idx,tex=struct.unpack_from('<ii',b,q+13);assert num==0 and assoc==2 and idx==-1
 bindings.append({'parameter':mi['name_map'][name],'texture':resolve(mi,tex),'serialized_offset':q,'structure':'Unversioned TextureParameterValue fragment(3), ParameterInfo fragment(3), FName, association, index, FPackageIndex, GUID'});q+=37
assert [b['parameter'] for b in bindings]==['Albedo','Normal','RMA','SSSMask'];assert all('/_BuzzMod/' in b['texture'] for b in bindings);assert bindings[0]['texture'].endswith('T_Buz_Apparel_01_C')
assert '/Game/_Augusta/Art/Characters/Materials/MM_Character' in mi['imported_packages']
assert all('/_BuzzMod/' in m['path'] for m in meta if '/Textures/' in m['path'])
# Independent conversion readback of the actual final container, including cached
# original MI shader payload and each native stream. All legacy payloads exact.
legacy_matches=0
for f in (root/'final-legacy').rglob('*'):
 if f.suffix not in ['.uexp','.ubulk']:continue
 assert f.read_bytes()==(root/'final-readback-legacy'/f.relative_to(root/'final-legacy')).read_bytes();legacy_matches+=1
original_mi=next((root/'stock-mi-legacy-v3').rglob('*.uexp'));cloned_mi=next((root/'final-readback-legacy').rglob('MI_*.uexp'));assert original_mi.read_bytes()==cloned_mi.read_bytes()
texture_report=json.loads((root/'textured/texture-write-report.json').read_text());mips=0
for t in texture_report['textures']:
 leaf=Path(t['path']).stem.replace('T_Max','T_Buz');d=root/('final-mips-'+leaf);j=json.loads((d/'texture.json').read_text());assert j['mip_count']==len(t['mips']) and j['pixel_format']==t['format']
 for e,got in zip(t['mips'],j['mips']):assert all(e[k]==got[k] for k in ['level','width','height','bytes','sha256']);mips+=1
# Independent BC decoder returns BGRA; explicitly convert to RGBA.
d=root/'final-mips-T_Buz_Apparel_01_C';decoded=np.frombuffer(texture2ddecoder.decode_bc3((d/'mip-00.bin').read_bytes(),4096,4096),dtype='u1').reshape(4096,4096,4)[:,:,[2,1,0,3]];atlas=np.asarray(Image.open(root/'atlas/Buzz-basecolor-atlas.png').convert('RGBA'));mae=float(np.mean(abs(decoded[:,:,:3].astype(float)-atlas[:,:,:3])));assert mae<5 and np.all(decoded[:,:,3]==255)
Image.fromarray(decoded).save(root/'final-decoded-atlas.png')
# Independently recover expected atlas affine UVs from original per-face source
# assignments, rather than accepting the writer's UV stream as its own oracle.
z=np.load(root/'atlas/Buzz-atlas-SKINNED.npz');src=np.load(root.parent/'rig-stage/skinned-export-v9/Buzz-geometry-SKINNED.npz');ar=json.loads((root/'atlas/atlas-report.json').read_text());uv_expected=np.empty_like(z['uv0']);uv_checked=np.zeros(len(z['uv0']),bool)
for record in ar['materials']:
 vertices=np.unique(z['indices'][z['source_materials']==record['material_slot']]);old=z['source_vertices'][vertices];uv=src['uv0'][old];lo,hi=np.array(record['source_uv_bounds']);repeat=hi-lo;x,y,w,h=record['atlas_cell'];g=record['gutter'];uv_expected[vertices]=np.c_[(x+g+(uv[:,0]-lo[0])/repeat[0]*(w-2*g))/4096,(y+g+(hi[1]-uv[:,1])/repeat[1]*(h-2*g))/4096];uv_checked[vertices]=True
assert uv_checked.all() and np.max(abs(uv_expected-z['uv0']))<1e-6
report={'status':'passed_offline','mesh_readbacks':mesh_reports,'material_texture_bindings':bindings,'material_parent':'Original MM_Character; cached MI shader/native payload preserved byte-exact','private_texture_and_MI_paths':True,'original_game_texture_or_MI_paths_overridden':False,'legacy_export_and_bulk_payloads_roundtrip_exact':legacy_matches,'texture_mips_read_by_CUE4Parse_and_hash_checked':mips,'independent_BC3_RGBA_mean_absolute_error':mae,'atlas_UVs':'Independent affine reconstruction, source repeat bounds, PNG V orientation and final native half-float readback passed','physics':'Existing Commander101 custom physics preserved, not stock; targeted assessment complete','pinky':'No unsupported bind changes; existing baseline preserved after focused diagnostic','runtime':'NOT TESTED: user Windows gameplay test required','limitations':['One opaque character material; eyes/face share simplified suit shading','Atlas downsampling and distant mip color bleed possible','Flat normal map, temporary matte RMA and black SSS','Original voices/portrait remain; no new facial animation','Extended wing panels omitted; backpack retained; original six panels preserved in authoring project','No input, movement, collision capsule or gliding mechanic changes']}
a.new_report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','texture_mips_read_by_CUE4Parse_and_hash_checked','independent_BC3_RGBA_mean_absolute_error']}))

#!/usr/bin/env python3
"""Compare independent CUE4Parse full-LOD exports and retoc Zen header readback."""
import json,hashlib,struct,sys,re
from pathlib import Path
import numpy as np
buffers,cooked,package,reader_root,zen,source,reference,output=map(Path,sys.argv[1:]);assert not output.exists()
m=json.loads((buffers/'manifest.json').read_text());e=np.load(buffers/'expected.npz');w=json.loads((cooked/'write-report.json').read_text());ref=json.loads(reference.read_text());fresh=json.loads((cooked/'reference-skeletons.json').read_text());assert all(a['bones']==ref['meshes'][0]['bones'] for a in fresh['meshes'])
local=e['local_joints'];weights=e['quantized_weights'];globalj=np.zeros_like(local,dtype='u2');mats=[]
for s in m['sections']:
 a,b=s['vertex_start'],s['vertex_start']+s['vertices'];palette=np.array(s['palette'],dtype='u2');globalj[a:b]=np.where(weights[a:b]>0,palette[local[a:b]],0);mats.extend([s['material']]*s['triangles'])
results=[]
for i,p in enumerate(w['packages']):
 r=Path(str(reader_root)+f'-{i}');j=json.loads((r/'mesh.json').read_text());n=len(e['positions'])
 read=lambda name,t,shape:np.fromfile(r/name,dtype=t).reshape(shape)
 assert j['skeleton_bones']==230 and j['vertices']==n and j['triangles']==m['triangles']
 assert np.array_equal(read('positions.f32','<f4',(n,3)),e['positions'].astype('f4'))
 assert np.array_equal(read('indices.u32','<u4',(-1,)),e['indices'])
 assert np.array_equal(read('uv0.f32','<f4',(n,2)),e['uv0'].astype('f2').astype('f4'))
 normal_error=float(np.max(np.abs(read('normals.f32','<f4',(n,3))-e['normals'])));assert normal_error<.008
 assert np.array_equal(read('weights.u16','<u2',(n,8)),weights)
 assert np.array_equal(read('joints.u16','<u2',(n,8)),globalj)
 assert np.array_equal(read('triangle-materials.u16','<u2',(-1,)),mats)
 assert np.array_equal(read('colors.rgba8','u1',(n,4)),e['colors'])
 assert j['required_bones']==list(range(230)) and j['active_bones']==w['active_bones']
 assert all(all(got[k]==s[k] for k in s) for got,s in zip(j['sections'],m['sections'])) and len(j['sections'])==len(m['sections'])
 assert j['remaining_native_tail_bytes']==100 and j['lod_start']==p['lod_start'] and j['lod_end']==p['lod_end']
 b=j['imported_bounds'];actual=[*b['origin'],*b['extent'],b['radius']];assert np.max(np.abs(np.array(actual)-w['imported_bounds_origin_extent_radius_cm']))<2e-5
 chunk=(package/'unpacked/chunks'/p['chunk']).read_bytes();assert hashlib.sha256(chunk).hexdigest()==p['output_sha256']==j['source_sha256']
 header_size=struct.unpack_from('<I',chunk,4)[0];assert header_size+struct.unpack_from('<q',chunk,p['bulk_serial_offset_field'])[0]==p['lod_end']+4
 name='SK_Male_Teen_01' if i==0 else 'SK_Male_Teen_01_w_BackPack';text=(zen/(name+'.header.txt')).read_text()
 assert f'cooked_serial_size: {p["new_export_size"]},' in text and f'serial_offset: {p["new_bulk_serial_offset"]},' in text
 results.append({'chunk':p['chunk'],'full_LOD_CUE4Parse_readback':'passed','retoc_Zen_export_and_bulk_offset_readback':'passed','positions_indices_material_sections_colors_global_joint_ids_integer_weights':'exact','uvs':'Exact after intended half-float conversion','packed_normal_max_component_error':normal_error,'required_and_active_bones':'exact','native_skeleton_and_rest_transforms':'exact','imported_bounds_max_error_cm':float(np.max(np.abs(np.array(actual)-w['imported_bounds_origin_extent_radius_cm']))),'output_sha256':p['output_sha256']})
changed=set(p['chunk'] for p in w['packages']);unchanged=0
for f in (source/'chunks').iterdir():
 if f.name.endswith('00000006'):continue
 if f.name not in changed:assert f.read_bytes()==(package/'unpacked/chunks'/f.name).read_bytes();unchanged+=1
rep=json.loads((package/'repackage-validation.json').read_text());assert rep['chunks_verified']==26 and rep['packages_recognized']==17 and rep['all_reextracted_chunk_hashes_match_staged']
report={'status':'passed_offline','vertices':m['output_vertices'],'triangles':m['triangles'],'render_sections':len(m['sections']),'skeleton_bones':230,'active_bones':len(w['active_bones']),'unchanged_non_header_non_mesh_chunks':unchanged,'originals_modified':False,'package_roundtrip':rep,'mesh_readbacks':results,'material_limit':'Unreal material imports remain Commander101. Eight Buzz texture/material slots are verified in Blender only; no finished textured or in-game-validated Buzz mod claim.','game_test':'NOT RUN'}
output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','vertices','triangles','render_sections','active_bones']}))

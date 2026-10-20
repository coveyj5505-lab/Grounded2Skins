"""Verify changed native meshes against intended shape, with unchanged FP split and other assets."""
import argparse,json,struct,hashlib
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('baseline',type=Path);p.add_argument('report',type=Path);a=p.parse_args();root=a.stage;check=root/'final-check-v6';raw=check/'final-unpacked/chunks';source=a.baseline/'package/unpacked/chunks';expected=np.load(root/'buffers-v5/expected.npz');inputmesh=np.load(root/'geometry-fp-v5.npz');newsource=np.load(root/'geometry-v5/BoPeep-geometry-SKINNED.npz');oldinput=np.load(a.baseline/'geometry.npz');oldsource=np.load('/workspace/mod-work/bopeep-v2-stage/geometry-v3/BoPeep-geometry-SKINNED.npz');manifest=json.loads((root/'buffers-v5/manifest.json').read_text());meta=json.loads((check/'final-metadata.json').read_text());bones=json.loads((check/'final-skeletons.json').read_text())['meshes'];oldbones=json.loads((a.baseline/'skeletons.json').read_text())['meshes']
assert np.array_equal(newsource['source_vertices'][newsource['indices']],oldsource['source_vertices'][oldsource['indices']][:6415])
assert np.array_equal(inputmesh['materials'],oldinput['materials'][:6415])
assert np.array_equal(newsource['uv0'][newsource['indices']],oldsource['uv0'][oldsource['indices']][:6415])
assert np.array_equal(newsource['weights'][newsource['indices']],oldsource['weights'][oldsource['indices']][:6415]) and np.array_equal(newsource['joints'][newsource['indices']],oldsource['joints'][oldsource['indices']][:6415])
reports=[]
for i,m in enumerate(x for x in meta if '/Player_Female01/' in x['path']):
 if not m['path'].endswith(('SK_Female_Teen_01.uasset','SK_Female_Teen_01_w_BackPack.uasset')):continue
 # Readback index follows all seven Female01 native meshes, not only the two bodies.
 directory=check/f'final-mesh-readback-{i}';j=json.loads((directory/'mesh.json').read_text());n=manifest['output_vertices'];read=lambda name,t,c:np.fromfile(directory/name,dtype=t).reshape(-1,c)
 assert (j['vertices'],j['triangles'],j['skeleton_bones'],j['lod_count'])==(n,6415,192,4)
 assert np.array_equal(read('positions.f32','<f4',3),expected['positions']) and np.array_equal(read('indices.u32','<u4',1).ravel(),expected['indices'])
 assert np.array_equal(read('uv0.f32','<f4',2),expected['uv0'].astype('f2').astype('f4'))
 assert np.array_equal(read('weights.u16','<u2',8),expected['quantized_weights'])
 assert np.max(abs(read('normals.f32','<f4',3)-expected['normals']))<.008
 assert set(read('triangle-materials.u16','<u2',1).ravel())=={0,3} and np.array_equal(read('triangle-materials.u16','<u2',1).ravel(),inputmesh['materials'][expected['source_triangles']])
 assert j['materials'][0]['package_index']==j['materials'][3]['package_index']
 cid=m['chunk_id'];blob=(raw/cid).read_bytes();blocks=[blob[x['start']:x['end']] for x in j['lods']];assert len(blocks)==4 and all(x==blocks[0] for x in blocks)
 sk=next(x for x in bones if x['chunk_sha256']==m['sha256']);old=next(x for x in oldbones if x['package']==sk['package']);assert sk['bones']==old['bones']
 original=(source/cid).read_bytes();assert blob[sk['offset']:sk['end']]==original[old['offset']:old['end']]
 legacy=check/'final-readback-legacy'/m['path'].replace('../../../','');assert legacy.with_suffix('.uexp').read_bytes()==blob[struct.unpack_from('<I',blob,4)[0]:]
 reports.append({'chunk':cid,'vertices':n,'triangles':6415,'lods':4,'positions_indices_weights_UVs_exact':True,'original_192_bone_table_exact':True,'head_slot3_body_slot0_private_material_preserved':True})
assert len(reports)==2
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir() if not p.name.endswith('00000006')};after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in raw.iterdir() if not p.name.endswith('00000006')};assert before.keys()==after.keys();changed=sorted(k for k in before if before[k]!=after[k]);assert changed==sorted(x['chunk'] for x in reports)
r={'status':'PASS_OFFLINE_ONLY','meshes':reports,'source_to_cooked':'New intended geometry verified; no added cooking distortion','source_cape_plate':'Disconnected56-vertex44-triangle helper plate excluded; retained in Blender','retained_triangles_UVs_weights_joint_ids_and_FP_assignments_exact':True,'only_changed_chunks':changed,'other_texture_material_hair_shader_chunks_byte_exact':len(before)-2,'animations_physics_camera_or_skeleton_changed':False,'runtime':'NOT TESTED; hunched native idle/sitting stance still requires gameplay comparison'};a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

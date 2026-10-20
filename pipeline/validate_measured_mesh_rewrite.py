"""Validate fresh packaged CUE4Parse reads, including every inline LOD and tail.

Works with the existing readback scripts; never treats container verification as
proof of runtime UObject loading or animation compatibility.
"""
import argparse,json,struct,hashlib
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser()
for name in ['baseline_raw','baseline_skeletons','check','buffers','profiles','report']:p.add_argument(name,type=Path)
a=p.parse_args();raw=a.check/'final-unpacked/chunks';meta=json.loads((a.check/'final-metadata.json').read_text());refs=json.loads((a.check/'final-skeletons.json').read_text())['meshes'];oldrefs=json.loads(a.baseline_skeletons.read_text())['meshes'];expected=np.load(a.buffers/'expected.npz');manifest=json.loads((a.buffers/'manifest.json').read_text());profiles=json.loads(a.profiles.read_text());reports=[]
for profile in profiles:
 cid=profile['chunk'];b=(raw/cid).read_bytes();sha=hashlib.sha256(b).hexdigest();dirs=[d for d in a.check.glob('final-mesh-readback-*') if d.is_dir() and json.loads((d/'mesh.json').read_text())['source_sha256']==sha];assert len(dirs)==1;d=dirs[0];j=json.loads((d/'mesh.json').read_text());read=lambda n,t,c:np.fromfile(d/n,dtype=t).reshape(-1,c)
 assert j['vertices']==manifest['output_vertices'] and j['triangles']==manifest['triangles'];assert np.array_equal(read('positions.f32','<f4',3),expected['positions']);assert np.array_equal(read('indices.u32','<u4',1).ravel(),expected['indices']);assert np.array_equal(read('uv0.f32','<f4',2),expected['uv0'].astype('f2').astype('f4'));assert np.array_equal(read('weights.u16','<u2',8),expected['quantized_weights']);assert np.max(abs(read('normals.f32','<f4',3)-expected['normals']))<.008
 # Resolve palette-local encoded slots back to global joints via sections.
 globalj=read('joints.u16','<u2',8);mapped=np.zeros_like(globalj)
 for sec in manifest['sections']:
  ids=slice(sec['vertex_start'],sec['vertex_start']+sec['vertices']);mapped[ids]=np.asarray(sec['palette'],dtype='u2')[expected['local_joints'][ids]]
 mask=expected['quantized_weights']>0;assert np.array_equal(globalj[mask],mapped[mask]);assert np.array_equal(read('colors.rgba8','u1',4),expected['colors'])
 static=(a.buffers/'static-vertices.bin').read_bytes();assert b.count(static)==profile['lod_count']
 assert j['materials']==profile['materials'];assert j['skeleton_bones']==profile['skeleton_bones'];assert j['lod_count']==profile['lod_count'];blocks=[b[x['start']:x['end']] for x in j['lods']];assert len(blocks)==profile['lod_count'] and all(v==blocks[0] for v in blocks)
 newref=next(r for r in refs if r['chunk_sha256']==sha);oldref=next(r for r in oldrefs if r['chunk_sha256']==profile['source_sha256']);assert newref['bones']==oldref['bones'];old=(a.baseline_raw/'chunks'/cid).read_bytes();assert b[newref['offset']:newref['end']]==old[oldref['offset']:oldref['end']];assert b[j['material_start']:j['lod_start']]==old[profile['material_start']:profile['lod_start']]
 m=next(m for m in meta if m['chunk_id']==cid);legacy=a.check/'final-readback-legacy'/m['path'].replace('../../../','');assert legacy.with_suffix('.uexp').read_bytes()==b[struct.unpack_from('<I',b,4)[0]:];reports.append({'chunk':cid,'vertices':j['vertices'],'triangles':j['triangles'],'lods':j['lod_count'],'fresh_positions_indices_UVs_weights_joints_exact':True,'normals_quantization_tolerance':.008,'original_materials_and_reference_bones_exact':True,'legacy_payload_exact':True})
before={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (a.baseline_raw/'chunks').iterdir() if not f.name.endswith('00000006')};after={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in raw.iterdir() if not f.name.endswith('00000006')};assert before.keys()==after.keys();changed=[c for c in before if before[c]!=after[c]];assert sorted(changed)==sorted(p['chunk'] for p in profiles)
r={'status':'PASS_OFFLINE_ONLY','meshes':reports,'only_changed_chunks':changed,'other_chunks_byte_exact':len(before)-len(changed),'runtime':'PENDING Windows; no UObject runtime load or animation claim'};a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

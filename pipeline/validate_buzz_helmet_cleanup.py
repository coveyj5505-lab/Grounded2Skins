"""Independent cooked read-back against retained baseline triangle corners."""
import argparse,json,hashlib,struct
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('stage',type=Path);a=p.parse_args();base=a.baseline;stage=a.stage;candidate=stage/'candidate-v1';check=stage/'final-check-v1'
oldexp=np.load(base/'buffers/expected.npz');newexp=np.load(candidate/'buffers/expected.npz');mapping=np.load(candidate/'retained-map.npz');oldsort=np.argsort(oldexp['source_triangles']);newsort=np.argsort(newexp['source_triangles']);retained=mapping['triangles'];assert len(retained)==19788
read=lambda folder,file,dtype,cols:np.fromfile(folder/file,dtype=dtype).reshape(-1,cols)
reports=[];oldrefs=json.loads((base/'skeletons.json').read_text())['meshes'];newrefs=json.loads((check/'final-skeletons.json').read_text())['meshes'];oldmeta=json.loads((base/'metadata.json').read_text());newmeta=json.loads((check/'final-metadata.json').read_text())
for i,cid in enumerate(['cd809abc483f179000000001','8021448bfc8c514500000001']):
 old=base/('readback-'+cid);raw=(check/'final-unpacked/chunks'/cid).read_bytes();sha=hashlib.sha256(raw).hexdigest();matches=[d for d in check.glob('final-mesh-readback-*') if d.is_dir() and json.loads((d/'mesh.json').read_text())['source_sha256']==sha];assert len(matches)==1;new=matches[0];j=json.loads((new/'mesh.json').read_text());assert j['triangles']==19788 and j['skeleton_bones']==230 and j['lod_count']==1
 oi=read(old,'indices.u32','<u4',3)[oldsort][retained];ni=read(new,'indices.u32','<u4',3)[newsort]
 for file,dtype,cols in [('positions.f32','<f4',3),('uv0.f32','<f4',2),('normals.f32','<f4',3),('joints.u16','<u2',8),('weights.u16','<u2',8),('colors.rgba8','u1',4)]:
  assert np.array_equal(read(old,file,dtype,cols)[oi],read(new,file,dtype,cols)[ni]),file
 def frames(folder,count):
  b=(folder/'static-vertices.bin').read_bytes();return np.frombuffer(b[26:26+count*8],dtype='u1').reshape(count,8)
 assert np.array_equal(frames(base/'buffers',len(oldexp['positions']))[oi],frames(candidate/'buffers',len(newexp['positions']))[ni])
 assert np.array_equal(read(old,'triangle-materials.u16','<u2',1)[oldsort][retained],read(new,'triangle-materials.u16','<u2',1)[newsort])
 assert next(r for r in oldrefs if r['chunk_sha256']==json.loads((old/'mesh.json').read_text())['source_sha256'])['bones']==next(r for r in newrefs if r['chunk_sha256']==sha)['bones'];assert next(m for m in oldmeta if m['chunk_id']==cid)['imported_packages']==next(m for m in newmeta if m['chunk_id']==cid)['imported_packages']
 oldj=json.loads((old/'mesh.json').read_text());assert oldj['materials']==j['materials']
 path=next(m for m in newmeta if m['chunk_id']==cid)['path'];legacy=check/'final-readback-legacy'/path.replace('../../../','');assert legacy.with_suffix('.uexp').read_bytes()==raw[struct.unpack_from('<I',raw,4)[0]:]
 reports.append({'chunk':cid,'retained_triangle_corner_positions_UVs_normals_weights_colors_packed_tangents_exact':True,'head_body_section_assignments_exact':True,'skeleton_materials_imports_exact':True,'legacy_payload_exact':True})
before=base/'package/unpacked/chunks';after=check/'final-unpacked/chunks';changed=[];unchanged=0
for f in before.iterdir():
 if f.name.endswith('00000006'):continue
 if f.read_bytes()!=(after/f.name).read_bytes():changed.append(f.name)
 else:unchanged+=1
assert sorted(changed)==sorted(r['chunk'] for r in reports)
r={'status':'PASS_OFFLINE_ONLY','removed_components':[15,55],'removed_triangles':336,'retained_triangles':19788,'meshes':reports,'other_chunks_byte_exact':unchanged,'arm_rig_unchanged':True,'runtime':'Windows pending; this removes fittings, not an arm-proportion correction'};(stage/'validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

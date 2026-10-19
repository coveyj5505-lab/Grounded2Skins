"""Compare final independent V2 read-back against the preserved V1 release."""
import json,hashlib,argparse
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('new_report',type=Path);a=p.parse_args();r=a.stage;assert not a.new_report.exists();old=r.parent/'jessie-stage';newcheck=r/'final-check-v4';oldcheck=old/'final-check-v2'
def hashes(raw):return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (raw/'chunks').iterdir() if not p.name.endswith('00000006')}
x=hashes(old/'raw-v2');y=hashes(r/'raw-v4');assert set(x)==set(y);body={'911395b71b48cf1a00000001','32e8e66fd14d9e8d00000001'};unchanged=[k for k in x if k not in body];assert len(unchanged)==13 and all(x[k]==y[k] for k in unchanged)
e=np.load(r/'fit-v4/expected.npz');mask=e['accepted_head'];newg=np.load(r/'geometry-v4/Jessie-geometry-SKINNED.npz');oldg=np.load(old/'geometry-v1/Jessie-geometry-SKINNED.npz');newc=np.load(r/'buffers-v4/expected.npz');oldc=np.load(old/'buffers-v1/expected.npz');new_ids=newg['source_vertices'][newc['source_vertices']];old_ids=oldg['source_vertices'][oldc['source_vertices']]
def native_dir(check,cid):return next(d for d in check.glob('final-mesh-readback-*') if d.is_dir() and json.loads((d/'mesh.json').read_text())['source'].endswith(cid))
results=[]
for cid in sorted(body):
 nd=native_dir(newcheck,cid);od=native_dir(oldcheck,cid)
 def read(d,name,dtype,shape):return np.fromfile(d/name,dtype=dtype).reshape(shape)
 npos=read(nd,'positions.f32','<f4',(-1,3));opos=read(od,'positions.f32','<f4',(-1,3));nj=read(nd,'joints.u16','<u2',(-1,8));oj=read(od,'joints.u16','<u2',(-1,8));nw=read(nd,'weights.u16','<u2',(-1,8));ow=read(od,'weights.u16','<u2',(-1,8));lookup={}
 for i,source in enumerate(old_ids):lookup[int(source)]=(opos[i],sorted((int(j),int(w)) for j,w in zip(oj[i],ow[i]) if w>0))
 count=0
 for i,source in enumerate(new_ids):
  if not mask[source]:continue
  pos,weights=lookup[int(source)];assert np.array_equal(npos[i],pos);assert sorted((int(j),int(w)) for j,w in zip(nj[i],nw[i]) if w>0)==weights;count+=1
 ni=read(nd,'indices.u32','<u4',(-1,3));oi=read(od,'indices.u32','<u4',(-1,3));assert np.array_equal(new_ids[ni],old_ids[oi]);nuv=read(nd,'uv0.f32','<f4',(-1,2));ouv=read(od,'uv0.f32','<f4',(-1,2));assert np.array_equal(nuv[ni],ouv[oi])
 results.append({'chunk':cid,'accepted_head_render_vertices_exact_position_and_raw_weights':count,'all_triangle_source_indices_and_UVs_exact_V1':True})
# Ensure existing verified character releases remain byte-exact.
repo=Path('/workspace/Grounded2Skins');preserved={}
for name,sha in [('Jessie-Hoops-First-Test.zip','f0a1f7ceeef3eed51d96d5b2dfa7016739b245e5ae17f01440e57bf4b0b8689a'),('BoPeep-Willow-First-Test.zip','1839b9e660a274f75a929a5387bd3daa7bba75dbceff92224b6e66fa578b5422'),('Buzz-Lightyear-V2-Proportions-Test.zip','42b0c50091bc7a5fb97a37ff91ff06da9c0f3f5eac5dd04fba241520aa837250')]:
 actual=hashlib.sha256((repo/name).read_bytes()).hexdigest();assert actual==sha;preserved[name]=actual
report={'only_body_and_backpack_chunks_modified':True,'unrelated_nonheader_chunks_unchanged':len(unchanged),'material_MI_all_texture_mips_hair_chunks_byte_exact_V1':True,'independent_cooked_comparison':results,'preserved_release_SHA256':preserved,'runtime':'V2 NOT TESTED in Grounded2'};a.new_report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

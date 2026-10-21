"""Compare final UE5.7 container readback to authored buffers and frozen baseline."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('stage',type=Path);p.add_argument('check',type=Path);p.add_argument('baseline',type=Path);p.add_argument('--other-updated-chunks',nargs='*',default=[]);a=p.parse_args();e=np.load(a.stage/'buffers/expected.npz');data=np.load(a.stage/'geometry.npz');profiles=json.load(open(a.stage/'profiles.json'));meta=json.load(open(a.check/'final-metadata.json'));refs=json.load(open(a.check/'final-skeletons.json'))['meshes'];raw=a.check/'final-unpacked/chunks';old=a.baseline/'final-unpacked/chunks';changed={r['chunk'] for r in profiles};others=set(a.other_updated_chunks);assert not changed&others;assert all(len(c)==24 and c.endswith('00000001') and (old/c).is_file() for c in others);checks=[]
for item in profiles:
 cid=item['chunk'];m=next(m for m in meta if m['chunk_id']==cid);d=next(d for d in a.check.glob('final-mesh-readback-*') if d.is_dir() and json.load(open(d/'mesh.json'))['source_sha256']==m['sha256']);v=json.load(open(d/'mesh.json'));b=(raw/cid).read_bytes();assert v['lod_count']==4 and len(b)-v['all_lods_end']==112
 assert np.array_equal(np.fromfile(d/'positions.f32',dtype='<f4').reshape(-1,3),e['positions'])
 assert np.array_equal(np.fromfile(d/'indices.u32',dtype='<u4').reshape(-1,3),e['indices'].reshape(-1,3))
 assert np.array_equal(np.fromfile(d/'uv0.f32',dtype='<f4').reshape(-1,2),e['uv0'].astype('f2').astype('f4'))
 expected_joints=np.zeros_like(e['local_joints']);sections=json.load(open(a.stage/'buffers/manifest.json'))['sections']
 for sec in sections:
  lo=sec['vertex_start'];hi=lo+sec['vertices'];expected_joints[lo:hi]=np.asarray(sec['palette'])[e['local_joints'][lo:hi]]
 joint=np.fromfile(d/'joints.u16',dtype='<u2').reshape(-1,8);weight=np.fromfile(d/'weights.f32',dtype='<f4').reshape(-1,8);q=e['quantized_weights'].astype('f4')/255;assert np.max(abs(weight-q))<1e-6;assert np.array_equal(joint[q>0],expected_joints[q>0])
 for field in ['normals','tangents']:
  fn=d/(field+'.f32')
  if fn.exists():assert np.max(abs(np.fromfile(fn,dtype='<f4').reshape(-1,3)-e[field]))<.009
 assert np.array_equal(np.fromfile(d/'colors.rgba8',dtype='u1').reshape(-1,4),e['colors'])
 materials=np.fromfile(d/'triangle-materials.u16',dtype='<u2');assert np.array_equal(materials,data['materials'][e['source_triangles']])
 expected_ref=next(r for r in json.load(open(a.baseline/'final-skeletons.json'))['meshes'] if r['chunk_sha256']==item['source_sha256'])['bones'];actual_ref=next(r for r in refs if r['chunk_sha256']==m['sha256']);assert actual_ref['bones']==expected_ref
 assert v['materials']==item['materials'];assert len({b[l['start']:l['end']] for l in v['lods']})==1
 checks.append({'chunk':cid,'vertices':v['vertices'],'triangles':v['triangles'],'four_LODs_exact':True,'author_buffers_exact_except_quantized_frames':True,'reference_and_material_records_exact':True,'FP_section_triangle_materials_exact':True})
unchanged=[]
for f in raw.iterdir():
 if f.name in changed|others or f.name.endswith('00000006'):continue
 assert (old/f.name).exists() and f.read_bytes()==(old/f.name).read_bytes(),f.name;unchanged.append(f.name)
report={'character':a.name,'status':'PASS_OFFLINE_WINDOWS_PENDING','meshes':checks,'all_other_chunks_exact':unchanged,'other_meshes_require_separate_validation':sorted(others),'textures_materials_hair_helpers_unchanged':True,'source_frames_limit':.009,'runtime':'No Windows claim; independent render review still required'};(a.stage/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',a.name,len(checks),'meshes;',len(unchanged),'unchanged chunks')

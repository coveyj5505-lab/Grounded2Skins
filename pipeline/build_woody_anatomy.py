"""Cook an isolated pelvis correction on the accepted FP-section baseline."""
import argparse,json,shutil
from pathlib import Path
import numpy as np
from native_buffers import encode,skeleton_signature
from write_pete_lods import write
p=argparse.ArgumentParser();p.add_argument('author',type=Path);p.add_argument('export',type=Path);p.add_argument('out',type=Path);a=p.parse_args();out=a.out;out.mkdir(exist_ok=False);root=Path('/workspace/mod-work');base=root/'first-person-stage/woody-v1';old=dict(np.load(root/'woody-polish-next/export-v2/Woody-geometry-SKINNED.npz'));new=dict(np.load(a.export/'Woody-geometry-SKINNED.npz'));fp=dict(np.load(base/'geometry.npz'));ti=old['source_vertices'][old['indices']];tn=new['source_vertices'][new['indices']];assert np.array_equal(ti,tn);assert np.array_equal(ti,fp['source_vertices'][fp['indices']]);c=np.load(a.author/'correction.npz');unchanged=~np.isin(ti,c['changed']);wunchanged=~np.isin(ti,c['weight_changed'])
assert np.array_equal(old['positions'][old['indices']][unchanged],new['positions'][new['indices']][unchanged])
for k in ['uv0','colors']:assert np.array_equal(old[k][old['indices']],new[k][new['indices']]),k
# Export sorts each weight row, so compare actual bone mass rather than slots.
def masses(d):
 result=np.zeros((len(d['positions']),188),dtype='f4')
 for j in range(8):np.add.at(result,(np.arange(len(result)),d['joints'][:,j]),d['weights'][:,j])
 return result[d['indices']]
assert np.max(abs(masses(old)[wunchanged]-masses(new)[wunchanged]))<2e-7
assert str(old['skeleton_signature'])==str(new['skeleton_signature']);new['materials']=fp['materials'].copy();new['material_count']=fp['material_count'].copy();np.savez_compressed(out/'geometry.npz',**new);shutil.copyfile(base/'reference.json',out/'reference.json');encode(new,skeleton_signature(out/'reference.json'),out/'buffers');profiles=[]
for cid in ['b0baaf49556b7e2200000001','69965555c28c2aae00000001']:
 q=json.loads((base/('readback-'+cid)/'mesh.json').read_text());q.update(chunk=cid,path=next(m['path'] for m in json.loads((base/'metadata.json').read_text()) if m['chunk_id']==cid),sha256=q['source_sha256']);profiles.append(q)
(out/'profiles.json').write_text(json.dumps(profiles,indent=2)+'\n');write(base/'raw',out/'profiles.json',out/'buffers',out/'reference.json',out/'rewritten');shutil.copytree(base/'raw',out/'raw')
for q in profiles:shutil.copyfile(out/'rewritten/chunks'/q['chunk'],out/'raw/chunks'/q['chunk'])
r={'status':'BUILT_READBACK_PENDING','meshes_changed':2,'source_triangles':len(ti),'FP_head_slot_3_triangle_mask_exact':True,'source_topology_UVs_colors_exact':True,'unchanged_position_corners':int(unchanged.sum()),'unchanged_weight_corners':int(wunchanged.sum()),'native_skeleton_reference_unchanged':True,'textures_materials_and_other_19_chunks_not_rebuilt':True,'runtime':'NOT TESTED'};(out/'build-report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

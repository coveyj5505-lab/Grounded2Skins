"""Build only Woody's main/backpack meshes on the accepted FP-section baseline."""
import json,sys,shutil,hashlib
from pathlib import Path
import numpy as np
from native_buffers import encode,skeleton_signature
from write_pete_lods import write
out=Path(sys.argv[1]);out.mkdir(exist_ok=False);root=Path('/workspace/mod-work');base=root/'first-person-stage/woody-v1';author=root/'woody-polish-next/authoring-v2';old=dict(np.load(base/'geometry.npz'));new=dict(np.load(root/'woody-polish-next/export-v2/Woody-geometry-SKINNED.npz'));tri_old=old['source_vertices'][old['indices']];tri_new=new['source_vertices'][new['indices']];assert np.array_equal(tri_old,tri_new);cor=np.load(author/'correction.npz');changed=cor['changed'];wchanged=cor['weight_changed'];mask=~np.isin(tri_old,changed);wmask=~np.isin(tri_old,wchanged)
for k in ['positions','uv0','weights','joints','colors']:
 a=old[k][old['indices']];b=new[k][new['indices']];sel=wmask if k=='joints' else mask if k=='positions' else np.ones(mask.shape,bool);assert np.array_equal(a[sel],b[sel]),k
assert str(old['skeleton_signature'])==str(new['skeleton_signature'])
# Split into the same existing Pete head/body sections; no new material refs.
new['materials']=old['materials'].copy();new['material_count']=old['material_count'].copy();np.savez_compressed(out/'geometry.npz',**new);shutil.copyfile(base/'reference.json',out/'reference.json');manifest=encode(new,skeleton_signature(out/'reference.json'),out/'buffers')
profiles=[]
for cid in ['b0baaf49556b7e2200000001','69965555c28c2aae00000001']:
 p=json.loads((base/('readback-'+cid)/'mesh.json').read_text());p.update(chunk=cid,path=next(m['path'] for m in json.loads((base/'metadata.json').read_text()) if m['chunk_id']==cid),sha256=p['source_sha256']);profiles.append(p)
(out/'profiles.json').write_text(json.dumps(profiles,indent=2)+'\n');write(base/'raw',out/'profiles.json',out/'buffers',out/'reference.json',out/'rewritten')
shutil.copytree(base/'raw',out/'raw')
for p in profiles:shutil.copyfile(out/'rewritten/chunks'/p['chunk'],out/'raw/chunks'/p['chunk'])
r={'status':'BUILT_INDEPENDENT_READBACK_PENDING','main_and_backpack_meshes_changed':2,'source_triangles':len(tri_old),'head_slot_3_triangle_mask_exact':True,'head_triangles':int(np.count_nonzero(new['materials']==3)),'all_original_triangle_source_IDs_and_UVs_exact':True,'unchanged_position_corner_count':int(mask.sum()),'unchanged_weight_corner_count':int(wmask.sum()),'all_other_positive_weight_bone_assignments_exact':True,'textures_and_materials_not_rebuilt':True,'frozen_combined_v03_not_modified':True,'runtime':'NOT TESTED'};(out/'build-report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

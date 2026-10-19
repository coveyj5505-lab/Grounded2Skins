"""Fresh Blender reopen: verify native rest, preserved source, weights and FK LBS."""
import bpy,json,sys
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
import numpy as np

args=sys.argv[sys.argv.index('--')+1:];stage=Path(args[0]);pose_dir=Path(args[1]) if len(args)>1 else stage/'poses-v3';report_path=Path(args[2]) if len(args)>2 else stage/'rig-v3/fresh-validation.json';o=bpy.data.objects['Woody_Skinned'];arm=o.find_armature()
ref=json.loads((stage/'pete-stock-normalized/rig-reference.json').read_text())['meshes'][0]['bones']
assert [g.name for g in o.vertex_groups]==[b['name'] for b in ref]
assert [b.name for b in arm.data.bones]==[b['name'] for b in ref]
B=Matrix.Diagonal((.01,-.01,.01,1));world=[];expected=[]
for b in ref:
 x,y,z,w=b['rotation_xyzw'];m=Matrix.LocRotScale(Vector(b['translation_cm']),Quaternion((w,x,y,z)),Vector(b['scale_xyz']));world.append(m if b['parent']<0 else world[b['parent']]@m);expected.append(np.asarray(B@world[-1]@B.inverted()))
rest=np.asarray([b.matrix_local[:] for b in arm.data.bones]);rest_error=float(np.max(np.abs(rest-expected)));# Blender edit-bone roll reconstruction rounds unit rotation bases; keep
# the measured error and independently bound head translations in meters.
assert rest_error<2e-5
position_error=float(np.max(np.abs(rest[:,:3,3]-np.asarray(expected)[:,:3,3])));assert position_error<2e-6
for i,b in enumerate(ref):assert (arm.data.bones[i].parent.name if arm.data.bones[i].parent else None)==(ref[b['parent']]['name'] if b['parent']>=0 else None)
points=np.asarray([v.co[:] for v in o.data.vertices]);assert len(points)==32379 and np.isfinite(points).all()
source=json.loads((stage/'inspection/inspection.json').read_text());preserved=[]
for item in source['objects']:
 if item['type']!='MESH':continue
 src=bpy.data.objects[item['name']];data=np.load(stage/'inspection'/(src.name.replace('/','_')+'-source.npz'));src.data.calc_loop_triangles()
 assert np.array_equal(np.asarray([v.co[:] for v in src.data.vertices]),data['positions'])
 assert np.array_equal(np.asarray([t.vertices[:] for t in src.data.loop_triangles]),data['indices'])
 assert np.array_equal(np.asarray(src.matrix_world),np.asarray(item['matrix_world']))
 preserved.append(src.name)
for v in o.data.vertices:assert 0<len(v.groups)<=8 and all(g.group<188 and g.weight>0 for g in v.groups) and abs(sum(g.weight for g in v.groups)-1)<1e-5
o.data.calc_loop_triangles();assert len(o.data.loop_triangles)==54801
o.data.calc_tangents(uvmap=o.data.uv_layers.active.name)
assert all(np.isfinite(l.tangent[:]).all() and np.isfinite(l.normal[:]).all() for l in o.data.loops)
images=[i for i in bpy.data.images if i.source=='FILE'];assert len(images)>=12 and all(i.packed_file for i in images)
poses=[];inv=np.linalg.inv(rest);p4=np.column_stack((points,np.ones(len(points))))
for path in sorted(pose_dir.glob('*.npz')):
 saved=np.load(path);mat=saved['bone_world'];deform=mat@inv;pred=np.zeros_like(points)
 for v in o.data.vertices:
  for g in v.groups:pred[v.index]+=(deform[g.group]@p4[v.index])[:3]*g.weight
 error=float(np.max(np.abs(pred-saved['positions'])));assert error<2e-5,(path,error)
 poses.append({'pose':path.stem,'independent_numpy_LBS_max_error_m':error})
assert len(poses)==6
report={'fresh_reopen':True,'native_bones':188,'native_rest_max_error':rest_error,'native_rest_translation_max_error_m':position_error,'native_parent_hierarchy_exact':True,'vertex_group_order_exact':True,'vertices':len(points),'triangles':len(o.data.loop_triangles),'normalized_weights':True,'source_meshes_geometry_triangles_transforms_preserved':preserved,'packed_original_maps':len(images),'finite_normals_tangents':True,'poses':poses,'limitations':['Synthetic FK checks, not game animation clips','Eye/mouth material remains provisional','No Woody cooked package or Windows test yet']}
report_path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

"""Independent saved-scene, cape isolation, finger stress and FK skin checks."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
import numpy as np
root=Path(sys.argv[sys.argv.index('--')+1]);o=bpy.data.objects['BoPeep_Skinned'];old=bpy.data.objects['BoPeep_V1_Preserved'];arm=o.find_armature();source=bpy.data.objects['BoPeep_Body'];crook=bpy.data.objects['Crook_Preserved_NOT_EXPORTED'];expected=np.load(root/'fit-v1/expected.npz');regions=expected['regions'];p=np.asarray([v.co[:] for v in o.data.vertices]);assert np.array_equal(p,expected['positions'].astype('f4'))
assert [g.name for g in o.vertex_groups]==[b.name for b in arm.data.bones] and len(arm.data.bones)==192
for v in o.data.vertices:assert 0<len(v.groups)<=8 and abs(sum(g.weight for g in v.groups)-1)<1e-5
rows=lambda obj:[{g.group:g.weight for g in v.groups if g.weight>0} for v in obj.data.vertices]
weights=rows(o);oldweights=rows(old);unchanged=np.flatnonzero(regions=='unchanged');assert np.array_equal(p[unchanged],np.asarray([v.co[:] for v in old.data.vertices])[unchanged]);assert all(weights[i]==oldweights[i] for i in unchanged)
for obj in [o,old]:obj.data.calc_loop_triangles()
assert np.array_equal(np.asarray([t.vertices[:] for t in o.data.loop_triangles]),np.asarray([t.vertices[:] for t in old.data.loop_triangles]))
assert np.array_equal(np.asarray([v.uv[:] for v in o.data.uv_layers.active.data]),np.asarray([v.uv[:] for v in old.data.uv_layers.active.data]))
assert list(o.data.materials)==list(old.data.materials)
cape=np.flatnonzero(regions=='cape');assert len(cape)==936
assert all({o.vertex_groups[g.group].name:g.weight for g in o.data.vertices[i].groups}=={'spine3_JNT':1.} for i in cape)
assert crook.hide_render and len(crook.data.vertices)==391
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE')
# Verify preserved crook against its exact original FBX partition, not just
# object presence. Enable the excluded source only in this unsaved validator.
bpy.data.collections['Source_Original_UNTOUCHED'].hide_viewport=False;bpy.data.objects['bo_peep_geo'].hide_set(False);bpy.context.view_layer.update()
original=bpy.data.objects['bo_peep_geo'];original.data.calc_loop_triangles();crook.data.calc_loop_triangles();partition=json.loads((root.parent/'bopeep-stage/body-and-crook-v2/prop-preservation.json').read_text())['objects']['Crook_Preserved_NOT_EXPORTED'];ids=np.asarray(partition['source_vertex_indices']);original_pos=np.asarray([v.co[:] for v in original.data.vertices]);assert np.array_equal(np.asarray([v.co[:] for v in crook.data.vertices]),original_pos[ids]);assert np.array_equal(np.asarray(crook.matrix_world),np.asarray(original.matrix_world));all_tri=np.asarray([t.vertices[:] for t in original.data.loop_triangles]);mask=np.isin(all_tri,ids).all(1);assert np.array_equal(ids[np.asarray([t.vertices[:] for t in crook.data.loop_triangles])],all_tri[mask]);all_loops=np.asarray([t.loops[:] for t in original.data.loop_triangles]);source_uv=np.asarray([v.uv[:] for v in original.data.uv_layers.active.data]);assert np.array_equal(np.asarray([v.uv[:] for v in crook.data.uv_layers.active.data]),source_uv[all_loops[mask]].reshape(-1,2))
for j,i in enumerate(ids):assert [(g.group,g.weight) for g in crook.data.vertices[j].groups]==[(g.group,g.weight) for g in original.data.vertices[int(i)].groups]
assert list(crook.data.materials)==list(original.data.materials)

rest=np.asarray([b.matrix_local[:] for b in arm.data.bones]);inverse=np.linalg.inv(rest);p4=np.column_stack((p,np.ones(len(p))));pose_reports=[]
for file in sorted((root/'poses-v1').glob('*.npz')):
 d=np.load(file);mat=d['bone_world']@inverse;pred=np.zeros_like(p)
 for i,row in enumerate(weights):
  for j,w in row.items():pred[i]+=(mat[j]@p4[i])[:3]*w
 error=float(np.max(np.abs(pred-d['positions'])));assert error<2e-5;pose_reports.append({'pose':file.stem,'independent_numpy_LBS_max_error_m':error})
assert len(pose_reports)==6
def reset():
 for b in arm.pose.bones:b.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def evaluate():
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();result=np.asarray([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();return result
reset();base=evaluate();finger=np.array([r.startswith('hand_') for r in regions]);stress=[]
for angle in [-75,75]:
 reset()
 for b in arm.pose.bones:
  if b.name.startswith(('LeftHand','RightHand')):b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion((1,0,0),math.radians(angle))
 bpy.context.view_layer.update();q=evaluate();maximum=float(np.max(np.linalg.norm(q[finger]-base[finger],axis=1)));assert maximum<.005;stress.append({'finger_joint_rotation_deg':angle,'max_hand_surface_displacement_m':maximum})
reset()
for name in ['l_upperArm_JNT','r_upperArm_JNT','l_lowerArm_JNT','r_lowerArm_JNT']:
 b=arm.pose.bones[name];b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion((1,0,0),math.radians(100))
bpy.context.view_layer.update();cape_error=float(np.max(abs(evaluate()[cape]-base[cape])));assert cape_error<1e-6
reset();report={'fresh_reopen':True,'bones':192,'vertices':5028,'triangles':len(o.data.loop_triangles),'normalized_weights':True,'unchanged_appearance_outside_masks_vertices':len(unchanged),'unaffected_positions_and_weights_exact':True,'topology_material_UVs_exact_V1':True,'cape_all_936_vertices_rigid_spine3':True,'cape_displacement_under_arm_stress_m':cape_error,'finger_stress':stress,'poses':pose_reports,'preserved_crook_hidden':True,'crook_original_positions_UVs_triangles_materials_weights_world_transform_exact':True,'limits':['Source-shaped predominantly rigid hands; fine finger animation/grips simplified','Cape stiffly follows torso, no cloth collision','Synthetic FK tests are not game clips','Windows test still required']}
(root/'fresh-rig-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

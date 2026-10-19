"""Fresh saved-scene validation plus independent NumPy linear skinning oracle."""
import bpy,json,sys
from pathlib import Path
import numpy as np
expected,skin,poses,report=map(Path,sys.argv[sys.argv.index('--')+1:]);assert not report.exists();e=np.load(expected);s=np.load(skin);o=bpy.data.objects['Jessie_Skinned'];arm=o.find_armature();assert len(arm.data.bones)==189
p=np.asarray([v.co[:] for v in o.data.vertices]);assert np.array_equal(p,e['positions']);assert np.array_equal(np.asarray([u.uv[:] for u in o.data.uv_layers.active.data]),e['loop_uv']);assert np.array_equal(np.asarray([t.vertices[:] for t in o.data.polygons]),e['indices'])
names=[b.name for b in arm.data.bones];ref=json.loads(Path('/workspace/mod-work/jessie-stage/hoops-stock-normalized/rig-reference.json').read_text())['meshes'][0]['bones'];assert names==[b['name'] for b in ref]
actual=np.zeros((4883,189))
for v in o.data.vertices:
 for g in v.groups:actual[v.index,g.group]=g.weight
expect=np.zeros_like(actual)
for slot in range(8):expect[np.arange(4883),s['joints'][:,slot]]+=s['weights'][:,slot]
assert np.max(abs(actual-expect))<1e-7 and np.max(abs(actual.sum(1)-1))<1e-5
leg={i for i,n in enumerate(names) if any(t in n for t in ['UpperLeg','LowerLeg','Foot_JNT','Toes_JNT'])};offset=0;arm_vertices=0
for name in ['park_jessie_ob0_L0','park_jessie_ob3_L0','park_jessie_ob6_L0']:
 source=bpy.data.objects[name]
 for v in source.data.vertices:
  arm_weight=sum(g.weight for g in v.groups if any(t in source.vertex_groups[g.group].name for t in ['UpperArm','UpArmTwist','Forearm','ForeTwist',' Hand','Finger']))
  if arm_weight>.05:assert actual[offset+v.index,list(leg)].sum()==0;arm_vertices+=1
 offset+=len(source.data.vertices)
rest=np.asarray([b.matrix_local[:] for b in arm.data.bones]);inv=np.linalg.inv(rest);hom=np.c_[p,np.ones(len(p))];pose_records=[]
for name in ['rest-front','standing','sitting','sitting-side','running']:
 posed=np.load(poses/(name+'.npz'));delta=posed['bone_world']@inv;predicted=np.zeros((4883,3))
 for bone in np.flatnonzero(actual.sum(0)>0):predicted+=actual[:,bone,None]*(hom@delta[bone].T)[:,:3]
 error=float(np.max(abs(predicted-posed['positions'])));assert error<5e-6,(name,error);pose_records.append({'pose':name,'numpy_vs_Blender_LBS_max_error_m':error})
digit_tests=[]
for angle in [-75,75]:
 for pb in arm.pose.bones:
  pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,np.deg2rad(angle)) if pb.name.startswith(('LeftHand','RightHand')) else (0,0,0)
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();posed=np.asarray([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();movement=float(np.max(np.linalg.norm(posed-p,axis=1)));assert movement<.01;digit_tests.append({'digit_curl_degrees':angle,'max_mesh_displacement_m':movement,'small_residual_wrist_digit_blends_only':True})
assert np.array_equal(p[e['accepted_head']],e['V1_positions'][e['accepted_head']]);assert len([i for i in bpy.data.images if i.source=='FILE' and i.packed_file])==4
r={'fresh_reopen':True,'native_bone_names_order_exact':True,'vertices':4883,'triangles':8757,'normalized_weights_match_saved_arrays':True,'original_V1_head_vertices_exact':int(e['accepted_head'].sum()),'atlas_UVs_exact':True,'arm_vertices_with_explicit_zero_leg_influence':arm_vertices,'independent_LBS':pose_records,'simplified_hand_curl_checks':digit_tests,'textures_packed':4,'runtime':'NOT TESTED; game animations not available for exact playback'};report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)

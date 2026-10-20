"""Offline visual flight-pose candidate only. Never edits released wings/runtime.

Pose the accepted V0.3 body and preserved deployed wings together on original
bones. This demonstrates a target silhouette; no native glide clip is supplied.
"""
import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False);body=bpy.data.objects['Buzz_Skinned'];arm=body.find_armature();assert len(arm.data.bones)==230
rest=np.array([b.matrix_local[:] for b in arm.data.bones]);original_positions=np.array([v.co[:] for v in body.data.vertices]);original_uv=np.array([v.uv[:] for v in body.data.uv_layers.active.data]);weights=[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices]
with bpy.data.libraries.load('/workspace/mod-work/wings-stage/states-v2/Buzz-Wing-States.blend',link=False) as (src,dst):dst.objects=['Wings_Deployed_Display']
wing=dst.objects[0];bpy.context.scene.collection.objects.link(wing);wing.parent=arm;wing.matrix_parent_inverse=Matrix.Identity(4);wing.matrix_basis=Matrix.Identity(4)
for mod in wing.modifiers:
 if mod.type=='ARMATURE':mod.object=arm
assert [g.name for g in wing.vertex_groups]==[b.name for b in arm.data.bones]
for x in bpy.data.objects:
 if x.type=='MESH':x.hide_render=x not in [body,wing]
wing.hide_set(False);wing.hide_render=False
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.render.resolution_x=960;scene.render.resolution_y=650;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard';scene.world.color=(.18,.18,.18)
for x in list(bpy.data.objects):
 if x.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(x,do_unlink=True)
for loc,power in [((3,-4,5),500),((-3,-1,3),350),((1,3,4),350)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.size=4;l.rotation_euler=(Vector((0,0,1))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=3.2
for mat in body.data.materials:
 if mat.use_nodes:
  for n in mat.node_tree.nodes:
   if n.type=='BSDF_PRINCIPLED':n.inputs['Roughness'].default_value=.8;n.inputs['Specular IOR Level'].default_value=.12

def reset():
 for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def rotate(name,degrees):
 p=arm.pose.bones[name];A=p.matrix.translation.copy();p.matrix=Matrix.Translation(A)@Matrix.Rotation(math.radians(degrees),4,'X')@Matrix.Translation(-A)@p.matrix;bpy.context.view_layer.update()
def aim(a,b,d):
 bpy.context.view_layer.update();p=arm.pose.bones[a];A=p.matrix.translation.copy();B=arm.pose.bones[b].matrix.translation.copy();R=(B-A).rotation_difference(Vector(d));p.matrix=Matrix.Translation(A)@R.to_matrix().to_4x4()@Matrix.Translation(-A)@p.matrix;bpy.context.view_layer.update()
def render(name,loc,target):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
reset()
for s,k in [('l',1),('r',-1)]:aim(s+'_upperArm_JNT',s+'_lowerArm_JNT',(k*.15,0,-1));aim(s+'_lowerArm_JNT',s+'_wrist_JNT',(k*.05,-.1,-1))
standing=np.array([p.matrix[:] for p in arm.pose.bones]);render('manual-wings-standing',(3,-5,2),(0,0,1.1))
reset();rotate('Hips_JNT',65);rotate('neck3_JNT',-55)
for s,k in [('l',1),('r',-1)]:
 aim(s+'_upperArm_JNT',s+'_lowerArm_JNT',(k*.38,-1,-.02));aim(s+'_lowerArm_JNT',s+'_wrist_JNT',(k*.04,-1,.08))
flight=np.array([p.matrix[:] for p in arm.pose.bones]);evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh();p=np.array([v.co[:] for v in mesh.vertices]);evaluated.to_mesh_clear();assert np.isfinite(p).all();center=(p.min(0)+p.max(0))/2
render('flight-quarter',(3,-5,3),center);render('flight-side',(5,0,1.8),center)
np.savez_compressed(out/'rest-and-evaluated.npz',rest=rest,bone_names=np.array([b.name for b in arm.data.bones]),source_rest=original_positions,source_evaluated=p)
np.savez_compressed(out/'pose-targets.npz',standing=standing,flight=flight,bone_names=np.array([b.name for b in arm.data.bones]));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Buzz-Flight-Visual-Candidate.blend'),compress=True)
assert np.array_equal(rest,np.array([b.matrix_local[:] for b in arm.data.bones]));assert np.array_equal(original_positions,np.array([v.co[:] for v in body.data.vertices]));assert np.array_equal(original_uv,np.array([v.uv[:] for v in body.data.uv_layers.active.data]));assert weights==[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices]
reset();assert all(np.max(abs(np.array(p.matrix_basis)-np.eye(4)))<1e-6 for p in arm.pose.bones)
report={'status':'OFFLINE_VISUAL_CANDIDATE_ONLY','native_glide_clip_available':False,'body_geometry_UVs_weights_rest_preserved':True,'native_bones':230,'standing_manual_wings_no_flight_pose':True,'flight_body_forward_pitch_degrees':65,'flight_neck_counter_pitch_degrees':55,'arms':'Forward with slight outward clearance','original_wings_reused':True,'landing_reset_verified_offline':True,'runtime_adapter_implemented':False,'released_v03_modified':False,'limitations':['Synthetic pose, not the actual running game glide animation','Runtime cosmetic pose layer, first-person isolation and wing attachment must be validated before shipping','No actor/camera/movement transforms may be used to implement this target']};(out/'candidate-report.json').write_text(json.dumps(report,indent=2)+'\n');print('FLIGHT_CANDIDATE_VALIDATED')

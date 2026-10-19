"""Independent fresh-scene checks and reproducible FK pose comparisons.
Uses requested world-space limb directions, not assumed local Euler axes.
Run on either preserved V1 or V2; no input blend is saved/modified.
"""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False)
o=bpy.data.objects['Woody_Skinned'];arm=o.find_armature();rest={b.name:[list(row) for row in b.matrix_local] for b in arm.data.bones};assert len(rest)==188
assert [g.name for g in o.vertex_groups]==[b.name for b in arm.data.bones]
assert all(g.group<188 for v in o.data.vertices for g in v.groups)
for v in o.data.vertices:assert 0<len(v.groups)<=8 and abs(sum(g.weight for g in v.groups)-1)<1e-5
scene=bpy.context.scene;scene.cycles.samples=10;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=720;scene.render.resolution_y=860;scene.render.resolution_percentage=100;camera=scene.camera;camera.data.ortho_scale=2.65
pose_data=[]
def aim(parent,child,direction):
 bpy.context.view_layer.update();pb=arm.pose.bones[parent];a=pb.matrix.translation.copy();b=arm.pose.bones[child].matrix.translation.copy();current=b-a;rot=current.rotation_difference(Vector(direction));pb.matrix=Matrix.Translation(a)@rot.to_matrix().to_4x4()@Matrix.Translation(-a)@pb.matrix;bpy.context.view_layer.update()
def reset():
 for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def render(name,view):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.asarray([v.co[:] for v in m.vertices]);assert np.isfinite(p).all() and len(p)==32379;ev.to_mesh_clear();pose_data.append({'name':name,'positions_finite':True,'min':p.min(0).tolist(),'max':p.max(0).tolist()})
 np.savez_compressed(out/(name+'.npz'),positions=p,bone_world=np.asarray([pb.matrix[:] for pb in arm.pose.bones]))
 camera.location=view;camera.rotation_euler=(Vector((0,0,1.1))-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
reset();render('rest-front',(0,-5,1.25));render('rest-side',(5,0,1.25))
for short,sign in [('l',1),('r',-1)]:
 aim(f'{short}_upperArm_JNT',f'{short}_lowerArm_JNT',(sign*.12,0,-1));aim(f'{short}_lowerArm_JNT',f'{short}_hand_JNT',(sign*.05,-.12,-1))
render('standing',(0,-5,1.25))
reset()
for short,sign in [('l',1),('r',-1)]:
 aim(f'{short}_UpperLeg_JNT',f'{short}_LowerLeg_JNT',(0,-1,-.05));aim(f'{short}_LowerLeg_JNT',f'{short}_Foot_JNT',(0,.04,-1));aim(f'{short}_upperArm_JNT',f'{short}_lowerArm_JNT',(sign*.12,-.10,-1));aim(f'{short}_lowerArm_JNT',f'{short}_hand_JNT',(sign*.05,-1,.12))
render('sitting',(3,-5,1.8));render('sitting-side',(5,-1,1.6))
reset()
for short,sign in [('l',1),('r',-1)]:
 aim(f'{short}_UpperLeg_JNT',f'{short}_LowerLeg_JNT',(0,-sign*.55,-.84));aim(f'{short}_LowerLeg_JNT',f'{short}_Foot_JNT',(0,sign*.35,-.94));aim(f'{short}_upperArm_JNT',f'{short}_lowerArm_JNT',(sign*.12,sign*.55,-.84));aim(f'{short}_lowerArm_JNT',f'{short}_hand_JNT',(0,-sign*.65,-.76))
render('running',(3,-5,1.8))
assert rest=={b.name:[list(row) for row in b.matrix_local] for b in arm.data.bones}
(out/'validation.json').write_text(json.dumps({'fresh_reopen':True,'bones':188,'vertices':32379,'normalized_weights':True,'native_rest_matrices_unchanged':True,'poses':pose_data,'pose_method':'FK aiming using world-space parent/child joint directions; synthetic, not extracted game clips','gameplay_compatibility':'NOT TESTED'},indent=2)+'\n')

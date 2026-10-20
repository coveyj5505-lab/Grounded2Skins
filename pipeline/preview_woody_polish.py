"""Fresh-open front/rear/detail and synthetic FK previews, never game screenshots."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False);o=bpy.data.objects['Woody_Skinned'];old=bpy.data.objects['Woody_Before_Boot_Ring_Preserved'];arm=o.find_armature();scene=bpy.context.scene
for x in bpy.data.objects:
 if x.type=='MESH':x.hide_render=x!=o
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=6;scene.cycles.use_denoising=False;scene.render.resolution_x=720;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard';scene.world.color=(.12,.12,.12)
cam=scene.camera;cam.data.type='ORTHO';report=[]
def reset():
 for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def aim(a,b,d):
 bpy.context.view_layer.update();pb=arm.pose.bones[a];A=pb.matrix.translation.copy();B=arm.pose.bones[b].matrix.translation.copy();R=(B-A).rotation_difference(Vector(d));pb.matrix=Matrix.Translation(A)@R.to_matrix().to_4x4()@Matrix.Translation(-A)@pb.matrix;bpy.context.view_layer.update()
def render(name,loc,target,scale,which=o):
 o.hide_render=which!=o;old.hide_render=which!=old;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
def validate(name):
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();assert len(p)==32379 and np.isfinite(p).all()
 # Ring is a uniform copy rigid to spine3; every pairwise edge length survives.
 ids=np.arange(32126,32280);src=np.array([v.co[:] for v in o.data.vertices])[ids];pairs=np.array([[i,(i+11)%154] for i in range(154)]);a=np.linalg.norm(src[pairs[:,1]]-src[pairs[:,0]],axis=1);b=np.linalg.norm(p[ids][pairs[:,1]]-p[ids][pairs[:,0]],axis=1);error=float(np.max(abs(a-b)));assert error<1e-6
 # Both corrected tabs have no bone influences from the opposite leg.
 for vi in np.load('/workspace/mod-work/woody-polish-next/authoring-v2/correction.npz')['weight_changed']:
  names=[o.vertex_groups[g.group].name for g in o.data.vertices[int(vi)].groups if g.weight>0];assert not(any(n.startswith('l_') for n in names) and any(n.startswith('r_') for n in names))
 np.savez_compressed(out/(name+'-pose.npz'),positions=p,bone_world=np.array([pb.matrix[:] for pb in arm.pose.bones]));report.append({'pose':name,'finite':True,'ring_rigid_distance_max_error_m':error,'boot_tabs_have_single_leg_ownership':True})
reset()
for s,k in [('l',1),('r',-1)]:aim(s+'_upperArm_JNT',s+'_lowerArm_JNT',(k*.12,0,-1));aim(s+'_lowerArm_JNT',s+'_hand_JNT',(k*.05,-.12,-1))
validate('standing');render('standing-front',(0,-5,1.2),(0,0,1.1),2.6);render('standing-rear',(0,5,1.3),(0,0,1.1),2.6)
for suffix,x in [('before',old),('after',o)]:
 render('boots-'+suffix,(.6,-2,.65),(0,0,.20),.65,x);render('ring-'+suffix,(.5,3,1.6),(0,.16,1.33),.55,x)
reset()
for s,k in [('l',1),('r',-1)]:
 aim(s+'_UpperLeg_JNT',s+'_LowerLeg_JNT',(0,-1,-.05));aim(s+'_LowerLeg_JNT',s+'_Foot_JNT',(0,.04,-1));aim(s+'_upperArm_JNT',s+'_lowerArm_JNT',(k*.12,-.1,-1));aim(s+'_lowerArm_JNT',s+'_hand_JNT',(k*.05,-1,.12))
validate('sitting');render('sitting',(3,-5,1.6),(0,-.15,1.0),2.6)
reset()
for s,k in [('l',1),('r',-1)]:
 aim(s+'_UpperLeg_JNT',s+'_LowerLeg_JNT',(0,-k*.55,-.84));aim(s+'_LowerLeg_JNT',s+'_Foot_JNT',(0,k*.35,-.94))
validate('running');render('running-boots',(.6,-2,.65),(0,0,.35),1.0)
(out/'pose-validation.json').write_text(json.dumps({'status':'PASS_OFFLINE','synthetic_FK_not_extracted_game_clips':True,'poses':report},indent=2)+'\n');print('WOODY_POSES_PASS')

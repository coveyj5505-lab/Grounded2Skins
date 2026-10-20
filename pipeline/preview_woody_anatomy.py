"""Anatomy review: neutral lighting, side/front and seated bench reference."""
import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False);o=bpy.data.objects['Woody_Skinned'];old=bpy.data.objects.get('Woody_Before_PelvisFix_Preserved');arm=o.find_armature();scene=bpy.context.scene
for ob in bpy.data.objects:
 if ob.type=='MESH':ob.hide_render=ob!=o
for ob in list(bpy.data.objects):
 if ob.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(ob,do_unlink=True)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.resolution_x=800;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard';scene.world.color=(.12,.12,.12)
for loc,power in [((3,-4,4),150),((-3,-1,3),100),((0,3,4),130)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.size=4;l.rotation_euler=(Vector((0,0,1.1))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO'
for mat in o.data.materials:
 if mat.use_nodes:
  for n in mat.node_tree.nodes:
   if n.type=='BSDF_PRINCIPLED':n.inputs['Roughness'].default_value=.8;n.inputs['Specular IOR Level'].default_value=.1
bench=[]
for loc,scale in [((0,.045,.94),(.30,.28,.018)),((0,.30,1.22),(.30,.018,.30))]:
 bpy.ops.mesh.primitive_cube_add(size=2,location=loc);q=bpy.context.object;q.scale=scale;bench.append(q);mat=bpy.data.materials.new('Neutral bench reference');mat.diffuse_color=(.09,.18,.24,1);q.data.materials.append(mat);q.hide_render=True
reports=[]
def reset():
 for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def aim(a,b,d):
 bpy.context.view_layer.update();p=arm.pose.bones[a];A=p.matrix.translation.copy();B=arm.pose.bones[b].matrix.translation.copy();R=(B-A).rotation_difference(Vector(d));p.matrix=Matrix.Translation(A)@R.to_matrix().to_4x4()@Matrix.Translation(-A)@p.matrix;bpy.context.view_layer.update()
def render(name,loc,target,scale,which=o):
 o.hide_render=which!=o
 if old:old.hide_render=which!=old
 bpy.context.view_layer.update();ev=which.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();assert np.isfinite(P).all();np.savez_compressed(out/(name+'.npz'),positions=P,bone_world=np.array([p.matrix[:] for p in arm.pose.bones]));cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True);reports.append(name)
reset()
for s,k in [('l',1),('r',-1)]:aim(s+'_upperArm_JNT',s+'_lowerArm_JNT',(k*.12,0,-1));aim(s+'_lowerArm_JNT',s+'_hand_JNT',(k*.05,-.12,-1))
render('standing-front',(0,-5,1.3),(0,0,1.1),2.45);render('standing-side',(5,0,1.3),(0,0,1.1),2.45);render('standing-rear',(0,5,1.3),(0,0,1.1),2.45)
reset()
for s,k in [('l',1),('r',-1)]:
 aim(s+'_UpperLeg_JNT',s+'_LowerLeg_JNT',(0,-1,-.05));aim(s+'_LowerLeg_JNT',s+'_Foot_JNT',(0,.04,-1));aim(s+'_upperArm_JNT',s+'_lowerArm_JNT',(k*.12,-.1,-1));aim(s+'_lowerArm_JNT',s+'_hand_JNT',(k*.05,-1,.12))
for q in bench:q.hide_render=False
render('sitting-side',(5,-.05,1.3),(0,-.08,1.10),2.35);render('sitting-quarter',(3,-5,1.7),(0,-.08,1.1),2.35)
if old:render('sitting-old-comparison',(5,-.05,1.3),(0,-.08,1.10),2.35,old)
for q in bench:q.hide_render=True
reset()
for s,k in [('l',1),('r',-1)]:aim(s+'_UpperLeg_JNT',s+'_LowerLeg_JNT',(0,-k*.55,-.84));aim(s+'_LowerLeg_JNT',s+'_Foot_JNT',(0,k*.35,-.94))
render('running',(3,-5,1.6),(0,0,1.1),2.45)
(out/'scope.json').write_text(json.dumps({'previews':reports,'pose_type':'Synthetic FK; bench is a visual scale reference, not extracted game furniture or animation','runtime':'NOT TESTED'},indent=2)+'\n');print('ANATOMY_PREVIEWS_COMPLETE')

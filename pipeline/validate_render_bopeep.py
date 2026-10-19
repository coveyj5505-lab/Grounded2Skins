"""Fresh-process Bo Peep rest/skin/crook validation and controlled-pose previews."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False)
obj=bpy.data.objects['BoPeep_Skinned'];arm=bpy.data.objects['Grounded2_Willow_192'];src=bpy.data.objects['BoPeep_Body'];crook=bpy.data.objects['Crook_Preserved_NOT_EXPORTED'];assert len(arm.data.bones)==192
assert len(obj.data.vertices)==5028 and len(obj.vertex_groups)==192
assert len(crook.data.vertices)==391 and crook.hide_render
assert [g.name for g in obj.vertex_groups]==[b.name for b in arm.data.bones]
for v in obj.data.vertices:assert abs(sum(g.weight for g in v.groups)-1)<1e-5 and 0<len(v.groups)<=8
assert all(i.packed_file for i in bpy.data.images if i.source=='FILE')
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=720;scene.render.resolution_y=820;scene.render.resolution_percentage=100
scene.world.color=(.35,.35,.35);scene.view_settings.view_transform='Standard'
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=2.55
for loc,power,size in [((3,-4,5),500,4),((-3,-1,3),300,3),((1,3,4),400,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
report=[]
def pose(name,values,view):
 for b in arm.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0)
 for bone,angles in values.items():arm.pose.bones[bone].rotation_euler=tuple(math.radians(v) for v in angles)
 bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.asarray([v.co[:] for v in m.vertices]);assert np.isfinite(p).all();assert len(p)==5028
 report.append({'pose':name,'finite_vertices':len(p),'min':p.min(0).tolist(),'max':p.max(0).tolist(),'synthetic_pose_only':True});ev.to_mesh_clear()
 camera.location=view;camera.rotation_euler=(Vector((0,0,1.05))-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
pose('front',{},(0,-5,1.2));pose('side',{},(5,0,1.2))
pose('sitting',{'l_UpperLeg_JNT':(0,0,-75),'r_UpperLeg_JNT':(0,0,-75),'l_LowerLeg_JNT':(0,0,90),'r_LowerLeg_JNT':(0,0,90),'l_lowerArm_JNT':(0,0,-65),'r_lowerArm_JNT':(0,0,65)},(3,-5,1.8))
pose('arms',{'l_upperArm_JNT':(25,0,25),'r_upperArm_JNT':(-25,0,-25),'l_lowerArm_JNT':(0,0,-65),'r_lowerArm_JNT':(0,0,65),'head_JNT':(0,20,0)},(0,-5,1.3))
(out/'validation.json').write_text(json.dumps({'fresh_blender_reopen':True,'bones':192,'weighted_vertices':5028,'normalized_weights':True,'packed_images':True,'crook_preserved_and_excluded':True,'poses':report,'runtime_test':'NOT RUN'},indent=2)+'\n')

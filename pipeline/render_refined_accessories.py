"""CPU previews from independently reopened candidate scenes; no gameplay claim."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
mode,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);out.mkdir(exist_ok=False);scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=10;scene.cycles.use_denoising=False;scene.render.resolution_x=800;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.world.color=(.15,.15,.15);scene.view_settings.view_transform='Standard';o=bpy.data.objects['BoPeep_Skinned'];arm=o.find_armature()
for ob in bpy.data.objects:
 if ob.type=='MESH':ob.hide_render=ob!=o
for mat in o.data.materials:
 if mat.use_nodes:
  for node in mat.node_tree.nodes:
   if node.type=='BSDF_PRINCIPLED':
    node.inputs['Roughness'].default_value=.8;node.inputs['Specular IOR Level'].default_value=.1
    for link in list(node.inputs['Alpha'].links):mat.node_tree.links.remove(link)
    node.inputs['Alpha'].default_value=1.
for loc,power in [((3,-4,5),450),((-3,4,4),550),((2,1,2),200)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.size=4;l.rotation_euler=(Vector((0,0,1))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam
if mode=='fp':
 for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 o.parent=None;o.location=(.75,-.43,-.32);cam.location=(0,0,0);cam.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP';cam.data.angle=1.57079632679;scene.render.resolution_x=960;scene.render.resolution_y=540;views=[('first-person',None,None)]
else:
 cam.data.type='ORTHO';cam.data.ortho_scale=2.2
 def aim(a,b,d):
  bpy.context.view_layer.update();pb=arm.pose.bones[a];A=pb.matrix.translation.copy();B=arm.pose.bones[b].matrix.translation.copy();rot=(B-A).rotation_difference(Vector(d));pb.matrix=Matrix.Translation(A)@rot.to_matrix().to_4x4()@Matrix.Translation(-A)@pb.matrix;bpy.context.view_layer.update()
 for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 for s,sign in [('l',1),('r',-1)]:aim(s+'_upperArm_JNT',s+'_lowerArm_JNT',(sign*.12,0,-1));aim(s+'_lowerArm_JNT',s+'_hand_JNT',(sign*.05,-.12,-1))
 views=[('rear',(0,5,1.4),(0,0,1.1)),('rear-shoulders',(2,4,1.65),(0,.08,1.4))]
for name,loc,target in views:
 if loc:cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
 if name=='rear-shoulders':cam.data.ortho_scale=.95
 scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'scope.json').write_text(json.dumps({'mode':mode,'Blender_fresh_reopen':True,'runtime':'NOT TESTED','pose':'Controlled preview, not actual animation clip'},indent=2));print('PREVIEWS_SAVED')

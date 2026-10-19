"""CPU-lit authoring previews; synthetic sitting pose, not game animation capture."""
import bpy,sys,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
args=sys.argv[sys.argv.index('--')+1:];source_mode='--source' in args
if source_mode:args.remove('--source')
root,out=map(Path,args);out.mkdir(exist_ok=False)
obj=bpy.data.objects['Buzz_Skinned'];arm=bpy.data.objects['Grounded2_Armature_230']
if source_mode:
 d=np.load(root/'expected.npz');src=np.load(root.parent/'landmarks/source.npz')['positions'][d['source_vertices']]*[-1,-1,1]+[0,-.43,0]
 obj.data.vertices.foreach_set('co',src.ravel());obj.data.normals_split_custom_set_from_vertices([(0.,0.,0.)]*len(src))
 for modifier in obj.modifiers:modifier.show_render=False
for o in bpy.data.objects:
 if o.type=='MESH' and o!=obj:o.hide_render=True
for mat in obj.data.materials:
 if mat.use_nodes:
  for n in mat.node_tree.nodes:
   if n.type=='BSDF_PRINCIPLED':n.inputs['Roughness'].default_value=.75;n.inputs['Specular IOR Level'].default_value=.15
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard';scene.world.color=(.18,.18,.18)
for loc,power,size in [((-3,-4,5),650,4),((3,-2,3),350,4),((0,3,4),450,3)]:
 data=bpy.data.lights.new('Softbox','AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new('Softbox',data);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new('ReviewCamera',cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=2.28
bones=list(arm.data.bones)
views=[('front',[],(0,-4,1.05),(0,0,1.0)),('side',[],(4,0,1.05),(0,0,1.0)),('sitting',[(24,'X',-75),(32,'X',-75),(25,'X',95),(33,'X',95),(59,'Z',-45),(163,'Z',45)],(2.7,-4,2.0),(0,-.15,1.0))]
if source_mode:views=views[:1]
for name,rotations,loc,target in views:
 for b in arm.pose.bones:b.matrix_basis.identity()
 for i,axis,degree in rotations:
  pb=arm.pose.bones[bones[i].name];direction=Vector({'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis]);local=bones[i].matrix_local.to_3x3().inverted()@direction;pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(local,math.radians(degree))
 bpy.context.view_layer.update();cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'scope.txt').write_text('Original source textures under neutral CPU lighting. Synthetic sitting rotations copied from the numerical rig validation; not actual game animation, shader, collision or chair contact. No source file saved or changed.\n')

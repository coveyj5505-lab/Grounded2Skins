"""Save/reopenable arm candidate and controlled standing/bent-arm previews."""
import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(sys.argv[sys.argv.index('--')+1]);o=bpy.data.objects['Buzz_Skinned'];arm=o.find_armature();fit=np.load('/workspace/mod-work/rig-stage/skinned-stowed-v2-proportions/expected.npz');keep=np.where(~np.isin(fit['component'],[15,55]))[0];z=np.load(root/('body-points-clearance.npz' if (root/'body-points-clearance.npz').exists() else 'body-points.npz'));assert len(keep)==len(o.data.vertices)
cooked='--cooked' in sys.argv
old=o.copy();old.data=o.data.copy();old.name='Buzz_Arms_PreRefinement_PRESERVED';bpy.context.scene.collection.objects.link(old);old.hide_render=True;old.hide_set(True)
if not cooked:
 for v,i in zip(o.data.vertices,keep):v.co=z['positions'][i]
 o.data.update();o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(root/('Buzz-Arms-Cooked-Review.blend' if cooked else 'Buzz-Arms-Reviewed.blend')),compress=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.render.resolution_x=600;scene.render.resolution_y=760;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard';scene.world.color=(.2,.2,.2)
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj!=o:obj.hide_render=True
for loc,power in [((3,-4,5),600),((-3,-1,3),400),((1,3,4),400)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.size=4;l.rotation_euler=(Vector((0,0,1))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.3
for mat in o.data.materials:
 if mat.use_nodes:
  for n in mat.node_tree.nodes:
   if n.type=='BSDF_PRINCIPLED':n.inputs['Roughness'].default_value=.8;n.inputs['Specular IOR Level'].default_value=.15

def aim(a,b,d):
 bpy.context.view_layer.update();pb=arm.pose.bones[a];A=pb.matrix.translation.copy();B=arm.pose.bones[b].matrix.translation.copy();rot=(B-A).rotation_difference(Vector(d));pb.matrix=Matrix.Translation(A)@rot.to_matrix().to_4x4()@Matrix.Translation(-A)@pb.matrix;bpy.context.view_layer.update()
def pose(bent=False):
 for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 for s,sign in [('l',1),('r',-1)]:
  aim(s+'_upperArm_JNT',s+'_lowerArm_JNT',(sign*.15,0,-1));aim(s+'_lowerArm_JNT',s+'_wrist_JNT',(sign*.05,-1,.1) if bent else (sign*.05,-.1,-1))
for name,loc,bent in [('standing-front',(0,-5,1.2),False),('standing-side',(5,0,1.2),False),('bent-arms',(3,-5,1.5),True)]:
 pose(bent);cam.location=loc;cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(root/(name+'.png'));bpy.ops.render.render(write_still=True)
print('ARM_PREVIEWS_COMPLETE')

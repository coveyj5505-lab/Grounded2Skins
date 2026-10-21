"""Compare authored buffers on controlled FK poses, not native game clips."""
import bpy,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
out=Path('/tmp/toystory-feedback-v4/previews');out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath='/workspace/mod-work/feedback-v3-source-backup/Buzz.blend');source=bpy.data.objects['Buzz_Skinned'];arm=source.find_armature();names=[g.name for g in source.vertex_groups]
for x in list(bpy.data.objects):
 if x.type=='MESH':x.hide_render=True
 if x.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(x,do_unlink=True)
mat=bpy.data.materials.new('Unchanged native Buzz atlas');mat.use_nodes=True;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load('/workspace/mod-work/ue57-migration/buzz-check-v1/actual-decoded-atlas.png');bs=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.8
objects=[]
for label,path in [('V3','/tmp/toystory-feedback-v3/Buzz-geometry.npz'),('RigidCandidate','/tmp/toystory-feedback-v4/Buzz-rigid-upper-candidate.npz')]:
 z=dict(np.load(path));p=z['positions']*[.01,-.01,.01];tri=z['indices'];m=bpy.data.meshes.new(label);m.from_pydata(p,[],tri);m.update();o=bpy.data.objects.new(label,m);bpy.context.collection.objects.link(o);uv=m.uv_layers.new()
 for f in m.polygons:
  f.use_smooth=True
  for li in f.loop_indices:q=z['uv0'][m.loops[li].vertex_index];uv.data[li].uv=(float(q[0]),float(1-q[1]))
 n=z['normals']*[1,-1,1];n/=np.linalg.norm(n,axis=1,keepdims=True);m.normals_split_custom_set(n[tri].reshape(-1,3).tolist());m.materials.append(mat)
 for name in names:o.vertex_groups.new(name=name)
 for i in range(len(p)):
  for j,w in zip(z['joints'][i],z['weights'][i]):
   if w>0:o.vertex_groups[int(j)].add([i],float(w),'REPLACE')
 mod=o.modifiers.new('Native rig','ARMATURE');mod.object=arm;objects.append(o)
for loc,power in [((3,-4,5),220),((-3,-1,3),160),((1,3,4),160)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.size=4;l.rotation_euler=(Vector((0,0,1.1))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(2,-4,1.6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.15))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.35;s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=4;s.cycles.use_denoising=False;s.render.resolution_x=560;s.render.resolution_y=640;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard';s.world.color=(.16,.16,.16)
def aim(a,b,d):
 bpy.context.view_layer.update();pb=arm.pose.bones[a];A=pb.matrix.translation.copy();B=arm.pose.bones[b].matrix.translation.copy();R=(B-A).rotation_difference(Vector(d));pb.matrix=Matrix.Translation(A)@R.to_matrix().to_4x4()@Matrix.Translation(-A)@pb.matrix
for pose in ['idle','raised','bent']:
 for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 for side,k in [('l',1),('r',-1)]:
  upper={'idle':(k*.12,0,-1),'raised':(k*.25,0,1),'bent':(k*.55,-.45,-.25)}[pose];lower={'idle':(k*.05,-.12,-1),'raised':(k*.1,-.2,1),'bent':(k*.05,-.7,.6)}[pose];aim(side+'_upperArm_JNT',side+'_lowerArm_JNT',upper);aim(side+'_lowerArm_JNT',side+'_wrist_JNT',lower)
 for o in objects:
  for x in objects:x.hide_render=x!=o
  s.render.filepath=str(out/(o.name+'-'+pose+'.png'));bpy.ops.render.render(write_still=True)

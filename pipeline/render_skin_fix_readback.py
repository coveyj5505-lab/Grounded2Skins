"""Render final independently decoded skin buffers on the unchanged authoring rig.
Controlled FK previews, not captured game animations.
"""
import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
name,stage,check,scene_file,baseline=sys.argv[sys.argv.index('--')+1:];root=Path(stage);check=Path(check);baseline=Path(baseline);out=root/'previews';out.mkdir(exist_ok=True);profiles=json.load(open(root/'profiles.json'));cid=profiles[0]['chunk'];meta=json.load(open(check/'final-metadata.json'));entry=next(m for m in meta if m['chunk_id']==cid);d=next(d for d in check.glob('final-mesh-readback-*') if d.is_dir() and json.load(open(d/'mesh.json'))['source_sha256']==entry['sha256']);p=np.fromfile(d/'positions.f32',dtype='<f4').reshape(-1,3)*[.01,-.01,.01];tri=np.fromfile(d/'indices.u32',dtype='<u4').reshape(-1,3);uv=np.fromfile(d/'uv0.f32',dtype='<f4').reshape(-1,2);normal=np.fromfile(d/'normals.f32',dtype='<f4').reshape(-1,3)*[1,-1,1];normal/=np.linalg.norm(normal,axis=1,keepdims=True);joints=np.fromfile(d/'joints.u16',dtype='<u2').reshape(-1,8);weights=np.fromfile(d/'weights.f32',dtype='<f4').reshape(-1,8)
bpy.ops.wm.open_mainfile(filepath=scene_file);source=bpy.data.objects[name+'_Skinned'];arm=source.find_armature();names=[g.name for g in source.vertex_groups];assert len(names)==len(arm.data.bones);m=bpy.data.meshes.new(name+' cooked');m.from_pydata(p.tolist(),[],tri.tolist());m.update();o=bpy.data.objects.new(name+' final decoded candidate',m);bpy.context.collection.objects.link(o);layer=m.uv_layers.new()
for f in m.polygons:
 f.use_smooth=True
 for li in f.loop_indices:q=uv[m.loops[li].vertex_index];layer.data[li].uv=(float(q[0]),float(1-q[1]))
m.normals_split_custom_set(normal[tri].reshape(-1,3).tolist())
for n in names:o.vertex_groups.new(name=n)
for i in range(len(p)):
 for j,w in zip(joints[i],weights[i]):
  if w>0:o.vertex_groups[int(j)].add([i],float(w),'REPLACE')
mod=o.modifiers.new('Unchanged native reference rig','ARMATURE');mod.object=arm;mat=bpy.data.materials.new('Unchanged actual decoded atlas');mat.use_nodes=True;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(baseline/'actual-decoded-atlas.png'));tex.image.pack();bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Roughness'].default_value=.8;bsdf.inputs['Specular IOR Level'].default_value=.1;mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);m.materials.append(mat)
for x in list(bpy.data.objects):
 if x.type=='MESH':x.hide_render=x!=o
 if x.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(x,do_unlink=True)
for loc,power in [((3,-4,5),180),((-3,-1,3),120),((1,3,4),160)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.size=4;l.rotation_euler=(Vector((0,0,1.1))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.45;s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=False;s.render.resolution_x=640;s.render.resolution_y=760;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard';s.world.color=(.16,.16,.16)
def reset():
 for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def aim(a,b,direction):
 bpy.context.view_layer.update();pb=arm.pose.bones[a];A=pb.matrix.translation.copy();B=arm.pose.bones[b].matrix.translation.copy();R=(B-A).rotation_difference(Vector(direction));pb.matrix=Matrix.Translation(A)@R.to_matrix().to_4x4()@Matrix.Translation(-A)@pb.matrix
reset()
for side,k in [('l',1),('r',-1)]:aim(side+'_upperArm_JNT',side+'_lowerArm_JNT',(k*.12,0,-1));aim(side+'_lowerArm_JNT',side+'_wrist_JNT',(k*.05,-.12,-1))
views={'Buzz':[('front',(0,-4,1.2)),('side',(4,0,1.2))],'BoPeep':[('rear',(0,4,1.2)),('front',(0,-4,1.2))],'Jessie':[('side',(4,0,1.2)),('front',(0,-4,1.2))],'Woody':[('quarter',(-3,-4,1.2))]}[name];records=[]
def render(label,loc):
 cam.location=loc;cam.rotation_euler=(Vector((0,0,1.1))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/(name+'-cooked-'+label+'.png'));bpy.ops.render.render(write_still=True);records.append(s.render.filepath)
for label,loc in views:render(label,loc)
if name=='Buzz':
 for side,k in [('l',1),('r',-1)]:aim(side+'_upperArm_JNT',side+'_lowerArm_JNT',(k*.8,-.3,.4));aim(side+'_lowerArm_JNT',side+'_wrist_JNT',(k*.1,-1,.2))
 render('raised-arms',(0,-4,1.2))
if name=='Woody':
 for side in ['l','r']:aim(side+'_UpperLeg_JNT',side+'_LowerLeg_JNT',(0,-1,-.05));aim(side+'_LowerLeg_JNT',side+'_Foot_JNT',(0,.04,-1))
 render('sitting-quarter',(-3,-4,1.2))
reset();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/(name+'-Final-Cooked-Review.blend')),compress=True);(out/'scope.json').write_text(json.dumps({'character':name,'actual_package_mesh':cid,'independent_native_readback':True,'atlas':'Unchanged private2048 decoded baseline atlas, byte-exact source textures verified','poses':'Controlled FK, not game clips','images':records},indent=2));print('COOKED_SKIN_PREVIEWS_SAVED',name)

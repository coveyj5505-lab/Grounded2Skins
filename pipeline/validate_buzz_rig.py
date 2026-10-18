"""Independent fresh-process Blender rig, rigid-wing and controlled-pose checks."""
import bpy,json,sys,hashlib,math
from pathlib import Path
import numpy as np
from mathutils import Vector,Quaternion
args=sys.argv[sys.argv.index('--')+1:];render='--no-render' not in args
if not render:args.remove('--no-render')
root,out=map(Path,args);out.mkdir(exist_ok=False)
d=np.load(root/'expected.npz');obj=bpy.data.objects['Buzz_Skinned'];arm=bpy.data.objects['Grounded2_Armature_230'];mesh=obj.data
p=np.asarray([v.co[:] for v in mesh.vertices]);tri=np.asarray([f.vertices[:] for f in mesh.polygons]);uv=np.asarray([v.uv[:] for v in mesh.uv_layers.active.data]);mats=np.asarray([f.material_index for f in mesh.polygons])
assert np.max(np.abs(p-d['positions']))<2e-7
assert np.array_equal(tri,d['triangles']) and np.array_equal(mats,d['materials']) and np.max(np.abs(uv-d['uv']))<1e-7
bones=list(arm.data.bones);assert len(bones)==230
rest={b.name:[list(row) for row in b.matrix_local] for b in bones};digest=hashlib.sha256(json.dumps(rest,sort_keys=True).encode()).hexdigest()
assert digest==json.loads((root/'build-report.json').read_text())['bone_rest_hash']
assert digest=='9f5fdc5fe294ebc2b7277536292437fb01346700f3dcbe54a5b9f8b3759450ac', 'Original reference rest matrices changed'
actual=np.zeros((len(p),230));expected=np.zeros_like(actual)
for v in mesh.vertices:
 for g in v.groups:actual[v.index,g.group]=g.weight
for k in range(8):np.add.at(expected,(np.arange(len(p)),d['joints'][:,k]),d['weights'][:,k])
assert np.max(np.abs(actual-expected))<1e-7 and np.max(np.abs(actual.sum(1)-1))<1e-6
assert np.all((actual>0).sum(1)<=8)
assert len(mesh.materials)==8 and sum(i.source=='FILE' and bool(i.packed_file) for i in bpy.data.images)==8
archive=bpy.data.collections['Wings_Extended_PRESERVED_NOT_EXPORTED'];assert len(archive.objects)==6 and archive.hide_render and archive.hide_viewport
originals=bpy.data.collections['Wings_Original_Source_UNTOUCHED'];assert len(originals.objects)==6 and originals.hide_render and originals.hide_viewport
source=np.load(root.parent/'landmarks/source.npz');fit=np.load(root.parent/root.name.replace('skinned','fit')/'fitted.npz')
for component in fit['wing_components']:
    original=bpy.data.objects[f'Wing_{component}_Original_Source'];extended=bpy.data.objects[f'Wing_{component}_Extended_Preserved']
    ix=np.flatnonzero(fit['component']==component)
    assert np.array_equal(np.asarray([v.co[:] for v in original.data.vertices]),source['positions'][ix])
    assert np.max(np.abs(np.asarray([v.co[:] for v in extended.data.vertices])-fit['positions'][ix]))<1e-7
    assert len(original.modifiers)==0 and len(original.vertex_groups)==0
    assert np.array_equal(np.asarray(original.matrix_world),np.eye(4))
    assert np.array_equal(np.asarray([x.uv[:] for x in original.data.uv_layers.active.data]),np.asarray([x.uv[:] for x in extended.data.uv_layers.active.data]))
assert sum(len(o.data.vertices) for o in archive.objects)==430
for o in archive.objects:
 assert len(o.vertex_groups)==1 and o.vertex_groups[0].name==bones[208].name
 assert all(len(v.groups)==1 and v.groups[0].weight==1 for v in o.data.vertices)
assert not np.any(np.isin(d['component'],[0,1,12,51,62,72]))
back=d['region']=='rigid-wings-backpack';assert np.all(actual[back,208]==1)
rest_inv=np.linalg.inv(np.array([b.matrix_local[:] for b in bones],dtype='f8'));h=np.c_[p,np.ones(len(p))]
edges=np.unique(np.sort(np.r_[tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]],axis=1),axis=0);base_lengths=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1)
poses={'rest':[], 'arm_raise':[(56,'Y',-55),(160,'Y',55)],'elbow_bend':[(59,'Z',-65),(163,'Z',65)],'head_turn':[(101,'Z',40)],'torso_turn':[(52,'Z',25)],'finger_curl':[(75,'X',45),(76,'X',45),(197,'X',45),(198,'X',45)],'sitting_approx':[(24,'X',-75),(32,'X',-75),(25,'X',95),(33,'X',95),(59,'Z',-45),(163,'Z',45)],'crouching_approx':[(24,'X',-65),(32,'X',-65),(25,'X',110),(33,'X',110),(52,'X',20)],'running_approx':[(24,'X',-45),(32,'X',30),(25,'X',30),(33,'X',70),(56,'Z',30),(160,'Z',30),(59,'Z',-45),(163,'Z',45)],'climbing_approx':[(56,'Y',-100),(160,'Y',100),(59,'Z',-35),(163,'Z',35),(24,'X',-60),(25,'X',95)]}
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.display.shading.light='STUDIO';scene.display.shading.color_type='TEXTURE';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.background_type='WORLD';scene.world.color=(.12,.12,.12)
camdata=bpy.data.cameras.new('ValidationCamera');cam=bpy.data.objects.new('ValidationCamera',camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=2.35
# Only visible Buzz is rendered; armature overlays do not enter the render.
for o in bpy.data.objects:
 if o.type=='MESH' and o!=obj:o.hide_render=True
records=[];saved={}
for name,changes in poses.items():
 for b in arm.pose.bones:b.matrix_basis.identity()
 for index,axis,degree in changes:
  pb=arm.pose.bones[bones[index].name];direction=Vector({'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis]);local=bones[index].matrix_local.to_3x3().inverted()@direction
  pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(local,math.radians(degree))
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();evaluated=obj.evaluated_get(deps);em=evaluated.to_mesh();q=np.asarray([v.co[:] for v in em.vertices]);evaluated.to_mesh_clear()
 matrix=np.asarray([arm.pose.bones[b.name].matrix[:] for b in bones])@rest_inv
 predicted=np.zeros((len(p),3))
 for i in np.flatnonzero(actual.sum(0)>0):predicted+=(h@matrix[i].T)[:,:3]*actual[:,i,None]
 error=float(np.linalg.norm(predicted-q,axis=1).max());assert error<3e-6,(name,error)
 if name=='rest':assert np.linalg.norm(q-p,axis=1).max()<3e-6
 if name in ('arm_raise','elbow_bend','head_turn'):assert np.linalg.norm(q[back]-p[back],axis=1).max()<3e-6
 rigid_error=0
 for bone in np.unique(d['rigid'][d['rigid']>=0]):
  ix=np.flatnonzero(d['rigid']==bone)
  old=np.linalg.norm(p[ix]-p[ix].mean(0),axis=1);new=np.linalg.norm(q[ix]-q[ix].mean(0),axis=1);rigid_error=max(rigid_error,float(np.max(np.abs(old-new))))
 assert rigid_error<3e-6,(name,rigid_error)
 lengths=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1);ratio=lengths[base_lengths>1e-6]/base_lengths[base_lengths>1e-6]
 records.append({'pose':name,'rotations_bone_axis_degrees':changes,'independent_LBS_max_error_m':error,'rigid_distance_error_m':rigid_error,'edge_length_ratio_p01_p99_max':np.quantile(ratio,[.01,.99,1]).tolist(),'finite':bool(np.isfinite(q).all()),'backpack_bbox_m':[q[back].min(0).tolist(),q[back].max(0).tolist()]});saved[name]=q
 if render:
  target=Vector((0,0,1));cam.location=(2.4,-4,2.3);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
  if name=='rest':
   cam.location=(-2.4,4,2.3);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/'rest_back.png');bpy.ops.render.render(write_still=True)
np.savez_compressed(out/'pose-vertices.npz',**saved)
report={'fresh_reopen':True,'vertices':len(p),'triangles':len(tri),'material_slots':len(mesh.materials),'packed_images':8,'bone_count':230,'rest_hash':digest,'normalized_weights':True,'max_influences':int((actual>0).sum(1).max()),'wing_archive':{'objects':6,'vertices':430,'rigid_chest_only':True,'hidden_from_initial_mesh':True},'untouched_source_wing_objects_verified':6,'source_wing_coordinates_and_matrices_exact':True,'backpack_chest_only':True,'pose_results':records,'scope':'Synthetic controlled poses, not original Grounded 2 animations or game collision tests','visual_review':'Render images require inspection; numerical skinning checks do not alone prove acceptable deformation','game_test':'NOT RUN'}
(out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

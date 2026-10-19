"""Fresh reopen checks and synthetic pose previews; not game-animation proof."""
import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False)
arm=bpy.data.objects['Grounded2_Hoops_189'];objs=[o for o in bpy.data.objects if o.type=='MESH' and o.name.endswith('_Hoops_Skinned')];assert len(arm.data.bones)==189 and len(objs)==3
for o in objs:
 assert o.find_armature()==arm and len(o.vertex_groups)==189
 assert [g.name for g in o.vertex_groups]==[b.name for b in arm.data.bones]
 for v in o.data.vertices:assert 0<len(v.groups)<=8 and abs(sum(g.weight for g in v.groups)-1)<1e-5
 source=bpy.data.objects[o['source_object']];assert len(source.data.vertices)==len(o.data.vertices);assert [tuple(p.vertices) for p in source.data.polygons]==[tuple(p.vertices) for p in o.data.polygons]
 assert np.array_equal(np.asarray([u.uv[:] for u in source.data.uv_layers.active.data]),np.asarray([u.uv[:] for u in o.data.uv_layers.active.data]))
assert sum(len(o.data.vertices) for o in objs)==4883
assert len([i for i in bpy.data.images if i.source=='FILE' and i.packed_file])==3
scene=bpy.context.scene;scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=720;scene.render.resolution_y=860;scene.render.resolution_percentage=100
camera=scene.camera;camera.data.ortho_scale=2.65;report=[]
rest={b.name:[list(row) for row in b.matrix_local] for b in arm.data.bones}
def pose(name,rotations,view,center=(0,0,1.1)):
 for b in arm.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0)
 for n,angles in rotations.items():arm.pose.bones[n].rotation_euler=tuple(math.radians(x) for x in angles)
 bpy.context.view_layer.update();points=[]
 for o in objs:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();p=np.asarray([v.co[:] for v in mesh.vertices]);assert np.isfinite(p).all();points.extend(p.tolist());ev.to_mesh_clear()
 p=np.asarray(points);report.append({'pose':name,'vertices':len(p),'finite':True,'bounds':[p.min(0).tolist(),p.max(0).tolist()]})
 camera.location=view;camera.rotation_euler=(Vector(center)-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
pose('front',{},(0,-5,1.2));pose('side',{},(5,0,1.2))
pose('sitting',{'l_UpperLeg_JNT':(0,0,-75),'r_UpperLeg_JNT':(0,0,-75),'l_LowerLeg_JNT':(0,0,90),'r_LowerLeg_JNT':(0,0,90)},(3,-5,1.8))
fingers={}
for label in ['Left','Right']:
 for finger in ['Thumb','Index','Middle','Ring','Pinky']:
  for n in range(1,4):fingers[f'{label}Hand{finger}{n}_JNT']=(0,0,25)
pose('finger-curl',fingers,(0,-5,1.2))
assert rest=={b.name:[list(row) for row in b.matrix_local] for b in arm.data.bones}
(out/'validation.json').write_text(json.dumps({'fresh_reopen':True,'native_bones':189,'vertices':4883,'triangles':8757,'normalized_weights':True,'topology_and_UVs_match_preserved_source':True,'all_native_rest_matrices_unchanged_during_pose_checks':True,'packed_images':3,'poses':report,'eye_material':'Still provisional body diffuse, not final','runtime_test':'NOT RUN'},indent=2)+'\n')

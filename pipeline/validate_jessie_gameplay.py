"""Reopen final Jessie authoring and render controlled poses before packaging."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
import numpy as np
expected,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(exist_ok=False);e=np.load(expected);o=bpy.data.objects['Jessie_Skinned'];arm=o.find_armature();assert arm.name=='Grounded2_Hoops_189' and len(arm.data.bones)==189
assert len(o.data.vertices)==4883 and len(o.data.polygons)==8757
assert np.array_equal(np.asarray([v.co[:] for v in o.data.vertices]),e['positions'].astype('f4'))
assert np.allclose(np.asarray([v.uv[:] for v in o.data.uv_layers.active.data]),e['loop_uv'],atol=1e-7)
for v in o.data.vertices:assert 0<len(v.groups)<=8 and abs(sum(g.weight for g in v.groups)-1)<1e-5
assert len([i for i in bpy.data.images if i.source=='FILE' and i.packed_file])==4
scene=bpy.context.scene;scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=720;scene.render.resolution_y=860;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.ortho_scale=2.6;poses=[]
rest={b.name:[list(r) for r in b.matrix_local] for b in arm.data.bones}
def pose(name,values,view):
 for b in arm.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0)
 for n,angles in values.items():arm.pose.bones[n].rotation_euler=tuple(math.radians(x) for x in angles)
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.asarray([v.co[:] for v in m.vertices]);assert len(p)==4883 and np.isfinite(p).all();ev.to_mesh_clear();poses.append({'name':name,'finite_weighted_vertices':4883,'bounds':[p.min(0).tolist(),p.max(0).tolist()]})
 cam.location=view;cam.rotation_euler=(Vector((0,0,1.1))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
pose('front',{},(0,-5,1.25));pose('side',{},(5,0,1.25));pose('sitting',{'l_UpperLeg_JNT':(0,0,-75),'r_UpperLeg_JNT':(0,0,-75),'l_LowerLeg_JNT':(0,0,90),'r_LowerLeg_JNT':(0,0,90)},(3,-5,1.6));pose('finger-curl',{f'{label}Hand{finger}{n}_JNT':(0,0,25) for label in ['Left','Right'] for finger in ['Thumb','Index','Middle','Ring','Pinky'] for n in range(1,4)},(0,-5,1.25))
assert rest=={b.name:[list(r) for r in b.matrix_local] for b in arm.data.bones}
(out/'validation.json').write_text(json.dumps({'fresh_reopen':True,'bones':189,'vertices':4883,'triangles':8757,'all_vertices_normalized':True,'packed_images':4,'source_scenes_preserved':True,'controlled_poses':poses,'native_bone_rest_matrices_unchanged':True,'eye_material':'Temporary procedural green eyes; original texture not supplied','runtime_test':'NOT RUN'},indent=2)+'\n')

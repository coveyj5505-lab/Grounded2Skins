"""Independent root-rigid carry/jab accessories, with a source-derived FP grip.
The original crook, Bo Peep body, skeleton, and native animations are untouched.
"""
import bpy,numpy as np,json,sys,math,bmesh
from pathlib import Path
from mathutils import Vector,Matrix
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False);arm=bpy.data.objects['Grounded2_Willow_192'];body=bpy.data.objects['BoPeep_StableBody_Preserved_NOT_EXPORTED'];crook=bpy.data.objects['BoPeep_Skinned'];assert len(crook.data.vertices)==391
original_crook=crook.copy();original_crook.data=crook.data.copy();original_crook.name='Crook_PreGripOrigin_PRESERVED';bpy.context.scene.collection.objects.link(original_crook);original_crook.hide_render=True;original_crook.hide_set(True)
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
sourcebody=bpy.data.objects['BoPeep_Body'];sa=sourcebody.find_armature()
for pb in sa.pose.bones:pb.matrix_basis=Matrix.Identity(4)
def world(name):return sa.matrix_world@sa.data.bones[name].head_local
hand=world('e_wrist_r');middle=world('e_middlefinger1_r');index=world('e_indexfinger1_r');thumb=world('e_thumbfinger1_r');a=(middle-hand).normalized();b=(index-thumb);b=(b-a*b.dot(a)).normalized();n=a.cross(b).normalized();basis=np.column_stack([a,b,n]);target=np.column_stack([[0,1.,0],[0,0,1.],[1.,0,0]]);R=target@basis.T;assert abs(np.linalg.det(R)-1)<1e-5
axis_local=(sa.matrix_world.to_3x3().inverted()@b).normalized()
# Use the preserved SOURCE FBX finger weights; the accepted playable hand is
# intentionally rigid and cannot be curled by posing its native finger bones.
for finger in ['index','middle','thumb']:
 for k,deg in [(1,-38),(2,-50),(3,-38)]:
  pb=sa.pose.bones.get('e_'+finger+'finger'+str(k)+'_r')
  if not pb:continue
  bpy.context.view_layer.update();origin=pb.matrix.translation.copy();rot=Matrix.Rotation(math.radians(deg if finger!='thumb' else deg*.65),4,axis_local);pb.matrix=Matrix.Translation(origin)@rot@Matrix.Translation(-origin)@pb.matrix
bpy.context.view_layer.update();se=sourcebody.evaluated_get(bpy.context.evaluated_depsgraph_get());sm=se.to_mesh();sourceposed=np.array([tuple(sourcebody.matrix_world@v.co) for v in sm.vertices]);se.to_mesh_clear();sourcerest=np.array([tuple(sourcebody.matrix_world@v.co) for v in sourcebody.data.vertices]);sourcepalmids=[v.index for v in sourcebody.data.vertices if sum(g.weight for g in v.groups if sourcebody.vertex_groups[g.group].name=='e_wrist_r')>.8];sourcepalm=sourcerest[sourcepalmids].mean(0)
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();posed=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();rest=np.array([v.co[:] for v in body.data.vertices]);wrist=np.array(arm.data.bones['r_wrist_JNT'].head_local);elbow=np.array(arm.data.bones['r_lowerArm_JNT'].head_local);axis=(elbow-wrist);axis/=np.linalg.norm(axis)
names=[g.name for g in body.vertex_groups];allowed={i for i,name in enumerate(names) if name.startswith('RightHand') or name in ['r_hand_JNT','r_wrist_JNT','r_lowerArm_JNT']};mass=np.array([sum(g.weight for g in v.groups if g.group in allowed) for v in body.data.vertices]);dist=(rest-wrist)@axis;select=(mass>.95)&(dist<.12)&(np.linalg.norm(rest-wrist,axis=1)<.24)
faces=[f for f in body.data.polygons if all(select[i] for i in f.vertices)];used=np.unique([i for f in faces for i in f.vertices]);assert len(used)>100
palmids=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if names[g.group]=='r_hand_JNT')>.8];palm=rest[palmids].mean(0);target_palm=np.array([-.028,-.040,0.]);handpoints=(sourceposed[used]-sourcepalm)@R.T*.25+target_palm
# Let the copied forearm enter from below the screen instead of a flat side cut.
t=np.clip(dist[used]/.12,0,1);handpoints[:,0]-=.16*t;handpoints[:,2]-=.16*t
# Preserve the geometry/UVs from the source; only the independent FP copy is posed.
handobj=body.copy();handobj.data=body.data.copy();handobj.name='FP_Grip_SourceHand_PRESERVED';bpy.context.scene.collection.objects.link(handobj);bm=bmesh.new();bm.from_mesh(handobj.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index not in set(used)],context='VERTS');bm.to_mesh(handobj.data);bm.free();assert len(handobj.data.vertices)==len(used)
for v,p in zip(handobj.data.vertices,handpoints):v.co=p
handobj.parent=None;handobj.matrix_world=Matrix.Identity(4)
for m in list(handobj.modifiers):handobj.modifiers.remove(m)
handobj.vertex_groups.clear()
for bone in arm.data.bones:handobj.vertex_groups.new(name=bone.name)
handobj.vertex_groups[0].add(list(range(len(handobj.data.vertices))),1.,'REPLACE');handobj.hide_render=True;handobj.hide_set(True)
source_points=np.array([v.co[:] for v in crook.data.vertices]);states=[]
for kind,scale,lift,yaw in [('TP',[.7,.7,1.12],.32,0),('FP',[.7,.7,.85],.85*.32/1.12,math.pi/2)]:
 for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 o=crook.copy();o.data=crook.data.copy();o.name='Crook_'+kind+'_GripLocal';bpy.context.scene.collection.objects.link(o);p=source_points*np.array(scale)+[0,0,lift]
 if yaw:
  # Y reflection: Unreal yaw+90 corresponds to Blender yaw-90.
  p=p@np.array([[0,1,0],[-1,0,0],[0,0,1]]).T
 for v,q in zip(o.data.vertices,p):v.co=q
 if kind=='FP':
  handcopy=handobj.copy();handcopy.data=handobj.data.copy();bpy.context.scene.collection.objects.link(handcopy);handcopy.hide_set(False);o.hide_set(False);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);handcopy.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join()
 # The independent accessory owns no animated skin influences.
 o.vertex_groups.clear()
 for bone in arm.data.bones:o.vertex_groups.new(name=bone.name)
 o.vertex_groups[0].add(list(range(len(o.data.vertices))),1.,'REPLACE');o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops));o.data.update();o.data.calc_loop_triangles();states.append({'kind':kind,'object':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),'root_only':True,'crook_original_scale_baked':scale,'origin_shift_m':lift});o.hide_render=True;o.hide_set(True)
crook.name='Original_Independent_Crook_PRESERVED';crook.hide_render=True;crook.hide_set(True)
# Exporter uses this named copy; save one source scene per accessory state.
for rec in states:
 o=bpy.data.objects[rec['object']];o.name='BoPeep_Skinned';o.hide_render=False;o.hide_set(False);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/(rec['kind']+'-Crook-Grip.blend')),compress=True);o.name=rec['object'];o.hide_render=True;o.hide_set(True)
(out/'report.json').write_text(json.dumps({'states':states,'source_hand_vertices':len(used),'source_hand_faces':len(faces),'source_hand_UVs_preserved':True,'source_finger_pose':'Preserved source FBX semantic finger weights and controlled FK; accepted rigid native hand remains unchanged','source_palm_blender_m':palm.tolist(),'FP_viewmodel':'Independent cosmetic source hand/forearm, not native hand animation replacement','body_animations_damage_collision_unchanged':True,'runtime':'PENDING; closed-grip visual needs preview and Windows confirmation'},indent=2));print('CROOK_GRIP_VIEWMODELS_SAVED')

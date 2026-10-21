import bpy,bmesh,numpy as np,json
from mathutils import Vector,Matrix
from pathlib import Path
r=Path('/tmp/toystory-feedback-v3');bpy.ops.wm.open_mainfile(filepath='/workspace/mod-work/refinement-next/crook-grip-v3d/FP-Crook-Grip.blend');o=bpy.data.objects['BoPeep_Skinned'];body=bpy.data.objects['BoPeep_StableBody_Preserved_NOT_EXPORTED'];src=bpy.data.objects['BoPeep_Body'];sa=src.find_armature();arm=o.find_armature()
for pb in sa.pose.bones:pb.matrix_basis=Matrix.Identity(4)
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
def world(n):return sa.matrix_world@sa.data.bones[n].head_local
hand=world('e_wrist_r');middle=world('e_middlefinger1_r');index=world('e_indexfinger1_r');thumb=world('e_thumbfinger1_r');a=(middle-hand).normalized();b=index-thumb;b=(b-a*b.dot(a)).normalized();n=a.cross(b).normalized();basis=np.column_stack([a,b,n]);target=np.column_stack([[0,1,0],[0,0,-1],[-1,0,0]]);R=target@basis.T;assert abs(np.linalg.det(R)-1)<1e-5
P=np.array([src.matrix_world@v.co for v in src.data.vertices]);palmids=[v.index for v in src.data.vertices if sum(g.weight for g in v.groups if src.vertex_groups[g.group].name=='e_wrist_r')>.8];palm=P[palmids].mean(0);rest=np.array([v.co[:] for v in body.data.vertices]);wrist=np.array(arm.data.bones['r_wrist_JNT'].head_local);elbow=np.array(arm.data.bones['r_lowerArm_JNT'].head_local);axis=elbow-wrist;axis/=np.linalg.norm(axis);names=[g.name for g in body.vertex_groups];allowed={i for i,n in enumerate(names) if n.startswith('RightHand') or n in ['r_hand_JNT','r_wrist_JNT','r_lowerArm_JNT']};mass=np.array([sum(g.weight for g in v.groups if g.group in allowed) for v in body.data.vertices]);dist=(rest-wrist)@axis;select=(mass>.95)&(dist<.12)&(np.linalg.norm(rest-wrist,axis=1)<.24);faces=[f for f in body.data.polygons if all(select[i] for i in f.vertices)];used=np.unique([i for f in faces for i in f.vertices]);Q=(P[used]-palm)@R.T*.25+[-.018,-.04,0]
# Start from untouched source-rest hand, not the failed curled/grip copy.
h=body.copy();h.data=body.data.copy();h.name='Natural_Flat_Right_Hand';bpy.context.collection.objects.link(h);bm=bmesh.new();bm.from_mesh(h.data);bm.verts.ensure_lookup_table();keep=set(used);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index not in keep],context='VERTS');bm.verts.ensure_lookup_table();assert len(bm.verts)==len(Q)
for v,q in zip(bm.verts,Q):v.co=Vector(q)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,-.08,0),plane_no=(0,1,0),clear_inner=True,clear_outer=False);edges=[e for e in bm.edges if e.is_boundary and all(abs(v.co.y+.08)<1e-5 for v in e.verts)];adj={}
for e in edges:
 a,b=e.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
assert len(adj)>3 and all(len(v)==2 for v in adj.values());start=next(iter(adj));ring=[start];prev=None;cur=start
while True:
 nxt=next(v for v in adj[cur] if v!=prev)
 if nxt==start:break
 assert nxt not in ring;ring.append(nxt);prev,cur=cur,nxt
assert len(ring)==len(adj);center=sum((v.co for v in ring),Vector())/len(ring);original=[v.co-center for v in ring];entry=Vector((-.15,-.22,-.11));uv=bm.loops.layers.uv.active;before=ring
for t in [.33,.67,1.]:
 C=center.lerp(entry,t);after=[bm.verts.new(C+q*(1-.12*t)) for q in original]
 for i in range(len(ring)):
  f=bm.faces.new([before[i],before[(i+1)%len(ring)],after[(i+1)%len(ring)],after[i]]);f.smooth=True;f.material_index=0
  for k,l in enumerate(f.loops):l[uv].uv=(.756377+.0001*(k in [1,2]),.456512+.0001*(k in [2,3]))
 before=after
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(h.data);bm.free();h.data.update();h.parent=None;h.matrix_world=Matrix.Identity(4)
for m in list(h.modifiers):h.modifiers.remove(m)
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index>=391],context='VERTS');bm.to_mesh(o.data);bm.free();assert len(o.data.vertices)==391
bpy.ops.object.select_all(action='DESELECT');h.hide_set(False);o.hide_set(False);h.select_set(True);o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join();o.vertex_groups.clear()
for bone in arm.data.bones:o.vertex_groups.new(name=bone.name)
o.vertex_groups[0].add(list(range(len(o.data.vertices))),1,'REPLACE');o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops));o.data.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'CrookHand.blend'),compress=True)
(r/'hand-report.json').write_text(json.dumps({'source':'Unposed source right hand; all source finger matrices reset; no curled pose or twisted previous proxy reused','natural_right_hand_vertices_before_cut':len(used),'wrist_ring_vertices':len(ring),'original_crook_vertices_exact':391,'scale':'source-to-game .25; no hand-specific rescale','thumb':'Source thumb side mapped upward; proper rotation determinant1, no mirror','forearm':'Single continuous tapered wrist tube','root_only':True},indent=2));print('NATURAL_FLAT_HAND_SAVED')

import bpy,bmesh,numpy as np,json
from pathlib import Path
from mathutils import Vector
out=Path('/workspace/mod-work/skin-fixes-next');bpy.ops.wm.open_mainfile(filepath='/workspace/mod-work/refinement-next/crook-grip-v3d/FP-Crook-Grip.blend');o=bpy.data.objects['BoPeep_Skinned'];arm=o.find_armature();assert len(o.data.vertices)==748
# Preserve complete source staff and isolate only the copied hand/forearm.
hand=o.copy();hand.data=o.data.copy();hand.name='Upright_FP_Hand_Work';bpy.context.collection.objects.link(hand);bm=bmesh.new();bm.from_mesh(hand.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index<391],context='VERTS')
pivot=np.array([-.028,-.04,0.]);R=np.diag([-1.,1.,-1.])
for v in bm.verts:v.co=Vector(R@(np.array(v.co)-pivot)+pivot)
# The original subset had an open/asymmetric forearm; retain the hand, replace
# just the entry tube instead of twisting that missing surface into view.
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,-.08,0),plane_no=(0,1,0),clear_inner=True,clear_outer=False);edges=[e for e in bm.edges if e.is_boundary and all(abs(v.co.y+.08)<1e-5 for v in e.verts)];assert len(edges)>=3,len(edges)
adj={}
for e in edges:
 a,b=e.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
assert all(len(n)==2 for n in adj.values());start=next(iter(adj));ring=[start];prev=None;cur=start
while True:
 nxt=next(v for v in adj[cur] if v!=prev)
 if nxt==start:break
 assert nxt not in ring;ring.append(nxt);prev,cur=cur,nxt
assert len(ring)==len(adj);center=sum((v.co for v in ring),Vector())/len(ring);entry=Vector((-.17,-.22,-.14));original=[v.co.copy()-center for v in ring];uvlayer=bm.loops.layers.uv.active
# Existing skin-only texel; tiny UV offsets avoid undefined tangents.
uv=Vector((.805,.265));before=ring;created=0
for step,t in enumerate([.35,.70,1.]):
 C=center.lerp(entry,t);scale=1-.15*t;after=[bm.verts.new(C+q*scale) for q in original]
 for i in range(len(ring)):
  f=bm.faces.new([before[i],before[(i+1)%len(ring)],after[(i+1)%len(ring)],after[i]]);f.material_index=0;f.smooth=True
  for k,l in enumerate(f.loops):l[uvlayer].uv=uv+Vector((.0002*(k in [1,2]),.0002*(k in [2,3])))
  created+=1
 before=after
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(hand.data);bm.free();hand.data.update()
# Keep shaft geometry and texture loops exact from the accepted source mesh.
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index>=391],context='VERTS');bm.to_mesh(o.data);bm.free();assert len(o.data.vertices)==391
bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);hand.hide_set(False);o.select_set(True);hand.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join()
o.vertex_groups.clear()
for bone in arm.data.bones:o.vertex_groups.new(name=bone.name)
o.vertex_groups[0].add(list(range(len(o.data.vertices))),1,'REPLACE');o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops));o.data.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Crook-FP-Hand-Upright-Candidate.blend'),compress=True)
(out/'Crook-FP-Hand-Upright.json').write_text(json.dumps({'hand_orientation':'180-degree roll around hand longitudinal axis; thumb above fingers','forearm':'Rebuilt continuous tapered tube from wrist boundary to original below-screen entry','boundary_vertices':len(ring),'tube_quads':created,'staff_vertices_preserved':391,'total_vertices':len(o.data.vertices),'weights':'Root only, 192-bone accessory reference','runtime':'Persistent view components unchanged; Windows pending'},indent=2));print('UPRIGHT_HAND_FOREARM_SAVED')

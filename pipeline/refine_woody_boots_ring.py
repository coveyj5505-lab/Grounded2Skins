"""Focused correction from preserved source; no changes to other characters.

Use original anatomical source weights for boot-side ownership, not the X sign
of each vertex. Restore the original circular ring with one uniform similarity.
Run on Woody-Pete-gameplay.blend; all source and pre-correction meshes retained.
"""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False)
old=bpy.data.objects['Woody_Skinned'];arm=old.find_armature();o=old.copy();o.data=old.data.copy();bpy.context.collection.objects.link(o);old.name='Woody_Before_Boot_Ring_Preserved';old.hide_render=True;old.hide_set(True);o.name='Woody_Skinned';m=o.data;before=np.array([v.co[:] for v in m.vertices]);after=before.copy()
source=bpy.data.objects['KH3 Woody V3_mesh.001'];sourcearm=bpy.data.objects['KH3 Woody V3_arm'];sw={b.name:np.array(sourcearm.matrix_world@b.head_local) for b in sourcearm.data.bones};nw={b.name:np.array(b.head_local) for b in arm.data.bones};names=[g.name for g in o.vertex_groups]
# Original join order is checked by the exact source mesh cardinalities.
parts=[bpy.data.objects['KH3 Woody V3_mesh'+s] for s in ['', '.001','.002','.003','.004','.005','.006','.007','.008']];assert sum(len(p.data.vertices) for p in parts)==len(m.vertices)==32379
start=len(parts[0].data.vertices);mapping=json.loads(Path('/workspace/mod-work/woody-stage/rig-v4/rig-report.json').read_text())['mapping'];hip=sw['bip_pelvis'];changed_weights=[];old_wrong=[];boot_ids=[];source_side={}
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def segment(p,a,b,A,B,width):
 d=b-a;t=np.dot(p-a,d)/np.dot(d,d);R=np.array(Vector(d).rotation_difference(Vector(B-A)).to_matrix());return A+t*(B-A)+width*(R@(p-a-t*d))
def leg(p,side):
 short='l' if side=='L' else 'r';a,b,c=[sw[f'bip_{n}_{side}'] for n in ['hip','knee','foot']];A,C,D=[nw[f'{short}_{n}_JNT'] for n in ['UpperLeg','LowerLeg','Foot']];knee=smooth((b[2]+.065-p[2])/.13);q=(1-knee)*segment(p,a,b,A,C,1.35)+knee*segment(p,b,c,C,D,1.35);ankle=smooth((c[2]+.04-p[2])/.08)
 if ankle:q=(1-ankle)*q+ankle*segment(p,c,sw[f'bip_toe_{side}'],D,nw[f'{short}_Toes_JNT'],1.25)
 row={names.index(short+'_UpperLeg_JNT'):(1-knee)*(1-ankle),names.index(short+'_LowerLeg_JNT'):knee*(1-ankle),names.index(short+'_Foot_JNT'):ankle};return q,{i:float(w) for i,w in row.items() if w>1e-7}
old_fit_error=[]
for v in source.data.vertices:
 vi=start+v.index;p=np.array(source.matrix_world@v.co);orig={source.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0};sides={s:sum(w for n,w in orig.items() if mapping[n] in [f'{s}_UpperLeg_JNT',f'{s}_LowerLeg_JNT',f'{s}_Foot_JNT',f'{s}_Toes_JNT']) for s in ['l','r']}
 if sum(sides.values())<.999:continue # Holster/belt share the Boots material; preserve them.
 side='L' if sides['l']>sides['r'] else 'R';assert max(sides.values())>.999
 oldside='L' if p[0]>hip[0] else 'R';q0,_=leg(p,oldside);old_fit_error.append(float(np.max(abs(q0-before[vi]))));q,row=leg(p,side);boot_ids.append(vi);source_side[vi]=side
 if oldside!=side:
  old_wrong.append(vi);after[vi]=q
  for group in o.vertex_groups:group.remove([vi])
  for i,w in row.items():o.vertex_groups[i].add([vi],w,'REPLACE')
  changed_weights.append(vi)
assert max(old_fit_error)<2e-6, max(old_fit_error)
# The two inner pull tabs are connected pieces: every vertex must stay on its
# source leg even when the source position crosses the character center plane.
for vi in boot_ids:
 side=source_side[vi];bad='r_' if side=='L' else 'l_';assert not any(names[g.group].startswith(bad) and g.weight>1e-7 for g in m.vertices[vi].groups)
ring_source=parts[-1];offset=sum(len(p.data.vertices) for p in parts[:-1]);assert offset==32126
S=np.array([tuple(ring_source.matrix_world@v.co) for v in ring_source.data.vertices]);mount=np.arange(154,253);anchor_src=S[mount].mean(0);anchor_dst=before[offset+mount].mean(0);after[offset:offset+253]=anchor_dst+(S-anchor_src)*1.35
for v,q in zip(m.vertices,after):v.co=q
m.update();changed=np.flatnonzero(np.max(abs(after-before),axis=1)>1e-7);assert set(changed)<=set(old_wrong)|set(range(offset,offset+253))
# Source inner pull-tabs themselves cross the center plane in the relaxed
# stance. Tuck each complete tab 3.3cm toward its own cuff; keep original shape,
# topology and texture, rather than trim/delete the cowboy-boot details.
adj=[set() for _ in source.data.vertices]
for edge in source.data.edges:
 a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
seen=set();tab_reports=[]
for vi in range(len(adj)):
 if vi in seen:continue
 todo=[vi];seen.add(vi);ids=[]
 while todo:
  v=todo.pop();ids.append(start+v)
  for w in adj[v]:
   if w not in seen:seen.add(w);todo.append(w)
 if len(ids)!=133 or abs(float(before[ids,0].mean()))>.03:continue
 assert all(i in source_side for i in ids);sides={source_side[i] for i in ids};assert len(sides)==1;side=sides.pop();sign=1 if side=='L' else -1
 delta=.018-float(np.min(sign*after[ids,0]));assert 0<delta<.05
 after[ids,0]+=sign*delta
 for i in ids:m.vertices[i].co=after[i]
 tab_reports.append({'side':side,'source_vertices':len(ids),'lateral_tuck_m':delta,'vertices':ids})
assert len(tab_reports)==2
changed=np.flatnonzero(np.max(abs(after-before),axis=1)>1e-7)
allowed=set(old_wrong)|set(range(offset,offset+253))|{i for t in tab_reports for i in t['vertices']};assert set(changed)<=allowed
m.update()
# All faces, UVs, head/body classification, and other weights stay untouched.
assert [tuple(p.vertices) for p in m.polygons]==[tuple(p.vertices) for p in old.data.polygons]
assert np.array_equal(np.array([d.uv[:] for d in m.uv_layers.active.data]),np.array([d.uv[:] for d in old.data.uv_layers.active.data]))
for vi in range(len(m.vertices)):
 if vi not in changed_weights:assert [(g.group,g.weight) for g in m.vertices[vi].groups]==[(g.group,g.weight) for g in old.data.vertices[vi].groups]
assert np.array_equal(after[np.setdiff1d(np.arange(len(after)),changed)],before[np.setdiff1d(np.arange(len(after)),changed)])
for pb in arm.pose.bones:pb.matrix_basis.identity()
ring_before=np.ptp(before[offset:offset+154],axis=0);ring_after=np.ptp(after[offset:offset+154],axis=0);report={'status':'AUTHORING_VALIDATED_WINDOWS_PENDING','source_vertices':len(m.vertices),'boot_source_vertices':len(boot_ids),'cross_leg_boot_vertices_corrected':len(old_wrong),'boot_original_fit_reproduction_max_error_m':max(old_fit_error),'inner_tabs_tucked_toward_own_cuff':tab_reports,'boot_cause':'Authored inner tabs also crossed the center plane at rest. Per-vertex source X-side classification split two inner boot pull-tabs across opposite lower-leg bones. Original anatomical source weights establish correct side.','ring_cause':'Torso nonuniform scale plus nonlinear height fitting stretched circular source ring; original spine3 rigid weights were already correct.','ring_source_diameter_xz_m':np.ptp(S[:154],axis=0)[[0,2]].tolist(),'ring_old_diameter_xz_m':ring_before[[0,2]].tolist(),'ring_new_diameter_xz_m':ring_after[[0,2]].tolist(),'ring_new_uniform_scale':1.35,'ring_mount_and_loop_same_similarity':True,'changed_vertex_ids':changed.tolist(),'weight_changed_vertex_ids':changed_weights,'original_source_and_baseline_mesh_preserved':True,'topology_UVs_materials_head_body_split_and_all_other_weights_preserved':True,'rest_bone_matrices_changed':False}
np.savez_compressed(out/'correction.npz',before=before,positions=after,changed=changed,weight_changed=np.array(changed_weights));(out/'authoring-report.json').write_text(json.dumps(report,indent=2)+'\n');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Woody-Boots-Ring-Corrected.blend'),compress=True);print(json.dumps({k:v for k,v in report.items() if not k.endswith('_ids')}))

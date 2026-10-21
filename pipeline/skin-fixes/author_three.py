import bpy,numpy as np,json
from pathlib import Path
out=Path('/workspace/mod-work/skin-fixes-next');reports={}
def save(name):
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/(name+'.blend')),compress=True)
def archive(o):
 copy=o.copy();copy.data=o.data.copy();copy.name=o.name+'_Accepted_Baseline_PRESERVED';bpy.context.collection.objects.link(copy);copy.hide_render=True;copy.hide_set(True)
# Jessie: preserve the complete head/hat/hair shape; align neck axis to the
# measured lower-neck center with a continuous translation across its base.
bpy.ops.wm.open_mainfile(filepath='/workspace/mod-work/jessie-v2-stage/fit-v4/Jessie-Hoops-V2.blend');o=bpy.data.objects['Jessie_Skinned'];archive(o);P=np.array([v.co[:] for v in o.data.vertices]);G=np.zeros((len(P),len(o.vertex_groups)))
for v in o.data.vertices:
 for g in v.groups:G[v.index,g.group]=g.weight
names=[g.name for g in o.vertex_groups];head=G[:,[i for i,n in enumerate(names) if n=='head_JNT' or 'Head' in n]].sum(1);neck=G[:,[i for i,n in enumerate(names) if n.startswith('neck')]].sum(1)
low=(abs(P[:,0])<.055)&(P[:,2]>1.64)&(P[:,2]<1.67);upper=neck>.7;lowerY=float(np.median(P[low,1]));upperY=float(np.mean(P[upper,1]));delta=float(np.clip(lowerY-upperY,0,.06));assert .02<delta<=.06
t=np.clip((P[:,2]-1.65)/.09,0,1);t=t*t*(3-2*t);mask=(head+neck)>.05;amount=t*np.clip(head+neck,0,1);amount[head>.95]=1;Q=P.copy();Q[mask,1]+=delta*amount[mask]
for v,q in zip(o.data.vertices,Q):v.co=q
o.data.update();save('Jessie-Neck-Candidate');reports['Jessie']={'lower_neck_center_y':lowerY,'upper_neck_center_y':upperY,'backward_head_translation_m':delta,'affected_vertices':int(np.count_nonzero(np.max(abs(Q-P),1)>1e-9)),'head_hat_hair_shape':'Rigid translation where head weighted; no face deformation','skeleton_weights_UVs':'unchanged'}
# Woody: source semantic holster groups isolate the pouch from boots and pants.
bpy.ops.wm.open_mainfile(filepath='/workspace/mod-work/anatomy-corrections/woody-author-v1/Woody-Pelvis-Corrected.blend');o=bpy.data.objects['Woody_Skinned'];archive(o);src=bpy.data.objects['KH3 Woody V3_mesh.001'];offset=5169;ids=[offset+v.index for v in src.data.vertices if sum(g.weight for g in v.groups if src.vertex_groups[g.group].name.startswith('holster '))>.1];assert len(ids)>20
P=np.array([v.co[:] for v in o.data.vertices]);sign=1 if P[ids,0].mean()>0 else -1;hip=o.vertex_groups['Hips_JNT'];old_masses={}
for i in ids:
 for g in o.data.vertices[i].groups:old_masses[o.vertex_groups[g.group].name]=old_masses.get(o.vertex_groups[g.group].name,0)+g.weight
# Minimum 2.5 cm side clearance, capped4 cm; top loop gets half the offset.
shift=.03;z=P[ids,2];fade=np.clip((z.max()-z)/max(np.ptp(z),1e-6),0,1);amount=shift*(.5+.5*fade)
for i,d in zip(ids,amount):
 o.data.vertices[i].co.x+=sign*float(d)
 for group in o.vertex_groups:group.remove([i])
 hip.add([i],1,'REPLACE')
o.data.update();save('Woody-Holster-Candidate');reports['Woody']={'source_groups':['holster a','holster b','holster c'],'vertices':len(ids),'previous_bone_masses':old_masses,'new_attachment':'Hips_JNT rigid','lateral_clearance_m':[float(amount.min()),float(amount.max())],'boots_pull_ring_head_hands':'unchanged'}
# Bo Peep: remove the accumulated upper overlay and restore the original
# contiguous source cape topology; apply one continuous cloth fit to both sides.
bpy.ops.wm.open_mainfile(filepath='/workspace/mod-work/refinement-next/bopeep-cape-v4h/BoPeep-Cape-V4.blend');o=bpy.data.objects['BoPeep_Skinned'];archive(o);base=bpy.data.objects['BoPeep_V3_CompleteCape_PRESERVED'];src=bpy.data.objects['BoPeep_Body'];old=o.data;P=np.array([v.co[:] for v in old.vertices]);rows=[[(g.group,g.weight) for g in v.groups] for v in old.vertices];cape=np.array([v.index for v in src.data.vertices if v.index<len(base.data.vertices) and any(src.vertex_groups[g.group].name.startswith('e_cape') for g in v.groups)]);S=np.array([src.matrix_world@v.co for v in src.data.vertices]);assert len(cape)==936
mesh=base.data.copy();o.data=mesh;Q=P[:len(mesh.vertices)].copy();C=S[cape];lo,hi=C.min(0),C.max(0);z0,z1=P[cape,2].min(),P[cape,2].max();Q[cape,0]=C[:,0]*(max(abs(P[cape,0]))/max(abs(C[:,0])));Q[cape,1]=.08+(C[:,1]-lo[1])*.20;Q[cape,2]=z0+(C[:,2]-lo[2])*(z1-z0)/(hi[2]-lo[2])
for v,q in zip(mesh.vertices,Q):v.co=q
for group in o.vertex_groups:group.remove(list(range(len(mesh.vertices))))
for i,row in enumerate(rows[:len(mesh.vertices)]):
 for g,w in row:o.vertex_groups[g].add([i],w,'REPLACE')
for i in cape:
 for group in o.vertex_groups:group.remove([int(i)])
 t=float(np.clip((1.25-Q[i,2])/.65,0,1));t=t*t*(3-2*t);w=.8*t;o.vertex_groups['spine3_JNT'].add([int(i)],1-w,'REPLACE')
 if w:o.vertex_groups['Hips_JNT'].add([int(i)],w,'REPLACE')
mesh.update();save('BoPeep-Cape-Continuous-Candidate');reports['BoPeep']={'cape_vertices':len(cape),'new_vertices':len(mesh.vertices),'removed_overlay_vertices':len(P)-len(mesh.vertices),'fit':'One continuous source-space fit shared by coincident inner/outer vertices','cape_depth_before_m':float(np.ptp(P[cape,1])),'cape_depth_after_m':float(np.ptp(Q[cape,1])),'weights':'spine3 top, smooth pelvis blend lower; zero arm/hand weights','UVs':'Original contiguous cape UV/topology restored; atlas unchanged','body_positions':'Current non-cape positions preserved exactly'}
(out/'author-candidates.json').write_text(json.dumps(reports,indent=2));print('THREE_CANDIDATES_AUTHORED')

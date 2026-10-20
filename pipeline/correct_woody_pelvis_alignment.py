"""Correct the measured source-waist/native-hinge inversion, preserving V2 boots/ring.
No skeleton/rest/material/first-person changes. New output scene only.
"""
import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False);old=bpy.data.objects['Woody_Skinned'];o=old.copy();o.data=old.data.copy();bpy.context.collection.objects.link(o);old.name='Woody_Before_PelvisFix_Preserved';old.hide_render=True;old.hide_set(True);o.name='Woody_Skinned';m=o.data;arm=o.find_armature();sourcearm=bpy.data.objects['KH3 Woody V3_arm'];sw={b.name:np.array(sourcearm.matrix_world@b.head_local) for b in sourcearm.data.bones};nw={b.name:np.array(b.head_local) for b in arm.data.bones};names=[g.name for g in o.vertex_groups];mapping=json.loads(Path('/workspace/mod-work/woody-stage/rig-v4/rig-report.json').read_text())['mapping'];parts=[bpy.data.objects['KH3 Woody V3_mesh'+s] for s in ['', '.001','.002','.003','.004','.005','.006','.007','.008']];assert sum(len(p.data.vertices) for p in parts)==len(m.vertices)==32379
before=np.array([v.co[:] for v in m.vertices]);after=before.copy();nativeH=nw['Hips_JNT'];sourceH=sw['bip_pelvis'];sourceHip=(sw['bip_hip_L'][2]+sw['bip_hip_R'][2])/2;targetHip=(nw['l_UpperLeg_JNT'][2]+nw['r_UpperLeg_JNT'][2])/2;records=[];changed_weights=[];oldfiterrors=[];crossside=[]
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def segment(p,a,b,A,B,width):
 d=b-a;t=np.dot(p-a,d)/np.dot(d,d);R=np.array(Vector(d).rotation_difference(Vector(B-A)).to_matrix());return A+t*(B-A)+width*(R@(p-a-t*d))
def leg(p,side):
 s='l' if side=='L' else 'r';a,b,c=[sw[f'bip_{n}_{side}'] for n in ['hip','knee','foot']];A,C,D=[nw[f'{s}_{n}_JNT'] for n in ['UpperLeg','LowerLeg','Foot']];knee=smooth((b[2]+.065-p[2])/.13);q=(1-knee)*segment(p,a,b,A,C,1.35)+knee*segment(p,b,c,C,D,1.35);return q,{names.index(s+'_UpperLeg_JNT'):1-knee,names.index(s+'_LowerLeg_JNT'):knee}
def mixed(a,b,t):
 r={i:w*(1-t) for i,w in a.items()}
 for i,w in b.items():r[i]=r.get(i,0)+w*t
 return {i:float(w) for i,w in r.items() if w>1e-7}
offset=0
for part in parts:
 for v in part.data.vertices:
  vi=offset+v.index;p=np.array(part.matrix_world@v.co);orig={part.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0};total=sum(orig.values());orig={n:w/total for n,w in orig.items()}
  if part==parts[-1] or not .73<p[2]<1.15:continue
  if any(w>.0001 and (mapping[n]=='head_JNT' or 'Arm' in mapping[n] or 'Hand' in mapping[n] or '_hand_' in mapping[n] or '_shoulder_' in mapping[n]) for n,w in orig.items()):continue
  qold=nativeH+(p-sourceH)*[1.35,1.35,1.6];qold[2]+=.12*smooth((p[2]-1.02)/.15)+.08*smooth((abs(p[0]-sourceH[0])-.04)/.08)*smooth((p[2]-1.04)/.10)
  qnew=qold.copy();desiredZ=targetHip+1.35*(p[2]-sourceHip);blendHeight=smooth((1.15-p[2])/.10);qnew[2]=(1-blendHeight)*qold[2]+blendHeight*desiredZ
  row={}
  for n,w in orig.items():
   # Waist/seat helper belongs to pelvis, not the lumbar bend.
   target='Hips_JNT' if n=='pelvis adj' else mapping[n];i=names.index(target);row[i]=row.get(i,0)+w
  legmasses={s:sum(w for n,w in orig.items() if mapping[n] in [f'{s}_{k}_JNT' for k in ['UpperLeg','LowerLeg','Foot','Toes']]) for s in ['l','r']};amount=sum(legmasses.values())
  if amount>.01:
   oldside='L' if p[0]>sourceH[0] else 'R';side='L' if legmasses['l']>legmasses['r'] else 'R';legold,_=leg(p,oldside);legnew,legrow=leg(p,side);blend=smooth(amount);qold=(1-blend)*qold+blend*legold;qnew=(1-blend)*qnew+blend*legnew;row=mixed(row,legrow,blend)
   if oldside!=side:crossside.append(vi)
  oldfiterrors.append(float(np.max(abs(qold-before[vi]))));assert oldfiterrors[-1]<2e-6,(part.name,vi,oldfiterrors[-1])
  after[vi]=qnew;newrow={i:w for i,w in row.items() if w>1e-7};total=sum(newrow.values());newrow={i:w/total for i,w in newrow.items()};oldrow={g.group:g.weight for g in m.vertices[vi].groups if g.weight>1e-7}
  if any(abs(newrow.get(i,0)-oldrow.get(i,0))>1e-6 for i in oldrow.keys()|newrow.keys()):
   for group in o.vertex_groups:group.remove([vi])
   for i,w in newrow.items():o.vertex_groups[i].add([vi],w,'REPLACE')
   changed_weights.append(vi)
  records.append(vi)
 offset+=len(part.data.vertices)
for v,q in zip(m.vertices,after):v.co=q
m.update();forbidden=np.r_[np.arange(5169,11429),np.arange(32126,32379)];bootsLow=before[forbidden,2]<.40;assert np.array_equal(after[forbidden[bootsLow]],before[forbidden[bootsLow]]);assert np.array_equal(after[32126:],before[32126:]);assert np.array_equal(np.array([d.uv[:] for d in m.uv_layers.active.data]),np.array([d.uv[:] for d in old.data.uv_layers.active.data]));assert [tuple(f.vertices) for f in m.polygons]==[tuple(f.vertices) for f in old.data.polygons]
# Recalculate frames only where geometry moved; preserve unrelated custom normals.
oldnorm=np.array([l.normal[:] for l in old.data.loops]);affected=set(records);adj=set(affected)
for f in m.polygons:
 if any(i in affected for i in f.vertices):adj.update(f.vertices)
# Zero custom vectors request geometric normals for the edited neighborhood.
frames=[(0,0,0) if l.vertex_index in adj else tuple(oldnorm[l.index]) for l in m.loops];m.normals_split_custom_set(frames)
for b in arm.pose.bones:b.matrix_basis=Matrix.Identity(4)
np.savez_compressed(out/'correction.npz',before=before,positions=after,changed=np.flatnonzero(np.max(abs(after-before),axis=1)>1e-7),weight_changed=np.array(changed_weights));r={'status':'AUTHORING_CANDIDATE','cause':'Source pelvis control0.923m is above source leg hinges0.769m, but old fit put pelvis-control geometry at native0.965m below native hinges0.990m. Seat hung0.26m below hinge; thighs entered above seat.','source_hip_hinge_z_m':float(sourceHip),'native_hip_hinge_z_m':float(targetHip),'source_waist_z_m':float(sourceH[2]),'new_waist_z_m':float(targetHip+1.35*(sourceH[2]-sourceHip)),'old_fit_reproduction_max_error_m':max(oldfiterrors),'geometry_vertices_changed':int(np.count_nonzero(np.max(abs(after-before),axis=1)>1e-7)),'weights_changed':len(changed_weights),'upper_pants_cross_side_assignments_corrected':len(crossside),'ring_and_low_boot_vertices_exact_V2':True,'head_hands_skeleton_material_UVs_and_head_split_preserved':True,'runtime':'NOT TESTED'};(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Woody-Pelvis-Corrected.blend'),compress=True);print(json.dumps(r))

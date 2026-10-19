"""Focused source-proportion Jessie V2; keep V1 head, UVs and native rig exact.
Correct semantic twist mapping; fit clothing through common continuous fields,
not a sum of unrelated per-bone fit transforms. New outputs only.
"""
import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(parents=True,exist_ok=False)
obj=bpy.data.objects['Jessie_Skinned'];arm=obj.find_armature();srcarm=bpy.data.objects['park_jessie_armature'];bpy.context.view_layer.update();assert len(arm.data.bones)==189
rest={b.name:[list(row) for row in b.matrix_local] for b in arm.data.bones};index={b.name:i for i,b in enumerate(arm.data.bones)};sw={b.name:np.asarray(srcarm.matrix_world@b.head_local,dtype=float) for b in srcarm.data.bones};nw={b.name:np.asarray(b.head_local,dtype=float) for b in arm.data.bones}
old=np.asarray([v.co[:] for v in obj.data.vertices]);old_weights=[{g.group:g.weight for g in v.groups if g.weight>0} for v in obj.data.vertices]
old_uv=np.asarray([u.uv[:] for u in obj.data.uv_layers.active.data]);mapping=json.loads(Path('/workspace/mod-work/jessie-stage/rig-v6/rig-report.json').read_text())['mapping']
fixes={}
for side,short in [('L','l'),('R','r')]:
 for name in mapping:
  if name.startswith(f'Bip001 {side}UpArmTwist'):fixes[name]={'old':mapping[name],'new':f'{short}_upperArm_JNT'};mapping[name]=f'{short}_upperArm_JNT'
  elif name.startswith(f'Bip001 {side} ForeTwist'):fixes[name]={'old':mapping[name],'new':f'{short}_lowerArm_JNT'};mapping[name]=f'{short}_lowerArm_JNT'
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def rotate(a,b):return np.asarray(Vector(a.tolist()).rotation_difference(Vector(b.tolist())).to_matrix())
def segment(p,a,b,A,B,width):
 axis=b-a;t=float((p-a)@axis/(axis@axis));r=p-a-t*axis
 return A+t*(B-A)+width*(rotate(axis,B-A)@r)
def normalized(row):
 row={int(k):float(v) for k,v in row.items() if v>1e-7};s=sum(row.values());assert s>0;return {k:v/s for k,v in row.items()}
def mix(a,b,t):
 row={k:v*(1-t) for k,v in a.items()}
 for k,v in b.items():row[k]=row.get(k,0)+v*t
 return normalized(row)
hip=sw['Bip001 Pelvis'];H=nw['Hips_JNT'];height_scale=(nw['head_JNT'][2]-H[2])/(sw['Bip001 Head'][2]-hip[2]);width_scale=1.35
points=[];rows=[];head_masks=[];regions=[];source_positions=[];component_labels=[];part_reports=[]
for part in ['park_jessie_ob0_L0','park_jessie_ob3_L0','park_jessie_ob6_L0']:
 source=bpy.data.objects[part];source.data.calc_loop_triangles();base=len(points);part_head=0
 for v in source.data.vertices:
  p=np.asarray(source.matrix_world@v.co,dtype=float);source_positions.append(p);orig={source.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0};head_sum=sum(w for n,w in orig.items() if mapping[n]=='head_JNT')
  accepted_head=part=='park_jessie_ob6_L0' or (part=='park_jessie_ob0_L0' and head_sum>.999) or (part=='park_jessie_ob3_L0' and p[2]>=sw['Bip001 Head'][2])
  if accepted_head:
   points.append(old[base+v.index]);rows.append(old_weights[base+v.index]);head_masks.append(True);regions.append('accepted_head');part_head+=1;continue
  q=H+(p-hip)*[width_scale,width_scale,height_scale]
  row={}
  for name,w in orig.items():i=index[mapping[name]];row[i]=row.get(i,0)+w
  row=normalized(row);region='torso'
  # One common anatomical field for every leg surface, irrespective of its
  # original mesh, clothing component or source skin weights.
  source_arm_weight=sum(w for n,w in orig.items() if any(tag in n for tag in ['UpperArm','UpArmTwist','Forearm','ForeTwist',' Hand','Finger']))
  legblend=0. if source_arm_weight>.05 else 1-smooth((p[2]-(hip[2]-.04))/.10)
  if legblend>0:
   side,short=('L','l') if p[0]>=0 else ('R','r');prefix=f'Bip001 {side} '
   s0,s1,s2=[sw[prefix+n] for n in ['Thigh','Calf','Foot']];t0,t1,t2=[nw[f'{short}_{n}_JNT'] for n in ['UpperLeg','LowerLeg','Foot']]
   upper=segment(p,s0,s1,t0,t1,1.30);lower=segment(p,s1,s2,t1,t2,1.30);knee=smooth((s1[2]+.07-p[2])/.14);leg=(1-knee)*upper+knee*lower
   legrow={index[f'{short}_UpperLeg_JNT']:1-knee,index[f'{short}_LowerLeg_JNT']:knee}
   ankle=smooth((s2[2]+.045-p[2])/.09)
   if ankle>0:
    foot=segment(p,s2,sw[prefix+'Toe0'],t2,nw[f'{short}_Toes_JNT'],1.18);leg=(1-ankle)*leg+ankle*foot;legrow=mix(legrow,{index[f'{short}_Foot_JNT']:1},ankle)
   q=(1-legblend)*q+legblend*leg;row=mix(row,legrow,legblend);region='leg'
  armweights={side:sum(w for n,w in orig.items() if n.startswith(f'Bip001 {side}') and any(k in n for k in ['UpperArm','UpArmTwist','Forearm','ForeTwist',' Hand','Finger'])) for side in ['L','R']}
  side=max(armweights,key=armweights.get);blend=smooth(armweights[side]);short='l' if side=='L' else 'r';label='Left' if side=='L' else 'Right';prefix=f'Bip001 {side} '
  if blend>0 and p[2]>.7:
   s0,s1,s2=[sw[prefix+n] for n in ['UpperArm','Forearm','Hand']];t0,t1,t2=[nw[f'{short}_{n}_JNT'] for n in ['upperArm','lowerArm','hand']]
   a=s1-s0;projection=float((p-s0)@a/(a@a));elbow=smooth((projection-.75)/.50)
   upper=segment(p,s0,s1,t0,t1,1.25);lower=segment(p,s1,s2,t1,t2,1.25);ap=(1-elbow)*upper+elbow*lower
   handweight=sum(w for n,w in orig.items() if n.startswith(prefix+'Hand') or n.startswith(prefix+'Finger'));hand=smooth(handweight)
   if hand>0:
    direction=sw[prefix+'Finger2']-s2;dest=nw[label+'HandMiddle1_JNT']-t2;hp=t2+1.15*(rotate(direction,dest)@(p-s2));ap=(1-hand)*ap+hand*hp
    # Keep the source hand silhouette intact instead of stretching each digit
    # to the longer native finger chain. No individual digit animation yet.
    row=mix(row,{index[f'{short}_hand_JNT']:1},hand)
   q=(1-blend)*q+blend*ap;region='hand' if hand>.5 else 'arm'
  if part=='park_jessie_ob3_L0' and region=='torso':
   neckblend=smooth((p[2]-1.30)/(sw['Bip001 Head'][2]-1.30));q=(1-neckblend)*q+neckblend*old[base+v.index]
  points.append(q);rows.append(normalized(row));head_masks.append(False);regions.append(region)
 # Small same-bone decorative components stay rigid/near rigid rather than
 # carrying inconsistent vertex weights through a tiny buckle/tassel.
 parent=list(range(len(source.data.vertices)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for tri in source.data.loop_triangles:
  for vi in tri.vertices[1:]:a,b=root(tri.vertices[0]),root(vi);parent[b]=a
 labels=np.asarray([root(i) for i in range(len(parent))]);component_labels.extend(labels.tolist())
 for lab in set(labels):
  ids=np.flatnonzero(labels==lab)+base
  if len(ids)>72 or any(head_masks[i] for i in ids) or any(regions[i]!='leg' for i in ids):continue
  if np.ptp(np.asarray(source_positions)[ids],axis=0).max()>=.09:continue  # long denim-leg components are not decorations
  # Uniform weights across small leg decorations; blend upper/lower by their
  # common centroid weights, preserving attachment to the same side.
  avg={}
  for vi in ids:
   for k,w in rows[vi].items():avg[k]=avg.get(k,0)+w/len(ids)
  avg=normalized(avg)
  for vi in ids:rows[vi]=avg.copy()
 part_reports.append({'part':part,'vertices':len(source.data.vertices),'accepted_head_vertices_exact':part_head})
leg_indices={i for n,i in index.items() if any(k in n for k in ['UpperLeg','LowerLeg','Foot_JNT','Toes_JNT'])}
for region,row in zip(regions,rows):
 if region in ['arm','hand']:assert not any(i in leg_indices for i in row),('Cross-limb leg influence',region,row)
positions=np.asarray(points);head_mask=np.asarray(head_masks);assert len(positions)==4883 and np.isfinite(positions).all();assert np.array_equal(positions[head_mask],old[head_mask]);obj.data=obj.data.copy()
for v,p in zip(obj.data.vertices,positions):v.co=p
obj.vertex_groups.clear()
for b in arm.data.bones:obj.vertex_groups.new(name=b.name)
for vi,row in enumerate(rows):
 assert len(row)<=8
 for j,w in row.items():obj.vertex_groups[j].add([vi],w,'REPLACE')
obj.data.update();assert np.array_equal(old_uv,np.asarray([u.uv[:] for u in obj.data.uv_layers.active.data]));assert rest=={b.name:[list(r) for r in b.matrix_local] for b in arm.data.bones}
# Update the existing hidden fitted parts only in the new scene, so generic
# provenance tools can compare the same per-part V2 data without old V1 clones.
offset=0
for part in ['park_jessie_ob0_L0','park_jessie_ob3_L0','park_jessie_ob6_L0']:
 fitted=bpy.data.objects[part+'_Hoops_Skinned'];count=len(fitted.data.vertices)
 for v,p in zip(fitted.data.vertices,positions[offset:offset+count]):v.co=p
 fitted.vertex_groups.clear()
 for b in arm.data.bones:fitted.vertex_groups.new(name=b.name)
 for vi,row in enumerate(rows[offset:offset+count]):
  for j,w in row.items():fitted.vertex_groups[j].add([vi],w,'REPLACE')
 offset+=count
np.savez_compressed(out/'expected.npz',positions=positions.astype('f4'),indices=np.asarray([p.vertices[:] for p in obj.data.polygons]),loop_uv=old_uv,accepted_head=head_mask,V1_positions=old,source_positions=np.asarray(source_positions),region=np.asarray(regions))
joints=np.zeros((len(rows),8),dtype='u2');weights=np.zeros((len(rows),8),dtype='f4')
for vi,row in enumerate(rows):
 for k,(j,w) in enumerate(sorted(row.items())):joints[vi,k]=j;weights[vi,k]=w
np.savez_compressed(out/'skin.npz',joints=joints,weights=weights)
report={'scope':'Focused V2 geometry/weight correction; original native bones, atlas and materials unchanged','twist_mapping_corrections':fixes,'torso_horizontal_scale':width_scale,'torso_vertical_scale':height_scale,'limb_transverse_scales':{'arm':1.25,'leg':1.30,'foot':1.18,'hand':1.15},'accepted_head_vertices_exact':int(head_mask.sum()),'parts':part_reports,'head_face_hat_hair_eye_positions_and_weights_preserved':True,'UVs_materials_native_rest_matrices_unchanged':True,'chaps':'Same continuous geometry and leg weights as pants; small decorations near rigid','hand_limit':'Source hand shape follows native hand rigidly; individual finger curls simplified','runtime_test':'NOT RUN'}
(out/'correction-report.json').write_text(json.dumps(report,indent=2)+'\n');obj['version']='Jessie V2 focused proportional/weight correction';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Jessie-Hoops-V2.blend'),compress=True);print(json.dumps(report),flush=True)

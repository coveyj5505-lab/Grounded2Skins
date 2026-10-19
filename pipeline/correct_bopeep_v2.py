"""Focused hands/cape correction on a new copy of the accepted Bo Peep rig.
Keep native rest, face/body/UVs, material and preserved crook unchanged.
Initially rigid source-shaped hands favor stable doll fingers over fine grips.
"""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(parents=True,exist_ok=False)
old=bpy.data.objects['BoPeep_Skinned'];arm=old.find_armature();source=bpy.data.objects['BoPeep_Body'];srcarm=source.find_armature();bpy.context.view_layer.update()
assert len(arm.data.bones)==192 and len(old.data.vertices)==len(source.data.vertices)==5028
oldpos=np.asarray([v.co[:] for v in old.data.vertices]);oldrows=[{g.group:g.weight for g in v.groups if g.weight>0} for v in old.data.vertices]
sw={b.name:np.asarray(srcarm.matrix_world@b.head_local,dtype=float) for b in srcarm.data.bones};nw={b.name:np.asarray(b.head_local,dtype=float) for b in arm.data.bones};idx={b.name:i for i,b in enumerate(arm.data.bones)}
o=old.copy();o.data=old.data.copy();bpy.context.collection.objects.link(o);old.name='BoPeep_V1_Preserved';old.hide_render=True;old.hide_set(True);o.name='BoPeep_Skinned';assert not o.data.shape_keys
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def rotate(a,b):return np.asarray(Vector(a.tolist()).rotation_difference(Vector(b.tolist())).to_matrix())
def mix(a,b,t):
 r={k:w*(1-t) for k,w in a.items()}
 for k,w in b.items():r[k]=r.get(k,0)+w*t
 r={k:w for k,w in r.items() if w>1e-7};total=sum(r.values());return {k:w/total for k,w in r.items()}
points=oldpos.copy();rows=[dict(r) for r in oldrows];regions=[];hand_ids=[];cape_ids=[];cape_old_arm=0
for v in source.data.vertices:
 i=v.index;p=np.asarray(source.matrix_world@v.co,dtype=float);g={source.vertex_groups[a.group].name:a.weight for a in v.groups if a.weight>0};region='unchanged'
 if any(n.startswith('e_cape') for n in g):
  # A single coherent chest transform for ALL cape vertices removes mixed
  # arm influence and inconsistent positional fitting at upper-cape seams.
  a=sw['e_neck_m']-sw['e_chest_m'];b=nw['neck1_JNT']-nw['spine3_JNT'];u=a/np.linalg.norm(a);scale=.25;along=np.eye(3)+(np.linalg.norm(b)/(np.linalg.norm(a)*scale)-1)*np.outer(u,u)
  points[i]=nw['spine3_JNT']+rotate(a,b)@along@((p-sw['e_chest_m'])*scale);rows[i]={idx['spine3_JNT']:1.};cape_ids.append(i);region='cape'
  cape_old_arm+=any(any(tag in name for tag in ['scapula','shoulder','elbow','wrist']) for name in g)
 else:
  amounts={side:sum(w for n,w in g.items() if n==f'e_wrist_{side}' or ('finger' in n and n.endswith('_'+side))) for side in ['l','r']};side=max(amounts,key=amounts.get);amount=smooth(amounts[side])
  if amount>0:
   label='Left' if side=='l' else 'Right';a=sw[f'e_middlefinger1_{side}']-sw[f'e_wrist_{side}'];b=nw[f'{label}HandMiddle1_JNT']-nw[f'{side}_hand_JNT'];q=nw[f'{side}_hand_JNT']+.25*(rotate(a,b)@(p-sw[f'e_wrist_{side}']))
   points[i]=(1-amount)*points[i]+amount*q;rows[i]=mix(rows[i],{idx[f'{side}_hand_JNT']:1},amount);hand_ids.append(i);region='hand_'+side
 regions.append(region)
assert len(cape_ids)==936 and cape_old_arm==54
for v,q,row in zip(o.data.vertices,points,rows):
 v.co=q
 for group in o.vertex_groups:group.remove([v.index])
 for j,w in row.items():o.vertex_groups[j].add([v.index],w,'REPLACE')
o.data.update();unchanged=[i for i,r in enumerate(regions) if r=='unchanged'];assert np.array_equal(points[unchanged],oldpos[unchanged])
assert all(rows[i]==oldrows[i] for i in unchanged)
np.savez_compressed(out/'expected.npz',positions=points,regions=regions,old_positions=oldpos)
report={'vertices':5028,'bones':192,'unchanged_vertices':len(unchanged),'hands_changed_vertices':len(hand_ids),'cape_vertices':len(cape_ids),'cape_previously_mixed_arm_vertices':cape_old_arm,'cape_new_arm_influences':0,'hands':'Uniform source-shaped hand fit; predominantly rigid native-hand weights; individual finger animation intentionally simplified','cape':'Single torso transform and rigid spine3 weights; stiff cape, no new cloth simulation','appearance_outside_masks_positions_and_weights_exact':True,'material_UVs_topology_native_rest_unchanged':True,'crook':'Preserved on original object; not exported','runtime':'NOT TESTED'}
(out/'corrections.json').write_text(json.dumps(report,indent=2)+'\n');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'BoPeep-Willow-V2.blend'),compress=True);print(json.dumps(report),flush=True)

#!/usr/bin/env python3
"""Name/parent/order and sign-invariant bind-pose comparison, no retargeting."""
import argparse,json,math
from pathlib import Path
import numpy as np


def compare(reference,candidate,translation_tol_cm=.001,rotation_tol_deg=.001,scale_tol=.000001):
 a={x['name']:x for x in reference};b={x['name']:x for x in candidate};assert len(a)==len(reference) and len(b)==len(candidate)
 def parent(table,bone):return None if bone['parent']<0 else table[bone['parent']]['name']
 common=sorted(a.keys()&b.keys());missing=sorted(a.keys()-b.keys());extra=sorted(b.keys()-a.keys());changes=[];max_t=max_r=max_s=0.
 exact=len(a)==len(b)
 for name in common:
  x,y=a[name],b[name];t=float(np.linalg.norm(np.asarray(x['translation_cm'])-y['translation_cm']));s=float(np.max(np.abs(np.asarray(x['scale_xyz'])-y['scale_xyz'])))
  q0=np.asarray(x['rotation_xyzw']);q1=np.asarray(y['rotation_xyzw']);q0/=np.linalg.norm(q0);q1/=np.linalg.norm(q1)
  # q and -q encode the same rotation; avoid treating sign as a rig change.
  dot=min(1.,abs(float(q0@q1)));r=0. if dot>1-1e-14 else math.degrees(2*math.acos(dot))
  p0,p1=parent(reference,x),parent(candidate,y);order=x['index']!=y['index']
  exact &= x['index']==y['index'] and x['parent']==y['parent'] and all(np.array_equal(np.asarray(x[k]),np.asarray(y[k])) for k in ['rotation_xyzw','translation_cm','scale_xyz']);max_t=max(max_t,t);max_r=max(max_r,r);max_s=max(max_s,s)
  if p0!=p1 or order or t>translation_tol_cm or r>rotation_tol_deg or s>scale_tol:
   changes.append({'bone':name,'reference_index':x['index'],'candidate_index':y['index'],'reference_parent':p0,'candidate_parent':p1,'translation_error_cm':t,'rotation_error_deg':r,'scale_error_max':s,'meaningful_pose_or_parent_difference':p0!=p1 or t>translation_tol_cm or r>rotation_tol_deg or s>scale_tol})
 identical_names=not missing and not extra;hierarchy=identical_names and all(parent(reference,a[n])==parent(candidate,b[n]) for n in common)
 return {'reference_bones':len(a),'candidate_bones':len(b),'missing_bones':missing,'extra_bones':extra,'bone_order_equal':identical_names and [x['name'] for x in reference]==[x['name'] for x in candidate],'hierarchy_equal_by_name':hierarchy,'raw_bone_records_exact':bool(exact),'rest_pose_equal_within_tolerance':hierarchy and max_t<=translation_tol_cm and max_r<=rotation_tol_deg and max_s<=scale_tol,'max_local_translation_error_cm':max_t,'max_local_rotation_error_deg':max_r,'max_local_scale_error':max_s,'tolerances':{'translation_cm':translation_tol_cm,'rotation_degrees':rotation_tol_deg,'scale':scale_tol},'differences':changes,'scope':'Compares actual supplied bone tables; does not prove all animation/retarget settings or runtime behavior.'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('reference',type=Path);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path);x=p.parse_args();assert not x.output.exists()
 load=lambda f:json.loads(f.read_text())['meshes'][0]['bones']
 x.output.write_text(json.dumps(compare(load(x.reference),load(x.candidate)),indent=2)+'\n')

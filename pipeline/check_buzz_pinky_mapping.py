#!/usr/bin/env python3
"""Controlled local-axis pinky diagnostic; no rig, weights or bind data edited."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
p=argparse.ArgumentParser(description=__doc__);p.add_argument('reference',type=Path);p.add_argument('stock',type=Path);p.add_argument('geometry',type=Path);p.add_argument('new_report',type=Path);a=p.parse_args();assert not a.new_report.exists()
r=json.loads(a.reference.read_text())['meshes'][0]['bones'];s=json.loads(a.stock.read_text())['meshes'][0]['bones'];z=np.load(a.geometry)
def world(bones):
 mats={}
 for b in bones:
  t=np.eye(4);t[:3,:3]=Rotation.from_quat(b['rotation_xyzw']).as_matrix()@np.diag(b['scale_xyz']);t[:3,3]=b['translation_cm'];mats[b['name']]=t if b['parent']<0 else mats[bones[b['parent']]['name']]@t
 return mats
rw,sw=world(r),world(s);used=sorted(set(z['joints'][z['weights']>0].astype(int)));assert all(0<=i<len(r) for i in used);assert len({r[i]['name'] for i in used})==len(used);assert all(r[i]['name'] in sw for i in used)
results=[];positions=np.c_[z['positions'],np.ones(len(z['positions']))]
for name in ['LeftHandPinky3_JNT','RightHandPinky3_JNT']:
 i=next(i for i,b in enumerate(r) if b['name']==name);w=np.sum(np.where(z['joints']==i,z['weights'],0),axis=1);mask=w>0;records=[]
 for axis in range(3):
  for deg in [-45,45]:
   rot=np.eye(4);v=np.zeros(3);v[axis]=np.radians(deg);rot[:3,:3]=Rotation.from_rotvec(v).as_matrix()
   deforms=[]
   for frames in [rw,sw]:
    t=frames[name];delta=t@rot@np.linalg.inv(t);deforms.append(z['positions']+w[:,None]*((positions@delta.T)[:,:3]-z['positions']))
   errors=np.linalg.norm(deforms[0]-deforms[1],axis=1);assert all(np.isfinite(d).all() for d in deforms)
   records.append({'local_axis':'XYZ'[axis],'degrees':deg,'max_displacement_difference_cm':float(errors.max()),'rms_influenced_difference_cm':float(np.sqrt(np.mean(errors[mask]**2)))})
 results.append({'bone':name,'influenced_render_vertices':int(mask.sum()),'maximum_weight':float(w.max()),'controlled_pose_results':records})
report={'weighted_bones':len(used),'all_positive_weight_joints_valid_unique_and_present_by_name_in_stock':True,'pinky_tests':results,'scope':'Same +/-45 degree local-axis rotation applied separately in recovered and stock bind frames. This measures sensitivity to frame choice, not real game animation or which frame is artistically correct. No animation tracks, sockets or retarget policies are inferred.','correction':'None: no invalid/missing weighted bone mapping found. Keep recovered baseline intact for first gameplay test. A bind-frame change without animation evidence could introduce errors.','runtime':'Buzz not yet tested in Grounded 2'}
a.new_report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'weighted_bones':len(used),'max_controlled_difference_cm':max(t['max_displacement_difference_cm'] for b in results for t in b['controlled_pose_results'])}))

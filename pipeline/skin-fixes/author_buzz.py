import bpy,numpy as np,json
from pathlib import Path
from mathutils import Matrix
out=Path('/workspace/mod-work/skin-fixes-next');base=Path('/workspace/mod-work/refinement-next/buzz-arms-v1');fit=np.load('/workspace/mod-work/rig-stage/skinned-stowed-v2-proportions/expected.npz');S=np.load('/workspace/mod-work/rig-stage/landmarks/source.npz')['positions']*[-1,-1,1];S=S[fit['source_vertices']];D=np.load(base/'body-points-clearance.npz');P=D['positions'];Q=P.copy();ids=D['body_original_ids'];z=dict(np.load(base/'geometry-clearance.npz'));W=z['weights'].copy();Joints=z['joints'].copy();records=[]
bpy.ops.wm.open_mainfile(filepath=str(base/'Buzz-Arms-Clearance.blend'));o=bpy.data.objects['Buzz_Skinned'];arm=o.find_armature();names=[g.name for g in o.vertex_groups];chest=names.index('chest_JNT');keep=np.where(~np.isin(fit['component'],[15,55]))[0];assert len(keep)==len(o.data.vertices)
archive=o.copy();archive.data=o.data.copy();archive.name='Buzz_Arm_Baseline_PRESERVED';bpy.context.collection.objects.link(archive);archive.hide_render=True;archive.hide_set(True)
for sign,upper,elbow in [(1,13,11),(-1,56,60)]:
 a=np.array([sign*.35,.435,1.425]);b=S[fit['component']==elbow].mean(0);v=b-a;t=((S-a)@v)/(v@v);mask=fit['component']==upper;prox=mask&(t<.3);before=P[prox].mean(0);target=np.array([sign*.369,.004,1.424]);delta=(target-before)*.70;x=np.clip((t-.3)/.7,0,1);blend=1-x*x*(3-2*x);Q[mask]+=blend[mask,None]*delta
 # Exact localized deformation frame for old fitted upper-arm points.
 coeff=np.linalg.lstsq(np.c_[P[mask],np.ones(mask.sum())],t[mask],rcond=None)[0];assert np.max(abs(np.c_[P[mask],np.ones(mask.sum())]@coeff-t[mask]))<1e-5
 render=np.where(mask[ids])[0];dets=[]
 for ri in render:
  bi=ids[ri];derivative=-(6*x[bi]-6*x[bi]*x[bi])/.7 if .3<t[bi]<1 else 0;J=np.eye(3)+np.outer(delta,coeff[:3]*derivative);C=np.diag([1.,-1,1]);J=C@J@C;dets.append(np.linalg.det(J));N=z['normals'][ri]@np.linalg.inv(J);N/=np.linalg.norm(N);T=z['tangents'][ri]@J.T;T-=N*np.dot(N,T);T/=np.linalg.norm(T);z['normals'][ri]=N;z['tangents'][ri]=T
  mass=float(blend[bi]);armbone=names.index(('l' if sign>0 else 'r')+'_upperArm_JNT');W[ri]=0;Joints[ri]=0;Joints[ri,0]=chest;W[ri,0]=mass;Joints[ri,1]=armbone;W[ri,1]=1-mass
 assert min(dets)>.25,('folded deformation',min(dets))
 # Use identical semantic blend in the authoring mesh.
 for vi,bi in enumerate(keep):
  if not mask[bi]:continue
  for g in o.vertex_groups:g.remove([vi])
  mass=float(blend[bi]);o.vertex_groups[chest].add([vi],mass,'REPLACE')
  if mass<1:o.vertex_groups[armbone].add([vi],1-mass,'REPLACE')
 records.append({'side':sign,'proximal_center_before':before.tolist(),'measured_side_socket_target':target.tolist(),'candidate_proximal_center':(before+delta).tolist(),'translation_m':delta.tolist(),'min_deformation_determinant':float(min(dets)),'upper_ball':'rigid translation and chest attachment; distal transition retains upper-arm animation','elbows_forearms_hands':'geometry and weights unchanged'})
z['weights']=W;z['joints']=Joints;changed=np.isin(fit['component'][ids],[13,56]);z['positions'][changed]=(Q[ids[changed]]*[100,-100,100]).astype('f4');np.savez_compressed(out/'Buzz-Shoulder-Candidate.npz',**z)
for vi,bi in enumerate(keep):o.data.vertices[vi].co=Q[bi]
o.data.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Buzz-Shoulder-Candidate.blend'),compress=True);(out/'Buzz-Shoulder-Report.json').write_text(json.dumps(records,indent=2));print('BUZZ_SHOULDER_CANDIDATE_SAVED')

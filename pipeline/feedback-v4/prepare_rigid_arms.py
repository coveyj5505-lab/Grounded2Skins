"""Offline rigid upper-shell candidate; preserve accepted controlled-idle placement.
This is not a native animation preview or a released asset.
"""
import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector,Matrix
out=Path('/tmp/toystory-feedback-v4');out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath='/workspace/mod-work/feedback-v3-source-backup/Buzz.blend')
o=bpy.data.objects['Buzz_Skinned'];arm=o.find_armature();names=[g.name for g in o.vertex_groups]
z=dict(np.load('/tmp/toystory-feedback-v3/Buzz-geometry.npz'));fit=np.load('/workspace/mod-work/rig-stage/skinned-stowed-v2-proportions/expected.npz');ids=np.load('/workspace/mod-work/refinement-next/buzz-arms-v1/body-points-clearance.npz')['body_original_ids'];comp=fit['component'][ids]
def reset():
 for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def aim(a,b,d):
 bpy.context.view_layer.update();pb=arm.pose.bones[a];A=pb.matrix.translation.copy();B=arm.pose.bones[b].matrix.translation.copy();R=(B-A).rotation_difference(Vector(d));pb.matrix=Matrix.Translation(A)@R.to_matrix().to_4x4()@Matrix.Translation(-A)@pb.matrix
reset()
for side,k in [('l',1),('r',-1)]:
 aim(side+'_upperArm_JNT',side+'_lowerArm_JNT',(k*.12,0,-1));aim(side+'_lowerArm_JNT',side+'_wrist_JNT',(k*.05,-.12,-1))
bpy.context.view_layer.update();skin=np.array([np.asarray(arm.pose.bones[n].matrix)@np.linalg.inv(np.asarray(arm.data.bones[n].matrix_local)) for n in names]);P=z['positions']*[.01,-.01,.01];M=np.sum(skin[z['joints']]*z['weights'][:,:,None,None],axis=1);posed=np.einsum('nij,nj->ni',M[:,:3,:3],P)+M[:,:3,3];records=[]
for c,side in [(13,'l'),(56,'r')]:
 mask=comp==c;j=names.index(side+'_upperArm_JNT');B=skin[j];new=np.linalg.solve(B[:3,:3],(posed[mask]-B[:3,3]).T).T;old=M[mask,:3,:3];J=np.einsum('ij,njk->nik',np.linalg.inv(B[:3,:3]),old);flip=np.diag([1.,-1,1]);J=np.einsum('ij,njk,kl->nil',flip,J,flip)
 N=np.einsum('ni,nij->nj',z['normals'][mask],np.linalg.inv(J));N/=np.linalg.norm(N,axis=1,keepdims=True);T=np.einsum('nij,nj->ni',J,z['tangents'][mask]);T-=N*np.sum(N*T,axis=1,keepdims=True);T/=np.linalg.norm(T,axis=1,keepdims=True)
 z['positions'][mask]=new*[100,-100,100];z['normals'][mask]=N;z['tangents'][mask]=T;z['joints'][mask]=0;z['weights'][mask]=0;z['joints'][mask,0]=j;z['weights'][mask,0]=1
 check=new@B[:3,:3].T+B[:3,3];records.append({'component':c,'bone':names[j],'vertices':int(mask.sum()),'idle_position_max_error_m':float(np.max(abs(check-posed[mask]))),'prior_chest_average_mass':float(np.mean(np.sum(np.load('/tmp/toystory-feedback-v3/Buzz-geometry.npz')['weights'][mask]*(np.load('/tmp/toystory-feedback-v3/Buzz-geometry.npz')['joints'][mask]==names.index('chest_JNT')),axis=1)))})
np.savez_compressed(out/'Buzz-rigid-upper-candidate.npz',**z);(out/'rigid-upper-report.json').write_text(json.dumps({'status':'OFFLINE_CANDIDATE_REQUIRES_POSED_RENDER_REVIEW','changes':records,'unchanged':'skeleton, hands, elbow/forearm weights, textures, all other geometry'},indent=2));reset();print('RIGID_UPPER_CANDIDATE',records)

# Measure existing shell stretching under non-idle controlled FK poses.
baseline=dict(np.load('/tmp/toystory-feedback-v3/Buzz-geometry.npz'));results=[]
mask=np.isin(comp,[13,56]);tri=z['indices'][np.all(mask[z['indices']],axis=1)];edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0)
rest=np.linalg.norm(posed[edges[:,0]]-posed[edges[:,1]],axis=1);edges=edges[rest>1e-5];rest=rest[rest>1e-5]
for pose in ['raised','bent']:
 reset()
 for side,k in [('l',1),('r',-1)]:
  aim(side+'_upperArm_JNT',side+'_lowerArm_JNT',(k*.25,0,1) if pose=='raised' else (k*.55,-.45,-.25));aim(side+'_lowerArm_JNT',side+'_wrist_JNT',(k*.1,-.2,1) if pose=='raised' else (k*.05,-.7,.6))
 bpy.context.view_layer.update();skin2=np.array([np.asarray(arm.pose.bones[n].matrix)@np.linalg.inv(np.asarray(arm.data.bones[n].matrix_local)) for n in names])
 for label,data in [('V3',baseline),('rigid',z)]:
  blend=np.sum(skin2[data['joints']]*data['weights'][:,:,None,None],axis=1);q=np.einsum('nij,nj->ni',blend[:,:3,:3],data['positions']*[.01,-.01,.01])+blend[:,:3,3];ratio=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/rest;results.append({'pose':pose,'candidate':label,'edge_length_ratio_min':float(ratio.min()),'edge_length_ratio_max':float(ratio.max()),'edge_length_ratio_p95':float(np.percentile(ratio,95))})
(out/'controlled-pose-strain.json').write_text(json.dumps(results,indent=2));print('STRAIN',results)

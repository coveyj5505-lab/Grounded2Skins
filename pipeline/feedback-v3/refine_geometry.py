import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector,Matrix
r=Path('/tmp/toystory-feedback-v3');old=Path('/workspace/mod-work/skin-fixes-next');sem=json.load(open(r/'semantic-source.json'))[''];bpy.ops.wm.open_mainfile(filepath=str(r/'Woody.blend'));o=bpy.data.objects['Woody_Skinned'];P=np.array(sem['source']);C=P.mean(0);_,_,vt=np.linalg.svd(P-C,full_matrices=False);N=vt[-1];N*=1 if N[1]<0 else -1;V=np.array([0.,0.,1.]);V-=N*np.dot(V,N);V/=np.linalg.norm(V);H=np.cross(V,N);assert H[0]>0;local=np.c_[(P-C)@H,(P-C)@N,(P-C)@V];scale=.145/max(np.ptp(local[:,0]),np.ptp(local[:,2]));Q=local*scale;Q[:,0]+=.091;Q[:,1]=-.162-Q[:,1]*.35;Q[:,2]+=1.445
for i,q in zip(sem['ids'],Q):o.data.vertices[i].co=q
badge=set(sem['ids']);norms=[]
for f in o.data.polygons:
 for li in f.loop_indices:norms.append((0,0,0) if all(i in badge for i in f.vertices) else o.data.loops[li].normal[:])
o.data.normals_split_custom_set(norms);o.data.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'Woody.blend'),compress=True)
# Curved shoulder-level underlay, with a lower central neckline.
bpy.ops.wm.open_mainfile(filepath=str(r/'BoPeep.blend'));o=bpy.data.objects['BoPeep_Skinned'];assert len(o.data.vertices)==5008
for i in range(9):o.data.vertices[4972+27+i].co.z=1.510+.040*abs(-1+i/4)
o.data.update();bpy.ops.wm.save_as_mainfile(filepath=str(r/'BoPeep.blend'),compress=True)
# Correct Buzz elbow clearance in a representative idle pose, then map that
# local cosmetic deformation back through each vertex's unchanged skin blend.
bpy.ops.wm.open_mainfile(filepath=str(old/'Buzz-Shoulder-Candidate.blend'));o=bpy.data.objects['Buzz_Skinned'];arm=o.find_armature();names=[g.name for g in o.vertex_groups]
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
def aim(a,b,d):
 bpy.context.view_layer.update();pb=arm.pose.bones[a];A=pb.matrix.translation.copy();B=arm.pose.bones[b].matrix.translation.copy();R=(B-A).rotation_difference(Vector(d));pb.matrix=Matrix.Translation(A)@R.to_matrix().to_4x4()@Matrix.Translation(-A)@pb.matrix
for side,k in [('l',1),('r',-1)]:aim(side+'_upperArm_JNT',side+'_lowerArm_JNT',(k*.12,0,-1));aim(side+'_lowerArm_JNT',side+'_wrist_JNT',(k*.05,-.12,-1))
bpy.context.view_layer.update();skin=np.array([np.asarray(arm.pose.bones[n].matrix)@np.linalg.inv(np.asarray(arm.data.bones[n].matrix_local)) for n in names]);z=dict(np.load(old/'Buzz-Shoulder-Candidate.npz'));P=z['positions']*[.01,-.01,.01];M=np.sum(skin[z['joints']]*z['weights'][:,:,None,None],axis=1);posed=np.einsum('nij,nj->ni',M[:,:3,:3],P)+M[:,:3,3];fit=np.load('/workspace/mod-work/rig-stage/skinned-stowed-v2-proportions/expected.npz');ids=np.load('/workspace/mod-work/refinement-next/buzz-arms-v1/body-points-clearance.npz')['body_original_ids'];comp=fit['component'][ids];records=[];bands={}
for sign,upper,elbow,forearm in [(1,13,11,10),(-1,56,60,61)]:
 center=posed[comp==elbow].mean(0);lo=float(np.min(posed[comp==forearm,2]));hi=float(np.max(posed[comp==upper,2]));mid=float(center[2]);delta=float(np.clip(.35-abs(center[0]),.035,.09));bands[sign]=(lo,mid,hi,delta);records.append({'side':sign,'idle_elbow_before':center.tolist(),'idle_elbow_after':(center+[sign*delta,0,0]).tolist(),'outward_delta_m':delta,'posed_band':[lo,mid,hi]})
def deform(q,c):
 if c not in [13,11,10,56,60,61]:return q.copy(),np.eye(3)
 sign=1 if c in [13,11,10] else -1;lo,mid,hi,delta=bands[sign];zz=q[2]
 if zz<mid:t=np.clip((zz-lo)/(mid-lo),0,1);w=t*t*(3-2*t);der=6*t*(1-t)/(mid-lo) if lo<zz<mid else 0
 else:t=np.clip((hi-zz)/(hi-mid),0,1);w=t*t*(3-2*t);der=-6*t*(1-t)/(hi-mid) if mid<zz<hi else 0
 out=q.copy();out[0]+=sign*delta*w;J=np.eye(3);J[0,2]=sign*delta*der;return out,J
for i,q in enumerate(posed):
 out,J=deform(q,int(comp[i]));A=M[i,:3,:3];assert abs(np.linalg.det(A))>.05;Q=np.linalg.solve(A,out-M[i,:3,3]);z['positions'][i]=Q*[100,-100,100];J=np.linalg.inv(A)@J@A;B=np.diag([1.,-1,1]);J=B@J@B;N=z['normals'][i]@np.linalg.inv(J);N/=np.linalg.norm(N);T=J@z['tangents'][i];T-=N*np.dot(N,T);T/=np.linalg.norm(T);z['normals'][i]=N;z['tangents'][i]=T
keep=np.where(~np.isin(fit['component'],[15,55]))[0]
for v,bi in zip(o.data.vertices,keep):
 A=sum((np.asarray(skin[g.group])*g.weight for g in v.groups),np.zeros((4,4)));q=A[:3,:3]@np.array(v.co)+A[:3,3];out,_=deform(q,int(fit['component'][bi]));v.co=np.linalg.solve(A[:3,:3],out-A[:3,3])
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
o.data.update();bpy.ops.wm.save_as_mainfile(filepath=str(r/'Buzz.blend'),compress=True);np.savez_compressed(r/'Buzz-geometry.npz',**z);(r/'posed-arm-refinement.json').write_text(json.dumps(records,indent=2));print('BADGE_PLANE_CAPE_NECKLINE_POSED_ARMS_REFINED')

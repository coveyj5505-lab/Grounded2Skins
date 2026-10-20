"""Bake a measured relaxed-pose torso-clearance correction back into rigid armor.
No bone, weight, hand, body or animation changes. Actual game poses remain a test.
"""
import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(sys.argv[sys.argv.index('--')+1]);fit=np.load('/workspace/mod-work/rig-stage/skinned-stowed-v2-proportions/expected.npz');old=np.load(root/'body-points.npz');full=old['positions'].copy();keep=np.where(~np.isin(fit['component'],[15,55]))[0];comp=fit['component'][keep];o=bpy.data.objects['Buzz_Skinned'];arm=o.find_armature()
def aim(a,b,d):
 bpy.context.view_layer.update();pb=arm.pose.bones[a];A=pb.matrix.translation.copy();B=arm.pose.bones[b].matrix.translation.copy();rot=(B-A).rotation_difference(Vector(d));pb.matrix=Matrix.Translation(A)@rot.to_matrix().to_4x4()@Matrix.Translation(-A)@pb.matrix;bpy.context.view_layer.update()
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
for s,sign in [('l',1),('r',-1)]:aim(s+'_upperArm_JNT',s+'_lowerArm_JNT',(sign*.15,0,-1));aim(s+'_lowerArm_JNT',s+'_wrist_JNT',(sign*.05,-.1,-1))
bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();posed=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();records=[]
for sign,pre,u,e,f in [(1,'l',13,11,10),(-1,'r',56,60,61)]:
 upper=np.where(comp==u)[0];center=posed[upper].mean(0);shell=(abs(posed[:,2]-center[2])<.16)&np.isin(comp,[14]);edge=float(np.quantile(posed[shell,0]*sign,.97));shift=max(0,edge-float(center[0]*sign));assert 0<=shift<.3
 for cid,factor in [(u,1.),(e,.65),(f,.65)]:
  ix=np.where(comp==cid)[0];bone=arm.pose.bones[pre+('_upperArm_JNT' if cid==u else '_lowerArm_JNT')];D=np.array(bone.matrix@bone.bone.matrix_local.inverted());amount=np.ones(len(ix))*shift*factor
  if cid==f:
   E=arm.pose.bones[pre+'_lowerArm_JNT'].matrix.translation;W=arm.pose.bones[pre+'_wrist_JNT'].matrix.translation;axis=np.array(W-E);t=np.clip(((posed[ix]-np.array(E))@axis)/(axis@axis),0,1);amount*=1-t
  delta=np.c_[sign*amount,np.zeros((len(ix),2))]@np.linalg.inv(D[:3,:3]).T;full[keep[ix]]+=delta
 records.append({'side':pre,'arm_center_before':center.tolist(),'measured_torso_side_m':edge,'relaxed_lateral_correction_m':shift,'method':'Place rigid upper-arm center at measured torso edge in controlled relaxed pose; elbow65%, wrist0%'})
z=dict(np.load(root/'geometry.npz'));ids=old['body_original_ids'];C=np.diag([1.,-1,1]);oldpoints=old['positions']
for cid in [13,56,11,60,10,61]:
 ix=np.where(fit['component']==cid)[0];M=np.linalg.lstsq(np.c_[oldpoints[ix],np.ones(len(ix))],full[ix],rcond=None)[0][:3].T;J=C@M@C;sel=np.isin(ids,ix);N=z['normals'][sel]@np.linalg.inv(J);N/=np.linalg.norm(N,axis=1,keepdims=True);T=z['tangents'][sel]@J.T;T-=N*np.sum(T*N,axis=1,keepdims=True);T/=np.linalg.norm(T,axis=1,keepdims=True);z['normals'][sel]=N;z['tangents'][sel]=T;z['positions'][sel]=(full[ids[sel]]*[100,-100,100]).astype('f4')
np.savez_compressed(root/'geometry-clearance.npz',**z);np.savez_compressed(root/'body-points-clearance.npz',positions=full,body_original_ids=ids)
for v,i in zip(o.data.vertices,keep):v.co=full[i]
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
o.data.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(root/'Buzz-Arms-Clearance.blend'),compress=True);(root/'clearance-report.json').write_text(json.dumps({'measurements':records,'reference_pose':'Controlled relaxed FK, not game clip','weights_bones_hands_body_unchanged':True,'runtime':'PENDING'},indent=2));print('CLEARANCE_BAKED')

"""Joint-centered similarity fits for Buzz's six rigid arm pieces.

Compare actual source->V2 transforms first, then remove the 70/20 mm visual
joint offsets and use a uniform segment scale instead of independent axial and
radial scales. All remaining source and cooked attributes are preserved.
"""
import argparse,json
from pathlib import Path
import numpy as np
from fit_buzz_rig import rotation
p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args();out=a.out;out.mkdir(exist_ok=False)
root=Path('/workspace/mod-work');baseline=root/'buzz-helmet-cleanup/candidate-v1';z=dict(np.load(baseline/'geometry.npz'));original=np.load(root/'rig-stage/landmarks/source.npz')['positions']*[-1,-1,1];fit=np.load(root/'rig-stage/skinned-stowed-v2-proportions/expected.npz');source=np.load(root/'buzz-v2-stage/source-geometry.npz');body_id=source['source_vertices'][z['source_vertices']];component=fit['component'];src=original[fit['source_vertices']];bones=json.loads((root/'rig-stage/landmarks/bones.json').read_text());heads={b['name']:np.array(b['head']) for b in bones};points=fit['positions'].copy();reports=[];changed=np.zeros(len(body_id),bool)
def affine(a,b,A,B,radial,uniform=False):
 axis=(b-a)/np.linalg.norm(b-a);ratio=np.linalg.norm(B-A)/np.linalg.norm(b-a);R=rotation(b-a,B-A);M=R*ratio if uniform else R@(radial*np.eye(3)+(ratio-radial)*np.outer(axis,axis));return M,A-M@a,ratio
for side,pre,upper,elbow,fore in [(1,'l',13,11,10),(-1,'r',56,60,61)]:
 U,E,W=[heads[pre+n] for n in ['_upperArm_JNT','_lowerArm_JNT','_wrist_JNT']];sU=np.array([side*.35,.435,1.425]);sE=src[component==elbow].mean(0);sW=np.array([side*.96,.24,1.40]);oldU=U+[side*.07,0,0];oldE=E+[side*.02,0,0]
 for c,aa,bb,oldA,oldB,newA,newB,radial in [(upper,sU,sE,oldU,oldE,U,E,1.02),(fore,sE,sW,oldE,W,E,W,1.)]:
  oldM,oldt,ratio=affine(aa,bb,oldA,oldB,radial);newM,newt,newratio=affine(aa,bb,newA,newB,radial,True);ids=np.where(component==c)[0];assert np.max(abs((src[ids]@oldM.T+oldt)-fit['positions'][ids]))<2e-6
  points[ids]=src[ids]@newM.T+newt;sel=np.isin(body_id,ids);changed|=sel
  # Unreal cm/Y-reflection conversion for existing cooked-space frames.
  C=np.diag([1.,-1,1]);J=C@newM@np.linalg.inv(oldM)@C;N=z['normals'][sel]@np.linalg.inv(J);N/=np.linalg.norm(N,axis=1,keepdims=True);T=z['tangents'][sel]@J.T;T-=N*np.sum(N*T,axis=1,keepdims=True);T/=np.linalg.norm(T,axis=1,keepdims=True);z['normals'][sel]=N;z['tangents'][sel]=T
  reports.append({'component':c,'old_axial_scale':ratio,'old_radial_scale':radial,'new_uniform_scale':newratio,'source_shape_similarity_error':float(np.max(abs(newM.T@newM-np.eye(3)*newratio**2)))})
 # The isolated spherical elbow follows the forearm; use a similarity delta
 # around the measured source center, rather than the previous blended fit.
 ids=np.where(component==elbow)[0];oldDelta=fit['positions'][ids]-oldE;oldCenter=oldDelta.mean(0);newratio=np.linalg.norm(W-E)/np.linalg.norm(sW-sE);R=rotation(sW-sE,W-E);points[ids]=(src[ids]-sE)@R.T*newratio+E
 # Recompute the elbow frame from a least-squares local old->new affine fit.
 A=np.c_[fit['positions'][ids],np.ones(len(ids))];M=np.linalg.lstsq(A,points[ids],rcond=None)[0][:3].T;sel=np.isin(body_id,ids);changed|=sel;C=np.diag([1.,-1,1]);J=C@M@C;N=z['normals'][sel]@np.linalg.inv(J);N/=np.linalg.norm(N,axis=1,keepdims=True);T=z['tangents'][sel]@J.T;T-=N*np.sum(T*N,axis=1,keepdims=True);T/=np.linalg.norm(T,axis=1,keepdims=True);z['normals'][sel]=N;z['tangents'][sel]=T
 # All six isolated pieces remain rigid to their previously validated bones.
 for c in [upper,elbow,fore]:assert np.all(fit['weights'][component==c,0]==1)
z['positions'][changed]=(points[body_id[changed]]*[100,-100,100]).astype('f4')
old=np.load(baseline/'geometry.npz')
for k in old.files:
 if k not in ['positions','normals','tangents']:assert np.array_equal(z[k],old[k]),k
assert np.array_equal(z['positions'][~changed],old['positions'][~changed])
np.savez_compressed(out/'geometry.npz',**z);np.savez_compressed(out/'body-points.npz',positions=points,changed=component==13,body_original_ids=body_id,changed_render=changed)
(out/'report.json').write_text(json.dumps({'source_fit_checked_before_edit':True,'components':[13,56,11,60,10,61],'segment_fits':reports,'upper_joint_lateral_offset_removed_cm':7,'elbow_lateral_offset_removed_cm':2,'all_weights_UVs_head_split_textures_backpack_other_geometry_unchanged':True,'render_vertices_changed':int(changed.sum()),'runtime':'NOT TESTED; controlled pose preview required'},indent=2)+'\n');print('BUZZ_ARM_SIMILARITY',int(changed.sum()))

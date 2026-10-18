#!/usr/bin/env python3
"""Source-specific anatomical fit plus constrained transfer from Commander101.

Never changes the reference skeleton. Component IDs refer to the hash-guarded
supplied OBJ after welding equal source positions for connectivity only.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from scipy.interpolate import RBFInterpolator


def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)


def rotation(a,b):
    a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);v=np.cross(a,b);c=np.dot(a,b)
    if c>1-1e-10:return np.eye(3)
    assert c>-1+1e-8
    K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3)+K+K@K/(1+c)


def segment(p,a,b,A,B,radial):
    a,b,A,B=map(np.asarray,(a,b,A,B));v=b-a;u=v/np.linalg.norm(v)
    d=p-a;along=np.outer(d@u,u);cross=d-along
    return (along*(np.linalg.norm(B-A)/np.linalg.norm(v))+cross*radial)@rotation(v,B-A).T+A


def curve_fit(p, source_points, target_points, radial=.65):
    center=source_points.mean(0);_,_,vt=np.linalg.svd(source_points-center,full_matrices=False)
    axis=vt[0]
    if abs(axis[0])>.5:
        if axis[0]*np.sign(center[0])<0:axis=-axis
    elif np.dot(axis,[0,-1,-1])<0:axis=-axis
    proj=(source_points-center)@axis;lo,hi=proj.min(),proj.max()
    u=np.clip(((p-center)@axis-lo)/(hi-lo),0,1)
    lengths=np.linalg.norm(np.diff(target_points,axis=0),axis=1);knots=np.r_[0,np.cumsum(lengths)];knots/=knots[-1]
    result=np.zeros_like(p)
    for k in range(len(lengths)):
        sel=(u>=knots[k]) & ((u<knots[k+1]) if k<len(lengths)-1 else (u<=1))
        a=center+axis*(lo+(hi-lo)*knots[k]);b=center+axis*(lo+(hi-lo)*knots[k+1])
        result[sel]=segment(p[sel],a,b,target_points[k],target_points[k+1],radial)
    root=center+axis*lo
    return result,root


def fit(inputs,output,reference_buffers=Path('/workspace/mod-work/mesh-stage/body')):
    output.mkdir(parents=True,exist_ok=False)
    data=np.load(inputs/'source.npz');original=data['positions'];faces=data['indices'];materials=data['materials']
    assert original.shape==(13450,3) and faces.shape==(20482,3)
    digest=hashlib.sha256()
    for key,dtype in [('positions','<f8'),('indices','<i4'),('materials','<u2')]:digest.update(data[key].astype(dtype).tobytes())
    assert digest.hexdigest()=='b9a9540f45263ce5df29172adae04e1797f78d7e3a00dd186203fb0e60bb0007','Unexpected source geometry; component IDs must be re-inspected'
    bones=json.loads((inputs/'bones.json').read_text());name={b['name']:b['index'] for b in bones};heads=np.array([b['head'] for b in bones])
    def point(n):return heads[name[n]]
    # Nose, toes and both hands of the actual native rig face Blender -Y.
    assert point('NoseEnd_JNT')[1]<point('head_JNT')[1] and point('l_Toes_JNT')[1]<point('l_Foot_JNT')[1]
    v=original*np.array([-1,-1,1])
    _,weld=np.unique(np.round(original,6),axis=0,return_inverse=True)
    a=weld[faces[:,[0,1,2,0]]];graph=coo_matrix((np.ones(faces.size),(a[:,:3].ravel(),a[:,1:].ravel())),shape=(weld.max()+1,)*2)
    _,ids=connected_components(graph,directed=False);component=ids[weld]
    assert len(np.unique(component))==73
    groups={i:np.flatnonzero(component==i) for i in np.unique(component)}
    body=str(reference_buffers)
    ref=np.fromfile(body+'/positions.f32',dtype='<f4').reshape(-1,3)*[.01,-.01,.01]
    refj=np.fromfile(body+'/joints.u16',dtype='<u2').reshape(-1,8)
    refw=np.fromfile(body+'/weights.f32',dtype='<f4').reshape(-1,8)
    weights=np.zeros((len(v),230));position=np.zeros_like(v);region=np.full(len(v),'torso',dtype='U32')
    rigid=np.full(len(v),-1,dtype='i4');transfers=[];anchors=[]

    def transfer(ix,allowed,label):
        if not len(ix):return
        weights[ix]=0;rigid[ix]=-1
        allowed=np.array(sorted(set(allowed)),dtype=int)
        keep=np.isin(refj,allowed);mass=(refw*keep).sum(1);candidate=np.flatnonzero(mass>.15)
        assert len(candidate)>0,label
        distances,near=cKDTree(ref[candidate]).query(position[ix],k=min(8,len(candidate)))
        sample=candidate[near];blend=1/np.maximum(distances,.002)**2;blend/=blend.sum(1,keepdims=True)
        for k in range(sample.shape[1]):
            for slot in range(8):
                j=refj[sample[:,k],slot];w=refw[sample[:,k],slot]*blend[:,k]*np.isin(j,allowed)
                np.add.at(weights,(ix,j),w)
        total=weights[ix].sum(1);assert np.all(total>0),label
        weights[ix]/=total[:,None];region[ix]=label
        transfers.append({'region':label,'vertices':len(ix),'reference_candidates':len(candidate),
                          'nearest_distance_median_m':float(np.median(distances[:,0])),
                          'nearest_distance_max_m':float(distances[:,0].max()),'allowed_bones':allowed.tolist()})

    def bind(ix,bone,label):
        weights[ix]=0;weights[ix,bone]=1;rigid[ix]=bone;region[ix]=label

    def body_fit(p):
        z=p[:,2];out=p.copy()
        out[:,0]*=np.interp(z,[.76,.97,1.1,1.43,1.60,1.94],[.75,.75,.68,.52,.52,.8])
        out[:,1]=(p[:,1]-.43)*.7
        out[:,2]=np.interp(z,[0,.76,.965,1.1,1.25,1.43,1.60,1.94],[0,.78,.965,1.0763,1.22,1.3551,1.55,1.94])
        return out

    position[:]=body_fit(v)
    # The small isolated source marker is removed from the output mesh later.
    helper=groups[39];assert np.ptp(v[helper],axis=0).max()<.001
    bind(helper,0,'removed-source-marker')
    # Back-mounted components and all wing vertices must stay independent of arms.
    back=(v[:,1]>.63)&(v[:,2]>1.03)
    # Keep the connected torso/back shell under one continuous position map.
    # Hard spatial cuts through component 14 produced torn armor in previews.
    bind(np.flatnonzero(back),name['chest_JNT'],'rigid-wings-backpack')
    # Rigid suit shell, with transferred soft waist and pelvis underneath it.
    torso=(np.abs(v[:,0])<.46)&~back&(component!=39)
    transfer(np.flatnonzero(torso),[23,52,53,54,98,99,100,101,208,222],'torso-transfer')
    bind(np.flatnonzero(torso&(v[:,2]>.125+1)&(v[:,2]<1.57)),name['chest_JNT'],'rigid-chest-shell')
    bind(np.flatnonzero(torso&(v[:,2]<1.09)),name['Hips_JNT'],'rigid-pelvis')
    # Fit eyes to native eye centers while retaining the native head pivot.
    eye=np.mean([v[groups[31]].mean(0),v[groups[38]].mean(0)],axis=0)
    source_pivot=np.array([0,.43,1.75]);target_pivot=point('head_JNT');target_eye=(point('l_Eye_JNT')+point('r_Eye_JNT'))/2
    scale=np.array([abs(point('l_Eye_JNT')[0])/abs(v[groups[31]].mean(0)[0]),
                    (target_eye[1]-target_pivot[1])/(eye[1]-source_pivot[1]),
                    (target_eye[2]-target_pivot[2])/(eye[2]-source_pivot[2])])
    # The connected OBJ body includes both the face and rigid collar. Its
    # supplied face material separates anatomical head geometry reliably;
    # coordinate-only tests incorrectly stretched the collar toward the head.
    face_vertices=np.unique(faces[materials==5]);head_surface=np.zeros(len(v),bool);head_surface[face_vertices]=True
    head=(head_surface|np.isin(component,[30,31,34,36,37,38,40]))&(v[:,2]>1.47)
    hi=np.flatnonzero(head);head_position=(v[hi]-source_pivot)*scale+target_pivot
    blend=smooth((v[hi,2]-1.47)/.18)*(1-smooth((v[hi,1]-.58)/.12))
    position[hi]=position[hi]*(1-blend[:,None])+head_position*blend[:,None]
    weights[hi]=0;weights[hi,name['neck3_JNT']]=1-blend;weights[hi,name['head_JNT']]=blend
    region[hi]='head-neck';rigid[hi]=-1
    core=hi[blend>.999999];bind(core,name['head_JNT'],'rigid-head')
    bind(np.flatnonzero(back),name['chest_JNT'],'rigid-wings-backpack')
    anchors.append({'name':'head-pivot','source':source_pivot.tolist(),'target':target_pivot.tolist(),'fitted':target_pivot.tolist(),'basis':'inferred neck/skull pivot; eye-pair driven anisotropic fit'})
    for c,bn in [(31,'l_Eye_JNT'),(38,'r_Eye_JNT')]:
        expected=point(bn);fitted=position[groups[c]].mean(0)
        # Component source sides swap after the required facing correction.
        if np.sign(fitted[0])!=np.sign(expected[0]):expected=point('r_Eye_JNT' if bn=='l_Eye_JNT' else 'l_Eye_JNT')
        anchors.append({'name':bn,'fitted':fitted.tolist(),'target':expected.tolist(),'error_m':float(np.linalg.norm(fitted-expected))})

    # Geometry-disconnected rigid parts can use one bone; spherical joints use
    # constrained original weights instead of accidental nearest-body weights.
    for side in [1,-1]:
        prefix='l' if side==1 else 'r';word='Left' if side==1 else 'Right'
        U,E,W,H=[point(prefix+s) for s in ['_upperArm_JNT','_lowerArm_JNT','_wrist_JNT','_hand_JNT']]
        upper_ids=[13,56];elbow_ids=[11,60];fore_ids=[10,61];palm_ids=[7,64]
        def side_group(candidates):return next(c for c in candidates if np.sign(v[groups[c],0].mean())==side)
        upper,elbow,fore,palm=map(side_group,(upper_ids,elbow_ids,fore_ids,palm_ids))
        source_U=np.array([side*.35,.435,1.425]);source_E=v[groups[elbow]].mean(0);source_W=np.array([side*.96,.24,1.40])
        upper_map=lambda p:segment(p,source_U,source_E,U,E,.72)
        fore_map=lambda p:segment(p,source_E,source_W,E,W,.75)
        arm=(v[:,0]*side>.28)&np.isin(component,[2,3,4,5,6,7,8,9,10,11,13,15,55,56,59,60,61,63,64,65,66,67,68,69,70,71])
        ix=np.flatnonzero(arm)
        blend=smooth((v[ix,0]*side-(abs(source_E[0])-.07))/.14)
        position[ix]=upper_map(v[ix])*(1-blend[:,None])+fore_map(v[ix])*blend[:,None]
        transfer(ix,[name[prefix+'_upperArm_JNT'],name[prefix+'_lowerArm_JNT'],name[prefix+'_wrist_JNT'],name[prefix+'_hand_JNT']],prefix+'-arm-transfer')
        for c,bn,label in [(upper,prefix+'_upperArm_JNT','upper-armor'),(fore,prefix+'_lowerArm_JNT','forearm-armor'),
                           (side_group([15,55]),prefix+'_upperArm_JNT','shoulder-armor')]:
            ci=groups[c];position[ci]=upper_map(v[ci]) if label!='forearm-armor' else fore_map(v[ci]);bind(ci,name[bn],prefix+'-rigid-'+label)
        ci=groups[elbow];bind_target=[name[prefix+'_upperArm_JNT'],name[prefix+'_lowerArm_JNT']]
        weights[ci]=0;transfer(ci,bind_target,prefix+'-elbow-joint')
        # Four separate source finger shells ordered anatomically across the palm.
        fingers=[c for c,g in groups.items() if len(g)==81 and np.sign(v[g,0].mean())==side and abs(v[g,0].mean())>1.0]
        fingers.sort(key=lambda c:v[groups[c],1].mean());assert len(fingers)==4
        thumb=side_group([9,65]);finger_defs=list(zip(fingers,['Index','Middle','Ring','Pinky']))+[(thumb,'Thumb')]
        roots=[];targets=[];models=[]
        for c,label in finger_defs:
            names=[word+'Hand'+label+str(k)+'_JNT' for k in range(1,5)]
            target=np.array([point(n) for n in names]);ci=groups[c]
            position[ci],root=curve_fit(v[ci],v[ci],target,.6)
            weights[ci]=0;transfer(ci,[name[n] for n in names],prefix+'-'+label.lower())
            roots.append(root);targets.append(target[0]);models.append((c,label,target))
        # Fit the palm/cuff from wrist plus all five digit roots. Regularized
        # affine fitting keeps the full 3-D depth defined for nearly coplanar roots.
        src=np.vstack([source_W,roots]);dst=np.vstack([W,targets]);A=np.column_stack([src,np.ones(len(src))])
        base_R=rotation(np.array([side,0,-.05]),(np.mean(targets[:4],axis=0)-W));base_M=base_R*.7
        prior=np.vstack([base_M.T,W-source_W@base_M.T]);reg=.0001
        fit=np.linalg.lstsq(np.vstack([A,np.eye(4)*np.sqrt(reg)]),np.vstack([dst,prior*np.sqrt(reg)]),rcond=None)[0]
        assert np.linalg.det(fit[:3])>0,'Palm fit reflected the glove'
        correction=RBFInterpolator(src,dst-A@fit,kernel='thin_plate_spline',smoothing=1e-9)
        ci=groups[palm];position[ci]=np.column_stack([v[ci],np.ones(len(ci))])@fit+correction(v[ci]);bind(ci,name[prefix+'_hand_JNT'],prefix+'-rigid-palm')
        fitted_landmarks=A@fit+correction(src)
        anchors.append({'name':prefix+'-palm-landmarks','rms_error_m':float(np.sqrt(np.mean(np.sum((fitted_landmarks-dst)**2,axis=1)))),'source':src.tolist(),'target':dst.tolist(),'fitted':fitted_landmarks.tolist(),'refinement':'Small thin-plate residual correction of the regularized affine palm fit'})
        # Small labels/nails on gloves follow their nearest source digit. The
        # cuff-mounted button remains with the forearm.
        extra=np.flatnonzero(arm&np.isin(component,[6,8,67,71]))
        claimed=np.concatenate([groups[palm]]+[groups[c] for c,_,_ in models])
        extra=np.setdiff1d(extra,claimed)
        for c in np.unique(component[extra]):
            ci=np.intersect1d(groups[c],extra)
            if not len(ci):continue
            model=min(models,key=lambda item:np.linalg.norm(v[ci].mean(0)-v[groups[item[0]]].mean(0)))
            fc,label,target=model
            position[ci],_=curve_fit(v[ci],v[groups[fc]],target,.6)
            weights[ci]=0;transfer(ci,[name[word+'Hand'+label+str(k)+'_JNT'] for k in range(1,5)],prefix+'-digit-detail')
        for a,b,label in [(source_U,U,'shoulder'),(source_E,E,'elbow'),(source_W,W,'wrist')]:
            anchors.append({'name':prefix+'-'+label,'source':a.tolist(),'target':b.tolist(),'fitted':b.tolist(),'error_m':0.0})
        # Legs, knees and boots. Source hinge centers come from the isolated
        # knee/ankle meshes; fitted anchors coincide with native joint heads.
        hip,knee,ankle=side_group([23,43]),side_group([25,45]),side_group([22,48])
        thigh,shin,foot=[name[prefix+n] for n in ['_UpperLeg_JNT','_LowerLeg_JNT','_Foot_JNT']]
        Ahip=np.array([side*.144,.421,.967]);Aknee=v[groups[knee]].mean(0);Afoot=v[groups[ankle]].mean(0)
        hipmap=lambda p:segment(p,Ahip,Aknee,heads[thigh],heads[shin],.75)
        shinmap=lambda p:segment(p,Aknee,Afoot,heads[shin],heads[foot],.75)
        foot_scale=np.array([.65,.55,heads[foot,2]/Afoot[2]])
        footmap=lambda p:(p-Afoot)*foot_scale+heads[foot]
        leg=(v[:,0]*side>0)&np.isin(component,[19,20,21,22,23,25,33,41,42,43,44,45,48,54])
        li=np.flatnonzero(leg);t=smooth((Aknee[2]+.08-v[li,2])/.16)
        position[li]=hipmap(v[li])*(1-t[:,None])+shinmap(v[li])*t[:,None]
        weights[li]=0;transfer(li,[23,thigh,shin,foot],prefix+'-leg-transfer')
        for c,bone,fn,label in [(hip,thigh,hipmap,'thigh'),(side_group([21,42]),shin,shinmap,'shin')]:
            ci=groups[c];position[ci]=fn(v[ci]);bind(ci,bone,prefix+'-rigid-'+label)
        ci=groups[knee];weights[ci]=0;transfer(ci,[thigh,shin],prefix+'-knee-joint')
        boot=np.flatnonzero(leg&np.isin(component,[19,20,33,41,44,54]));position[boot]=footmap(v[boot]);bind(boot,foot,prefix+'-rigid-boot')
        ci=groups[ankle];t=smooth((Afoot[2]+.06-v[ci,2])/.12)
        position[ci]=shinmap(v[ci])*(1-t[:,None])+footmap(v[ci])*t[:,None];weights[ci]=0;transfer(ci,[shin,foot],prefix+'-ankle-joint')
        for a,b,label in [(Ahip,heads[thigh],'hip'),(Aknee,heads[shin],'knee'),(Afoot,heads[foot],'ankle')]:
            anchors.append({'name':prefix+'-'+label,'source':a.tolist(),'target':b.tolist(),'fitted':b.tolist(),'error_m':0.0})

    # Identical seam positions must retain identical fits and weight fields.
    for node in np.unique(weld):
        ix=np.flatnonzero(weld==node)
        if len(ix)>1:
            position[ix]=position[ix].mean(0);weights[ix]=weights[ix].mean(0)
    # A face/neck material seam can combine chest and neck weights. Such a
    # seam is deliberately soft and must not retain the old rigid-shell label.
    mixed=(rigid>=0)&(weights[np.arange(len(v)),np.maximum(rigid,0)]<1-1e-10)
    assert np.all(component[mixed]==14) and np.all(rigid[mixed]==name['chest_JNT'])
    rigid[mixed]=-1;region[mixed]='neck-seam-blend'
    require=np.ones(len(v),bool);require[helper]=False
    assert np.isfinite(position).all() and np.all(weights.sum(1)>0)
    weights/=weights.sum(1,keepdims=True)
    order=np.argsort(-weights,axis=1,kind='stable')[:,:8]
    kept=np.take_along_axis(weights,order,axis=1);dropped=1-kept.sum(1)
    assert dropped.max()<.01
    kept/=kept.sum(1,keepdims=True)
    assert np.all(kept.sum(1)>.999999)
    # Remove only the tiny non-character source marker and degenerate faces.
    tri=position[faces];area2=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
    face_keep=(component[faces[:,0]]!=39)&(area2>1e-12)
    use=np.unique(faces[face_keep]);lookup=np.full(len(v),-1);lookup[use]=np.arange(len(use))
    np.savez_compressed(output/'fitted.npz',positions=position,weights=kept,joints=order,
                        source_vertices=use,faces=faces,face_keep=face_keep,component=component,region=region,rigid=rigid)
    report={'method':'Anatomical segment/eye/finger fitting, then constrained KNN transfer from original Commander101 weights; rigid armor overrides',
            'reference_bones':230,'facing_correction':'180deg from prior inspection; native nose/toes face Blender -Y',
            'source_vertices':len(v),'output_vertices':len(use),'output_triangles':int(face_keep.sum()),
            'removed_source_marker_component':39,'removed_triangle_ids':np.flatnonzero(~face_keep).tolist(),
            'anchors':anchors,'transfers':transfers,'maximum_weight_pruned_mass':float(dropped.max()),
            'used_bone_ids':np.unique(order[kept>0]).tolist(),'source_reference_weights':'Original recovered native Commander101 integer weights normalized to floats',
            'skeleton_rest_changed':False,'game_animation_test':'NOT RUN','facial_expressions':'Face/eyes are rigid to head; facial animation compatibility not claimed'}
    (output/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['output_vertices','output_triangles','maximum_weight_pruned_mass']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('landmarks',type=Path);p.add_argument('new_output',type=Path);p.add_argument('--reference-buffers',type=Path,default=Path('/workspace/mod-work/mesh-stage/body'));a=p.parse_args();fit(a.landmarks,a.new_output,a.reference_buffers)

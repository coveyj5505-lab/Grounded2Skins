"""Bake the isolated flight target into a root-rigid cosmetic visual candidate.

Native player mesh, animation and camera remain untouched. This is a fallback
visual asset for a future TP-only runtime adapter, not an installable feature.
"""
import argparse,json,hashlib
from PIL import Image
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from native_buffers import skeleton_signature,validate
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('out',type=Path);a=p.parse_args();a.out.mkdir(exist_ok=False);r=Path('/workspace/mod-work');saved=np.load(a.candidate/'rest-and-evaluated.npz');target=np.load(a.candidate/'pose-targets.npz');rest=saved['rest'];pose=target['flight'];assert np.array_equal(saved['bone_names'],target['bone_names']);assert len(rest)==230;skin=pose@np.linalg.inv(rest)
body=dict(np.load(r/'refinement-next/buzz-arms-v1/geometry-clearance.npz'));wing=dict(np.load(r/'wings-stage/atlas-deployed-v1/Buzz-atlas-SKINNED.npz'));pieces=[];report=[]
def bake(data,M):
 P=data['positions']*[.01,-.01,.01];N=data['normals']*[1,-1,1];T=data['tangents']*[1,-1,1];J=M[:,:3,:3];det=np.linalg.det(J);assert np.min(det)>1e-6
 P=np.einsum('nij,nj->ni',J,P)+M[:,:3,3];N=np.einsum('ni,nij->nj',N,np.linalg.inv(J));N/=np.linalg.norm(N,axis=1,keepdims=True);T=np.einsum('nij,nj->ni',J,T);T-=N*np.sum(N*T,axis=1,keepdims=True);T/=np.linalg.norm(T,axis=1,keepdims=True)
 return {'positions':(P*[100,-100,100]).astype('f4'),'normals':(N*[1,-1,1]).astype('f4'),'tangents':(T*[1,-1,1]).astype('f4'),'signs':data['signs'].copy(),'uv0':data['uv0'].copy(),'colors':data['colors'].copy(),'indices':data['indices'].copy()},P,float(det.min())
M=np.sum(skin[body['joints']]*body['weights'][:,:,None,None],axis=1);baked,P,mindet=bake(body,M);distance,ids=cKDTree(saved['source_rest']).query(body['positions']*[.01,-.01,.01]);assert distance.max()<2e-6;error=float(np.max(abs(P-saved['source_evaluated'][ids])));assert error<3e-6,error;pieces.append(baked);report.append({'part':'body','triangles':len(body['indices']),'Blender_evaluated_max_position_error_m':error,'rest_correspondence_error_m':float(distance.max()),'min_skin_Jacobian_determinant':mindet})
chest=np.flatnonzero(saved['bone_names']=='chest_JNT');assert len(chest)==1;C=pose[int(chest[0])];baked,_,_=bake(wing,np.tile(C,(len(wing['positions']),1,1)));pieces.append(baked);report.append({'part':'wings','triangles':len(wing['indices']),'mapping':'Existing atlas chest-local deployed geometry transformed by the flight chest pose'})
# Preserve the two validated UV layouts in separate halves of one private atlas.
# Half-width resampling reduces horizontal texture detail but does not stretch
# colors on geometry because UV X is remapped by the same factor.
pieces[0]['uv0'][:,0]*=.5;pieces[1]['uv0'][:,0]=.5+.5*pieces[1]['uv0'][:,0]
body_image=r/'buzz-v2-stage/atlas/Buzz-basecolor-atlas.png';wing_image=r/'wings-stage/atlas-deployed-v1/Buzz-basecolor-atlas.png';atlas=Image.new('RGBA',(4096,4096))
for x,path in [(0,body_image),(2048,wing_image)]:
 image=Image.open(path).convert('RGBA');assert image.size==(4096,4096);atlas.paste(image.resize((2048,4096),Image.Resampling.LANCZOS),(x,0))
atlas.save(a.out/'Flight-basecolor-atlas.png')
n=sum(len(x['positions']) for x in pieces);data={k:np.concatenate([x[k] for x in pieces]) for k in ['positions','normals','tangents','signs','uv0','colors']};offset=0;indices=[]
for piece in pieces:indices.append(piece['indices']+offset);offset+=len(piece['positions'])
data.update(indices=np.concatenate(indices).astype('u4'),materials=np.zeros(sum(len(x['indices']) for x in pieces),dtype='u2'),material_count=np.array(7),source_vertices=np.arange(n,dtype='i4'),joints=np.zeros((n,8),dtype='u2'),weights=np.pad(np.ones((n,1),dtype='f4'),((0,0),(0,7))),skeleton_signature=np.array(skeleton_signature(r/'crook-stage/reference.json')),skeleton_bone_count=np.array(192));validate(data,str(data['skeleton_signature']));np.savez_compressed(a.out/'geometry.npz',**data);(a.out/'report.json').write_text(json.dumps({'status':'BAKED_VISUAL_CANDIDATE','parts':report,'render_input_vertices':n,'triangles':len(data['indices']),'atlas':'Private4096x4096; body left half, wing right half; matching UV remap; original eight textures and released textures unchanged','body_atlas_source_sha256':hashlib.sha256(body_image.read_bytes()).hexdigest(),'wing_atlas_source_sha256':hashlib.sha256(wing_image.read_bytes()).hexdigest(),'weights':'Independent root0 only; never run player animation on this visual','original_body_and_runtime_changes':False,'implementation_scope':'Proposed TP-only gliding visual swap, no actor/camera transform changes','limitations':['Static flying pose while visible; no flight limb animation','Body and wing atlas horizontal texel resolution halved; geometry and color proportions preserved','Requires a separate runtime adapter; not included in v0.3','Original tuft visual remains until a separate verified visual-only hide']},indent=2)+'\n');print('FLIGHT_VISUAL_BAKED',n,len(data['indices']),error)

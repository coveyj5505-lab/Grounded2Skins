"""Restore original toy arms, using the actual armor openings as flight pivots.

This edits only an independent root-rigid flight visual, never live player bones.
The measured socket triangle IDs refer to the hash-checked frozen body topology.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from native_buffers import validate
p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args();a.out.mkdir(exist_ok=False);r=Path('/workspace/mod-work');base=r/'woody-polish-next/buzz-flight-baked-v2';d=dict(np.load(base/'geometry.npz'));before=d['positions'].copy();assert hashlib.sha256((r/'refinement-next/buzz-arms-v1/geometry-clearance.npz').read_bytes()).hexdigest()=='6f7e1b167ffaf8f258e7aa5539bf382c5515d26ab8b317b53f88da706a4d54d9';body=dict(np.load(r/'refinement-next/buzz-arms-v1/geometry-clearance.npz'));f=np.load(r/'rig-stage/skinned-stowed-v2-proportions/expected.npz');ids=np.load(r/'refinement-next/buzz-arms-v1/body-points-clearance.npz')['body_original_ids'];S=np.load(r/'rig-stage/landmarks/source.npz')['positions'][f['source_vertices'][ids]]*[-1,-1,1];labels=f['component'][ids];assert len(S)==18413;assert np.array_equal(d['indices'][:len(body['indices'])],body['indices']);P=d['positions']*[.01,-.01,.01];arm_components=[2,3,4,5,6,7,8,9,10,11,13,56,59,60,61,63,64,65,66,67,68,69,70,71];reports=[];changed=np.zeros(len(P),bool)
patches={'l':[2141,2397,2396,2147,2149,2151,2153,2155,2154,2152,2150,2148,2146,2390,2389,2388,2387,2386,2145,2144,2395,2143,2142],'r':[1604,1987,1986,1610,1612,1614,1616,1618,1617,1615,1613,1611,1609,1980,1979,1978,1977,1976,1608,1607,1985,1606,1605]}
def center(q):
 w=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1);return np.average(q.mean(1),axis=0,weights=w)
def rotation_between(v,w):
 v=v/np.linalg.norm(v);w=w/np.linalg.norm(w);axis=np.cross(v,w);angle=np.arctan2(np.linalg.norm(axis),np.dot(v,w));return Rotation.from_rotvec(axis/np.linalg.norm(axis)*angle).as_matrix()
for side,sign in [('l',1),('r',-1)]:
 ix=body['indices'][patches[side]];A=center(S[ix]);B=center(P[ix]);sel=np.flatnonzero(np.isin(labels,arm_components)&(S[:,0]*sign>.28));wrist=np.array([sign*.96,.24,1.40]);R=rotation_between(wrist-A,np.array([sign*.035,-1,-.025]));scale=.90;P[sel]=(S[sel]-A)@R.T*scale+B;changed[sel]=True
 # Similarity preserves every original joint/armor relationship and aspect ratio.
 dist0=np.linalg.norm(S[sel]-A,axis=1);dist1=np.linalg.norm(P[sel]-B,axis=1);err=float(np.max(abs(dist1-scale*dist0)));assert err<1e-12
 reports.append({'side':side,'source_socket_m':A.tolist(),'flight_armor_socket_m':B.tolist(),'arm_vertices':len(sel),'uniform_scale':scale,'similarity_distance_error_m':err,'rotation':R.tolist(),'socket_triangle_ids':patches[side]})
tri=d['indices'];touch=changed[tri];assert not np.any(touch.any(1)&~touch.all(1)), 'An arm shares triangles with torso; split requires review';d['positions']=(P*[100,-100,100]).astype('f4');assert np.array_equal(d['positions'][~changed],before[~changed])
# Rebuild only changed frames from the original seam-split topology. Existing
# UV/hard-normal splits remain separate render vertices.
q=d['positions'][tri].astype('f8');e1=q[:,1]-q[:,0];e2=q[:,2]-q[:,0];fn=np.cross(e1,e2);N=np.zeros_like(P)
# Unreal winding after Y reflection is opposite mathematical cross-product.
for k in range(3):np.add.at(N,tri[:,k],-fn)
N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-20);uv=d['uv0'][tri];u=uv[:,1]-uv[:,0];v=uv[:,2]-uv[:,0];den=u[:,0]*v[:,1]-u[:,1]*v[:,0];valid=abs(den)>1e-12;ft=np.zeros_like(e1);fb=np.zeros_like(e1);ft[valid]=(e1[valid]*v[valid,1,None]-e2[valid]*u[valid,1,None])/den[valid,None];fb[valid]=(e2[valid]*u[valid,0,None]-e1[valid]*v[valid,0,None])/den[valid,None];T=np.zeros_like(P);BT=np.zeros_like(P)
for k in range(3):np.add.at(T,tri[:,k],ft);np.add.at(BT,tri[:,k],fb)
T-=N*np.sum(N*T,axis=1,keepdims=True);bad=np.linalg.norm(T,axis=1)<1e-10;T[bad]=np.cross(np.eye(3)[np.argmin(abs(N[bad]),axis=1)],N[bad]);T/=np.maximum(np.linalg.norm(T,axis=1,keepdims=True),1e-20);signs=np.where(np.sum(np.cross(N,T)*BT,axis=1)<0,-1,1).astype('f4');d['normals'][changed]=N[changed];d['tangents'][changed]=T[changed];d['signs'][changed]=signs[changed];validate(d,str(d['skeleton_signature']));np.savez_compressed(a.out/'geometry.npz',**d);shutil.copyfile(base/'Flight-basecolor-atlas.png',a.out/'Flight-basecolor-atlas.png');np.savez_compressed(a.out/'correction.npz',changed=changed,before=before,source_arm_positions=S,labels=labels);report={'status':'CORRECTED_SOURCE_CANDIDATE_REQUIRES_VISUAL_REVIEW','arms':reports,'changed_vertices':int(changed.sum()),'all_non_arm_positions_exact':True,'original_arm_proportions_preserved_by_uniform_similarity':True,'UVs_colors_wings_torso_head_and_root_weights_unchanged':True,'input_geometry_sha256':hashlib.sha256((base/'geometry.npz').read_bytes()).hexdigest(),'runtime':'NOT TESTED'};(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

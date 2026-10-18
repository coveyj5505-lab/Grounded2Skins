"""Deterministic rigid containment search; failure is not an impossibility proof."""
import numpy as np,json,sys
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog
from pathlib import Path
source,fit,output=map(Path,sys.argv[1:]);assert not output.exists()
d=np.load(fit/'fitted.npz');s=np.load(source/'source.npz')['positions']*[-1,-1,1];v=d['positions'];c=d['component'];wing=[0,1,12,51,62,72];pack=(s[:,1]>.63)&(s[:,2]>1.03)&~np.isin(c,wing);h=ConvexHull(v[pack]);A,b=h.equations[:,:3],h.equations[:,3]
rng=np.random.default_rng(51023);rotations=np.concatenate([np.eye(3)[None],Rotation.random(1000,random_state=rng).as_matrix()]);results=[]
for k in [0,12]:
 x=v[c==k];ctr=x.mean(0);x=x-ctr;best=None
 for R in rotations:
  q=x@R.T;r=linprog([0,0,0,-1],A_ub=np.c_[A,np.ones(len(A))],b_ub=-b-(q@A.T).max(0),bounds=[(None,None)]*4,method='highs')
  if r.success and (best is None or r.x[3]>best['clearance_m']):best={'component':k,'clearance_m':float(r.x[3]),'rotation':R.tolist(),'center':r.x[:3].tolist(),'source_center':ctr.tolist()}
 results.append(best);print(best,flush=True)
output.write_text(json.dumps({'seed':51023,'rotations_tested':len(rotations),'container':'Convex hull of fitted backpack points (necessary, not sufficient containment test)','limitation':'Finite orientation search; not proof that no physical packing exists. Symmetric opposite-side panels use mirrored geometry. No simultaneous collision-free panel packing established.','results':results},indent=2)+'\n')

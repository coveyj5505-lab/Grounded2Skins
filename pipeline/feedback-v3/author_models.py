import bpy,bmesh,numpy as np,json
from pathlib import Path
r=Path('/tmp/toystory-feedback-v3');old=Path('/workspace/mod-work/skin-fixes-next');reports={}
def save(n):
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/(n+'.blend')),compress=True)
# Woody: keep belt anchor; shorten only the source-semantic holster. Flatten
# the bent badge depth and remove its exact duplicate, not the hat or vest.
bpy.ops.wm.open_mainfile(filepath=str(old/'Woody-Holster-Candidate.blend'));o=bpy.data.objects['Woody_Skinned'];src=bpy.data.objects['KH3 Woody V3_mesh.001'];ids=[5169+v.index for v in src.data.vertices if any(src.vertex_groups[g.group].name.startswith('holster ') and g.weight>.1 for g in v.groups)];zmax=max(o.data.vertices[i].co.z for i in ids)
for i in ids:o.data.vertices[i].co.z=zmax+(o.data.vertices[i].co.z-zmax)*.62
sem=json.load(open(r/'semantic-source.json'));badge=sem['']['ids'];duplicate=sem['.003']['ids'];assert len(badge)==len(duplicate)==397
P=np.array([o.data.vertices[i].co[:] for i in badge]);center=float(np.median(P[:,1]))
for i in badge:o.data.vertices[i].co.y=-.163+(o.data.vertices[i].co.y-center)*.08
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in duplicate],context='VERTS');bm.to_mesh(o.data);bm.free();o.data.update();save('Woody')
reports['Woody']={'holster_length_ratio':.62,'belt_anchor_z':zmax,'badge':'Retained one original textured star, depth flattened to8% about a chest-front plane; exact overlapping duplicate badge removed','badge_source_vertices':397,'vest_boots_pullring':'untouched'}
# Cape: discard the previous high-neck panel and fit a low shoulder-level
# rear underlay. Shoulder joint is1.5089m; no new cape point exceeds1.50m.
bpy.ops.wm.open_mainfile(filepath=str(old/'BoPeep-Cape-Continuous-Candidate.blend'));o=bpy.data.objects['BoPeep_Skinned'];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();assert len(bm.verts)==5017;bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index>=4972],context='VERTS');uv=bm.loops.layers.uv.active;deform=bm.verts.layers.deform.verify();group=o.vertex_groups['spine3_JNT'].index;old_uv=json.load(open(old/'collar-patch.json'))['atlas_uv'];rows=[]
for z,width in [(1.39,.215),(1.44,.215),(1.48,.21),(1.50,.19)]:
 row=[]
 for t in np.linspace(-1,1,9):v=bm.verts.new((float(t*width),float(.105+.026*(1-t*t)),z));v[deform][group]=1;row.append(v)
 rows.append(row)
for a,b in zip(rows,rows[1:]):
 for i in range(8):
  f=bm.faces.new([a[i],b[i],b[i+1],a[i+1]]);f.smooth=True;f.material_index=0
  for k,l in enumerate(f.loops):l[uv].uv=(old_uv[0]+.0002*(k in [2,3]),old_uv[1]+.0002*(k in [1,2]))
bm.to_mesh(o.data);bm.free();o.data.update();save('BoPeep');reports['BoPeep']={'removed_high_underlay':45,'new_upper_limit_m':1.50,'actual_upper_arm_joint_z':1.508871,'rear_panel_vertices':36,'lower_cape':'unchanged'}
# Buzz: retain the accepted cap/socket fit, move the elbow area outward,
# blend back to the unchanged wrist and shoulder. This is a shear, det=1.
bpy.ops.wm.open_mainfile(filepath=str(old/'Buzz-Shoulder-Candidate.blend'));o=bpy.data.objects['Buzz_Skinned'];fit=np.load('/workspace/mod-work/rig-stage/skinned-stowed-v2-proportions/expected.npz');keep=np.where(~np.isin(fit['component'],[15,55]))[0];z=dict(np.load(old/'Buzz-Shoulder-Candidate.npz'));D=np.load('/workspace/mod-work/refinement-next/buzz-arms-v1/body-points-clearance.npz');ids=D['body_original_ids'];C=fit['component'];P=z['positions']*[.01,-.01,.01]
def shear(p,component):
 sign=1 if component in [13,11,10] else -1
 if component not in [13,11,10,56,60,61]:return p.copy(),np.eye(3)
 zz=p[2];lo,hi=.90,1.52;t=np.clip((zz-lo)/(hi-lo),0,1);amount=.045*np.sin(np.pi*t)**2;deriv=.045*np.pi*np.sin(2*np.pi*t)/(hi-lo) if lo<zz<hi else 0;Q=p.copy();Q[0]+=sign*amount;J=np.eye(3);J[0,2]=sign*deriv;return Q,J
for vi,bi in enumerate(keep):q,_=shear(np.array(o.data.vertices[vi].co),int(C[bi]));o.data.vertices[vi].co=q
for i,p in enumerate(P):
 q,J=shear(p,int(C[ids[i]]));z['positions'][i]=q*[100,-100,100];B=np.diag([1.,-1.,1.]);J=B@J@B;N=z['normals'][i]@np.linalg.inv(J);N/=np.linalg.norm(N);T=z['tangents'][i]@J.T;T-=N*np.dot(N,T);T/=np.linalg.norm(T);z['normals'][i]=N;z['tangents'][i]=T
np.savez_compressed(r/'Buzz-geometry.npz',**z);o.data.update();save('Buzz');reports['Buzz']={'elbow_outward_max_m':.045,'blend_z_m':[.90,1.52],'scope':'Only upper-arm/elbow/forearm geometry; hand, wrist, shoulder bones, skeleton weights, armor, textures unchanged','deformation':'X shear; determinant1; normals/tangents transformed analytically'}
(r/'author-report.json').write_text(json.dumps(reports,indent=2));print('THREE_MODELS_AUTHORED')

import bpy,numpy as np,json
from pathlib import Path
r=Path('/tmp/toystory-feedback-v3');D=np.load('/workspace/mod-work/skin-fixes-next/BoPeep/geometry.npz');cap=set(np.load('/workspace/mod-work/skin-fixes-next/BoPeep-source.npz')['cape'].tolist());P=D['positions']*[.01,-.01,.01];tris=P[D['indices'][np.array([all(int(i) in cap for i in row) for row in D['source_vertices'][D['indices']]])]]
def surface(x,z):
 hits=[]
 for t in tris:
  A=np.array([[t[1,0]-t[0,0],t[2,0]-t[0,0]],[t[1,2]-t[0,2],t[2,2]-t[0,2]]]);det=np.linalg.det(A)
  if abs(det)<1e-10:continue
  u,v=np.linalg.solve(A,np.array([x-t[0,0],z-t[0,2]]))
  if min(u,v,1-u-v)>-1e-4:hits.append(t[0,1]+u*(t[1,1]-t[0,1])+v*(t[2,1]-t[0,1]))
 if hits:return max(hits)+.0006
 flat=tris.reshape(-1,3);d=(flat[:,0]-x)**2+(flat[:,2]-z)**2;ids=np.argsort(d)[:6];return float(np.average(flat[ids,1],weights=1/(d[ids]+1e-5)))+.0006
bpy.ops.wm.open_mainfile(filepath=str(r/'BoPeep.blend'));o=bpy.data.objects['BoPeep_Skinned'];assert len(o.data.vertices)==5057
rows=[(1.54,.190,.190,.080),(1.49,.198,.175,.090),(1.44,.209,.155,.098),(1.39,.220,.150,.095),(1.34,.233694,.160,.084)]
for j,(z,width,yc,ye) in enumerate(rows):
 for i,t in enumerate(np.linspace(-1,1,17)):
  x=float(t*width);y=float(yc-(yc-ye)*t*t)
  if j==4:y=surface(x,z)
  elif j==3:y=(y+surface(x,z))*.5
  o.data.vertices[4972+j*17+i].co=(x,y,z)
norms=[]
for f in o.data.polygons:
 for li in f.loop_indices:norms.append((0,0,0) if any(i>=4972 for i in f.vertices) else o.data.loops[li].normal[:])
o.data.normals_split_custom_set(norms);o.data.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'BoPeep.blend'),compress=True);(r/'cape-conform-report.json').write_text(json.dumps({'shape':'Curved shoulder wrap; sides and lower edge follow preserved cape surface rather than forming a floating flat board','upper_z_m':1.54,'bottom_z_m':1.34,'bottom_surface_gap_m':.0006,'full_width_top_m':.38,'full_width_bottom_m':.467388,'original_lower_cape':'unmodified'},indent=2));print('CURVED_CAPE_COVER_CONFORMED')

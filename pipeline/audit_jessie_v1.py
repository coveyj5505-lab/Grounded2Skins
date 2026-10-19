"""Read-only source/fitted topology, weights, frames and connected-component audit."""
import bpy,json,sys
from pathlib import Path
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False)
arm=bpy.data.objects['park_jessie_armature'];native=bpy.data.objects['Grounded2_Hoops_189'];report=[]
for name in ['park_jessie_ob0_L0','park_jessie_ob3_L0','park_jessie_ob6_L0']:
 src=bpy.data.objects[name];fit=bpy.data.objects[name+'_Hoops_Skinned'];mesh=src.data;mesh.calc_loop_triangles();p=np.asarray([tuple(src.matrix_world@v.co) for v in mesh.vertices]);q=np.asarray([v.co[:] for v in fit.data.vertices]);tri=np.asarray([t.vertices[:] for t in mesh.loop_triangles]);j=np.zeros((len(p),8),dtype='u2');w=np.zeros((len(p),8));parent=list(range(len(p)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for t in tri:
  for i in t[1:]:a,b=root(int(t[0])),root(int(i));parent[b]=a
 for v in mesh.vertices:
  for k,g in enumerate(v.groups):j[v.index,k]=g.group;w[v.index,k]=g.weight
 labels=np.asarray([root(i) for i in range(len(p))]);edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0);s=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);f=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1);ratio=f/np.maximum(s,1e-10)
 components=[]
 for label in sorted(set(labels),key=lambda x:-np.sum(labels==x)):
  ids=np.flatnonzero(labels==label);counts={}
  for vi in ids:
   for gi,weight in zip(j[vi],w[vi]):
    if weight>0:n=src.vertex_groups[int(gi)].name;counts[n]=counts.get(n,0)+float(weight)
  ee=np.flatnonzero(labels[edges[:,0]]==label)
  components.append({'id':int(label),'vertices':len(ids),'source_bounds':[p[ids].min(0).tolist(),p[ids].max(0).tolist()],'V1_bounds':[q[ids].min(0).tolist(),q[ids].max(0).tolist()],'dominant_source_groups':sorted(counts.items(),key=lambda x:-x[1])[:8],'edge_stretch_max':float(ratio[ee].max()) if len(ee) else None})
 np.savez_compressed(out/(name+'.npz'),source=p,V1=q,triangles=tri,joints=j,weights=w,component=labels)
 report.append({'source':name,'components':components,'group_names':[g.name for g in src.vertex_groups],'source_weight_sum_min_max':[float(w.sum(1).min()),float(w.sum(1).max())],'edge_stretch_percentiles':np.quantile(ratio,[0,.5,.9,.99,1]).tolist(),'nonidentity_source_pose_bones':[b.name for b in arm.pose.bones if np.max(abs(np.asarray(b.matrix_basis)-np.eye(4)))>1e-5]})
bones=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(arm.matrix_world@b.head_local),'tail':list(arm.matrix_world@b.tail_local)} for b in arm.data.bones];target=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local)} for b in native.data.bones]
(out/'audit.json').write_text(json.dumps({'source_bones':bones,'native_bones':target,'meshes':report},indent=2)+'\n');print('Source fitting audit exported')

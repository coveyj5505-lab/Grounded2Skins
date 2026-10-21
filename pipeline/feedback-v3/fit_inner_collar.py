import bpy,numpy as np,json
from PIL import Image
from pathlib import Path
r=Path('/tmp/toystory-feedback-v3');bpy.ops.wm.open_mainfile(filepath=str(r/'BoPeep.blend'));o=bpy.data.objects['BoPeep_Skinned'];im=np.asarray(Image.open('/workspace/mod-work/ue57-migration/bopeep-check-v1/actual-decoded-atlas.png').convert('RGB'))/255;h,w=im.shape[:2];cloth=set();o.data.calc_loop_triangles();triangles=[]
for t in o.data.loop_triangles:
 if all(i>=4972 for i in t.vertices):triangles.append(np.array([o.data.vertices[i].co[:] for i in t.vertices]))
for f in o.data.polygons:
 tex=np.mean([o.data.uv_layers.active.data[i].uv[:] for i in f.loop_indices],0);c=im[int((1-tex[1])*h)%h,int(tex[0]*w)%w];navy=c[0]<.35 and c[1]<.30 and c[2]>c[0]*1.2;lining=c.min()>.72
 if navy or lining:cloth.update(i for i in f.vertices if i<4972)
changed=[]
for i in cloth:
 v=o.data.vertices[i];x,y,z=v.co
 if not (abs(x)<.27 and y>.01 and 1.34<z<1.68):continue
 head=sum(g.weight for g in v.groups if o.vertex_groups[g.group].name=='head_JNT')
 if head>.1:continue
 v.co.z=min(z,1.525);hits=[]
 for t in triangles:
  A=np.array([[t[1,0]-t[0,0],t[2,0]-t[0,0]],[t[1,2]-t[0,2],t[2,2]-t[0,2]]]);det=np.linalg.det(A)
  if abs(det)<1e-10:continue
  u,b=np.linalg.solve(A,[x-t[0,0],v.co.z-t[0,2]])
  if min(u,b,1-u-b)>-1e-4:hits.append(t[0,1]+u*(t[1,1]-t[0,1])+b*(t[2,1]-t[0,1]))
 outer=max(hits) if hits else .085
 v.co.y=min(y,outer-.004)
 for g in o.vertex_groups:g.remove([i])
 o.vertex_groups['spine3_JNT'].add([i],1,'REPLACE');changed.append(i)
o.data.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'BoPeep.blend'),compress=True);(r/'inner-collar-fit.json').write_text(json.dumps({'old_rear_collar_lining_vertices_fitted_under_outer_shoulder_wrap':len(changed),'clearance_m':.004,'rear_cloth_height_limit_m':1.525,'rear_cloth_attachment':'spine3 only','front_body_head_and_lower_cape':'excluded from this correction'},indent=2));print('OLD_REAR_LINING_FITTED',len(changed))

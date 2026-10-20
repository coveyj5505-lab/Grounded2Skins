"""Replace only the broken upper cape sheet, preserving the entire lower cape.
The original topology is archived. No body/hand/skeleton fitting is repeated.
"""
import bpy,numpy as np,json,math,sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False);o=bpy.data.objects['BoPeep_Skinned'];src=bpy.data.objects['BoPeep_Body'];arm=o.find_armature();old=o.data;groupnames=[g.name for g in o.vertex_groups];points=[v.co[:] for v in old.vertices];weights=[[(g.group,g.weight) for g in v.groups] for v in old.vertices];cape={v.index for v in src.data.vertices if v.index<len(points) and any(src.vertex_groups[g.group].name.startswith('e_cape') for g in v.groups)}
copy=o.copy();copy.data=old.copy();copy.name='BoPeep_V3_CompleteCape_PRESERVED';bpy.context.scene.collection.objects.link(copy);copy.hide_render=True;copy.hide_set(True)
kept=[f for f in old.polygons if not (all(i in cape for i in f.vertices) and max(points[i][2] for i in f.vertices)>1.25)];removed=[f.index for f in old.polygons if f not in kept];faces=[tuple(f.vertices) for f in kept];uvs=[old.uv_layers.active.data[i].uv[:] for f in kept for i in f.loop_indices];normals=[old.loops[i].normal[:] for f in kept for i in f.loop_indices];mats=[f.material_index for f in kept];assert len(removed)>0
# Use a verified dark-blue texel in the unchanged original texture.
img=next(n.image for n in old.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image);w,h=img.size;pixels=np.array(img.pixels[:]).reshape(h,w,4);samples=[]
for f in old.polygons:
 if not all(i in cape for i in f.vertices):continue
 uv=np.mean([old.uv_layers.active.data[i].uv[:] for i in f.loop_indices],0);x,y=np.floor(uv*[w,h]).astype(int);x%=w;y%=h;c=pixels[y,x,:3]
 if c[2]>.04 and c[2]>c[0]*1.4 and c[2]>c[1]*1.2:samples.append((float(c.sum()),int(x),int(y)))
assert samples;_,px,py=sorted(samples)[len(samples)//10];uvbase=np.array([(px+.5)/w,(py+.5)/h]);step=np.array([.6/w,.6/h]);start=len(points);rows=8;cols=21;layer=rows*cols
# The flipped, light lining triangles in the upper back look like holes against
# the dark outer cape. Recolor only those back-facing cloth loops using the
# existing dark-blue texel; the lower cape and all skin/arm UVs remain intact.
sourcegroups=[{src.vertex_groups[g.group].name:g.weight for g in v.groups} for v in src.data.vertices]
recolored=[];rigid_collar=set();cursor=0
for f in kept:
 ids=list(f.vertices);q=np.array([points[i] for i in ids]);cloth=all(sum(weight for name,weight in sourcegroups[i].items() if name.startswith('e_cape') or name=='e_chest_m')>.8 for i in ids)
 if q[:,2].min()>1.25 and q[:,2].max()<1.515 and q[:,1].mean()>.025 and abs(q[:,0]).max()<.31:
  uvmean=np.mean([old.uv_layers.active.data[i].uv[:] for i in f.loop_indices],0);tx,ty=np.floor(uvmean*[w,h]).astype(int);color=pixels[ty%h,tx%w,:3]
  is_white=color.min()>.50 and color[2]>=color[0]*.90
  is_blue=color[2]>.04 and color[2]>color[0]*1.25 and color[2]>color[1]*1.1
  if is_white or is_blue:rigid_collar.update(ids)
  if is_white or is_blue:
   for k in range(len(ids)):uvs[cursor+k]=(uvbase+step*np.array([k==1,k==2])).tolist()
   recolored.append(f.index)
 cursor+=len(ids)

for back in [0,.0025]:
 for j in range(rows):
  t=j/(rows-1)
  for i in range(cols):
   u=-1+2*i/(cols-1);width=(1-t)*.235+t*.3035;x=u*width;ytop=.071-.018*u*u;ybottom=.190-1.15*x*x;y=(1-t)*ytop+t*ybottom+back;ztop=1.505-.082*abs(u)**1.6;z=(1-t)*ztop+t*1.234;points.append((x,y,z))
newfaces=[]
for k in range(2):
 for j in range(rows-1):
  for i in range(cols-1):
   a=start+k*layer+j*cols+i;b=a+1;c=b+cols;d=a+cols;newfaces.append((a,b,c,d) if k==0 else (a,d,c,b))
edge=[]
for i in range(cols-1):edge.extend([(start+i,start+i+1),(start+(rows-1)*cols+i+1,start+(rows-1)*cols+i)])
for j in range(rows-1):edge.extend([(start+(j+1)*cols,start+j*cols),(start+j*cols+cols-1,start+(j+1)*cols+cols-1)])
for a,b in edge:newfaces.append((a,b,b+layer,a+layer))
for f in newfaces:
 faces.append(f);mats.append(0)
 for k in range(len(f)):uvs.append((uvbase+step*np.array([k in [1,2],k in [2,3]])).tolist())
mesh=bpy.data.meshes.new('BoPeep_CapeUpper_Replacement');mesh.from_pydata(points,[],faces);mesh.update()
for mat in old.materials:mesh.materials.append(mat)
uv=mesh.uv_layers.new(name=old.uv_layers.active.name)
for d,q in zip(uv.data,uvs):d.uv=q
for f,m in zip(mesh.polygons,mats):f.material_index=m;f.use_smooth=True
o.data=mesh
o.vertex_groups.clear()
for name in groupnames:o.vertex_groups.new(name=name)
for i,row in enumerate(weights):
 for group,weight in row:o.vertex_groups[group].add([i],weight,'REPLACE')
for vi in sorted(rigid_collar):
 for g in list(mesh.vertices[vi].groups):o.vertex_groups[g.group].remove([vi])
 o.vertex_groups['spine3_JNT'].add([vi],1.,'REPLACE')
o.vertex_groups['spine3_JNT'].add(list(range(start,len(points))),1.,'REPLACE');auto=[l.normal[:] for l in mesh.loops];mesh.normals_split_custom_set(normals+auto[len(normals):]);mesh.update()
assert np.array_equal(np.array(points[:start]),np.array([v.co[:] for v in old.vertices]));assert len(arm.data.bones)==192
np.savez_compressed(out/'preservation.npz',retained_source_faces=np.array([f.index for f in kept]),removed_upper_faces=np.array(removed));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'BoPeep-Cape-V4.blend'),compress=True)
(out/'report.json').write_text(json.dumps({'retained_source_vertices_unchanged':start,'removed_upper_cape_triangles':len(removed),'added_upper_vertices':len(points)-start,'added_upper_quads':len(newfaces),'lower_cape':'All original vertices and all faces below1.25m retained with exact UVs/normals/weights','new_upper_sheet':'Closed thin dark-blue back/shoulder panel; lower edge overlaps retained cape at1.234m','upper_back_cloth_vertices_bound_to_torso':len(rigid_collar),'upper_back_cloth_triangles_solid_blue':recolored,'original_complete_cape_preserved':True,'source_texture_pixel':[px,py],'runtime':'PENDING'},indent=2));print('UPPER_CAPE_REPLACED',len(removed))

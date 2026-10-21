import bpy,numpy as np,json
from collections import defaultdict
from pathlib import Path
from PIL import Image
out=Path('/workspace/mod-work/skin-fixes-next');bpy.ops.wm.open_mainfile(filepath=str(out/'BoPeep-Cape-Continuous-Candidate.blend'));o=bpy.data.objects['BoPeep_Skinned'];src=bpy.data.objects['BoPeep_Body'];cape={v.index for v in src.data.vertices if v.index<len(o.data.vertices) and any(src.vertex_groups[g.group].name.startswith('e_cape') for g in v.groups)};pix=np.asarray(Image.open('/workspace/mod-work/bopeep-stage/bopeep-atlas.png').convert('RGB'))/255.;h,w=pix.shape[:2];outer=set();inner=set()
for f in o.data.polygons:
 if not all(i in cape for i in f.vertices):continue
 uv=np.mean([o.data.uv_layers.active.data[i].uv[:] for i in f.loop_indices],0);x,y=(int(uv[0]*w)%w,int((1-uv[1])*h)%h);c=pix[y,x]
 if c[2]>c[0]*1.35 and c[2]>c[1]*1.15:outer.update(f.vertices)
 elif c.min()>.35:inner.update(f.vertices)
for i in outer-inner:o.data.vertices[i].co.y+=.004
for i in inner-outer:o.data.vertices[i].co.y-=.004
# Close source-coincident cape/body seams without moving any body vertices.
weld=defaultdict(list)
for v in src.data.vertices:
 if v.index<len(o.data.vertices):weld[tuple(np.round(np.asarray(src.matrix_world@v.co),5))].append(v.index)
fixed=[]
for ids in weld.values():
 cloth=[i for i in ids if i in cape];body=[i for i in ids if i not in cape]
 if not cloth or not body:continue
 q=np.mean([o.data.vertices[i].co[:] for i in body],0)
 for i in cloth:
  o.data.vertices[i].co=q
  for g in o.vertex_groups:g.remove([i])
  o.vertex_groups['spine3_JNT'].add([i],1,'REPLACE');fixed.append(i)
o.data.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'BoPeep-Cape-Continuous-Candidate.blend'),compress=True);(out/'cape-layer-seams.json').write_text(json.dumps({'outer_vertices':len(outer),'inner_vertices':len(inner),'outer_layer_offset_m':.004,'inner_layer_offset_m':-.004,'body_seam_vertices_rejoined':fixed},indent=2));print('CAPE_LAYER_SEAMS_DONE')

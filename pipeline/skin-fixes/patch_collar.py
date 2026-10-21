import bpy,bmesh,numpy as np,json
from PIL import Image
from scipy.ndimage import uniform_filter
from mathutils import Vector
from pathlib import Path
r=Path('/workspace/mod-work/skin-fixes-next');im=np.asarray(Image.open('/workspace/mod-work/bopeep-stage/bopeep-atlas.png').convert('RGB'))/255
mask=(im[:,:,2]>im[:,:,0]*1.5)&(im[:,:,2]>im[:,:,1]*1.4)&(im[:,:,0]<.2)&(im[:,:,2]>.15)
a=uniform_filter(mask.astype(float),size=13);y,x=np.unravel_index(a.argmax(),a.shape);uv=Vector(((x+.5)/im.shape[1],1-(y+.5)/im.shape[0]));assert a[y,x]>.9
bpy.ops.wm.open_mainfile(filepath=str(r/'BoPeep-Cape-Continuous-Candidate.blend'));o=bpy.data.objects['BoPeep_Skinned'];bm=bmesh.new();bm.from_mesh(o.data);layer=bm.loops.layers.uv.active;deform=bm.verts.layers.deform.verify();g=o.vertex_groups['spine3_JNT'].index;rows=[]
# Small continuous lining beneath the rear collar, not a replacement lower cape.
for z,width in [(1.42,.205),(1.50,.205),(1.58,.185),(1.64,.145),(1.67,.085)]:
 ring=[]
 for t in np.linspace(-1,1,9):
  v=bm.verts.new((float(t*width),float(.105+.032*(1-t*t)),z));v[deform][g]=1;ring.append(v)
 rows.append(ring)
for j in range(len(rows)-1):
 for i in range(8):
  f=bm.faces.new([rows[j][i],rows[j+1][i],rows[j+1][i+1],rows[j][i+1]]);f.material_index=0;f.smooth=True
  for k,l in enumerate(f.loops):l[layer].uv=uv+Vector((.0003*(k in [2,3]),.0003*(k in [1,2])))
bm.to_mesh(o.data);bm.free();o.data.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'BoPeep-Cape-Continuous-Candidate.blend'),compress=True)
(r/'collar-patch.json').write_text(json.dumps({'patch_vertices':45,'patch_quads':32,'attachment':'spine3_JNT only','area':'Rear collar underlay; lower cape unmodified','atlas_uv':list(uv),'atlas_rgb':im[y,x].tolist()},indent=2))
# Fix new forearm's atlas UV to an actual interior skin texel.
mask=(im[:,:,0]>.65)&(im[:,:,1]>.38)&(im[:,:,1]<.7)&(im[:,:,2]>.25)&(im[:,:,2]<.55)&(im[:,:,0]>im[:,:,1]*1.2)
a=uniform_filter(mask.astype(float),size=13);y,x=np.unravel_index(a.argmax(),a.shape);assert a[y,x]>.9;uv=Vector(((x+.5)/im.shape[1],1-(y+.5)/im.shape[0]))
bpy.ops.wm.open_mainfile(filepath=str(r/'Crook-FP-Hand-Upright-Candidate.blend'));o=bpy.data.objects['BoPeep_Skinned'];n=0
for f in o.data.polygons:
 old=np.mean([o.data.uv_layers.active.data[i].uv[:] for i in f.loop_indices],0)
 if abs(old[0]-.805)<.001 and abs(old[1]-.265)<.001:
  for k,li in enumerate(f.loop_indices):o.data.uv_layers.active.data[li].uv=uv+Vector((.0002*(k in [1,2]),.0002*(k in [2,3])))
  n+=1
assert n>0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'Crook-FP-Hand-Upright-Candidate.blend'),compress=True);print('COLLAR_PATCH_AND_SKIN_TEXEL',n,list(uv),im[y,x])

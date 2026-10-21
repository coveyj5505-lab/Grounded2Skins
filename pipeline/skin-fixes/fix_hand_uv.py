import bpy
from mathutils import Vector
p='/workspace/mod-work/skin-fixes-next/Crook-FP-Hand-Upright-Candidate.blend';bpy.ops.wm.open_mainfile(filepath=p);o=bpy.data.objects['BoPeep_Skinned'];n=0
for f in o.data.polygons:
 if all(i>=391 for i in f.vertices) and any(o.data.vertices[i].co.y<-.08001 for i in f.vertices):
  for k,li in enumerate(f.loop_indices):o.data.uv_layers.active.data[li].uv=Vector((.756377,.456512))+Vector((.0001*(k in [1,2]),.0001*(k in [2,3])))
  n+=1
print('FOREARM_MATCHED_EXISTING_PALM_TEXEL',n);assert n>0;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=p,compress=True)

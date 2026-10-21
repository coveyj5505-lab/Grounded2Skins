import bpy,numpy as np,json
from pathlib import Path
r=Path('/tmp/toystory-feedback-v3');bpy.ops.wm.open_mainfile(filepath=str(r/'CrookHand.blend'));o=bpy.data.objects['BoPeep_Skinned']
# Recenter the wrapped handle on the hand, lengthening only the straight
# region above it. The hook/hand/third-person shape is not stretched.
for v in o.data.vertices[:391]:
 z=v.co.z-.20;t=np.clip((z-.10)/.15,0,1);v.co.z=z+.20*t
norms=[]
for f in o.data.polygons:
 for li in f.loop_indices:norms.append((0,0,0) if all(i<391 for i in f.vertices) else o.data.loops[li].normal[:])
o.data.normals_split_custom_set(norms);o.data.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'CrookHand.blend'),compress=True)
import bmesh
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index>=391],context='VERTS');bm.to_mesh(o.data);bm.free();bpy.ops.wm.save_as_mainfile(filepath=str(r/'CrookBare.blend'),compress=True)
(r/'fp-grip-alignment.json').write_text(json.dumps({'handle_recenter_m':-.20,'upper_straight_extension_m':.20,'hook':'Translated rigidly; no scale/shear','hand':'Natural flat source rest; no finger curl','TP_length_and_hook':'unchanged; radial inflation only','FP_placement_candidate_cm':[85,72,-32],'screen_anchor':'92% of viewport width, live projection calibration; FOV90 16:9 preview'},indent=2))

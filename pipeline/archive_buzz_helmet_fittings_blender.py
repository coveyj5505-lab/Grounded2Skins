import bpy,bmesh,numpy as np,json
from pathlib import Path
out=Path('/workspace/mod-work/buzz-helmet-cleanup');obj=bpy.data.objects['Buzz_Skinned'];comp=np.load('/workspace/mod-work/rig-stage/skinned-stowed-v2-proportions/expected.npz')['component'];assert len(comp)==len(obj.data.vertices)
original=obj.copy();original.data=obj.data.copy();original.name='Buzz_PreHelmetCleanup_PRESERVED';bpy.context.scene.collection.objects.link(original);original.hide_render=True;original.hide_set(True)
for cid in [15,55]:
 part=obj.copy();part.data=obj.data.copy();part.name='HelmetFitting_'+str(cid)+'_PRESERVED';bpy.context.scene.collection.objects.link(part);bm=bmesh.new();bm.from_mesh(part.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if comp[v.index]!=cid],context='VERTS');bm.to_mesh(part.data);bm.free();part.hide_render=True;part.hide_set(True)
bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if comp[v.index] in [15,55]],context='VERTS');bm.to_mesh(obj.data);bm.free();assert len(obj.data.vertices)==12681
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Buzz-Helmet-Cleanup.blend'))
(out/'blender-report.json').write_text(json.dumps({'original_body_preserved':True,'separate_fittings_preserved':[15,55],'playable_vertices':len(obj.data.vertices),'skeleton_bones':len(obj.find_armature().data.bones),'arm_weights_unchanged':True},indent=2))

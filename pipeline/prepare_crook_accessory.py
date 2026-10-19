"""Blender: preserve original Bo Peep scene; author separate rigid grip-local crook."""
import bpy,json,hashlib,sys,argparse
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--scale',type=float,default=.16);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=a.source)
original=bpy.data.objects['Crook_Preserved_NOT_EXPORTED'];bpy.context.view_layer.update()
def signature(o):
 m=o.data
 return hashlib.sha256(repr(([tuple(v.co) for v in m.vertices],[tuple(f.vertices) for f in m.polygons],[[tuple(v.uv) for v in layer.data] for layer in m.uv_layers],[list(r) for r in o.matrix_world])).encode()).hexdigest()
source_sig=signature(original);pivot=bpy.data.objects['Crook_AuthoredPivot_Candidate'].matrix_world.translation.copy();arm=bpy.data.objects['Grounded2_Willow_192'];assert len(arm.data.bones)==192
# Only copies and the NEW saved scene are edited; source .blend remains byte-exact.
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render=True;o.hide_set(True)
old=bpy.data.objects.get('BoPeep_Skinned')
if old:old.name='BoPeep_StableBody_Preserved_NOT_EXPORTED'
obj=original.copy();obj.data=original.data.copy();obj.name='BoPeep_Skinned';bpy.context.scene.collection.objects.link(obj)
for modifier in list(obj.modifiers):obj.modifiers.remove(modifier)
obj.parent=None;obj.matrix_world=arm.matrix_world.copy()
for target,source in zip(obj.data.vertices,original.data.vertices):target.co=(original.matrix_world@source.co-pivot)*a.scale
obj.vertex_groups.clear()
for bone in arm.data.bones:obj.vertex_groups.new(name=bone.name)
obj.vertex_groups[0].add(list(range(len(obj.data.vertices))),1.0,'REPLACE')
mod=obj.modifiers.new('Rigid_Root_Reference_Only','ARMATURE');mod.object=arm
obj.hide_viewport=False;obj.hide_render=False;obj.hide_set(False)
obj['attachment_space']='Grip-local, shaft +Z; attach as independent cosmetic component, NOT leader-pose body mesh.'
obj['uniform_source_scale']=a.scale
obj['runtime_status']='NOT SPAWNED OR ATTACHED; component collision/physics/postprocess must be disabled before presentation.'
for layer in bpy.context.view_layer.layer_collection.children:
 if layer.name==obj.users_collection[0].name:layer.exclude=False
obj.data.calc_loop_triangles();assert len(obj.data.vertices)==391;assert len(obj.data.loop_triangles)==590
assert signature(original)==source_sig
points=[v.co for v in obj.data.vertices];lo=[min(v[i] for v in points) for i in range(3)];hi=[max(v[i] for v in points) for i in range(3)]
assert all(len(v.groups)==1 and v.groups[0].group==0 and v.groups[0].weight==1 for v in obj.data.vertices)
images=[]
for image in bpy.data.images:
 if image.source=='FILE':
  if not image.packed_file:
   try:image.pack()
   except RuntimeError:pass
  images.append({'name':image.name,'packed':bool(image.packed_file)})
report={'source':a.source,'original_crook_signature':source_sig,'original_preserved':True,'vertices':391,'triangles':590,'source_pivot_world':list(pivot),'uniform_scale':a.scale,'bounds_local_m':{'min':lo,'max':hi},'height_m':hi[2]-lo[2],'weighting':'All vertices root0 weight1; independent rigid component intended, not a new body rig','native_reference_bones':192,'textures':images,'placement':'Authored e_stick pivot preserved as origin; +Z shaft; size/hand orientation provisional pending actual attachment test','runtime':'NOT TESTED; no skin/package changes'}
bpy.ops.wm.save_as_mainfile(filepath=str(out/'BoPeep-Crook-Accessory-Source.blend'))
(out/'crook-authoring-report.json').write_text(json.dumps(report,indent=2)+'\n');print('CROOK_SOURCE_PASS',report['height_m'])

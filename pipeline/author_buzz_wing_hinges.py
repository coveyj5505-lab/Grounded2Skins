"""Blender authoring prototype only; never edits the native animation skeleton."""
import bpy, json, math, hashlib, argparse, sys
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--candidates',required=True);p.add_argument('--out',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]); out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=a.source)
def signature(o):
    return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(f.vertices) for f in o.data.polygons],[list(r) for r in o.matrix_world])).encode()).hexdigest()
originals={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Wing_')}
col=bpy.data.collections.new('Wing_Folding_PROTOTYPE_NOT_GAME_READY');bpy.context.scene.collection.children.link(col)
panels={r['component']:r for r in json.loads(Path(a.candidates).read_text())['panels']}
rig={}; copies={}; records=[]
# Inner hinges rotate in XZ plane around Y. Outer tips follow the outer panel.
for root,outer,tip,side in [(12,0,1,1),(51,62,72,-1)]:
    for cid,parent in [(root,None),(outer,root)]:
        e=bpy.data.objects.new(f'Wing_Hinge_{cid}_PROVISIONAL',None);col.objects.link(e)
        e.location=panels[cid]['fitted_extended_candidate'];e.empty_display_type='ARROWS';e.empty_display_size=.08
        bpy.context.view_layer.update()
        if parent is not None:
            world=e.matrix_world.copy();e.parent=rig[parent];e.matrix_world=world
        rig[cid]=e
    for cid,hinge in [(root,root),(outer,outer),(tip,outer)]:
        src=bpy.data.objects[f'Wing_{cid}_Extended_Preserved'];obj=src.copy();obj.data=src.data.copy();obj.name=f'Wing_{cid}_FoldingPreview';col.objects.link(obj)
        obj.hide_viewport=False;obj.hide_render=False;obj.hide_set(False)
        # Preserve rest world geometry, remove skin modifier from rigid preview copies only.
        world=src.matrix_world.copy()
        for m in list(obj.modifiers):
            if m.type=='ARMATURE':obj.modifiers.remove(m)
        obj.parent=rig[hinge];obj.matrix_world=world;copies[cid]=obj
    for cid,angle in [(root,side*82),(outer,side*96)]:
        e=rig[cid]; e.rotation_mode='XYZ'
        for frame,deg in [(1,0),(24,angle),(48,0)]:
            e.rotation_euler.y=math.radians(deg);e.keyframe_insert(data_path='rotation_euler',frame=frame)
        for fc in e.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='BEZIER'
        records.append({'component':cid,'pivot':panels[cid]['fitted_extended_candidate'],'axis':'local Y','fold_degrees':angle,'status':'provisional; no backpack clearance certification'})
s=bpy.context.scene;s.frame_start=1;s.frame_end=48
s.timeline_markers.new('EXTENDED',frame=1);s.timeline_markers.new('FOLDED_PROTOTYPE',frame=24);s.timeline_markers.new('DEPLOYED',frame=48)
s.frame_set(1);bpy.context.view_layer.update()
error=0
for cid,obj in copies.items():
    src=bpy.data.objects[f'Wing_{cid}_Extended_Preserved']
    error=max(error,max(((obj.matrix_world@v.co)-(src.matrix_world@w.co)).length for v,w in zip(obj.data.vertices,src.data.vertices)))
assert error<1e-5,error
assert originals=={n:signature(bpy.data.objects[n]) for n in originals}
report={'scope':'Blender mechanical motion prototype; no cooked or runtime changes','source':a.source,'original_signatures':originals,'originals_unchanged':True,'extended_world_error_m':error,'hinges':records,'tip_parenting':{'1':0,'72':62},'native_skeleton_modified':False,'fold_clearance':'UNVERIFIED; panels can intersect backpack or each other. Visibility stow remains the playable baseline.','runtime':'NOT IMPLEMENTED; needs discovered glide state and owned accessory component control','poses':{}}
for frame in [1,24,48]:
    s.frame_set(frame);bpy.context.view_layer.update();points=[o.matrix_world@v.co for o in copies.values() for v in o.data.vertices]
    report['poses'][str(frame)]={'bounds_min':[min(p[i] for p in points) for i in range(3)],'bounds_max':[max(p[i] for p in points) for i in range(3)]}
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/'Buzz-Wing-Hinges-PROTOTYPE.blend'))
(out/'wing-hinge-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('WING_AUTHORING_PASS',error)

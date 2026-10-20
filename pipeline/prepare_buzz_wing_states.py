"""Author independent nested/deployed wing states; preserve accepted body and originals."""
import bpy,sys,argparse,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(exist_ok=False)
bpy.ops.wm.open_mainfile(filepath=str(a.source));arm=bpy.data.objects['Grounded2_Armature_230'];body=bpy.data.objects['Buzz_Skinned']
def signature(o):
 return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(f.vertices) for f in o.data.polygons],[[tuple(u.uv) for u in l.data] for l in o.data.uv_layers],[list(r) for r in o.matrix_world],[[ (g.group,g.weight) for g in v.groups] for v in o.data.vertices])).encode()).hexdigest()
originals={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH'};rest={b.name:[list(r) for r in b.matrix_local] for b in arm.data.bones}
chest=arm.data.bones[208];assert chest.name=='chest_JNT';C=chest.matrix_local.copy();inv=C.inverted();panels=[12,0,1,51,62,72];states={};records={}
col=bpy.data.collections.new('Wing_States_AUTHORED');bpy.context.scene.collection.children.link(col)
for state in ['Deployed','Retracted']:
 points=[];faces=[];uvs=[];slots=[];normals=[];panel_records=[]
 for cid in panels:
  src=bpy.data.objects[f'Wing_{cid}_Extended_Preserved'];src.data.calc_loop_triangles();world=np.array([tuple(src.matrix_world@v.co) for v in src.data.vertices]);lo,hi=world.min(0),world.max(0)
  if state=='Retracted':
   side=1 if cid in [12,0,1] else -1;level=0 if cid in [12,51] else 1 if cid in [0,62] else 2
   # New compact copies only: nested storage layer, compressed X/Z, distinct thin Y layers.
   target_lo=np.array([.008,.195+level*.009,1.34]);target_hi=np.array([.057,.201+level*.009,1.50])
   if side<0:target_lo[0],target_hi[0]=-.057,-.008
   scale=(target_hi-target_lo)/(hi-lo);positions=(world-lo)*scale+target_lo
   T=Matrix.Diagonal((*scale,1));T.translation=Vector(target_lo-scale*lo)
  else:positions=world;T=Matrix.Identity(4)
  offset=len(points);points.extend(positions.tolist());normal_matrix=(T@src.matrix_world).to_3x3().inverted().transposed()
  for tri in src.data.loop_triangles:
   faces.append(tuple(offset+i for i in tri.vertices));slots.append(tri.material_index)
   for loop in tri.loops:
    uvs.append(tuple(src.data.uv_layers.active.data[loop].uv));normals.append(tuple((normal_matrix@src.data.loops[loop].normal).normalized()))
  panel_records.append({'component':cid,'vertices':len(positions),'bounds_min':positions.min(0).tolist(),'bounds_max':positions.max(0).tolist(),'transform':[list(r) for r in T]})
 mesh=bpy.data.meshes.new('Wing_'+state+'_Display');mesh.from_pydata(points,[],faces);mesh.update()
 for mat in body.data.materials:mesh.materials.append(mat)
 mesh.polygons.foreach_set('material_index',slots);mesh.polygons.foreach_set('use_smooth',[True]*len(faces));uv=mesh.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',np.array(uvs).ravel());mesh.normals_split_custom_set(normals)
 o=bpy.data.objects.new('Wings_'+state+'_Display',mesh);col.objects.link(o);o.parent=arm
 for b in arm.data.bones:o.vertex_groups.new(name=b.name)
 o.vertex_groups[208].add(list(range(len(points))),1,'REPLACE');mod=o.modifiers.new('Rigid_Chest','ARMATURE');mod.object=arm
 o.hide_render=state=='Deployed';states[state]=o
 # The export copy is chest-local and rigid root weighted for an independent component attached to chest_JNT.
 export=o.copy();export.data=mesh.copy();export.name='Wings_'+state+'_Export';col.objects.link(export);export.parent=None;export.matrix_world=Matrix.Identity(4)
 for v in export.data.vertices:v.co=inv@v.co
 normal_rotation=inv.to_3x3().inverted().transposed();export.data.normals_split_custom_set([tuple((normal_rotation@Vector(n)).normalized()) for n in normals])
 export.vertex_groups.clear()
 for b in arm.data.bones:export.vertex_groups.new(name=b.name)
 export.vertex_groups[0].add(list(range(len(points))),1,'REPLACE');export.hide_render=True;export.hide_set(True)
 export['attachment_bone']='chest_JNT';export['coordinate_space']='native chest rest-local after standard exporter Y conversion; independent root0 mesh'
 p=np.array(points);records[state]={'vertices':len(points),'triangles':len(faces),'bounds_min':p.min(0).tolist(),'bounds_max':p.max(0).tolist(),'panels':panel_records,'export_rest_reconstruction_max_error_m':max((C@v.co-Vector(points[v.index])).length for v in export.data.vertices)}
 assert records[state]['export_rest_reconstruction_max_error_m']<1e-5
# Check sampled stored surfaces are occluded by the unchanged body from 8 gameplay-relevant horizontal viewpoints.
verts=[body.matrix_world@v.co for v in body.data.vertices];body.data.calc_loop_triangles();tree=BVHTree.FromPolygons(verts,[tuple(t.vertices) for t in body.data.loop_triangles],all_triangles=True)
stored=states['Retracted'];sample=[v.co.copy() for v in stored.data.vertices]+[f.center.copy() for f in stored.data.polygons]
views={}
for dx,dy in [(0,1),(1,0),(-1,0),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
 camera=Vector((dx*4,dy*4,1.4));blocked=0
 for v in sample:
  direction=(v-camera);length=direction.length;hit=tree.ray_cast(camera,direction.normalized(),length-.0001)
  blocked+=hit[0] is not None
 views[f'{dx},{dy}']={'occluded':blocked,'samples':len(sample),'fraction':blocked/len(sample)}
assert originals=={name:signature(bpy.data.objects[name]) for name in originals};assert rest=={b.name:[list(r) for r in b.matrix_local] for b in arm.data.bones}
body.hide_render=False
report={'source':str(a.source),'source_file_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'original_object_signatures':originals,'body_and_originals_unchanged':True,'native_bones_unchanged':230,'bone_rest_hash':hashlib.sha256(json.dumps(rest,sort_keys=True).encode()).hexdigest(),'states':records,'stored_surface_occlusion_samples':views,'scope':'Separate visual state swap, not mechanically accurate hinges; tucked copies compressed/nested inside backpack, six extended originals intact','runtime':'NOT IMPLEMENTED OR TESTED','attachment_bone':'chest_JNT'}
for image in bpy.data.images:
 if image.source=='FILE':assert image.packed_file
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(a.out/'Buzz-Wing-States.blend'),compress=True)
(a.out/'authoring-report.json').write_text(json.dumps(report,indent=2)+'\n');print('WING_STATES_PASS',json.dumps({k:v['fraction'] for k,v in views.items()}))

"""Read-only FBX inspection and packed working copy; no fitting or rig edits."""
import bpy,sys,json,hashlib
from pathlib import Path
import numpy as np
args=sys.argv[sys.argv.index('--')+1:];source,out=map(Path,args);out.mkdir(exist_ok=False)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
fbx=next(source.rglob('*.fbx'));bpy.ops.import_scene.fbx(filepath=str(fbx))
images=[]
files={p.name.casefold():p for p in source.rglob('*') if p.is_file()}
for im in bpy.data.images:
 if im.source!='FILE':continue
 old=im.filepath;name=old.replace('\\','/').split('/')[-1].casefold()
 if name in files:im.filepath=str(files[name]);im.reload();im.pack()
 images.append({'name':im.name,'original_path':old,'resolved_path':im.filepath,'dimensions':list(im.size),'packed':bool(im.packed_file)})
objects=[]
for o in bpy.data.objects:
 item={'name':o.name,'type':o.type,'matrix_world':[list(r) for r in o.matrix_world]}
 if o.type=='MESH':
  m=o.data;m.calc_loop_triangles();p=np.array([v.co[:] for v in m.vertices]);weights=[sum(g.weight for g in v.groups) for v in m.vertices]
  item.update(vertices=len(m.vertices),triangles=len(m.loop_triangles),uv_layers=[v.name for v in m.uv_layers],materials=[m.name if m else None for m in m.materials],vertex_groups=[g.name for g in o.vertex_groups],weighted_vertices=sum(w>0 for w in weights),weight_sum_min_max=[min(weights),max(weights)],mesh_local_bounds=[p.min(0).tolist(),p.max(0).tolist()],modifiers=[{'name':m.name,'type':m.type,'target':m.object.name if m.type=='ARMATURE' and m.object else None} for m in o.modifiers]);np.savez_compressed(out/(o.name.replace('/','_')+'-source.npz'),positions=p,indices=np.array([t.vertices[:] for t in m.loop_triangles]),materials=np.array([t.material_index for t in m.loop_triangles]))
 elif o.type=='ARMATURE':item['bones']=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrix_local':[list(r) for r in b.matrix_local]} for b in o.data.bones]
 objects.append(item)
materials=[]
for m in bpy.data.materials:
 materials.append({'name':m.name,'diffuse_color':list(m.diffuse_color),'textures':[{'node':n.name,'image':n.image.name if n.image else None} for n in m.node_tree.nodes if n.type=='TEX_IMAGE'] if m.use_nodes else []})
report={'source_fbx_sha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),'objects':objects,'images':images,'materials':materials,'actions':[a.name for a in bpy.data.actions],'source_files_changed':False,'Willow_compatibility':'Not yet determined; stock Willow skeletal packages are not in the workspace','crook':'Object/component inspection pending; do not merge any prop into the playable body'}
(out/'inspection.json').write_text(json.dumps(report,indent=2)+'\n');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'BoPeep-source-inspection.blend'),compress=True);print(json.dumps({'meshes':[(o['name'],o.get('vertices'),o.get('triangles')) for o in objects if o['type']=='MESH'],'armatures':[(o['name'],len(o['bones'])) for o in objects if o['type']=='ARMATURE'],'images':images}))

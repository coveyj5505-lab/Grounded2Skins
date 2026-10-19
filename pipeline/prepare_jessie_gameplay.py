"""Combine the three fitted meshes with explicit atlas UVs and temporary eye UVs.
Original source and fitted parts remain preserved, hidden from playable export.
"""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
import numpy as np
atlas,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(exist_ok=False)
parts=sorted([o for o in bpy.data.objects if o.type=='MESH' and o.name.endswith('_Hoops_Skinned')],key=lambda o:o.name);assert len(parts)==3
arm=bpy.data.objects['Grounded2_Hoops_189'];layout=json.loads((atlas/'atlas-layout.json').read_text());positions=[];triangles=[];uvs=[];weights=[];records=[]
for obj in parts:
 mesh=obj.data;mesh.calc_loop_triangles();base=len(positions);positions.extend([v.co[:] for v in mesh.vertices]);weights.extend([{g.group:g.weight for g in v.groups if g.weight>0} for v in mesh.vertices]);eye='ob6_' in obj.name
 if eye:
  source=bpy.data.objects[obj['source_object']];src=np.asarray([tuple(source.matrix_world@v.co) for v in source.data.vertices]);labels=src[:,0]>=0;eye_uv=np.zeros((len(src),2))
  for side in [False,True]:
   ids=np.flatnonzero(labels==side);p=src[ids][:,[0,2]];lo=p.min(0);hi=p.max(0);assert np.all(hi>lo);eye_uv[ids]=(p-lo)/(hi-lo)
 for t in mesh.loop_triangles:
  triangles.append([base+v for v in t.vertices]);x,y,w,h=layout['eyes' if eye else 'body']
  for li in t.loops:
   vertex=mesh.loops[li].vertex_index;u,v=eye_uv[vertex] if eye else mesh.uv_layers.active.data[li].uv
   uvs.append(((x+float(u)*w)/4096,1-(y+(1-float(v))*h)/4096))
 records.append({'part':obj.name,'source':obj['source_object'],'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),'eyes':eye})
 obj.hide_render=True;obj.hide_set(True)
mesh=bpy.data.meshes.new('Jessie_Playable_Atlas_Mesh');mesh.from_pydata(positions,[],triangles);mesh.update();obj=bpy.data.objects.new('Jessie_Skinned',mesh);bpy.context.collection.objects.link(obj);uv=mesh.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',np.asarray(uvs).ravel())
for p in mesh.polygons:p.use_smooth=True
for b in arm.data.bones:obj.vertex_groups.new(name=b.name)
for i,row in enumerate(weights):
 assert abs(sum(row.values())-1)<1e-5
 for j,w in row.items():obj.vertex_groups[j].add([i],w,'REPLACE')
obj.parent=arm;mod=obj.modifiers.new('StockHoopsSkeleton','ARMATURE');mod.object=arm
mat=bpy.data.materials.new('Jessie_Atlas_Preview');mat.use_nodes=True;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(atlas/'Jessie-basecolor-atlas.png'));tex.image.pack();tex.image.use_fake_user=True;bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=.8;mesh.materials.append(mat)
obj['runtime_test']='NOT RUN';obj['source_object']='Combined preserved source parts; see part report';obj['eye_material']='Temporary procedural green iris/sclera texture, not missing original texture recovered'
(out/'parts-and-uvs.json').write_text(json.dumps({'parts':records,'vertices':len(positions),'triangles':len(triangles),'eye_UV':'Front planar projection per original eye sphere; original eye UVs preserved on source','layout':layout},indent=2)+'\n');np.savez_compressed(out/'expected.npz',positions=np.asarray(positions),indices=np.asarray(triangles),loop_uv=np.asarray(uvs))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Jessie-Hoops-gameplay.blend'),compress=True)

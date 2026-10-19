"""Pack the supplied Jessie textures and create a reversible diffuse preview.
Does not fit geometry or change the source rig/weights. FBX material slots have
no texture nodes, so the shared source sheet is an explicitly provisional bind.
"""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
import numpy as np
source,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(exist_ok=False)
images=[]
for path in sorted((source/'textures').glob('*.png')):
 im=bpy.data.images.load(str(path),check_existing=True);im.pack();im.use_fake_user=True;images.append(im)
diffuse=next(i for i in images if 'diffuse' in i.name)
report=[];positions=[]
for o in [x for x in bpy.data.objects if x.type=='MESH']:
 coords=np.asarray([tuple(o.matrix_world@v.co) for v in o.data.vertices]);positions.extend(coords.tolist());o.data.calc_loop_triangles();uv=np.asarray([x.uv[:] for x in o.data.uv_layers.active.data])
 report.append({'object':o.name,'vertices':len(coords),'triangles':len(o.data.loop_triangles),'world_bounds':[coords.min(0).tolist(),coords.max(0).tolist()],'uv_bounds':[uv.min(0).tolist(),uv.max(0).tolist()],'material_triangles':{m.name:sum(t.material_index==i for t in o.data.loop_triangles) for i,m in enumerate(o.data.materials)},'used_groups':sorted({o.vertex_groups[g.group].name for v in o.data.vertices for g in v.groups if g.weight>0})})
 for mat in o.data.materials:
  mat.use_nodes=True;nodes=mat.node_tree.nodes;tex=nodes.new('ShaderNodeTexImage');tex.image=diffuse;bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=.75
  mat['texture_binding']='Provisional shared supplied diffuse sheet; inspect against actual UVs'
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=720;scene.render.resolution_y=840;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard';scene.world.color=(.2,.2,.2)
p=np.asarray(positions);center=Vector((p.min(0)+p.max(0))/2);height=float(np.ptp(p[:,2]));assert height>0
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=height*1.15
for offset,power in [((2,-3,3),500),((-2,1,2),300)]:
 bpy.ops.object.light_add(type='AREA',location=center+Vector(offset)*height);light=bpy.context.object;light.data.energy=power*height**2;light.data.size=height*2;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
# Save before temporary preview cameras and any render-side pose changes.
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Jessie-source-textured.blend'),compress=True)
(out/'source-preparation.json').write_text(json.dumps({'mesh_objects':report,'packed_textures':[i.name for i in images],'geometry_or_rig_changes':False,'material_binding':'Provisional shared diffuse; original FBX unmodified','native_Hoops_binding':'NOT CREATED'},indent=2)+'\n')
for name,direction in [('front',(0,-3,.08)),('back',(0,3,.08)),('side',(3,0,.08))]:
 cam.location=center+Vector(direction)*height;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)

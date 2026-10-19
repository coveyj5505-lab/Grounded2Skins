"""Restore supplied Woody diffuse bindings and preserve non-playable helpers.
No fitting/native rig changes. Detect exact duplicate geometry before hiding it.
"""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False)
helpers=[o for o in bpy.data.objects if o.type=='MESH' and all(m.name.startswith('mmd_tools_rigid_') for m in o.data.materials)]
for o in helpers:o.hide_render=True;o.hide_set(True);o['export_to_game']=False;o['role']='Preserved source MMD physics helper, not playable character geometry'
a=bpy.data.objects['KH3 Woody V3_mesh'];b=bpy.data.objects['KH3 Woody V3_mesh.003']
def fingerprint(o):
 m=o.data;m.calc_loop_triangles();return {'positions':[[float(c) for c in v.co] for v in m.vertices],'triangles':[list(t.vertices) for t in m.loop_triangles],'UVs':[[list(v.uv) for v in layer.data] for layer in m.uv_layers],'weights':[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in m.vertices],'world':[[float(v) for v in row] for row in o.matrix_world]}
identical=fingerprint(a)==fingerprint(b)
if identical:b.hide_render=True;b.hide_set(True);b['export_to_game']=False;b['role']='Exact duplicate geometry/UV/weights/matrix, alternate material name; preserved, excluded from initial export'
images={i.name:i for i in bpy.data.images if i.source=='FILE'};bindings={}
for matname,part in [('22_hat_0','Hat'),('22_hat_0+','Hat'),('22_boots_0','Boots'),('22_clothes_0','Clothes'),('22_shirt_0','Shirt'),('24_hair_0','Hair'),('24_skin_0','Head')]:
 mat=bpy.data.materials[matname];image=images[f'Woody_{part}_D.tga.png'];mat.use_nodes=True;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=.75;bindings[matname]=image.name
# No dedicated eye/teeth map is bundled; preserve and inspect this material.
mat=bpy.data.materials['New '];mat.use_nodes=True;next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'].default_value=(.9,.9,.85,1);mat['status']='Unresolved original eye/mouth material; neutral placeholder for inspection only'
for i in images.values():assert i.packed_file;i.use_fake_user=True
parts=[o for o in bpy.data.objects if o.type=='MESH' and o not in helpers and not o.hide_render];positions=np.asarray([tuple(o.matrix_world@v.co) for o in parts for v in o.data.vertices]);center=Vector((positions.min(0)+positions.max(0))/2);height=float(np.ptp(positions[:,2]))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=720;scene.render.resolution_y=840;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard';scene.world.color=(.2,.2,.2)
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=height*1.35
for delta,power in [((2,-3,3),500),((-2,2,2),350)]:
 bpy.ops.object.light_add(type='AREA',location=center+Vector(delta)*height);light=bpy.context.object;light.data.energy=power*height**2;light.data.size=height*2;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
report={'physics_helpers_preserved_excluded':len(helpers),'duplicate_geometry_exact':identical,'duplicate_excluded_if_exact':b.name if identical else None,'visible_parts':len(parts),'visible_vertices':sum(len(o.data.vertices) for o in parts),'visible_triangles':sum(len(o.data.loop_triangles) for o in parts),'diffuse_bindings':bindings,'packed_images':len(images),'source_geometry_weights_rig_transforms_changed':False,'native_Pete_binding':'NOT CREATED','unresolved_material':'New  (eye/mouth region); no dedicated original texture provided'}
(out/'preparation.json').write_text(json.dumps(report,indent=2)+'\n');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Woody-source-prepared.blend'),compress=True)
for name,direction in [('front',(0,-3,.1)),('back',(0,3,.1))]:
 cam.location=center+Vector(direction)*height;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
print(json.dumps(report),flush=True)

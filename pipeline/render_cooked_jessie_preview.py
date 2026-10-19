import bpy,numpy as np,sys,json
from pathlib import Path
from mathutils import Vector
p=Path(sys.argv[sys.argv.index('--')+1]);d=next(d for d in p.glob('final-mesh-readback-*') if d.is_dir() and json.loads((d/'mesh.json').read_text())['source'].endswith('911395b71b48cf1a00000001'));bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
pos=np.fromfile(d/'positions.f32',dtype='<f4').reshape(-1,3)*[.01,-.01,.01];idx=np.fromfile(d/'indices.u32',dtype='<u4').reshape(-1,3);uv=np.fromfile(d/'uv0.f32',dtype='<f4').reshape(-1,2)
mesh=bpy.data.meshes.new('ReadBack');mesh.from_pydata(pos.tolist(),[],idx[:,::-1].tolist());mesh.update();o=bpy.data.objects.new('Actual cooked Jessie readback',mesh);bpy.context.collection.objects.link(o);layer=mesh.uv_layers.new()
for poly in mesh.polygons:
 poly.use_smooth=True
 for li in poly.loop_indices:
  u,v=uv[mesh.loops[li].vertex_index];layer.data[li].uv=(float(u),float(1-v))
mat=bpy.data.materials.new('Decoded cooked BC3 atlas - emission preview');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(p/'final-decoded-atlas.png'));out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');mat.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);mat.node_tree.links.new(em.outputs[0],out.inputs[0]);mesh.materials.append(mat)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.world.color=(.08,.08,.08);scene.view_settings.view_transform='Standard';scene.render.image_settings.file_format='PNG';center=Vector((pos.min(0)+pos.max(0))/2);height=float(np.ptp(pos[:,2]));camd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camd);bpy.context.collection.objects.link(cam);scene.camera=cam;camd.type='ORTHO';camd.ortho_scale=height*1.18
for name,vec in [('front',(0,-3,.25)),('side',(3,0,.25))]:
 cam.location=center+Vector(vec)*height;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(p/('cooked-readback-'+name+'.png'));bpy.ops.render.render(write_still=True)

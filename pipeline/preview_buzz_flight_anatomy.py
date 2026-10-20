"""Preview actual independently decoded flight candidate streams and atlas."""
import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector
root=Path(sys.argv[sys.argv.index('--')+1]);out=root/'previews';out.mkdir(exist_ok=False);g=dict(np.load(root/'geometry.npz'));p=g['positions']*[.01,-.01,.01];idx=g['indices'];uv=g['uv0'];n=g['normals']*[1,-1,1];n/=np.linalg.norm(n,axis=1,keepdims=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);m=bpy.data.meshes.new('FlightActualCooked');m.from_pydata(p.tolist(),[],idx.tolist());m.update();o=bpy.data.objects.new('Buzz Flight - Actual cooked candidate',m);bpy.context.collection.objects.link(o);layer=m.uv_layers.new()
for f in m.polygons:
 f.use_smooth=True
 for li in f.loop_indices:
  q=uv[m.loops[li].vertex_index];layer.data[li].uv=(float(q[0]),float(1-q[1]))
m.normals_split_custom_set(n[idx].reshape(-1,3).tolist());mat=bpy.data.materials.new('Actual decoded private atlas');mat.use_nodes=True;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(root/'Flight-basecolor-atlas.png'));tex.image.pack();bsdf=next(x for x in mat.node_tree.nodes if x.type=='BSDF_PRINCIPLED');bsdf.inputs['Roughness'].default_value=.8;bsdf.inputs['Specular IOR Level'].default_value=.12;mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);m.materials.append(mat)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.cycles.use_denoising=False;s.render.resolution_x=960;s.render.resolution_y=650;s.render.resolution_percentage=100;s.world.color=(.18,.18,.18);s.view_settings.view_transform='Standard';center=Vector((p.min(0)+p.max(0))/2)
for loc,power in [((3,-4,5),400),((-3,-1,3),280),((1,3,4),280)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.size=4;l.rotation_euler=(center-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=3.2
for name,loc in [('cooked-flight-quarter',(3,-5,3)),('cooked-flight-side',(5,0,1.8)),('flight-front',(0,-5,1.4)),('flight-rear',(0,5,2.5))]:
 cam.location=loc;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Buzz-Flight-Actual-Cooked.blend'),compress=True);print('ACTUAL_COOKED_FLIGHT_PREVIEWS_SAVED')

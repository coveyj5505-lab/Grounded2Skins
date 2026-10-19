import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector
root=Path(sys.argv[sys.argv.index('--')+1]);o=bpy.data.objects['BoPeep_Skinned'];scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=False;scene.render.resolution_x=720;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.world.color=(.3,.3,.3);scene.view_settings.view_transform='Standard';scene.cycles.device='CPU'
for loc,power in [((3,-4,5),500),((-3,-1,3),300),((1,3,4),400)]:
 bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.size=4;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO';regions=np.load(root/'fit-v1/expected.npz')['regions'];p=np.asarray([v.co[:] for v in o.data.vertices])
for name in ['hand_l','hand_r']:
 pts=p[regions==name];center=Vector((pts.min(0)+pts.max(0))/2);camera.data.ortho_scale=.30;camera.location=center+Vector((0,-2,.5));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(root/'poses-v1'/(name+'-closeup.png'));bpy.ops.render.render(write_still=True)
camera.data.ortho_scale=2.55;center=Vector((0,0,1.05));camera.location=(0,5,1.2);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(root/'poses-v1/back-cape.png');bpy.ops.render.render(write_still=True)

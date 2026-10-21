import bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='/tmp/toystory-feedback-v3/CrookHand.blend');o=bpy.data.objects['BoPeep_Skinned']
for x in list(bpy.data.objects):
 if x.type=='MESH':x.hide_render=x!=o
 if x.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(x,do_unlink=True)
for loc in [(2,-3,3),(-2,-1,1)]:
 bpy.ops.object.light_add(type='AREA',location=loc);bpy.context.object.data.energy=120;bpy.context.object.data.size=2
bpy.ops.object.camera_add(location=(-.85,.714,.32));c=bpy.context.object;c.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler();c.data.type='PERSP';c.data.lens=18;c.data.sensor_width=36;s=bpy.context.scene;s.camera=c;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=False;s.render.resolution_x=1280;s.render.resolution_y=720;s.world.color=(.2,.2,.2);s.render.filepath='/tmp/toystory-feedback-v3/Hand-camera-90.png';bpy.ops.render.render(write_still=True)

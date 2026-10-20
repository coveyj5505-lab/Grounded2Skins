"""Neutral CPU previews of isolated wing states; doesn't save or alter source scene."""
import bpy,sys,argparse,json
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--blend',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(exist_ok=False)
bpy.ops.wm.open_mainfile(filepath=a.blend)
for o in list(bpy.data.objects):
 if o.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(o,do_unlink=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.cycles.use_denoising=False;s.cycles.seed=7;s.render.resolution_x=760;s.render.resolution_y=760;s.render.resolution_percentage=100;s.world.color=(.22,.22,.22);s.view_settings.view_transform='Standard'
for loc,power,size in [((-3,3,5),700,4),((3,3,3),500,4),((0,-3,4),450,3)]:
 d=bpy.data.lights.new('WingReviewLight','AREA');d.energy=power;d.size=size;o=bpy.data.objects.new('WingReviewLight',d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('WingReview');cam=bpy.data.objects.new('WingReview',d);s.collection.objects.link(cam);s.camera=cam;d.type='ORTHO'
for state,view,loc,scale in [('Retracted','rear',(0,4,1.2),2.3),('Deployed','rear',(0,4,1.2),2.75),('Retracted','side',(4,0,1.2),2.3),('Deployed','quarter',(2.5,4,1.7),2.75)]:
 for name in ['Retracted','Deployed']:bpy.data.objects['Wings_'+name+'_Display'].hide_render=name!=state
 cam.location=loc;cam.rotation_euler=(Vector((0,.05,1.0))-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=scale
 s.render.filepath=str(a.out/(state+'-'+view+'.png'));bpy.ops.render.render(write_still=True)
print('WING_PREVIEWS_PASS')

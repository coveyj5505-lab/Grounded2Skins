"""Fit the preserved source rig to stock Willow; preserve source and crook.
Blender: --background source.blend --python this.py -- reference.json NEW_OUT
"""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
import numpy as np
ref,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(exist_ok=False)
bones=json.loads(ref.read_text())['meshes'][0]['bones'];assert len(bones)==192
source=bpy.data.objects['BoPeep_Body'];srcarm=source.find_armature();assert srcarm
bpy.context.view_layer.update();sw={b.name:srcarm.matrix_world@b.head_local for b in srcarm.data.bones}
B=Matrix.Diagonal((.01,-.01,.01,1));world=[]
for b in bones:
 x,y,z,w=b['rotation_xyzw'];m=Matrix.LocRotScale(Vector(b['translation_cm']),Quaternion((w,x,y,z)),Vector(b['scale_xyz']));world.append(m if b['parent']<0 else world[b['parent']]@m)
rest=[B@m@B.inverted() for m in world];target={b['name']:m.translation for b,m in zip(bones,rest)}
armdata=bpy.data.armatures.new('Willow_Native_192');arm=bpy.data.objects.new('Grounded2_Willow_192',armdata);bpy.context.collection.objects.link(arm)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for b,m in zip(bones,rest):
 eb=armdata.edit_bones.new(b['name']);eb.length=.015;eb.matrix=m
 if b['parent']>=0:eb.parent=armdata.edit_bones[bones[b['parent']]['name']]
bpy.ops.object.mode_set(mode='OBJECT')
# Each record maps an authored joint segment to its native animation segment.
# Preserve transverse dimensions; only the longitudinal dimension fits length.
spec={
 'e_root':('Root_NSK',None,None),
 'e_root_m':('Hips_JNT','e_spine1_m','spine1_JNT'),
 'e_spine1_m':('spine1_JNT','e_chest_m','spine3_JNT'),
 'e_chest_m':('spine3_JNT','e_neck_m','neck1_JNT'),
 'e_neck_m':('neck1_JNT','e_head_m','head_JNT'),
 'e_head_m':('head_JNT',None,None),
}
for side,label in [('l','Left'),('r','Right')]:
 for a,b,c,d in [('hip','UpperLeg','knee','LowerLeg'),('knee','LowerLeg','ankle','Foot'),('ankle','Foot','toes','Toes'),('scapula','shoulder','shoulder','upperArm'),('shoulder','upperArm','elbow','lowerArm'),('elbow','lowerArm','wrist','hand')]:
  spec[f'e_{a}_{side}']=(f'{side}_{b}_JNT',f'e_{c}_{side}',f'{side}_{d}_JNT')
 spec[f'e_toes_{side}']=(f'{side}_Toes_JNT',None,None)
 spec[f'e_wrist_{side}']=(f'{side}_hand_JNT',f'e_middlefinger1_{side}',f'{label}HandMiddle1_JNT')
 for finger,game in [('middle','Middle'),('index','Index'),('thumb','Thumb')]:
  for n in range(1,4):
   name=f'e_{finger}finger{n}_{side}'
   if name not in sw:continue
   end=f'e_{finger}finger{n+1}_{side}';native=f'{label}Hand{game}{n}_JNT';nend=f'{label}Hand{game}{n+1}_JNT'
   spec[name]=(native,end if end in sw and nend in target else None,nend if end in sw and nend in target else None)
# Cape stays on torso, avoiding accidental arm influence. Bandage follows arm.
for name in sw:
 if name.startswith('e_cape'):spec[name]=spec['e_chest_m']
spec['e_bandage']=spec['e_shoulder_r']
scale=.25
transforms={};mapping={}
for name,(dest,srcend,dstend) in spec.items():
 assert dest in target,(name,dest)
 anchor=name
 if name.startswith('e_cape'):anchor='e_chest_m'
 if name=='e_bandage':anchor='e_shoulder_r'
 rot=Matrix.Identity(3);along=Matrix.Identity(3);ratio=1.
 if srcend:
  a=sw[srcend]-sw[anchor];b=target[dstend]-target[dest];rot=a.rotation_difference(b).to_matrix();ratio=b.length/(a.length*scale)
  u=a.normalized();along=Matrix.Identity(3)+(ratio-1)*Matrix([[u[i]*u[j] for j in range(3)] for i in range(3)])
 # The head is deliberately uniform: no facial-landmark anisotropic scaling.
 transforms[name]=(target[dest],rot@along*scale,sw[anchor]);mapping[name]=dest
positions=[];weights=[];special=[]
for v in source.data.vertices:
 p=source.matrix_world@v.co;acc=Vector();total=0.;native={}
 for g in v.groups:
  if g.weight<=0:continue
  name=source.vertex_groups[g.group].name
  if name.startswith('banjnt'):
   name='e_ankle_l' if p.x>=0 else 'e_ankle_r'
  assert name in transforms,(v.index,name)
  dest,m,origin=transforms[name];acc+=(dest+m@(p-origin))*g.weight;total+=g.weight
  idx=next(b['index'] for b in bones if b['name']==mapping[name]);native[idx]=native.get(idx,0)+g.weight
 assert total>0
 positions.append(tuple(acc/total));weights.append({i:w/total for i,w in native.items()})
mesh=source.data.copy();mesh.name='BoPeep_Willow_Skinned_Mesh';obj=bpy.data.objects.new('BoPeep_Skinned',mesh);bpy.context.collection.objects.link(obj)
for v,p in zip(mesh.vertices,positions):v.co=p
# Existing FBX groups remain on the preserved source only.
obj.vertex_groups.clear()
for b in bones:obj.vertex_groups.new(name=b['name'])
for vi,row in enumerate(weights):
 for i,w in row.items():obj.vertex_groups[i].add([vi],w,'REPLACE')
obj.parent=arm;mod=obj.modifiers.new('Native_Willow_Animation_Skeleton','ARMATURE');mod.object=arm
for p in mesh.polygons:p.use_smooth=True
mesh.update();obj['game_test']='NOT RUN';obj['fit']='Source semantic weights; uniform head and transverse scale; longitudinal limb fit';obj['crook_exported']=False
source.hide_render=True;source.hide_set(True);srcarm.hide_render=True;srcarm.hide_set(True)
arm.show_in_front=True
for image in bpy.data.images:
 if image.source=='FILE':assert image.packed_file
# Store expected native rest positions, not Blender display bone lengths.
np.savez_compressed(out/'expected.npz',positions=np.asarray(positions),joints=np.asarray([[i for i in row]+[0]*(8-len(row)) for row in weights],dtype='u2'),weights=np.asarray([[w for w in row.values()]+[0]*(8-len(row)) for row in weights],dtype='f4'))
report={'bones':len(bones),'vertices':len(mesh.vertices),'triangles':sum(len(p.vertices)-2 for p in mesh.polygons),'material_slots':len(mesh.materials),'source_world_uniform_scale':scale,'mapping':mapping,'segment_longitudinal_ratios':{k:float((m[1].determinant()/scale**3)) for k,m in transforms.items()},'crook_preserved':bpy.data.objects.get('Crook_Preserved_NOT_EXPORTED') is not None,'game_test':'NOT RUN'}
(out/'rig-report.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'BoPeep-Willow-skinned.blend'),compress=True)
print(json.dumps(report),flush=True)

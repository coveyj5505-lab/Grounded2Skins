"""Source-weight anatomical fitting to verified stock Hoops; new outputs only.
Preserve original source and use a common rigid head transform for facial/hat/
braid groups. Terminal finger segments inherit their preceding segment frame.
"""
import bpy,json,sys
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
import numpy as np
ref,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(exist_ok=False)
bones=json.loads(ref.read_text())['meshes'][0]['bones'];assert len(bones)==189
sourcearm=bpy.data.objects['park_jessie_armature'];sources=[o for o in bpy.data.objects if o.type=='MESH'];bpy.context.view_layer.update();sw={b.name:sourcearm.matrix_world@b.head_local for b in sourcearm.data.bones}
B=Matrix.Diagonal((.01,-.01,.01,1));world=[]
for b in bones:
 x,y,z,w=b['rotation_xyzw'];m=Matrix.LocRotScale(Vector(b['translation_cm']),Quaternion((w,x,y,z)),Vector(b['scale_xyz']));world.append(m if b['parent']<0 else world[b['parent']]@m)
rest=[B@m@B.inverted() for m in world];target={b['name']:m.translation for b,m in zip(bones,rest)};index={b['name']:b['index'] for b in bones}
armdata=bpy.data.armatures.new('Hoops_Stock_189');arm=bpy.data.objects.new('Grounded2_Hoops_189',armdata);bpy.context.collection.objects.link(arm);bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for b,m in zip(bones,rest):
 eb=armdata.edit_bones.new(b['name']);eb.length=.015;eb.matrix=m
 if b['parent']>=0:eb.parent=armdata.edit_bones[bones[b['parent']]['name']]
bpy.ops.object.mode_set(mode='OBJECT')
spec={'Bip001':('Hips_JNT',None,None),'Bip001 Pelvis':('Hips_JNT','Bip001 Spine','spine1_JNT'),'Bip001 Spine':('spine1_JNT','Bip001 Spine1','spine2_JNT'),'Bip001 Spine1':('spine2_JNT','Bip001 Spine2','spine3_JNT'),'Bip001 Spine2':('spine3_JNT','Bip001 Neck','neck3_JNT'),'Bip001 Neck':('neck3_JNT','Bip001 Head','head_JNT'),'Bip001 Head':('head_JNT',None,None)}
for side,short,label in [('L','l','Left'),('R','r','Right')]:
 prefix=f'Bip001 {side} '
 for a,b,c,d in [('Clavicle','shoulder','UpperArm','upperArm'),('UpperArm','upperArm','Forearm','lowerArm'),('Forearm','lowerArm','Hand','hand'),('Thigh','UpperLeg','Calf','LowerLeg'),('Calf','LowerLeg','Foot','Foot'),('Foot','Foot','Toe0','Toes')]:spec[prefix+a]=(f'{short}_{b}_JNT',prefix+c,f'{short}_{d}_JNT')
 spec[prefix+'Hand']=(f'{short}_hand_JNT',prefix+'Finger2',f'{label}HandMiddle1_JNT');spec[prefix+'Toe0']=(f'{short}_Toes_JNT',None,None)
 for digit,game in enumerate(['Thumb','Index','Middle','Ring','Pinky']):
  for seg,suffix in enumerate(['','1','2'],1):
   name=prefix+f'Finger{digit}{suffix}';end=prefix+f'Finger{digit}'+('1' if seg==1 else '2');spec[name]=(f'{label}Hand{game}{seg}_JNT',end if seg<3 else None,f'{label}Hand{game}{seg+1}_JNT' if seg<3 else None)
def frame(direction):
 u=direction.normalized();v=Vector((0,-1,0));v-=u*v.dot(u)
 if v.length<1e-5:v=Vector((0,0,1));v-=u*v.dot(u)
 v.normalize();w=u.cross(v);return Matrix((u,v,w)).transposed()
transforms={};mapping={};ratios={}
for name,(dest,end,dend) in spec.items():
 assert dest in target,(name,dest)
 m=Matrix.Identity(3);ratio=1.
 if end:
  a=sw[end]-sw[name];b=target[dend]-target[dest];ratio=b.length/a.length;u=a.normalized();stretch=Matrix.Identity(3)+(ratio-1)*Matrix([[u[i]*u[j] for j in range(3)] for i in range(3)]);m=frame(b)@frame(a).transposed()@stretch
 elif 'Finger' in name:
  parent=sourcearm.data.bones[name].parent.name;m=transforms[parent][1].copy()
 elif name.endswith('Toe0'):
  m=transforms[sourcearm.data.bones[name].parent.name][1].copy()
 transforms[name]=(target[dest],m,sw[name]);mapping[name]=dest;ratios[name]=ratio
weighted_source={o.vertex_groups[g.group].name for o in sources for v in o.data.vertices for g in v.groups if g.weight>0}
# All facial/hat/ponytail helpers use the same head-space fit, not helper pivots.
for b in sourcearm.data.bones:
 if b.name in transforms:continue
 p=b.parent
 while p and p.name not in transforms:p=p.parent
 if p is None:
  assert b.name not in weighted_source,('Unmapped weighted root',b.name)
  transforms[b.name]=(target['Root_NSK'],Matrix.Identity(3),sw[b.name]);mapping[b.name]='Root_NSK'
 else:transforms[b.name]=transforms[p.name];mapping[b.name]=mapping[p.name]
objects=[]
for source in sources:
 mesh=source.data.copy();obj=bpy.data.objects.new(source.name+'_Hoops_Skinned',mesh);bpy.context.collection.objects.link(obj);obj.vertex_groups.clear()
 for b in bones:obj.vertex_groups.new(name=b['name'])
 used=set();maxinf=0
 for v in source.data.vertices:
  p=source.matrix_world@v.co;acc=Vector();total=0.;row={}
  for g in v.groups:
   if g.weight<=0:continue
   name=source.vertex_groups[g.group].name;dest,m,origin=transforms[name];acc+=(dest+m@(p-origin))*g.weight;total+=g.weight;i=index[mapping[name]];row[i]=row.get(i,0)+g.weight
  assert total>0;mesh.vertices[v.index].co=acc/total
  for i,w in row.items():obj.vertex_groups[i].add([v.index],w/total,'REPLACE');used.add(i)
  maxinf=max(maxinf,len(row))
 assert maxinf<=8
 obj.parent=arm;mod=obj.modifiers.new('Stock_Hoops_Skeleton','ARMATURE');mod.object=arm;obj['runtime_test']='NOT RUN';obj['source_object']=source.name
 mesh.update();source.hide_render=True;source.hide_set(True);objects.append({'name':obj.name,'source':source.name,'vertices':len(mesh.vertices),'triangles':sum(len(p.vertices)-2 for p in mesh.polygons),'used_bones':sorted(used),'max_influences':maxinf})
sourcearm.hide_render=True;sourcearm.hide_set(True);arm.show_in_front=True
for image in bpy.data.images:
 if image.source=='FILE':
  assert image.packed_file
  image.use_fake_user=True
report={'native_bones':189,'source_bones':163,'objects':objects,'mapping':mapping,'segment_length_ratios':ratios,'head_fit':'Common uniform world-space head transform; no facial shaping','source_preserved':True,'textures':'Provisional diffuse; eye material unresolved','runtime_test':'NOT RUN'}
(out/'rig-report.json').write_text(json.dumps(report,indent=2)+'\n');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Jessie-Hoops-skinned.blend'),compress=True);print(json.dumps({'bones':189,'objects':objects}),flush=True)

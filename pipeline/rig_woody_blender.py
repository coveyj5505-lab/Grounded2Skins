"""First proportion-conscious Woody fit to independently decoded stock Pete.
New outputs only. Keep source parts/rig/maps, rigid face/hat and coherent limb
fields. This is a review rig, not a claim of cooked or runtime compatibility.
"""
import bpy,bmesh,json,sys
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
import numpy as np

ref,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(exist_ok=False)
bones=json.loads(ref.read_text())['meshes'][0]['bones'];assert len(bones)==188
sourcearm=bpy.data.objects['KH3 Woody V3_arm'];bpy.context.view_layer.update()
sources=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]
assert len(sources)==9
sw={b.name:np.asarray(sourcearm.matrix_world@b.head_local,dtype=float) for b in sourcearm.data.bones}
B=Matrix.Diagonal((.01,-.01,.01,1));world=[]
for b in bones:
 x,y,z,w=b['rotation_xyzw'];m=Matrix.LocRotScale(Vector(b['translation_cm']),Quaternion((w,x,y,z)),Vector(b['scale_xyz']));world.append(m if b['parent']<0 else world[b['parent']]@m)
rest=[B@m@B.inverted() for m in world];nw={b['name']:np.asarray(m.translation) for b,m in zip(bones,rest)};index={b['name']:b['index'] for b in bones}
data=bpy.data.armatures.new('Pete_Stock_188');arm=bpy.data.objects.new('Grounded2_Pete_188',data);bpy.context.collection.objects.link(arm);bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for b,m in zip(bones,rest):
 e=data.edit_bones.new(b['name']);e.length=.015;e.matrix=m
 if b['parent']>=0:e.parent=data.edit_bones[bones[b['parent']]['name']]
bpy.ops.object.mode_set(mode='OBJECT')
mapping=dict(zip(['bip_pelvis','hips','bip_spine_0','bip_spine_1','bip_spine_2','bip_neck','bip_head'],['Hips_JNT','Hips_JNT','spine1_JNT','spine2_JNT','spine3_JNT','neck3_JNT','head_JNT']))
for side,short in [('L','l'),('R','r')]:
 for src,dst in [('collar','shoulder'),('upperArm','upperArm'),('lowerArm','lowerArm'),('hand','hand'),('hip','UpperLeg'),('knee','LowerLeg'),('foot','Foot'),('toe','Toes')]:mapping[f'bip_{src}_{side}']=f'{short}_{dst}_JNT'
 # Preserve source hands as doll shapes initially, rather than force each
 # finger onto the different native finger lengths/orientations.
 for b in sourcearm.data.bones:
  if b.name.startswith(tuple('bip_'+n+'_' for n in ['thumb','index','middle','ring','pinky'])) and b.name.endswith((side,side+'_end')):mapping[b.name]=f'{short}_hand_JNT'
for b in sourcearm.data.bones:
 if b.name in mapping:continue
 if b.name.startswith('leg left thigh adj'):mapping[b.name]='l_UpperLeg_JNT'
 elif b.name.startswith('leg right thigh adj'):mapping[b.name]='r_UpperLeg_JNT'
 else:
  parent=b.parent
  while parent and parent.name not in mapping:parent=parent.parent
  if parent:mapping[b.name]=mapping[parent.name]
weighted={o.vertex_groups[g.group].name for o in sources for v in o.data.vertices for g in v.groups if g.weight>0}
assert weighted<=mapping.keys(),sorted(weighted-mapping.keys())
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def rotate(a,b):return np.asarray(Vector(a.tolist()).rotation_difference(Vector(b.tolist())).to_matrix())
def segment(p,a,b,A,B,width):
 d=b-a;t=(p-a)@d/(d@d);return A+t*(B-A)+width*(rotate(d,B-A)@(p-a-t*d))
def mix(a,b,t):
 r={k:v*(1-t) for k,v in a.items()}
 for k,v in b.items():r[k]=r.get(k,0)+v*t
 return {k:v for k,v in r.items() if v>1e-7}
hip=sw['bip_pelvis'];H=nw['Hips_JNT'];width=1.35;zscale=(nw['head_JNT'][2]-H[2])/(sw['bip_head'][2]-hip[2])
points=[];rows=[];regions=[];parts=[];head_count=0
for source in sources:
 start=len(points)
 for v in source.data.vertices:
  p=np.asarray(source.matrix_world@v.co,dtype=float);orig={source.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0};total=sum(orig.values());assert total>0;orig={n:w/total for n,w in orig.items()};row={}
  for n,w in orig.items():row[index[mapping[n]]]=row.get(index[mapping[n]],0)+w
  head=sum(w for n,w in orig.items() if mapping[n]=='head_JNT')
  if head>.999:
   q=nw['head_JNT']+1.30*(p-sw['bip_head']);row={index['head_JNT']:1};region='head';head_count+=1
  else:
   q=H+(p-hip)*[width,width,zscale];region='torso'
   for side,short in [('L','l'),('R','r')]:
    upper,lower,hand=[f'{short}_{n}_JNT' for n in ['upperArm','lowerArm','hand']]
    amount=sum(w for n,w in orig.items() if mapping[n] in [upper,lower,hand]);blend=smooth(amount)
    if blend>0:
     a,b,c=[sw[f'bip_{n}_{side}'] for n in ['upperArm','lowerArm','hand']];A,C,D=[nw[n] for n in [upper,lower,hand]];d=b-a;elbow=smooth((((p-a)@d/(d@d))-.75)/.5)
     limb=(1-elbow)*segment(p,a,b,A,C,1.35)+elbow*segment(p,b,c,C,D,1.35)
     handblend=smooth(sum(w for n,w in orig.items() if mapping[n]==hand))
     if handblend:
      finger=sw[f'bip_middle_0_{side}'];label='Left' if side=='L' else 'Right';hp=D+1.35*(rotate(finger-c,nw[f'{label}HandMiddle1_JNT']-D)@(p-c));limb=(1-handblend)*limb+handblend*hp;row=mix(row,{index[hand]:1},handblend)
     q=(1-blend)*q+blend*limb;region='hand' if handblend>.5 else 'arm'
   # Common leg field applies to all clothing meshes, using anatomical
   # source weights to prevent low T-pose arms being classified as legs.
   legamount=sum(w for n,w in orig.items() if any(mapping[n]==f'{short}_{part}_JNT' for short in ['l','r'] for part in ['UpperLeg','LowerLeg','Foot','Toes']))
   if legamount>.01:
    side,short=('L','l') if p[0]>hip[0] else ('R','r');a,b,c=[sw[f'bip_{n}_{side}'] for n in ['hip','knee','foot']];A,C,D=[nw[f'{short}_{n}_JNT'] for n in ['UpperLeg','LowerLeg','Foot']];knee=smooth((b[2]+.065-p[2])/.13)
    limb=(1-knee)*segment(p,a,b,A,C,1.35)+knee*segment(p,b,c,C,D,1.35);legrow={index[f'{short}_UpperLeg_JNT']:1-knee,index[f'{short}_LowerLeg_JNT']:knee};ankle=smooth((c[2]+.04-p[2])/.08)
    if ankle:
     foot=segment(p,c,sw[f'bip_toe_{side}'],D,nw[f'{short}_Toes_JNT'],1.25);limb=(1-ankle)*limb+ankle*foot;legrow=mix(legrow,{index[f'{short}_Foot_JNT']:1},ankle)
    blend=smooth(legamount);q=(1-blend)*q+blend*limb;row=mix(row,legrow,blend);region='leg'
   if head>0:q=(1-head)*q+head*(nw['head_JNT']+1.30*(p-sw['bip_head']))
  row={k:w for k,w in row.items() if w>1e-7};s=sum(row.values());row={k:w/s for k,w in row.items()};assert len(row)<=8
  points.append(q);rows.append(row);regions.append(region)
 mesh=source.data.copy();bm=bmesh.new();bm.from_mesh(mesh);deform=bm.verts.layers.deform.active
 if deform:
  for bv in bm.verts:bv[deform].clear()
 bm.to_mesh(mesh);bm.free();o=bpy.data.objects.new(source.name+'_Pete',mesh);bpy.context.collection.objects.link(o);o.vertex_groups.clear()
 # Copied FBX shape-key Basis coordinates otherwise override fitted vertices.
 # Clear only this playable copy; originals retain every source shape key.
 if o.data.shape_keys:o.shape_key_clear()
 for b in bones:o.vertex_groups.new(name=b['name'])
 for v,q,row in zip(mesh.vertices,points[start:],rows[start:]):
  v.co=q
  for i,w in row.items():o.vertex_groups[i].add([v.index],w,'REPLACE')
 mesh.update();o.parent=arm;mod=o.modifiers.new('Verified_stock_Pete','ARMATURE');mod.object=arm;o['source_object']=source.name;source.hide_render=True;source.hide_set(True);parts.append(o)
sourcearm.hide_set(True);sourcearm.hide_render=True
# Combine copies only, retaining original source parts and material assignments.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();obj=bpy.context.object;obj.name='Woody_Skinned';arm.show_in_front=True
assert len(obj.data.vertices)==32379
assert [g.name for g in obj.vertex_groups]==[b['name'] for b in bones]
for v in obj.data.vertices:assert abs(sum(g.weight for g in v.groups)-1)<1e-5
for im in bpy.data.images:
 if im.source=='FILE':assert im.packed_file;im.use_fake_user=True
report={'stock_bones':188,'source_bones':290,'vertices':len(obj.data.vertices),'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),'materials':[m.name for m in obj.data.materials],'mapping':mapping,'head_uniform_scale':1.30,'head_rigid_vertices':head_count,'torso_width_scale':width,'torso_height_scale':zscale,'limb_width_scale':1.35,'hand_policy':'Source doll silhouette rigid to native hand; fine finger articulation deferred','geometry_stage':'First review fit, not packaged','source_preserved':True,'runtime_test':'NOT RUN'}
(out/'rig-report.json').write_text(json.dumps(report,indent=2)+'\n');np.savez_compressed(out/'fit.npz',positions=points,regions=regions);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Woody-Pete-review.blend'),compress=True)
print(json.dumps({k:v for k,v in report.items() if k!='mapping'}),flush=True)
